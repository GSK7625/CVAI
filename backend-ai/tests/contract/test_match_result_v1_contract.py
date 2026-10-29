"""Contract tests for MatchResult Contract v1 (AI-MATCH-004).

Freezes and verifies:
- MatchResult v1 field names, types, and semantics.
- Fixture validation (with-explanation and no-explanation variants).
- JSON round-trip serialization and deserialization.
- Optionality of match_explanation (supports strings and None without error).
- Score bounds (0 to 100, rejecting negative, >100, NaN, Inf).
- Invalid types rejection.
- Metadata contract validation and provenance (meta.contract_version == "match-result-v1").
- CandidateRankResponse schema reuse (embeds exact canonical MatchResult).
- OpenAPI contract schema verification.
"""

import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from app.contracts.common import ResponseMeta
from app.contracts.matching import (
    CandidateRankResponse,
    MatchResult,
    RankedCandidateItem,
)
from app.main import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "contracts"


# =====================================================================
# 1. Canonical Fixture Validation Tests
# =====================================================================


def test_match_result_v1_with_explanation_fixture():
    """Verify canonical fixture with LLM explanation parses and validates cleanly."""
    fixture_path = FIXTURES_DIR / "match_result_v1_with_explanation.json"
    with fixture_path.open(encoding="utf-8") as f:
        data = json.load(f)

    result = MatchResult.model_validate(data)
    assert result.match_score == 88
    assert result.matched_skills == ["Python", "FastAPI", "PostgreSQL"]
    assert result.missing_skills == ["Docker"]
    assert len(result.match_explanation) > 0
    assert result.explanation_details is not None
    assert len(result.explanation_details.strengths) == 3
    assert len(result.explanation_details.gaps) == 1
    assert result.meta.contract_version == "match-result-v1"
    assert result.meta.algorithm_variant == "matching-v0"
    assert result.meta.llm_invoked is True
    assert result.meta.explanation_mode == "llm"


def test_match_result_v1_no_explanation_fixture():
    """Verify canonical fixture without LLM explanation parses and validates cleanly."""
    fixture_path = FIXTURES_DIR / "match_result_v1_no_explanation.json"
    with fixture_path.open(encoding="utf-8") as f:
        data = json.load(f)

    result = MatchResult.model_validate(data)
    assert result.match_score == 88
    assert result.matched_skills == ["Python", "FastAPI", "PostgreSQL"]
    assert result.missing_skills == ["Docker"]
    assert "Điểm phù hợp:" in result.match_explanation
    assert result.explanation_details is not None
    assert len(result.explanation_details.strengths) == 3
    assert result.meta.contract_version == "match-result-v1"
    assert result.meta.llm_invoked is False
    assert result.meta.explanation_mode == "deterministic"


def test_candidate_rank_response_v1_fixture():
    """Verify canonical CandidateRankResponse fixture parses and embeds canonical MatchResult."""
    fixture_path = FIXTURES_DIR / "candidate_rank_response_v1.json"
    with fixture_path.open(encoding="utf-8") as f:
        data = json.load(f)

    response = CandidateRankResponse.model_validate(data)
    assert response.job_title == "Senior Python Developer"
    assert response.total_evaluated == 2
    assert len(response.ranked_candidates) == 2
    assert response.ranked_candidates[0].rank == 1
    assert response.ranked_candidates[0].candidate_id == "cand-001"
    assert isinstance(response.ranked_candidates[0].match_result, MatchResult)
    assert response.ranked_candidates[0].match_result.match_score == 88
    assert response.ranked_candidates[1].rank == 2
    assert response.ranked_candidates[1].match_result.match_score == 50
    assert response.meta.contract_version == "match-result-v1"


# =====================================================================
# 2. JSON Round-Trip Serialization & Exact Field Names
# =====================================================================


def test_match_result_v1_json_round_trip():
    """Verify MatchResult serializes to JSON and round-trips back to identical model."""
    original = MatchResult(
        match_score=92,
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Kubernetes"],
        experience_comparison="Exceeds requirement",
        education_comparison="Meets requirement",
        project_domain_relevance="High domain match",
        match_explanation="Candidate demonstrates strong backend skills.",
        meta=ResponseMeta(
            contract_version="match-result-v1",
            algorithm_variant="matching-v0",
            llm_invoked=True,
            explanation_mode="llm",
            processing_time_ms=150.0,
            correlation_id="corr-round-trip-01",
        ),
    )

    serialized_dict = original.model_dump(mode="json")
    json_str = json.dumps(serialized_dict)
    reloaded_dict = json.loads(json_str)
    reconstituted = MatchResult.model_validate(reloaded_dict)

    assert reconstituted.match_score == original.match_score
    assert reconstituted.matched_skills == original.matched_skills
    assert reconstituted.missing_skills == original.missing_skills
    assert reconstituted.experience_comparison == original.experience_comparison
    assert reconstituted.education_comparison == original.education_comparison
    assert reconstituted.project_domain_relevance == original.project_domain_relevance
    assert reconstituted.match_explanation == original.match_explanation
    assert reconstituted.meta.contract_version == "match-result-v1"
    assert reconstituted.meta.algorithm_variant == "matching-v0"
    assert reconstituted.meta.llm_invoked is True
    assert reconstituted.meta.correlation_id == "corr-round-trip-01"


def test_match_result_exact_json_field_names():
    """Verify frozen MatchResult v1 defines exact expected JSON top-level keys."""
    res = MatchResult(match_score=75)
    dumped = res.model_dump(mode="json")

    expected_exact_keys = {
        "match_score",
        "matched_skills",
        "missing_skills",
        "experience_comparison",
        "education_comparison",
        "project_domain_relevance",
        "match_explanation",
        "explanation_details",
        "status",
        "warning",
        "meta",
    }
    assert set(dumped.keys()) == expected_exact_keys


def test_response_meta_exact_json_field_names():
    """Verify frozen ResponseMeta defines exact expected JSON fields including contract_version."""
    meta = ResponseMeta(contract_version="match-result-v1")
    dumped = meta.model_dump(mode="json")

    expected_keys = {
        "contract_version",
        "algorithm_version",
        "algorithm_variant",
        "schema_version",
        "prompt_version",
        "provider",
        "model",
        "embedding_provider",
        "embedding_model",
        "llm_invoked",
        "explanation_mode",
        "processing_time_ms",
        "correlation_id",
    }
    assert expected_keys.issubset(dumped.keys())
    assert dumped["contract_version"] == "match-result-v1"


# =====================================================================
# 3. Optionality Rules & Absence Behavior
# =====================================================================


def test_match_explanation_none_is_valid():
    """Verify match_explanation=None (JSON null) is valid and serializes to null."""
    res = MatchResult(match_score=80, match_explanation=None)
    assert res.match_explanation is None

    dumped = res.model_dump(mode="json")
    assert dumped["match_explanation"] is None

    # Round-trip with null explanation
    reconstituted = MatchResult.model_validate(dumped)
    assert reconstituted.match_explanation is None


def test_match_explanation_string_is_valid():
    """Verify match_explanation with text string validates and serializes normally."""
    res = MatchResult(match_score=80, match_explanation="Detailed review.")
    assert res.match_explanation == "Detailed review."

    dumped = res.model_dump(mode="json")
    assert dumped["match_explanation"] == "Detailed review."


# =====================================================================
# 4. Score Bounds & Type Validation Enforcement
# =====================================================================


@pytest.mark.parametrize("valid_score", [0, 1, 50, 99, 100])
def test_match_score_valid_bounds(valid_score: int):
    """Verify scores between 0 and 100 inclusive are accepted."""
    res = MatchResult(match_score=valid_score)
    assert res.match_score == valid_score


@pytest.mark.parametrize("invalid_score", [-1, -50, 101, 150])
def test_match_score_invalid_bounds_rejected(invalid_score: int):
    """Verify scores < 0 or > 100 raise ValidationError."""
    with pytest.raises(ValidationError):
        MatchResult(match_score=invalid_score)


def test_match_score_nan_and_inf_rejected():
    """Verify NaN and Infinity cannot be passed as match_score."""
    for bad_val in [float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValidationError):
            MatchResult(match_score=bad_val)  # type: ignore[arg-type]


def test_match_result_missing_required_match_score():
    """Verify MatchResult without match_score raises ValidationError."""
    with pytest.raises(ValidationError):
        MatchResult.model_validate({"matched_skills": ["Python"]})


def test_match_result_invalid_skill_list_type():
    """Verify non-list passed to matched_skills raises ValidationError."""
    with pytest.raises(ValidationError):
        MatchResult.model_validate({"match_score": 80, "matched_skills": "Python"})


# =====================================================================
# 5. Candidate Ranking Schema Reuse
# =====================================================================


def test_candidate_ranking_reuses_canonical_match_result_schema():
    """Verify RankedCandidateItem.match_result embeds the exact canonical MatchResult."""
    match_res = MatchResult(
        match_score=85,
        matched_skills=["React"],
        missing_skills=[],
        match_explanation="Good match",
        meta=ResponseMeta(contract_version="match-result-v1"),
    )
    ranked_item = RankedCandidateItem(
        rank=1,
        candidate_id="cand-xyz",
        match_result=match_res,
    )
    assert isinstance(ranked_item.match_result, MatchResult)
    assert ranked_item.match_result.match_score == 85
    assert ranked_item.match_result.meta.contract_version == "match-result-v1"


# =====================================================================
# 6. OpenAPI Contract Schema Verification
# =====================================================================


def test_openapi_exposes_canonical_match_result():
    """Verify FastAPI OpenAPI schema registers canonical MatchResult and references it in routes."""
    openapi_schema = app.openapi()
    schemas = openapi_schema.get("components", {}).get("schemas", {})

    # 1. Canonical MatchResult schema exists
    assert "MatchResult" in schemas
    match_result_schema = schemas["MatchResult"]
    props = match_result_schema.get("properties", {})

    # Check required fields and types
    assert "match_score" in props
    assert props["match_score"]["type"] == "integer"
    assert props["match_score"]["minimum"] == 0.0
    assert props["match_score"]["maximum"] == 100.0

    assert "matched_skills" in props
    assert props["matched_skills"]["type"] == "array"

    assert "missing_skills" in props
    assert props["missing_skills"]["type"] == "array"

    assert "match_explanation" in props
    assert "meta" in props
    assert "$ref" in props["meta"]
    assert "ResponseMeta" in props["meta"]["$ref"]

    # 2. POST /api/v1/job/match response points to MatchResult
    post_match_op = openapi_schema.get("paths", {}).get("/api/v1/job/match", {}).get("post", {})
    match_resp_ref = (
        post_match_op.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
    )
    assert "MatchResult" in match_resp_ref

    # 3. POST /api/v1/candidates/rank response points to CandidateRankResponse
    post_rank_op = openapi_schema.get("paths", {}).get("/api/v1/candidates/rank", {}).get("post", {})
    rank_resp_ref = (
        post_rank_op.get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("$ref", "")
    )
    assert "CandidateRankResponse" in rank_resp_ref

    # 4. RankedCandidateItem references MatchResult
    assert "RankedCandidateItem" in schemas
    item_props = schemas["RankedCandidateItem"].get("properties", {})
    assert "match_result" in item_props
    assert "MatchResult" in item_props["match_result"].get("$ref", "")
