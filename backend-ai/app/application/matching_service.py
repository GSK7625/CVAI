"""Matching application service orchestrating hybrid deterministic scoring and LLM explanations."""

import time

from app.application.semantic_representation import (
    build_cv_semantic_text,
    build_job_semantic_text,
)
from app.application.text_sanitization import sanitize_free_text
from app.contracts.common import ResponseMeta
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import (
    MATCH_RESULT_CONTRACT_VERSION,
    MatchExplanation,
    MatchResult,
)
from app.core.exceptions import ProviderError
from app.domain.matching.education_match import calculate_education_match
from app.domain.matching.experience_match import (
    calculate_experience_match,
    calculate_total_experience_years,
)
from app.domain.matching.project_match import evaluate_project_relevance
from app.domain.matching.scoring import (
    MATCHING_ALGORITHM_VERSION,
    MATCHING_V1_ALGORITHM_VERSION,
    compute_overall_match_score,
    compute_overall_match_score_v1,
)
from app.domain.matching.similarity import cosine_similarity, similarity_to_semantic_score
from app.domain.matching.skill_match import calculate_skill_match
from app.observability.logging import correlation_id_ctx, get_logger
from app.ports.embeddings import EmbeddingPort
from app.ports.llm import LlmPort
from app.prompts.match_explanation_v1 import (
    FORBIDDEN_LOW_SCORE_PHRASES,
    MATCH_EXPLANATION_SYSTEM_PROMPT_V1,
    MATCH_EXPLANATION_USER_TEMPLATE_V1,
    build_deterministic_structured_explanation,
    format_explanation_as_text,
    get_score_band,
    validate_explanation_tone,
    validate_grounding,
)

logger = get_logger(__name__)


def _validate_match_explanation(
    explanation: str | MatchExplanation,
    final_score: int,
) -> bool:
    """
    Validate that LLM explanation does not contradict match score.

    Supports both structured MatchExplanation models and legacy raw strings.
    """
    if isinstance(explanation, MatchExplanation):
        return validate_explanation_tone(final_score, explanation)

    if final_score < 60:
        lower_exp = explanation.lower()
        for phrase in FORBIDDEN_LOW_SCORE_PHRASES:
            if phrase in lower_exp:
                return False
    return True


def _build_deterministic_explanation(
    final_score: int,
    matched_skills: list[str],
    missing_skills: list[str],
    total_req_count: int,
    matched_req_count: int,
    exp_cmp: str,
    edu_cmp: str,
    warning: str | None = None,
    is_v1: bool = False,
    skill_score: float = 0.0,
    experience_score: float = 0.0,
    education_score: float = 0.0,
    project_score: float = 0.0,
    semantic_score: float = 0.0,
    missing_preferred_skills: list[str] | None = None,
) -> str:
    """Construct a grounded, informative deterministic explanation with score band label."""
    structured = build_deterministic_structured_explanation(
        final_score=final_score,
        matched_skills=matched_skills,
        missing_required_skills=missing_skills,
        missing_preferred_skills=missing_preferred_skills or [],
        exp_cmp=exp_cmp,
        edu_cmp=edu_cmp,
    )
    return format_explanation_as_text(
        final_score=final_score,
        explanation=structured,
        warning=warning,
        is_v1=is_v1,
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        project_score=project_score,
        semantic_score=semantic_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_req_count=matched_req_count,
        total_req_count=total_req_count,
        exp_cmp=exp_cmp,
        edu_cmp=edu_cmp,
    )


class MatchingService:
    """Core matching engine evaluating candidate CV compatibility with a Job Posting."""

    def __init__(
        self,
        llm: LlmPort,
        embedding_provider: EmbeddingPort | None = None,
        matching_algorithm: str = MATCHING_ALGORITHM_VERSION,
        semantic_mode: str = "integrated",
    ) -> None:
        self.llm = llm
        self.embedding_provider = embedding_provider
        self.matching_algorithm = matching_algorithm
        self.semantic_mode = semantic_mode

    @property
    def is_v1_active(self) -> bool:
        """Return True if matching-v1-experimental algorithm is active."""
        return self.matching_algorithm == MATCHING_V1_ALGORITHM_VERSION

    @property
    def algorithm_variant(self) -> str:
        """Return the active matching algorithm variant identifier."""
        return self.matching_algorithm

    async def match(
        self,
        cv: StructuredCv,
        job: StructuredJob,
        generate_explanation: bool = True,
        precomputed_job_embedding: list[float] | None = None,
        precomputed_cv_embedding: list[float] | None = None,
    ) -> MatchResult:
        """
        Evaluate candidate CV against a Job Posting using multi-criteria scoring.

        When algorithm is 'matching-v0':
        - Uses Skill (50%), Experience (30%), Education (20%).
        - Project relevance is informational only.
        - ZERO embedding calls or vector operations are executed.

        When algorithm is 'matching-v1-experimental':
        - Uses Skill (40%), Experience (20%), Education (10%), Project (10%), Semantic (20%).
        - Generates/uses text embeddings and computes pure domain cosine similarity.
        - Controlled failure if embedding provider fails (no silent fallback).

        When generate_explanation is True:
        - Calls LLM for detailed natural language explanation (llm_invoked=True).
        When generate_explanation is False:
        - Generates deterministic summary without calling LLM (llm_invoked=False).
        """
        start_time = time.perf_counter()
        correlation_id = correlation_id_ctx.get()

        # 1. Candidate skill gathering
        all_candidate_skills = list(cv.skills)
        for tech in cv.technologies:
            if tech not in all_candidate_skills:
                all_candidate_skills.append(tech)
        for proj in cv.projects:
            for p_tech in proj.technologies:
                if p_tech not in all_candidate_skills:
                    all_candidate_skills.append(p_tech)

        # 2. Skill matching
        skill_res = calculate_skill_match(
            candidate_skills=all_candidate_skills,
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills,
        )

        # 3. Experience matching
        candidate_years = calculate_total_experience_years(cv.work_experience)
        exp_res = calculate_experience_match(
            candidate_years=candidate_years,
            required_years=job.minimum_experience_years,
        )

        # 4. Education matching
        candidate_degrees = [edu.degree for edu in cv.education if edu.degree]
        edu_res = calculate_education_match(
            candidate_degrees=candidate_degrees,
            required_education=job.education_requirement,
        )

        # 5. Project relevance evaluation
        proj_res = evaluate_project_relevance(
            projects=cv.projects,
            required_skills=job.required_skills,
            preferred_skills=job.preferred_skills,
        )

        # 6. Overall match score calculation
        effective_algorithm = self.matching_algorithm

        # Calculate baseline v0 scores
        overall_v0 = compute_overall_match_score(
            skill_res=skill_res,
            exp_res=exp_res,
            edu_res=edu_res,
        )

        semantic_score = 0.0
        semantic_similarity_val: float | None = None
        semantic_score_int: int | None = None
        semantic_available = False

        should_invoke_embeddings = (self.semantic_mode == "advisory" and self.embedding_provider is not None) or (
            self.matching_algorithm == MATCHING_V1_ALGORITHM_VERSION and self.semantic_mode != "disabled"
        )

        if should_invoke_embeddings:
            if self.embedding_provider is None:
                raise ProviderError(
                    "Embedding provider is required for matching-v1-experimental",
                    provider="unconfigured",
                )

            try:
                # Resolve embeddings: reuse precomputed if available (e.g. from ranking batch)
                cv_vector = precomputed_cv_embedding
                job_vector = precomputed_job_embedding

                if cv_vector is None or job_vector is None:
                    cv_text = build_cv_semantic_text(cv)
                    job_text = build_job_semantic_text(job)

                    if cv_vector is None and job_vector is not None:
                        vectors = await self.embedding_provider.embed_texts([cv_text])
                        if len(vectors) != 1:
                            raise ProviderError(
                                f"Embedding provider returned {len(vectors)} vectors for 1 requested text",
                                provider=self.embedding_provider.provider_name,
                            )
                        cv_vector = vectors[0]
                    elif cv_vector is not None and job_vector is None:
                        vectors = await self.embedding_provider.embed_texts([job_text])
                        if len(vectors) != 1:
                            raise ProviderError(
                                f"Embedding provider returned {len(vectors)} vectors for 1 requested text",
                                provider=self.embedding_provider.provider_name,
                            )
                        job_vector = vectors[0]
                    else:
                        # Single-match: embed both texts in a single batch call
                        vectors = await self.embedding_provider.embed_texts([cv_text, job_text])
                        if len(vectors) != 2:
                            raise ProviderError(
                                f"Embedding provider returned {len(vectors)} vectors for 2 requested texts",
                                provider=self.embedding_provider.provider_name,
                            )
                        cv_vector = vectors[0]
                        job_vector = vectors[1]

                sim = cosine_similarity(cv_vector, job_vector)
                semantic_score = similarity_to_semantic_score(sim)
                semantic_similarity_val = round(max(0.0, min(1.0, sim)), 4)
                semantic_score_int = round(semantic_score)
                semantic_available = True

            except Exception as exc:
                if self.semantic_mode == "advisory":
                    logger.warning(
                        "Advisory embedding generation failed (%s: %s). "
                        "Continuing with matching-v0 without semantic score.",
                        exc.__class__.__name__,
                        exc,
                    )
                    semantic_available = False
                    semantic_similarity_val = None
                    semantic_score_int = None
                    semantic_score = 0.0
                else:
                    # In integrated mode, embedding failure must fail fast without silent fallback
                    raise

        if self.semantic_mode == "integrated" and self.matching_algorithm == MATCHING_V1_ALGORITHM_VERSION:
            # Integrated mode: blend semantic similarity into v1 final_score
            overall_v1 = compute_overall_match_score_v1(
                skill_res=skill_res,
                exp_res=exp_res,
                edu_res=edu_res,
                proj_res=proj_res,
                semantic_score=semantic_score,
            )
            final_score = overall_v1.final_score
            skill_score = overall_v1.skill_score
            experience_score = overall_v1.experience_score
            education_score = overall_v1.education_score
            project_score = overall_v1.project_score
            effective_algorithm = MATCHING_V1_ALGORITHM_VERSION
        else:
            # Advisory mode or baseline v0: authoritative score is strictly deterministic matching-v0
            final_score = overall_v0.final_score
            skill_score = overall_v0.skill_score
            experience_score = overall_v0.experience_score
            education_score = overall_v0.education_score
            project_score = proj_res.project_score
            effective_algorithm = MATCHING_ALGORITHM_VERSION

        # Check for insufficient job data
        has_skills_req = bool(job.required_skills or job.preferred_skills)
        has_exp_req = job.minimum_experience_years is not None and job.minimum_experience_years > 0.0

        status: str | None = None
        warning: str | None = None

        if not has_skills_req and not has_exp_req:
            logger.warning(
                "Job '%s' lacks sufficient criteria (both skills and experience requirements are missing) "
                "for reliable matching.",
                job.title,
            )
            status = "insufficient_job_data"
            warning = "JD chưa có đủ tiêu chí để chấm độ phù hợp đáng tin cậy."

        # 7. Explanation generation (LLM if requested with deterministic fallback on error or contradiction;
        # deterministic summary for bulk ranking)
        llm_invoked = False
        explanation_mode: str = "deterministic"
        _, score_band_label = get_score_band(final_score)

        clean_job_title = sanitize_free_text(job.title)
        clean_matched_skills = sanitize_free_text(", ".join(skill_res.matched_skills)) or "Không có"
        clean_missing_req = sanitize_free_text(", ".join(skill_res.missing_required_skills)) or "Không có"
        clean_missing_pref = sanitize_free_text(", ".join(skill_res.missing_preferred_skills)) or "Không có"
        clean_exp_cmp = sanitize_free_text(exp_res.comparison_text)
        clean_edu_cmp = sanitize_free_text(edu_res.comparison_text)

        all_matched = skill_res.matched_required_skills + skill_res.matched_preferred_skills
        all_missing = skill_res.missing_required_skills + skill_res.missing_preferred_skills
        clean_evidence = (
            "CV skills: " + ", ".join(all_matched)
            if all_matched
            else "Chưa đủ bằng chứng trong CV để xác nhận."
        )

        semantic_section = ""
        if (self.is_v1_active or self.semantic_mode == "advisory") and self.embedding_provider and semantic_score > 0:
            semantic_section = f"\n- Độ tương đồng ngữ nghĩa (bổ trợ): {semantic_score:.1f}/100"

        explanation_details: MatchExplanation | None = None
        explanation: str | None = None

        if generate_explanation:
            llm_invoked = True
            prompt = MATCH_EXPLANATION_USER_TEMPLATE_V1.format(
                job_title=clean_job_title,
                match_score=final_score,
                score_band_label=score_band_label,
                skill_score=skill_score,
                experience_score=experience_score,
                education_score=education_score,
                semantic_section=semantic_section,
                matched_skills=clean_matched_skills,
                missing_required_skills=clean_missing_req,
                missing_preferred_skills=clean_missing_pref,
                experience_comparison=clean_exp_cmp,
                education_comparison=clean_edu_cmp,
                evidence=clean_evidence,
            )

            try:
                raw_structured = await self.llm.generate_structured(
                    prompt=prompt,
                    response_model=MatchExplanation,
                    system_prompt=MATCH_EXPLANATION_SYSTEM_PROMPT_V1,
                    temperature=0.0,
                )

                if isinstance(raw_structured, MatchExplanation):
                    explanation_obj = raw_structured
                elif isinstance(raw_structured, dict):
                    explanation_obj = MatchExplanation.model_validate(raw_structured)
                elif isinstance(raw_structured, str):
                    import json

                    explanation_obj = MatchExplanation.model_validate(json.loads(raw_structured))
                else:
                    explanation_obj = MatchExplanation.model_validate(raw_structured)

                tone_ok = validate_explanation_tone(final_score, explanation_obj)
                grounding_ok = validate_grounding(
                    explanation=explanation_obj,
                    matched_skills=all_matched,
                    missing_skills=all_missing,
                    missing_required_skills=skill_res.missing_required_skills,
                )

                if not tone_ok or not grounding_ok:
                    logger.warning(
                        "LLM explanation post-validation failed for score %d (tone_ok=%s, grounding_ok=%s). "
                        "Falling back to deterministic structured explanation.",
                        final_score,
                        tone_ok,
                        grounding_ok,
                    )
                    explanation_obj = build_deterministic_structured_explanation(
                        final_score=final_score,
                        matched_skills=all_matched,
                        missing_required_skills=skill_res.missing_required_skills,
                        missing_preferred_skills=skill_res.missing_preferred_skills,
                        exp_cmp=clean_exp_cmp,
                        edu_cmp=clean_edu_cmp,
                    )
                    explanation_mode = "deterministic-fallback"
                else:
                    explanation_mode = "llm"

                explanation_details = explanation_obj
                explanation = format_explanation_as_text(
                    final_score=final_score,
                    explanation=explanation_obj,
                    warning=warning,
                    is_v1=self.is_v1_active,
                    skill_score=skill_score,
                    experience_score=experience_score,
                    education_score=education_score,
                    project_score=project_score,
                    semantic_score=semantic_score,
                    matched_skills=skill_res.matched_skills,
                    missing_skills=skill_res.missing_skills,
                    matched_req_count=skill_res.matched_required_count,
                    total_req_count=skill_res.total_required_count,
                    exp_cmp=clean_exp_cmp,
                    edu_cmp=clean_edu_cmp,
                )

            except Exception as exc:
                logger.warning(
                    "LLM structured explanation failed with %s (%s). Falling back to deterministic explanation.",
                    exc.__class__.__name__,
                    exc,
                )
                explanation_obj = build_deterministic_structured_explanation(
                    final_score=final_score,
                    matched_skills=all_matched,
                    missing_required_skills=skill_res.missing_required_skills,
                    missing_preferred_skills=skill_res.missing_preferred_skills,
                    exp_cmp=clean_exp_cmp,
                    edu_cmp=clean_edu_cmp,
                )
                explanation_details = explanation_obj
                explanation = format_explanation_as_text(
                    final_score=final_score,
                    explanation=explanation_obj,
                    warning=warning,
                    is_v1=self.is_v1_active,
                    skill_score=skill_score,
                    experience_score=experience_score,
                    education_score=education_score,
                    project_score=project_score,
                    semantic_score=semantic_score,
                    matched_skills=skill_res.matched_skills,
                    missing_skills=skill_res.missing_skills,
                    matched_req_count=skill_res.matched_required_count,
                    total_req_count=skill_res.total_required_count,
                    exp_cmp=clean_exp_cmp,
                    edu_cmp=clean_edu_cmp,
                )
                explanation_mode = "deterministic-fallback"
        else:
            # Deterministic concise summary avoiding LLM inference cost and latency during bulk ranking
            explanation_obj = build_deterministic_structured_explanation(
                final_score=final_score,
                matched_skills=all_matched,
                missing_required_skills=skill_res.missing_required_skills,
                missing_preferred_skills=skill_res.missing_preferred_skills,
                exp_cmp=clean_exp_cmp,
                edu_cmp=clean_edu_cmp,
            )
            explanation_details = explanation_obj
            explanation = format_explanation_as_text(
                final_score=final_score,
                explanation=explanation_obj,
                warning=warning,
                is_v1=self.is_v1_active,
                skill_score=skill_score,
                experience_score=experience_score,
                education_score=education_score,
                project_score=project_score,
                semantic_score=semantic_score,
                matched_skills=skill_res.matched_skills,
                missing_skills=skill_res.missing_skills,
                matched_req_count=skill_res.matched_required_count,
                total_req_count=skill_res.total_required_count,
                exp_cmp=clean_exp_cmp,
                edu_cmp=clean_edu_cmp,
            )
            explanation_mode = "deterministic"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "Completed Job Matching (variant=%s, score=%d, matched=%d, missing=%d, llm=%s, mode=%s, elapsed=%.2fms)",
            self.matching_algorithm,
            final_score,
            len(skill_res.matched_skills),
            len(skill_res.missing_skills),
            llm_invoked,
            explanation_mode,
            elapsed_ms,
        )

        emb_prov_name = (
            self.embedding_provider.provider_name if (should_invoke_embeddings and self.embedding_provider) else None
        )
        emb_model_name = (
            self.embedding_provider.model_name if (should_invoke_embeddings and self.embedding_provider) else None
        )

        semantic_mode_val = self.semantic_mode if (should_invoke_embeddings and self.embedding_provider) else None

        meta = ResponseMeta(
            contract_version=MATCH_RESULT_CONTRACT_VERSION,
            algorithm_version=effective_algorithm,
            algorithm_variant=effective_algorithm,
            schema_version="1.0.0",
            prompt_version="v1" if generate_explanation else "deterministic",
            provider=self.llm.provider_name,
            model=self.llm.model_name,
            embedding_provider=emb_prov_name,
            embedding_model=emb_model_name,
            semantic_similarity=semantic_similarity_val,
            semantic_score=semantic_score_int,
            semantic_mode=semantic_mode_val,
            semantic_available=semantic_available if (should_invoke_embeddings and self.embedding_provider) else False,
            llm_invoked=llm_invoked,
            explanation_mode=explanation_mode,  # type: ignore[arg-type]
            processing_time_ms=round(elapsed_ms, 2),
            correlation_id=correlation_id,
        )

        return MatchResult(
            match_score=final_score,
            matched_skills=skill_res.matched_skills,
            missing_skills=skill_res.missing_skills,
            experience_comparison=exp_res.comparison_text,
            education_comparison=edu_res.comparison_text,
            project_domain_relevance=proj_res.relevance_explanation,
            match_explanation=explanation,
            explanation_details=explanation_details,
            status=status,
            warning=warning,
            meta=meta,
        )
