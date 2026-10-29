"""Unit tests for optional LLM explanation fallback, scoring preservation, and provenance metadata."""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.embeddings import EmbeddingPort
from app.ports.llm import LlmPort


class FailingLlmProvider(LlmPort):
    """LLM provider that always raises ProviderError."""

    def __init__(self, message: str = "OpenAI service overloaded") -> None:
        self.message = message

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return "gpt-4o-mini"

    async def generate_text(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        raise ProviderError(self.message, provider="openai")

    async def generate_structured(
        self,
        prompt: str,
        response_model: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> Any:
        raise ProviderError(self.message, provider="openai")


class RateLimitLlmProvider(LlmPort):
    """LLM provider that always raises RateLimitExceededError (HTTP 429 exhaustion)."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return "gpt-4o-mini"

    async def generate_text(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> str:
        raise RateLimitExceededError("Rate limit exceeded on OpenAI chat completions")

    async def generate_structured(
        self,
        prompt: str,
        response_model: Any,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> Any:
        raise RateLimitExceededError("Rate limit exceeded on OpenAI chat completions")


class FailingEmbeddingProvider(EmbeddingPort):
    """Embedding provider that always raises ProviderError."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return "text-embedding-3-small"

    async def embed_texts(self, texts: Any) -> list[list[float]]:
        raise ProviderError("Embedding cluster unavailable", provider="openai")


class RateLimitEmbeddingProvider(EmbeddingPort):
    """Embedding provider that raises RateLimitExceededError."""

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return "text-embedding-3-small"

    async def embed_texts(self, texts: Any) -> list[list[float]]:
        raise RateLimitExceededError("Rate limit exceeded on OpenAI embeddings")


@pytest.fixture
def sample_cv() -> StructuredCv:
    return StructuredCv(
        skills=["Python", "FastAPI"],
        technologies=["Docker"],
        career_summary="Backend developer with 3 years experience.",
    )


@pytest.fixture
def sample_job() -> StructuredJob:
    return StructuredJob(
        title="Backend Engineer",
        description="Looking for Python FastAPI dev.",
        required_skills=["Python"],
        preferred_skills=["FastAPI"],
    )


@pytest.mark.asyncio
async def test_v0_generate_explanation_llm_success(sample_cv: StructuredCv, sample_job: StructuredJob):
    """v0 + generate_explanation=True + LLM success -> llm_invoked=True, explanation_mode='llm'."""
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )

    result = await service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert result.match_score > 0
    assert "Mức độ phù hợp cao" in result.match_explanation
    assert result.explanation_details is not None
    assert result.meta.algorithm_variant == "matching-v0"
    assert result.meta.prompt_version == "v1"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "llm"


@pytest.mark.asyncio
async def test_v0_generate_explanation_llm_provider_error_fallback(sample_cv: StructuredCv, sample_job: StructuredJob):
    """
    CRITICAL PROOF (FIX I): v0 + generate_explanation=True + ProviderError:
    - Preserves exact computed score
    - Uses deterministic explanation fallback
    - Provenance accurately records llm_invoked=True and explanation_mode='deterministic-fallback'
    """
    mock_success = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )
    expected_score = (await mock_success.match(cv=sample_cv, job=sample_job, generate_explanation=False)).match_score

    failing_service = MatchingService(
        llm=FailingLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )

    result = await failing_service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    # Score must be 100% preserved
    assert result.match_score == expected_score
    # Explanation fell back to deterministic summary
    assert "Điểm phù hợp:" in result.match_explanation
    assert "Kỹ năng đáp ứng:" in result.match_explanation
    # Provenance
    assert result.meta.algorithm_variant == "matching-v0"
    assert result.meta.prompt_version == "v1"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "deterministic-fallback"


@pytest.mark.asyncio
async def test_v0_llm_rate_limit_exceeded_falls_back_to_deterministic(
    sample_cv: StructuredCv,
    sample_job: StructuredJob,
):
    """
    CRITICAL PROOF (BLOCKER 1): v0 + LLM RateLimitExceededError (HTTP 429 retries exhausted):
    - Must follow the explanation fallback policy
    - Preserves exact computed score
    - Sets explanation_mode='deterministic-fallback' and llm_invoked=True
    - Does NOT escape as an unhandled exception or crash the request
    """
    mock_success = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )
    expected_score = (await mock_success.match(cv=sample_cv, job=sample_job, generate_explanation=False)).match_score

    rate_limited_service = MatchingService(
        llm=RateLimitLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )

    result = await rate_limited_service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert result.match_score == expected_score
    assert "Điểm phù hợp:" in result.match_explanation
    assert result.meta.algorithm_variant == "matching-v0"
    assert result.meta.prompt_version == "v1"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "deterministic-fallback"


@pytest.mark.asyncio
async def test_v0_generate_explanation_false_zero_llm(sample_cv: StructuredCv, sample_job: StructuredJob):
    """v0 + generate_explanation=False -> zero LLM calls, explanation_mode='deterministic'."""
    spy_llm = MockLlmProvider()
    spy_llm.generate_text = AsyncMock()  # type: ignore[method-assign]

    service = MatchingService(
        llm=spy_llm,
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )

    result = await service.match(cv=sample_cv, job=sample_job, generate_explanation=False)

    spy_llm.generate_text.assert_not_called()
    assert result.meta.llm_invoked is False
    assert result.meta.explanation_mode == "deterministic"
    assert result.meta.prompt_version == "deterministic"


@pytest.mark.asyncio
async def test_v1_embeddings_and_llm_success(sample_cv: StructuredCv, sample_job: StructuredJob):
    """v1 + embeddings succeed + LLM success -> normal v1 result with explanation_mode='llm'."""
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=MockEmbeddingProvider(dimension=64),
        matching_algorithm="matching-v1-experimental",
    )

    result = await service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert result.meta.algorithm_variant == "matching-v1-experimental"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "llm"
    assert result.meta.embedding_provider == "mock"


@pytest.mark.asyncio
async def test_v1_llm_provider_error_preserves_v1_score_and_falls_back(
    sample_cv: StructuredCv,
    sample_job: StructuredJob,
):
    """
    v1 + embeddings succeed + LLM ProviderError:
    - Preserves exact v1 score (including semantic component)
    - Falls back to deterministic summary
    - Does NOT crash the request
    """
    mock_emb = MockEmbeddingProvider(dimension=64)
    v1_baseline = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=mock_emb,
        matching_algorithm="matching-v1-experimental",
    )
    expected_v1_score = (await v1_baseline.match(cv=sample_cv, job=sample_job, generate_explanation=False)).match_score

    failing_service = MatchingService(
        llm=FailingLlmProvider(),
        embedding_provider=mock_emb,
        matching_algorithm="matching-v1-experimental",
    )

    result = await failing_service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert result.match_score == expected_v1_score
    assert "Độ tương đồng ngữ nghĩa:" in result.match_explanation
    assert result.meta.algorithm_variant == "matching-v1-experimental"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "deterministic-fallback"


@pytest.mark.asyncio
async def test_v1_llm_rate_limit_exceeded_preserves_score_and_falls_back(
    sample_cv: StructuredCv,
    sample_job: StructuredJob,
):
    """
    v1 + embeddings succeed + LLM RateLimitExceededError:
    - Preserves exact v1 score (including semantic component)
    - Falls back to deterministic summary with explanation_mode='deterministic-fallback'
    - Does NOT crash the request
    """
    mock_emb = MockEmbeddingProvider(dimension=64)
    v1_baseline = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=mock_emb,
        matching_algorithm="matching-v1-experimental",
    )
    expected_v1_score = (await v1_baseline.match(cv=sample_cv, job=sample_job, generate_explanation=False)).match_score

    rate_limited_service = MatchingService(
        llm=RateLimitLlmProvider(),
        embedding_provider=mock_emb,
        matching_algorithm="matching-v1-experimental",
    )

    result = await rate_limited_service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert result.match_score == expected_v1_score
    assert "Độ tương đồng ngữ nghĩa:" in result.match_explanation
    assert result.meta.algorithm_variant == "matching-v1-experimental"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "deterministic-fallback"


@pytest.mark.asyncio
async def test_v1_embedding_failure_fails_fast_without_fallback_to_v0(
    sample_cv: StructuredCv,
    sample_job: StructuredJob,
):
    """
    CRITICAL INVARIANT 5: Semantic embedding failure in matching-v1 MUST fail fast.
    NEVER silently fall back from matching-v1 to matching-v0.
    """
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=FailingEmbeddingProvider(),
        matching_algorithm="matching-v1-experimental",
    )

    with pytest.raises(ProviderError) as exc_info:
        await service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert "Embedding cluster unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_v1_embedding_rate_limit_fails_fast_without_fallback(
    sample_cv: StructuredCv,
    sample_job: StructuredJob,
):
    """
    CRITICAL INVARIANT: RateLimitExceededError during embedding in matching-v1 MUST fail fast.
    Embedding rate limits must NOT fall back silently to v0.
    """
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=RateLimitEmbeddingProvider(),
        matching_algorithm="matching-v1-experimental",
    )

    with pytest.raises(RateLimitExceededError) as exc_info:
        await service.match(cv=sample_cv, job=sample_job, generate_explanation=True)

    assert "Rate limit exceeded on OpenAI embeddings" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ranking_zero_llm_calls_and_deterministic_provenance(sample_job: StructuredJob, sample_cv: StructuredCv):
    """
    CRITICAL INVARIANT 6 (FIX J): Candidate Ranking makes exactly ZERO calls to llm.generate_text
    and produces deterministic provenance (llm_invoked=False, explanation_mode='deterministic').
    """
    spy_llm = MockLlmProvider()
    spy_llm.generate_text = AsyncMock()  # type: ignore[method-assign]

    matching_service = MatchingService(
        llm=spy_llm,
        embedding_provider=MockEmbeddingProvider(dimension=64),
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    req = CandidateRankRequest(
        job=sample_job,
        candidates=[
            CandidateItem(candidate_id="c1", cv=sample_cv),
            CandidateItem(candidate_id="c2", cv=sample_cv),
        ],
    )

    response = await ranking_service.rank_candidates(req)

    # Invariant: 0 LLM calls
    spy_llm.generate_text.assert_not_called()
    assert response.meta.llm_invoked is False
    assert response.meta.explanation_mode == "deterministic"
    assert response.meta.prompt_version == "deterministic"

    # Also check individual candidate match results
    for candidate in response.ranked_candidates:
        assert candidate.match_result.meta.llm_invoked is False
        assert candidate.match_result.meta.explanation_mode == "deterministic"
