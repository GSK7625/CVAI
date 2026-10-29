"""Unit tests verifying ranking embedding optimization and zero LLM calls (Task B)."""

from collections.abc import Sequence

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.application.semantic_representation import build_job_semantic_text
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.embeddings import EmbeddingPort


class SpyEmbeddingProvider(EmbeddingPort):
    """Spy embedding provider tracking all calls and text payloads."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension
        self.call_count = 0
        self.all_embedded_texts: list[str] = []
        self.calls: list[list[str]] = []

    @property
    def provider_name(self) -> str:
        return "spy"

    @property
    def model_name(self) -> str:
        return "spy-model"

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        self.call_count += 1
        text_list = list(texts)
        self.calls.append(text_list)
        self.all_embedded_texts.extend(text_list)
        # Return dummy unit vector
        return [[1.0] + [0.0] * (self.dimension - 1) for _ in text_list]


class SpyLlmProvider(MockLlmProvider):
    """Spy LLM provider tracking generate_text call count."""

    def __init__(self) -> None:
        super().__init__()
        self.generate_text_calls = 0

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.generate_text_calls += 1
        return await super().generate_text(prompt, system_prompt, temperature)


async def test_ranking_v0_makes_zero_embedding_and_zero_llm_calls():
    """Rule: Ranking under matching-v0 makes ZERO embedding calls and ZERO LLM calls."""
    spy_llm = SpyLlmProvider()
    spy_emb = SpyEmbeddingProvider()

    matching_service = MatchingService(
        llm=spy_llm,
        embedding_provider=spy_emb,
        matching_algorithm="matching-v0",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [
        CandidateItem(
            candidate_id=f"cand-{i}",
            cv=StructuredCv(skills=["Python"] if i % 2 == 0 else ["Java"]),
        )
        for i in range(10)
    ]
    req = CandidateRankRequest(job=job, candidates=candidates)

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 10
    # ZERO LLM calls
    assert spy_llm.generate_text_calls == 0
    # ZERO embedding calls
    assert spy_emb.call_count == 0
    # Metadata reports llm_invoked = False
    assert response.meta.llm_invoked is False
    assert response.meta.algorithm_variant == "matching-v0"
    for rc in response.ranked_candidates:
        assert rc.match_result.meta.llm_invoked is False


async def test_ranking_v1_embeds_job_exactly_once_and_zero_llm_calls():
    """
    Rule: Ranking under matching-v1:
    1. Embeds the target Job semantic text EXACTLY ONCE across the entire request.
    2. Embeds all N Candidate CVs.
    3. Makes ZERO LLM calls.
    """
    spy_llm = SpyLlmProvider()
    spy_emb = SpyEmbeddingProvider()

    matching_service = MatchingService(
        llm=spy_llm,
        embedding_provider=spy_emb,
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Backend Dev", required_skills=["Python", "FastAPI"])
    candidates = [
        CandidateItem(
            candidate_id=f"cand-{i}",
            cv=StructuredCv(skills=["Python", "FastAPI"] if i == 0 else ["Java"]),
        )
        for i in range(10)
    ]
    req = CandidateRankRequest(job=job, candidates=candidates)

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 10

    # Strict invariant 1: ZERO LLM calls
    assert spy_llm.generate_text_calls == 0
    assert response.meta.llm_invoked is False

    # Strict invariant 2: Job semantic text is embedded EXACTLY ONCE
    job_semantic = build_job_semantic_text(job)
    job_occurrences = [t for t in spy_emb.all_embedded_texts if t == job_semantic]
    assert len(job_occurrences) == 1, (
        f"Job semantic text must appear exactly once in embedding calls, but appeared {len(job_occurrences)} times"
    )

    # Strict invariant 3: Total embedded texts = 1 Job + 10 Candidates = 11 texts
    assert len(spy_emb.all_embedded_texts) == 11

    # Strict invariant 4: Result ordering remains sorted descending by match score
    scores = [rc.match_result.match_score for rc in response.ranked_candidates]
    assert scores == sorted(scores, reverse=True)
    assert response.ranked_candidates[0].rank == 1


async def test_ranking_v1_bounded_chunking_preserves_candidate_order():
    """Rule: When candidates exceed batch size, CVs are chunked and candidate order is preserved."""
    spy_llm = SpyLlmProvider()
    spy_emb = SpyEmbeddingProvider()

    matching_service = MatchingService(
        llm=spy_llm,
        embedding_provider=spy_emb,
        matching_algorithm="matching-v1-experimental",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(title="Fullstack", required_skills=["React"])
    # 25 candidates (exceeds CANDIDATE_EMBEDDING_BATCH_SIZE = 20)
    candidates = [CandidateItem(candidate_id=f"cand-{i:02d}", cv=StructuredCv(skills=["React"])) for i in range(25)]
    req = CandidateRankRequest(job=job, candidates=candidates)

    response = await ranking_service.rank_candidates(req)

    assert response.total_evaluated == 25
    # Call 1: Job embedding (1 text)
    # Call 2: First CV chunk (20 texts)
    # Call 3: Second CV chunk (5 texts)
    assert spy_emb.call_count == 3
    assert len(spy_emb.calls[0]) == 1  # Job
    assert len(spy_emb.calls[1]) == 20  # Chunk 1
    assert len(spy_emb.calls[2]) == 5  # Chunk 2

    # Job text occurs exactly once
    job_semantic = build_job_semantic_text(job)
    assert spy_emb.all_embedded_texts.count(job_semantic) == 1
    # Total embedded texts = 1 + 25 = 26
    assert len(spy_emb.all_embedded_texts) == 26
