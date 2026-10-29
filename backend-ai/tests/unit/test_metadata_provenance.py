"""Unit tests for MatchResult and ResponseMeta provenance metadata (Task A / Task 1)."""

from pydantic import BaseModel

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.career import CareerAssistantResponse
from app.contracts.common import ResponseMeta
from app.contracts.cv import StructuredCv
from app.contracts.cv_analysis import CvAnalysisResponse
from app.contracts.job import StructuredJob
from app.contracts.matching import (
    MATCH_RESULT_CONTRACT_VERSION,
    CandidateItem,
    CandidateRankRequest,
    CandidateRankResponse,
    MatchResult,
)
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider


class LegacyResponseMeta(BaseModel):
    """
    Representation of the legacy (HEAD) consumer contract.

    Notice that in HEAD, ResponseMeta had only these 6 fields with Pydantic default
    extra='ignore'.
    """

    algorithm_version: str
    prompt_version: str
    provider: str
    model: str
    processing_time_ms: float
    correlation_id: str


def test_response_meta_default_fields_preserved():
    """Verify backward-compatible fields in ResponseMeta exist with expected defaults."""
    meta = ResponseMeta()
    assert meta.contract_version is None
    assert meta.algorithm_version == "1.0.0"
    assert meta.schema_version == "1.0.0"
    assert meta.prompt_version == "v1"
    assert meta.provider == "mock"
    assert meta.model == "default"
    assert meta.processing_time_ms == 0.0
    assert meta.correlation_id == "-"
    # Additive optional fields
    assert meta.algorithm_variant is None
    assert meta.embedding_provider is None
    assert meta.embedding_model is None
    # BLOCKER 1: Tri-state default MUST be None, not False
    assert meta.llm_invoked is None
    assert meta.explanation_mode is None


def test_response_meta_legacy_consumer_compatibility():
    """
    Verify legacy consumers (deserializing with the 6-field HEAD schema) can successfully
    deserialize modern ResponseMeta payloads containing additive fields.
    """
    modern_meta = ResponseMeta(
        algorithm_version="matching-v0",
        algorithm_variant="matching-v0",
        schema_version="1.0.0",
        prompt_version="deterministic",
        provider="mock",
        model="mock-deterministic",
        embedding_provider=None,
        embedding_model=None,
        llm_invoked=False,
        processing_time_ms=12.5,
        correlation_id="corr-legacy-test",
    )

    serialized = modern_meta.model_dump()
    assert "algorithm_variant" in serialized
    assert "schema_version" in serialized
    assert "llm_invoked" in serialized

    # Deserialize using the Legacy contract
    # Under Pydantic's default extra='ignore' behavior, extra unknown keys are discarded gracefully
    legacy_obj = LegacyResponseMeta.model_validate(serialized)
    assert legacy_obj.algorithm_version == "matching-v0"
    assert legacy_obj.prompt_version == "deterministic"
    assert legacy_obj.provider == "mock"
    assert legacy_obj.model == "mock-deterministic"
    assert legacy_obj.processing_time_ms == 12.5
    assert legacy_obj.correlation_id == "corr-legacy-test"


def test_generic_shared_response_meta_does_not_falsely_claim_llm_false():
    """
    Verify shared services (like CvAnalyzerService or CareerAssistantService) that instantiate
    ResponseMeta without explicitly declaring llm_invoked emit None rather than False.
    """
    generic_meta = ResponseMeta(
        algorithm_version="career-v0",
        prompt_version="v1",
        provider="mock",
        model="mock-deterministic",
        processing_time_ms=5.0,
    )
    assert generic_meta.llm_invoked is None
    dumped = generic_meta.model_dump()
    assert dumped["llm_invoked"] is None


def test_non_matching_services_metadata_contract_version_is_none():
    """Verify generic/CV/Career responses do NOT leak match-result-v1 contract version."""
    cv_meta = ResponseMeta(algorithm_version="cv-v0", prompt_version="v1")
    career_meta = ResponseMeta(algorithm_version="career-v0", prompt_version="v1")
    assert cv_meta.contract_version is None
    assert career_meta.contract_version is None

    # Also check CvAnalysisResponse and CareerAssistantResponse default metadata
    cv_response = CvAnalysisResponse(
        structured_cv=StructuredCv(),
        cv_score=80,
        strengths=[],
        weaknesses=[],
        improvement_suggestions=[],
    )
    assert cv_response.meta.contract_version is None

    career_response = CareerAssistantResponse(
        reply="Test reply",
        suggested_followups=[],
    )
    assert career_response.meta.contract_version is None


def test_match_result_and_candidate_rank_response_default_contract_version():
    """Verify MatchResult and CandidateRankResponse models stamp match-result-v1 contract_version."""
    mr = MatchResult(match_score=80)
    assert mr.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION

    crr = CandidateRankResponse(job_title="Dev", total_evaluated=0, ranked_candidates=[])
    assert crr.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION


async def test_matching_v0_provenance_metadata():
    """Verify matching-v0 populates wire algorithm_version 'matching-v0' and correct provenance."""
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )
    cv = StructuredCv(skills=["Python", "FastAPI"])
    job = StructuredJob(title="Backend Dev", required_skills=["Python"])

    # Flow 2: v0 single LLM
    res = await service.match(cv=cv, job=job, generate_explanation=True)
    assert res.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert res.meta.algorithm_version == "matching-v0"
    assert res.meta.algorithm_variant == "matching-v0"
    assert res.meta.schema_version == "1.0.0"
    assert res.meta.provider == "mock"
    assert res.meta.model == "mock-deterministic"
    assert res.meta.embedding_provider is None
    assert res.meta.embedding_model is None
    assert res.meta.llm_invoked is True
    assert res.meta.explanation_mode == "llm"
    assert res.meta.prompt_version == "v1"

    # Flow 1: v0 single deterministic
    res_no_llm = await service.match(cv=cv, job=job, generate_explanation=False)
    assert res_no_llm.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert res_no_llm.meta.algorithm_version == "matching-v0"
    assert res_no_llm.meta.algorithm_variant == "matching-v0"
    assert res_no_llm.meta.schema_version == "1.0.0"
    assert res_no_llm.meta.embedding_provider is None
    assert res_no_llm.meta.embedding_model is None
    assert res_no_llm.meta.llm_invoked is False
    assert res_no_llm.meta.explanation_mode == "deterministic"
    assert res_no_llm.meta.prompt_version == "deterministic"


async def test_matching_v1_provenance_metadata():
    """Verify matching-v1 populates wire algorithm_version 'matching-v1-experimental' and neutral prompt_version."""
    mock_embedding = MockEmbeddingProvider(dimension=64)
    service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=mock_embedding,
        matching_algorithm="matching-v1-experimental",
    )
    cv = StructuredCv(skills=["Python", "FastAPI"])
    job = StructuredJob(title="Backend Dev", required_skills=["Python"])

    # Flow 4: v1 single LLM
    res = await service.match(cv=cv, job=job, generate_explanation=True)
    assert res.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert res.meta.algorithm_version == "matching-v1-experimental"
    assert res.meta.algorithm_variant == "matching-v1-experimental"
    assert res.meta.schema_version == "1.0.0"
    assert res.meta.provider == "mock"
    assert res.meta.model == "mock-deterministic"
    assert res.meta.embedding_provider == "mock"
    assert res.meta.embedding_model == "mock-hash-64"
    assert res.meta.llm_invoked is True
    assert res.meta.explanation_mode == "llm"
    assert res.meta.prompt_version == "v1"

    # Flow 3: v1 single deterministic
    res_deterministic = await service.match(cv=cv, job=job, generate_explanation=False)
    assert res_deterministic.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert res_deterministic.meta.algorithm_version == "matching-v1-experimental"
    assert res_deterministic.meta.algorithm_variant == "matching-v1-experimental"
    assert res_deterministic.meta.schema_version == "1.0.0"
    assert res_deterministic.meta.embedding_provider == "mock"
    assert res_deterministic.meta.embedding_model == "mock-hash-64"
    assert res_deterministic.meta.llm_invoked is False
    assert res_deterministic.meta.explanation_mode == "deterministic"
    # Invariant: prompt_version must NOT mislabel v1 as "deterministic-v0"
    assert res_deterministic.meta.prompt_version == "deterministic"
    assert res_deterministic.meta.prompt_version != "deterministic-v0"


async def test_ranking_provenance_metadata():
    """Verify candidate ranking provenance for both v0 and v1 with neutral prompt_version."""
    mock_llm = MockLlmProvider()
    mock_embedding = MockEmbeddingProvider(dimension=64)
    job = StructuredJob(title="Backend Dev", required_skills=["Python"])
    candidates = [CandidateItem(candidate_id="c1", cv=StructuredCv(skills=["Python"]))]
    req = CandidateRankRequest(job=job, candidates=candidates)

    # Flow 5: v0 ranking
    v0_matching = MatchingService(llm=mock_llm, embedding_provider=None, matching_algorithm="matching-v0")
    v0_ranking = RankingService(matching_service=v0_matching)
    v0_resp = await v0_ranking.rank_candidates(req)
    assert v0_resp.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert v0_resp.ranked_candidates[0].match_result.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert v0_resp.meta.algorithm_version == "matching-v0"
    assert v0_resp.meta.algorithm_variant == "matching-v0"
    assert v0_resp.meta.schema_version == "1.0.0"
    assert v0_resp.meta.prompt_version == "deterministic"
    assert v0_resp.meta.llm_invoked is False
    assert v0_resp.meta.explanation_mode == "deterministic"
    assert v0_resp.meta.embedding_provider is None
    assert v0_resp.meta.embedding_model is None

    # Flow 6: v1 ranking
    v1_matching = MatchingService(
        llm=mock_llm,
        embedding_provider=mock_embedding,
        matching_algorithm="matching-v1-experimental",
    )
    v1_ranking = RankingService(matching_service=v1_matching)
    v1_resp = await v1_ranking.rank_candidates(req)
    assert v1_resp.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert v1_resp.ranked_candidates[0].match_result.meta.contract_version == MATCH_RESULT_CONTRACT_VERSION
    assert v1_resp.meta.algorithm_version == "matching-v1-experimental"
    assert v1_resp.meta.algorithm_variant == "matching-v1-experimental"
    assert v1_resp.meta.schema_version == "1.0.0"
    assert v1_resp.meta.prompt_version == "deterministic"
    assert v1_resp.meta.prompt_version != "deterministic-v0"
    assert v1_resp.meta.llm_invoked is False
    assert v1_resp.meta.explanation_mode == "deterministic"
    assert v1_resp.meta.embedding_provider == "mock"
    assert v1_resp.meta.embedding_model == "mock-hash-64"
