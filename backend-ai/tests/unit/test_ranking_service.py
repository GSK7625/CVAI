"""Unit tests for RankingService sorting and reuse of Matching Engine."""

import pytest

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.cv import EducationItem, ProjectItem, StructuredCv, WorkExperienceItem
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest
from app.core.exceptions import ProviderError
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.embeddings import EmbeddingPort


class SpyLlmProvider(MockLlmProvider):
    """Spy LLM provider recording invocations."""

    def __init__(self) -> None:
        self.generate_text_calls = 0

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.generate_text_calls += 1
        return await super().generate_text(prompt, system_prompt, temperature)


@pytest.mark.asyncio
async def test_ranking_service_sorts_descending():
    """Verify candidates are sorted descending by match score and ranks are 1-based ordinal."""
    llm = MockLlmProvider()
    matching_service = MatchingService(llm=llm)
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Fullstack Developer",
        required_skills=["React", "TypeScript", "Node.js"],
        minimum_experience_years=3.0,
    )

    cv1 = StructuredCv(
        full_name="High Match Candidate",
        skills=["React", "TypeScript", "Node.js", "Docker"],
        work_experience=[{"job_title": "Dev", "years_of_experience": 4.0}],
    )
    cv2 = StructuredCv(
        full_name="Low Match Candidate",
        skills=["Photoshop"],
        work_experience=[{"job_title": "Junior", "years_of_experience": 0.5}],
    )
    cv3 = StructuredCv(
        full_name="Mid Match Candidate",
        skills=["React", "TypeScript"],
        work_experience=[{"job_title": "Dev", "years_of_experience": 2.0}],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-2", cv=cv2),
            CandidateItem(candidate_id="cand-1", cv=cv1),
            CandidateItem(candidate_id="cand-3", cv=cv3),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 3
    assert len(response.ranked_candidates) == 3

    # Verify order: cand-1 (rank 1), cand-3 (rank 2), cand-2 (rank 3)
    assert response.ranked_candidates[0].candidate_id == "cand-1"
    assert response.ranked_candidates[0].rank == 1

    assert response.ranked_candidates[1].candidate_id == "cand-3"
    assert response.ranked_candidates[1].rank == 2

    assert response.ranked_candidates[2].candidate_id == "cand-2"
    assert response.ranked_candidates[2].rank == 3

    # Check strictly descending match_score
    scores = [c.match_result.match_score for c in response.ranked_candidates]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_ranking_service_makes_zero_llm_generate_text_calls():
    """Verify Candidate Ranking disables LLM explanation and makes zero generate_text calls."""
    spy_llm = SpyLlmProvider()
    matching_service = MatchingService(llm=spy_llm)
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python", "FastAPI"])
    candidates = [
        CandidateItem(
            candidate_id=f"cand-{i}",
            cv=StructuredCv(skills=["Python"]),
        )
        for i in range(5)
    ]
    req = CandidateRankRequest(job=job, candidates=candidates)

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 5
    # Strict assertion: ZERO LLM calls made
    assert spy_llm.generate_text_calls == 0
    # Deterministic explanations present
    for rc in response.ranked_candidates:
        assert len(rc.match_result.match_explanation) > 0
        assert "Điểm phù hợp:" in rc.match_result.match_explanation
        assert rc.match_result.meta.algorithm_version == "matching-v0"
        assert rc.match_result.meta.algorithm_variant == "matching-v0"
        assert rc.match_result.meta.schema_version == "1.0.0"
        assert rc.match_result.meta.llm_invoked is False


@pytest.mark.asyncio
async def test_ranking_required_skills_outrank_preferred_skills():
    """Verify candidate matching required skills strictly outranks candidate matching preferred skills."""
    llm = MockLlmProvider()
    matching_service = MatchingService(llm=llm)
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Senior Backend Engineer",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker", "Kubernetes"],
        minimum_experience_years=3.0,
    )

    # Candidate 1: Has required skills (Python, FastAPI), no preferred skills
    cand_1_cv = StructuredCv(
        full_name="Candidate Required Match",
        skills=["Python", "FastAPI"],
        work_experience=[{"job_title": "Backend Dev", "years_of_experience": 3.0}],
    )

    # Candidate 2: Has preferred skills (Docker, Kubernetes), no required skills
    cand_2_cv = StructuredCv(
        full_name="Candidate Preferred Match",
        skills=["Docker", "Kubernetes"],
        work_experience=[{"job_title": "DevOps Dev", "years_of_experience": 3.0}],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-pref", cv=cand_2_cv),
            CandidateItem(candidate_id="cand-req", cv=cand_1_cv),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 2
    # Candidate with required skills must be Rank 1
    assert response.ranked_candidates[0].candidate_id == "cand-req"
    assert response.ranked_candidates[0].rank == 1
    # Candidate with preferred skills only must be Rank 2
    assert response.ranked_candidates[1].candidate_id == "cand-pref"
    assert response.ranked_candidates[1].rank == 2

    # Invariant: Score of required-matched candidate must be strictly greater than preferred-only candidate
    req_score = response.ranked_candidates[0].match_result.match_score
    pref_score = response.ranked_candidates[1].match_result.match_score
    assert req_score > pref_score


@pytest.mark.asyncio
async def test_ranking_experience_outranks_underqualified():
    """Verify candidate with qualified experience ranks above underqualified candidate when skills match."""
    llm = MockLlmProvider()
    matching_service = MatchingService(llm=llm)
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Senior Python Engineer",
        required_skills=["Python", "FastAPI"],
        minimum_experience_years=3.0,
    )

    # Candidate 1: 4.0 years experience (meets/exceeds requirement -> 100% experience score)
    cand_1_cv = StructuredCv(
        full_name="Experienced Candidate",
        skills=["Python", "FastAPI"],
        work_experience=[
            WorkExperienceItem(
                job_title="Backend Dev",
                start_date="2020-01",
                end_date="2024-01",
                years_of_experience=4.0,
            )
        ],
    )

    # Candidate 2: 1.0 year experience (under requirement -> 33.33% experience score)
    cand_2_cv = StructuredCv(
        full_name="Junior Candidate",
        skills=["Python", "FastAPI"],
        work_experience=[
            WorkExperienceItem(
                job_title="Junior Backend Dev",
                start_date="2023-01",
                end_date="2024-01",
                years_of_experience=1.0,
            )
        ],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-junior", cv=cand_2_cv),
            CandidateItem(candidate_id="cand-senior", cv=cand_1_cv),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 2
    # Senior candidate must rank at Rank 1
    assert response.ranked_candidates[0].candidate_id == "cand-senior"
    assert response.ranked_candidates[0].rank == 1
    # Junior candidate must rank at Rank 2
    assert response.ranked_candidates[1].candidate_id == "cand-junior"
    assert response.ranked_candidates[1].rank == 2

    # Verify score separation
    senior_score = response.ranked_candidates[0].match_result.match_score
    junior_score = response.ranked_candidates[1].match_result.match_score
    assert senior_score > junior_score

    # Check experience comparison text parity
    senior_exp_cmp = response.ranked_candidates[0].match_result.experience_comparison
    assert "4.0 năm kinh nghiệm" in senior_exp_cmp
    assert "vượt 1.0 năm" in senior_exp_cmp

    junior_exp_cmp = response.ranked_candidates[1].match_result.experience_comparison
    assert "1.0 năm kinh nghiệm" in junior_exp_cmp
    assert "thiếu khoảng 2.0 năm" in junior_exp_cmp


@pytest.mark.asyncio
async def test_ranking_education_outranks_lower_degree():
    """Verify candidate with required degree ranks above candidate with lower degree when other factors match."""
    llm = MockLlmProvider()
    matching_service = MatchingService(llm=llm)
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Research Scientist",
        required_skills=["Python", "PyTorch"],
        education_requirement="Master",
    )

    # Candidate 1: Master degree (meets requirement -> 100% education score)
    cand_1_cv = StructuredCv(
        full_name="Master Candidate",
        skills=["Python", "PyTorch"],
        education=[EducationItem(degree="Master of Science in AI", institution="University A")],
    )

    # Candidate 2: Bachelor degree (1 level below requirement -> 75% education score)
    cand_2_cv = StructuredCv(
        full_name="Bachelor Candidate",
        skills=["Python", "PyTorch"],
        education=[EducationItem(degree="Bachelor of Science in CS", institution="University B")],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-bachelor", cv=cand_2_cv),
            CandidateItem(candidate_id="cand-master", cv=cand_1_cv),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 2
    # Candidate with Master must rank at Rank 1
    assert response.ranked_candidates[0].candidate_id == "cand-master"
    assert response.ranked_candidates[0].rank == 1
    # Candidate with Bachelor must rank at Rank 2
    assert response.ranked_candidates[1].candidate_id == "cand-bachelor"
    assert response.ranked_candidates[1].rank == 2

    # Score comparison: Master (100% * 20% = 20) vs Bachelor (75% * 20% = 15) -> 5 point delta
    master_score = response.ranked_candidates[0].match_result.match_score
    bachelor_score = response.ranked_candidates[1].match_result.match_score
    assert master_score > bachelor_score

    # Comparison text parity
    master_edu_cmp = response.ranked_candidates[0].match_result.education_comparison
    assert "đáp ứng hoặc vượt" in master_edu_cmp

    bachelor_edu_cmp = response.ranked_candidates[1].match_result.education_comparison
    assert "gần tương đương" in bachelor_edu_cmp


class ConstantEmbeddingProvider(MockEmbeddingProvider):
    """Deterministic embedding provider returning constant unit vectors to isolate semantic score."""

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        # Return identical normalized vector for all texts so semantic score is identical
        return [[1.0] * self._dimension for _ in texts]


@pytest.mark.asyncio
async def test_ranking_project_relevance_under_matching_v1():
    """Verify that under matching-v1, candidate with matching project technologies outranks candidate without.

    Strictly isolates project score: skill, experience, education, and semantic scores are identical.
    """
    llm = MockLlmProvider()
    embedding_provider = ConstantEmbeddingProvider()
    matching_service = MatchingService(
        llm=llm,
        embedding_provider=embedding_provider,
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Python Backend Engineer",
        required_skills=["Python", "FastAPI"],
        minimum_experience_years=2.0,
        education_requirement="Bachelor",
    )

    work_exp = [
        WorkExperienceItem(
            job_title="Backend Developer",
            duration="2022 - 2024",
            years_of_experience=2.0,
        )
    ]

    # Candidate 1: Has matching project technologies (Python, FastAPI) -> 100% project relevance
    cand_1_cv = StructuredCv(
        full_name="Candidate With Projects",
        skills=["Python", "FastAPI"],
        work_experience=work_exp,
        education=[EducationItem(degree="Bachelor", institution="Uni A")],
        projects=[ProjectItem(name="API Service", technologies=["Python", "FastAPI"])],
    )

    # Candidate 2: Same skills, exp, and education, but projects use unrelated stack
    # (PHP, WordPress) -> 0% project relevance
    cand_2_cv = StructuredCv(
        full_name="Candidate Without Projects",
        skills=["Python", "FastAPI"],
        work_experience=work_exp,
        education=[EducationItem(degree="Bachelor", institution="Uni A")],
        projects=[ProjectItem(name="CMS Website", technologies=["PHP", "WordPress"])],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-unrelated-proj", cv=cand_2_cv),
            CandidateItem(candidate_id="cand-relevant-proj", cv=cand_1_cv),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 2
    # Candidate with relevant projects must be Rank 1
    cand_rel = response.ranked_candidates[0]
    cand_unrel = response.ranked_candidates[1]

    assert cand_rel.candidate_id == "cand-relevant-proj"
    assert cand_rel.rank == 1
    assert cand_unrel.candidate_id == "cand-unrelated-proj"
    assert cand_unrel.rank == 2

    # Score comparison: 10% project weight delta in matching-v1 (100 vs 90)
    score_rel = cand_rel.match_result.match_score
    score_unrel = cand_unrel.match_result.match_score
    assert score_rel == 100
    assert score_unrel == 90
    assert score_rel > score_unrel

    # Strict component isolation verification
    exp_rel = cand_rel.match_result.match_explanation or ""
    exp_unrel = cand_unrel.match_result.match_explanation or ""
    assert "Kỹ năng: 100%" in exp_rel and "Kỹ năng: 100%" in exp_unrel
    assert "Kinh nghiệm: 100%" in exp_rel and "Kinh nghiệm: 100%" in exp_unrel
    assert "Học vấn: 100%" in exp_rel and "Học vấn: 100%" in exp_unrel
    assert "Độ tương đồng ngữ nghĩa: 100%" in exp_rel and "Độ tương đồng ngữ nghĩa: 100%" in exp_unrel
    assert "Dự án: 100%" in exp_rel
    assert "Dự án: 0%" in exp_unrel

    assert "1/1 dự án thực tế" in cand_rel.match_result.project_domain_relevance
    assert "chưa thể hiện sự trùng khớp" in cand_unrel.match_result.project_domain_relevance


@pytest.mark.asyncio
async def test_matching_v1_single_and_ranking_parity():
    """Verify single match and ranking produce exact identical match score and component values under matching-v1."""
    llm = MockLlmProvider()
    embedding_provider = MockEmbeddingProvider()

    matching_service = MatchingService(
        llm=llm,
        embedding_provider=embedding_provider,
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Senior Python Backend",
        description="Build scalable distributed microservices.",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        minimum_experience_years=3.0,
        education_requirement="Bachelor",
    )

    cv = StructuredCv(
        full_name="Nguyen Van Parity",
        skills=["Python", "FastAPI", "Docker"],
        work_experience=[
            WorkExperienceItem(
                job_title="Backend Developer",
                company="Parity Labs",
                years_of_experience=4.0,
                description="Built high-performance APIs.",
            )
        ],
        education=[EducationItem(degree="Bachelor", institution="HUST")],
        projects=[ProjectItem(name="API Platform", technologies=["Python", "Docker"])],
    )

    # 1. Single match evaluation
    single_res = await matching_service.match(cv=cv, job=job, generate_explanation=False)

    # 2. Ranking evaluation
    req = CandidateRankRequest(job=job, candidates=[CandidateItem(candidate_id="cand-01", cv=cv)])
    rank_resp = await ranking_service.rank_candidates(req)
    ranked_res = rank_resp.ranked_candidates[0].match_result

    # 3. Assert exact parity
    assert single_res.match_score == ranked_res.match_score
    assert single_res.matched_skills == ranked_res.matched_skills
    assert single_res.missing_skills == ranked_res.missing_skills
    assert single_res.experience_comparison == ranked_res.experience_comparison
    assert single_res.education_comparison == ranked_res.education_comparison
    assert single_res.project_domain_relevance == ranked_res.project_domain_relevance
    assert single_res.match_explanation == ranked_res.match_explanation
    assert ranked_res.meta.llm_invoked is False
    assert ranked_res.meta.algorithm_variant == "matching-v1-experimental"


class FailingRankingEmbeddingProvider(EmbeddingPort):
    """Failing embedding provider for ranking error testing."""

    @property
    def provider_name(self) -> str:
        return "failing-ranking-emb"

    @property
    def model_name(self) -> str:
        return "fail-rank-model"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise ProviderError("Ranking embedding service down", provider="failing-ranking-emb")


@pytest.mark.asyncio
async def test_ranking_v1_embedding_failure_fails_fast():
    """Verify Candidate Ranking raises ProviderError without silent fallback when embedding provider fails."""
    matching_service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=FailingRankingEmbeddingProvider(),
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [CandidateItem(candidate_id="c1", cv=StructuredCv(skills=["Python"]))]
    req = CandidateRankRequest(job=job, candidates=candidates)

    with pytest.raises(ProviderError) as exc_info:
        await ranking_service.rank_candidates(req)

    assert "Ranking embedding service down" in str(exc_info.value)


class CardinalityMismatchedRankingProvider(EmbeddingPort):
    """Embedding provider returning custom vector counts for job vs candidates."""

    def __init__(self, job_vector_count: int = 1, candidate_vector_count: int | None = None) -> None:
        self.job_vector_count = job_vector_count
        self.candidate_vector_count = candidate_vector_count
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return "cardinality-mismatch-rank-emb"

    @property
    def model_name(self) -> str:
        return "mismatch-model"

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls == 1:
            # First call is Job embedding
            return [[1.0, 0.0] for _ in range(self.job_vector_count)]
        # Subsequent calls are candidate chunks
        count = self.candidate_vector_count if self.candidate_vector_count is not None else len(texts)
        return [[1.0, 0.0] for _ in range(count)]


@pytest.mark.asyncio
async def test_ranking_v1_job_embedding_cardinality_mismatch():
    """Rule: When provider returns wrong vector count for Job text, RankingService raises ProviderError."""
    matching_service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=CardinalityMismatchedRankingProvider(job_vector_count=2),
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [CandidateItem(candidate_id="c1", cv=StructuredCv(skills=["Python"]))]
    req = CandidateRankRequest(job=job, candidates=candidates)

    with pytest.raises(ProviderError) as exc_info:
        await ranking_service.rank_candidates(req)

    assert "Embedding provider returned 2 vectors for 1 requested job text" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ranking_v1_candidate_chunk_cardinality_too_few():
    """Rule: When provider returns fewer vectors than candidate chunk count, RankingService raises ProviderError."""
    matching_service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=CardinalityMismatchedRankingProvider(job_vector_count=1, candidate_vector_count=1),
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [
        CandidateItem(candidate_id="c1", cv=StructuredCv(skills=["Python"])),
        CandidateItem(candidate_id="c2", cv=StructuredCv(skills=["Java"])),
    ]
    req = CandidateRankRequest(job=job, candidates=candidates)

    with pytest.raises(ProviderError) as exc_info:
        await ranking_service.rank_candidates(req)

    assert "Embedding provider returned 1 vectors for 2 requested candidate texts" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ranking_v1_candidate_chunk_cardinality_too_many():
    """Rule: When provider returns more vectors than candidate chunk count, RankingService raises ProviderError."""
    matching_service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=CardinalityMismatchedRankingProvider(job_vector_count=1, candidate_vector_count=3),
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [
        CandidateItem(candidate_id="c1", cv=StructuredCv(skills=["Python"])),
        CandidateItem(candidate_id="c2", cv=StructuredCv(skills=["Java"])),
    ]
    req = CandidateRankRequest(job=job, candidates=candidates)

    with pytest.raises(ProviderError) as exc_info:
        await ranking_service.rank_candidates(req)

    assert "Embedding provider returned 3 vectors for 2 requested candidate texts" in str(exc_info.value)
