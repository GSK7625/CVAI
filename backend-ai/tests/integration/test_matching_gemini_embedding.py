"""Integration tests for Candidate-Job matching with Gemini Embedding Provider in Advisory/Shadow mode."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from google.genai import types
import pytest

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest
from app.core.config import Settings
from app.infrastructure.embeddings.factory import get_embedding_provider
from app.infrastructure.embeddings.providers.gemini_provider import GeminiEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider


def _build_stubbed_gemini_embedding_provider() -> GeminiEmbeddingProvider:
    """Build a GeminiEmbeddingProvider with a stubbed genai.Client returning 64-dim unit vectors."""
    mock_client = MagicMock()
    mock_client.aio = MagicMock()

    async def mock_embed_content(model: str, contents: list[str]) -> types.EmbedContentResponse:
        # Generate predictable normalized vectors based on content hash
        embeddings = []
        for text in contents:
            # Deterministic pseudo-random float vector of length 64
            base_val = (hash(text) % 100) / 100.0
            vec = [base_val if i == 0 else 0.1 for i in range(64)]
            embeddings.append(types.ContentEmbedding(values=vec))
        return types.EmbedContentResponse(embeddings=embeddings)

    mock_client.aio.models.embed_content = AsyncMock(side_effect=mock_embed_content)
    mock_client.aio.aclose = AsyncMock()

    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        EMBEDDING_MODEL="gemini-embedding-2",
        GEMINI_API_KEY="AIzaSyIntegrationTestKey",
        LLM_TIMEOUT_SECONDS=10,
        LLM_MAX_RETRIES=1,
    )
    return GeminiEmbeddingProvider(settings=settings, client=mock_client)


# =============================================================================
# 1. Factory Creation Tests
# =============================================================================


def test_factory_returns_gemini_embedding_provider():
    """Verify get_embedding_provider returns GeminiEmbeddingProvider when configured."""
    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        EMBEDDING_MODEL="gemini-embedding-2",
        GEMINI_API_KEY="test-key",
    )
    provider = get_embedding_provider(settings=settings)

    assert isinstance(provider, GeminiEmbeddingProvider)
    assert provider.provider_name == "gemini"
    assert provider.model_name == "gemini-embedding-2"


# =============================================================================
# 2. Advisory / Shadow Mode Match Flow Tests
# =============================================================================


@pytest.mark.asyncio
async def test_matching_with_gemini_embedding_in_advisory_mode():
    """
    Verify full matching flow with Gemini embeddings in Advisory Mode:
    - match_score uses deterministic matching-v0 formula.
    - semantic_similarity is populated from embeddings.
    - semantic_mode is 'advisory'.
    - meta reflects embedding provider and model with matching-v0 algorithm.
    """
    gemini_emb = _build_stubbed_gemini_embedding_provider()
    mock_llm = MockLlmProvider()

    service = MatchingService(
        llm=mock_llm,
        embedding_provider=gemini_emb,
        matching_algorithm="matching-v1-experimental",
        semantic_mode="advisory",
    )

    cv = StructuredCv(
        skills=["Python", "FastAPI", "PostgreSQL"],
        technologies=["Docker"],
    )
    job = StructuredJob(
        title="Senior Backend Engineer",
        description="Build high-performance REST APIs",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["PostgreSQL"],
        minimum_experience_years=2.0,
    )

    result = await service.match(cv=cv, job=job, generate_explanation=False)

    # 1. match_score is deterministic v0
    assert result.match_score > 0
    assert isinstance(result.match_score, int)

    # 2. semantic_similarity is present and bounded [0, 100]
    assert result.semantic_similarity is not None
    assert 0.0 <= result.semantic_similarity <= 100.0
    assert result.semantic_mode == "advisory"
    assert result.semantic_available is True
    assert result.semantic_score is not None
    assert 0 <= result.semantic_score <= 100

    # 3. ResponseMeta provenance
    assert result.meta.semantic_similarity == result.semantic_similarity
    assert result.meta.semantic_score == result.semantic_score
    assert result.meta.semantic_mode == "advisory"
    assert result.meta.semantic_available is True
    assert result.meta.embedding_provider == "gemini"
    assert result.meta.embedding_model == "gemini-embedding-2"
    assert result.meta.algorithm_version == "matching-v0"
    assert result.meta.algorithm_variant == "matching-v0"


@pytest.mark.asyncio
async def test_matching_with_gemini_embedding_failure_in_advisory_mode_falls_back_gracefully():
    """
    Verify graceful degradation in Advisory Mode when embedding fails:
    - Embedding call throws an error.
    - match() does NOT raise an exception.
    - match_score continues on deterministic matching-v0.
    - semantic_available is False, semantic_similarity is None, semantic_score is None.
    - Natural language explanation falls back cleanly.
    """
    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models.embed_content = AsyncMock(
        side_effect=Exception("Simulated network disconnection during embedding call")
    )
    mock_client.aio.aclose = AsyncMock()

    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        EMBEDDING_MODEL="gemini-embedding-2",
        GEMINI_API_KEY="test-key",
        LLM_TIMEOUT_SECONDS=5,
        LLM_MAX_RETRIES=0,
    )
    failing_emb = GeminiEmbeddingProvider(settings=settings, client=mock_client)
    mock_llm = MockLlmProvider()

    service = MatchingService(
        llm=mock_llm,
        embedding_provider=failing_emb,
        matching_algorithm="matching-v0",
        semantic_mode="advisory",
    )

    cv = StructuredCv(skills=["Python", "FastAPI"])
    job = StructuredJob(
        title="Backend Engineer",
        required_skills=["Python"],
    )

    result = await service.match(cv=cv, job=job, generate_explanation=True)

    # 1. Matching continues and succeeds
    assert result.match_score > 0

    # 2. Semantic metadata indicates graceful degradation
    assert result.semantic_available is False
    assert result.semantic_similarity is None
    assert result.semantic_score is None
    assert result.meta.semantic_available is False
    assert result.meta.semantic_similarity is None
    assert result.meta.semantic_score is None
    assert result.meta.algorithm_version == "matching-v0"

    # 3. Explanation is present without crash
    assert result.match_explanation is not None
    assert len(result.match_explanation) > 0


@pytest.mark.asyncio
async def test_matching_with_gemini_embedding_explanation_receives_semantic_context():
    """Verify LLM explanation prompt receives supplementary semantic similarity in advisory mode."""
    gemini_emb = _build_stubbed_gemini_embedding_provider()

    captured_prompts: list[str] = []

    class CapturingLlm(MockLlmProvider):
        async def generate_text(self, prompt: str, system_prompt: str | None = None, temperature: float = 0.3) -> str:
            captured_prompts.append(prompt)
            return "Ứng viên phù hợp với vị trí Senior Backend Engineer."

        async def generate_structured(
            self,
            prompt: str,
            response_model: Any,
            system_prompt: str | None = None,
            temperature: float = 0.1,
        ) -> Any:
            captured_prompts.append(prompt)
            return await super().generate_structured(prompt, response_model, system_prompt, temperature)

    service = MatchingService(
        llm=CapturingLlm(),
        embedding_provider=gemini_emb,
        matching_algorithm="matching-v1-experimental",
        semantic_mode="advisory",
    )

    cv = StructuredCv(skills=["Python"])
    job = StructuredJob(title="Python Dev", required_skills=["Python"])

    result = await service.match(cv=cv, job=job, generate_explanation=True)

    assert result.match_score > 0
    assert result.semantic_similarity is not None
    assert len(captured_prompts) == 1
    # Verify semantic similarity line was injected into the LLM prompt
    assert "Độ tương đồng ngữ nghĩa (bổ trợ)" in captured_prompts[0]


# =============================================================================
# 3. Bulk Ranking with Gemini Embeddings in Advisory Mode
# =============================================================================


@pytest.mark.asyncio
async def test_candidate_ranking_with_gemini_embeddings():
    """Verify Candidate Ranking sorts descending by match_score and preserves semantic fields."""
    gemini_emb = _build_stubbed_gemini_embedding_provider()
    mock_llm = MockLlmProvider()

    matching_service = MatchingService(
        llm=mock_llm,
        embedding_provider=gemini_emb,
        matching_algorithm="matching-v1-experimental",
        semantic_mode="advisory",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Python Dev",
        required_skills=["Python", "FastAPI"],
    )
    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-001", cv=StructuredCv(skills=["Python"])),
            CandidateItem(candidate_id="cand-002", cv=StructuredCv(skills=["Python", "FastAPI"])),
        ],
    )

    ranked_res = await ranking_service.rank_candidates(req)

    assert ranked_res.total_evaluated == 2
    # Candidate 2 (both skills) has higher match score than candidate 1 (one skill)
    assert ranked_res.ranked_candidates[0].candidate_id == "cand-002"
    assert ranked_res.ranked_candidates[0].rank == 1
    assert ranked_res.ranked_candidates[1].candidate_id == "cand-001"
    assert ranked_res.ranked_candidates[1].rank == 2

    # Verify each item has semantic_similarity and advisory mode
    first_match = ranked_res.ranked_candidates[0].match_result
    assert first_match.semantic_similarity is not None
    assert first_match.semantic_mode == "advisory"
    assert first_match.meta.embedding_provider == "gemini"
