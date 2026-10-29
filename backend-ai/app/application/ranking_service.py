"""Ranking application service reusing MatchingService with bounded concurrency."""

import asyncio
import time

from app.application.matching_service import MatchingService
from app.application.semantic_representation import (
    build_cv_semantic_text,
    build_job_semantic_text,
)
from app.contracts.common import ResponseMeta
from app.contracts.matching import (
    MATCH_RESULT_CONTRACT_VERSION,
    CandidateItem,
    CandidateRankRequest,
    CandidateRankResponse,
    MatchResult,
    RankedCandidateItem,
)
from app.core.exceptions import ProviderError
from app.observability.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)

# Maximum batch size when chunking candidate CV embedding requests
CANDIDATE_EMBEDDING_BATCH_SIZE = 20


class RankingService:
    """Orchestrates candidate ranking by reusing MatchingService with bounded concurrency."""

    def __init__(self, matching_service: MatchingService, concurrency_limit: int = 5) -> None:
        self.matching_service = matching_service
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def _match_single_candidate(
        self,
        candidate: CandidateItem,
        req: CandidateRankRequest,
        precomputed_job_embedding: list[float] | None = None,
        precomputed_cv_embedding: list[float] | None = None,
    ) -> tuple[str, MatchResult]:
        """Evaluate a single candidate against the job posting under concurrency semaphore."""
        async with self.semaphore:
            # Candidate Ranking disables LLM explanation (generate_explanation=False) to ensure zero LLM calls
            result = await self.matching_service.match(
                cv=candidate.cv,
                job=req.job,
                generate_explanation=False,
                precomputed_job_embedding=precomputed_job_embedding,
                precomputed_cv_embedding=precomputed_cv_embedding,
            )
            return candidate.candidate_id, result

    async def rank_candidates(self, req: CandidateRankRequest) -> CandidateRankResponse:
        """
        Rank candidates for a given job posting:
        1. When matching-v1-experimental is active:
           - Embeds the target Job semantic text EXACTLY ONCE per ranking request.
           - Embeds Candidate CV semantic texts in bounded batches (preserving candidate order).
           - Job semantic text is NEVER re-embedded for every candidate or every batch.
        2. When matching-v0 is active:
           - Makes ZERO embedding calls.
        3. Evaluates all candidates through Matching Engine with generate_explanation=False (ZERO LLM calls).
        4. Sorts results descending by MatchScore.
        5. Assigns ordinal ranks and attaches provenance metadata.
        """
        start_time = time.perf_counter()
        correlation_id = correlation_id_ctx.get()

        job_embedding: list[float] | None = None
        cv_embeddings: list[list[float]] | None = None

        # Precompute embeddings if v1 is active and provider is configured
        if self.matching_service.is_v1_active and self.matching_service.embedding_provider:
            embedding_provider = self.matching_service.embedding_provider

            # Invariant: Job semantic representation is embedded EXACTLY ONCE
            job_text = build_job_semantic_text(req.job)
            job_vectors = await embedding_provider.embed_texts([job_text])
            if len(job_vectors) != 1:
                raise ProviderError(
                    f"Embedding provider returned {len(job_vectors)} vectors for 1 requested job text",
                    provider=embedding_provider.provider_name,
                )
            job_embedding = job_vectors[0]

            # Embed Candidate CVs in bounded chunks to respect provider request limits
            cv_texts = [build_cv_semantic_text(c.cv) for c in req.candidates]
            cv_embeddings = []
            for i in range(0, len(cv_texts), CANDIDATE_EMBEDDING_BATCH_SIZE):
                chunk = cv_texts[i : i + CANDIDATE_EMBEDDING_BATCH_SIZE]
                chunk_vectors = await embedding_provider.embed_texts(chunk)
                if len(chunk_vectors) != len(chunk):
                    raise ProviderError(
                        f"Embedding provider returned {len(chunk_vectors)} vectors for "
                        f"{len(chunk)} requested candidate texts",
                        provider=embedding_provider.provider_name,
                    )
                cv_embeddings.extend(chunk_vectors)

        # Evaluate all candidates concurrently under semaphore
        tasks = [
            self._match_single_candidate(
                candidate=c,
                req=req,
                precomputed_job_embedding=job_embedding,
                precomputed_cv_embedding=cv_embeddings[idx] if cv_embeddings else None,
            )
            for idx, c in enumerate(req.candidates)
        ]
        evaluated = await asyncio.gather(*tasks)

        # Sort descending by match_score
        sorted_results = sorted(evaluated, key=lambda item: item[1].match_score, reverse=True)

        ranked_items: list[RankedCandidateItem] = []
        for index, (candidate_id, match_res) in enumerate(sorted_results, start=1):
            ranked_items.append(
                RankedCandidateItem(
                    rank=index,
                    candidate_id=candidate_id,
                    match_result=match_res,
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "Ranked %d candidates for job '%s' (variant=%s, llm=False, elapsed=%.2fms)",
            len(ranked_items),
            req.job.title,
            self.matching_service.algorithm_variant,
            elapsed_ms,
        )

        is_v1 = self.matching_service.is_v1_active
        emb_prov = self.matching_service.embedding_provider

        meta = ResponseMeta(
            contract_version=MATCH_RESULT_CONTRACT_VERSION,
            algorithm_version=self.matching_service.algorithm_variant,
            algorithm_variant=self.matching_service.algorithm_variant,
            schema_version="1.0.0",
            prompt_version="deterministic",
            provider=self.matching_service.llm.provider_name,
            model=self.matching_service.llm.model_name,
            embedding_provider=emb_prov.provider_name if is_v1 and emb_prov else None,
            embedding_model=emb_prov.model_name if is_v1 and emb_prov else None,
            llm_invoked=False,
            explanation_mode="deterministic",
            processing_time_ms=round(elapsed_ms, 2),
            correlation_id=correlation_id,
        )

        return CandidateRankResponse(
            job_title=req.job.title,
            total_evaluated=len(ranked_items),
            ranked_candidates=ranked_items,
            meta=meta,
        )
