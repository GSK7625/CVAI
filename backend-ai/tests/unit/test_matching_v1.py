"""Unit tests for matching-v1-experimental formula, execution, and error handling."""

from collections.abc import Sequence

import pytest

from app.application.matching_service import MatchingService
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.core.exceptions import ProviderError
from app.domain.matching.education_match import EducationMatchResult
from app.domain.matching.experience_match import ExperienceMatchResult
from app.domain.matching.project_match import ProjectRelevanceResult
from app.domain.matching.scoring import (
    MATCHING_V1_ALGORITHM_VERSION,
    V1_EDUCATION_WEIGHT,
    V1_EXPERIENCE_WEIGHT,
    V1_PROJECT_WEIGHT,
    V1_SEMANTIC_WEIGHT,
    V1_SKILL_WEIGHT,
    compute_overall_match_score_v1,
)
from app.domain.matching.skill_match import SkillMatchResult
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.embeddings import EmbeddingPort


class FailingEmbeddingProvider(EmbeddingPort):
    """Embedding provider simulating a network or service failure."""

    @property
    def provider_name(self) -> str:
        return "failing-mock"

    @property
    def model_name(self) -> str:
        return "fail-model"

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise ProviderError("Connection to embedding service failed", provider="failing-mock")


def test_v1_weights_sum_to_one():
    """Verify uncalibrated experimental weights sum to exactly 1.0 (100%)."""
    total = V1_SKILL_WEIGHT + V1_EXPERIENCE_WEIGHT + V1_EDUCATION_WEIGHT + V1_PROJECT_WEIGHT + V1_SEMANTIC_WEIGHT
    assert pytest.approx(total, abs=1e-6) == 1.0
    assert V1_SKILL_WEIGHT == 0.40
    assert V1_EXPERIENCE_WEIGHT == 0.20
    assert V1_EDUCATION_WEIGHT == 0.10
    assert V1_PROJECT_WEIGHT == 0.10
    assert V1_SEMANTIC_WEIGHT == 0.20


def test_compute_overall_match_score_v1_perfect_scores():
    """Verify v1 formula with 100 across all components yields 100."""
    skill_res = SkillMatchResult(skill_score=100.0, matched_required_skills=["Python"], missing_required_skills=[])
    exp_res = ExperienceMatchResult(score=100.0, candidate_years=5.0, required_years=3.0, comparison_text="Valid")
    edu_res = EducationMatchResult(score=100.0, comparison_text="Valid")
    proj_res = ProjectRelevanceResult(project_score=100.0)
    semantic_score = 100.0

    res = compute_overall_match_score_v1(
        skill_res=skill_res,
        exp_res=exp_res,
        edu_res=edu_res,
        proj_res=proj_res,
        semantic_score=semantic_score,
    )

    assert res.final_score == 100
    assert res.algorithm_version == MATCHING_V1_ALGORITHM_VERSION


def test_compute_overall_match_score_v1_weighted_calculation():
    """
    Verify v1 calculation with varied component scores:
    Skill: 80 * 0.40 = 32.0
    Exp: 50 * 0.20 = 10.0
    Edu: 100 * 0.10 = 10.0
    Proj: 60 * 0.10 = 6.0
    Semantic: 70 * 0.20 = 14.0
    Total = 32 + 10 + 10 + 6 + 14 = 72.0 -> 72
    """
    skill_res = SkillMatchResult(skill_score=80.0, matched_required_skills=[], missing_required_skills=[])
    exp_res = ExperienceMatchResult(score=50.0, candidate_years=2.0, required_years=4.0, comparison_text="Shortage")
    edu_res = EducationMatchResult(score=100.0, comparison_text="Valid")
    proj_res = ProjectRelevanceResult(project_score=60.0)
    semantic_score = 70.0

    res = compute_overall_match_score_v1(
        skill_res=skill_res,
        exp_res=exp_res,
        edu_res=edu_res,
        proj_res=proj_res,
        semantic_score=semantic_score,
    )

    assert res.final_score == 72


async def test_matching_v1_embedding_failure_fails_fast_without_silent_fallback():
    """Rule: When v1 embedding fails, MatchingService raises controlled ProviderError (no silent fallback to v0)."""
    failing_emb = FailingEmbeddingProvider()
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=failing_emb,
        matching_algorithm="matching-v1-experimental",
    )
    cv = StructuredCv(skills=["Python"])
    job = StructuredJob(title="Python Dev", required_skills=["Python"])

    with pytest.raises(ProviderError) as exc_info:
        await service.match(cv=cv, job=job)

    assert "Connection to embedding service failed" in str(exc_info.value)


async def test_matching_v0_preserves_zero_embedding_calls():
    """Rule: When v0 is active, MatchingService never invokes the embedding provider."""
    failing_emb = FailingEmbeddingProvider()  # Would fail if invoked
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=failing_emb,
        matching_algorithm="matching-v0",
    )
    cv = StructuredCv(skills=["Python"])
    job = StructuredJob(title="Python Dev", required_skills=["Python"])

    # Must succeed because v0 NEVER calls embedding provider
    res = await service.match(cv=cv, job=job, generate_explanation=False)
    assert res.match_score > 0
    assert res.meta.algorithm_variant == "matching-v0"
    assert res.meta.embedding_provider is None


class CardinalityMismatchedEmbeddingProvider(EmbeddingPort):
    """Embedding provider returning wrong number of vectors."""

    def __init__(self, returned_count: int) -> None:
        self.returned_count = returned_count

    @property
    def provider_name(self) -> str:
        return "mismatched-emb"

    @property
    def model_name(self) -> str:
        return "mismatch-model"

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in range(self.returned_count)]


async def test_matching_v1_embedding_cardinality_too_few_vectors():
    """Rule: When provider returns fewer vectors than requested texts, MatchingService raises ProviderError."""
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=CardinalityMismatchedEmbeddingProvider(returned_count=1),
        matching_algorithm="matching-v1-experimental",
    )
    cv = StructuredCv(skills=["Python"])
    job = StructuredJob(title="Python Dev", required_skills=["Python"])

    with pytest.raises(ProviderError) as exc_info:
        await service.match(cv=cv, job=job)

    assert "Embedding provider returned 1 vectors for 2 requested texts" in str(exc_info.value)


async def test_matching_v1_embedding_cardinality_too_many_vectors():
    """Rule: When provider returns more vectors than requested texts, MatchingService raises ProviderError."""
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=CardinalityMismatchedEmbeddingProvider(returned_count=3),
        matching_algorithm="matching-v1-experimental",
    )
    cv = StructuredCv(skills=["Python"])
    job = StructuredJob(title="Python Dev", required_skills=["Python"])

    with pytest.raises(ProviderError) as exc_info:
        await service.match(cv=cv, job=job)

    assert "Embedding provider returned 3 vectors for 2 requested texts" in str(exc_info.value)
