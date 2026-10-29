"""Unit tests for Match Explanation constraints, temperature, score bands, and 4-layer defense."""

from unittest.mock import AsyncMock, MagicMock

from pydantic import ValidationError
import pytest

from app.application.matching_service import MatchingService
from app.contracts.matching import (
    MatchExplanation,
    MatchGap,
    MatchStrength,
)
from app.domain.matching.demo_job import (
    DEMO_CV_HIGH,
    DEMO_CV_LOW,
    DEMO_JOB,
)
from app.ports.llm import LlmPort
from app.prompts.match_explanation_v1 import (
    EXPECTED_BAND_LABELS,
    FORBIDDEN_LOW_SCORE_PHRASES,
    build_deterministic_structured_explanation,
    get_score_band,
    validate_explanation_tone,
    validate_grounding,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Temperature is strictly 0.0 and Structured Generation Invoked
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_explanation_generation_uses_temperature_zero() -> None:
    """Verify LLM explanation generation is called with temperature=0.0 using generate_structured."""
    mock_llm = MagicMock(spec=LlmPort)
    mock_llm.provider_name = "gemini"
    mock_llm.model_name = "gemini-2.5-flash-lite"
    mock_llm.generate_structured = AsyncMock(
        return_value=MatchExplanation(
            summary="Mức độ phù hợp cao theo các tiêu chí đã được hệ thống đánh giá.",
            strengths=[
                MatchStrength(
                    item="Python",
                    statement="CV có đề cập kỹ năng Python.",
                    evidence_source="cv.skills",
                    evidence_text="Python",
                )
            ],
            gaps=[
                MatchGap(
                    requirement="Kubernetes",
                    statement="Chưa có thông tin về kỹ năng ưu tiên Kubernetes.",
                )
            ],
            recommendations=["Tiếp tục duy trì và nâng cao các kỹ năng chuyên môn."],
        )
    )

    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")
    await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=True)

    assert mock_llm.generate_structured.call_count == 1
    call_kwargs = mock_llm.generate_structured.call_args.kwargs
    assert call_kwargs.get("temperature") == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Score Bands Categorization (All Boundary Scores)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("score", "expected_code", "expected_label"),
    [
        (0, "low", "Mức độ phù hợp thấp"),
        (39, "low", "Mức độ phù hợp thấp"),
        (40, "partial", "Phù hợp một phần"),
        (59, "partial", "Phù hợp một phần"),
        (60, "good", "Mức độ phù hợp tốt"),
        (79, "good", "Mức độ phù hợp tốt"),
        (80, "strong", "Mức độ phù hợp cao"),
        (100, "strong", "Mức độ phù hợp cao"),
    ],
)
def test_score_bands_boundary_classification(score: int, expected_code: str, expected_label: str) -> None:
    """Verify exact score band codes and labels at all critical boundary values."""
    band_code, band_label = get_score_band(score)
    assert band_code == expected_code
    assert band_label == expected_label


# ─────────────────────────────────────────────────────────────────────────────
# 3. Tone & Anti-Contradiction Validation Across All Fields
# ─────────────────────────────────────────────────────────────────────────────


def test_validate_explanation_tone_rejects_missing_mandatory_band_label() -> None:
    """Verify validator rejects summary missing the exact required band phrase."""
    exp_low_without_label = MatchExplanation(
        summary="Ứng viên còn thiếu nhiều kỹ năng nhưng có tiềm năng học hỏi.",
        strengths=[],
        gaps=[],
        recommendations=[],
    )
    assert validate_explanation_tone(25, exp_low_without_label) is False

    exp_low_with_label = MatchExplanation(
        summary="Mức độ phù hợp thấp. Ứng viên chưa đáp ứng các kỹ năng cốt lõi.",
        strengths=[],
        gaps=[],
        recommendations=[],
    )
    assert validate_explanation_tone(25, exp_low_with_label) is True


def test_validate_explanation_tone_checks_strengths_and_all_fields() -> None:
    """Verify validator detects forbidden praise hidden inside strengths, evidence, or recommendations."""
    for phrase in FORBIDDEN_LOW_SCORE_PHRASES:
        # Forbidden phrase placed in strengths.statement
        exp_bad_strength = MatchExplanation(
            summary="Mức độ phù hợp thấp. Ứng viên còn thiếu kỹ năng.",
            strengths=[
                MatchStrength(
                    item="Python",
                    statement=f"Ứng viên là một lựa chọn {phrase} cho dự án.",
                    evidence_source="cv.skills",
                    evidence_text="Python",
                )
            ],
            gaps=[],
            recommendations=[],
        )
        assert validate_explanation_tone(35, exp_bad_strength) is False

        # Forbidden phrase placed in recommendations
        exp_bad_rec = MatchExplanation(
            summary="Mức độ phù hợp thấp. Ứng viên còn thiếu kỹ năng.",
            strengths=[],
            gaps=[],
            recommendations=[f"Đây là {phrase} mà công ty nên cân nhắc tuyển."],
        )
        assert validate_explanation_tone(35, exp_bad_rec) is False


def test_validate_explanation_tone_rejects_good_claim_on_partial_score() -> None:
    """Verify score=55 (partial) rejects summary claiming good fit."""
    exp_partial_claiming_good = MatchExplanation(
        summary="Mức độ phù hợp tốt. Ứng viên đáp ứng phần lớn kỹ năng.",
        strengths=[],
        gaps=[],
        recommendations=[],
    )
    assert validate_explanation_tone(55, exp_partial_claiming_good) is False


def test_validate_explanation_tone_rejects_hiring_guarantees_on_high_scores() -> None:
    """Verify high scores (>= 80) reject definitive hiring guarantees."""
    exp_high_guarantee = MatchExplanation(
        summary="Mức độ phù hợp cao. Ứng viên chắc chắn trúng tuyển vị trí này.",
        strengths=[],
        gaps=[],
        recommendations=[],
    )
    assert validate_explanation_tone(90, exp_high_guarantee) is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. Grounding Set Validation
# ─────────────────────────────────────────────────────────────────────────────


def test_validate_grounding_rejects_hallucinated_skill() -> None:
    """Verify validator rejects explanation when LLM mentions a skill not in matched skills."""
    explanation = MatchExplanation(
        summary="Mức độ phù hợp tốt.",
        strengths=[
            MatchStrength(
                item="Rust",  # Hallucinated skill
                statement="CV có đề cập Rust.",
                evidence_source="cv.skills",
                evidence_text="Rust",
            )
        ],
        gaps=[],
        recommendations=[],
    )
    assert validate_grounding(explanation, matched_skills=["Python", "FastAPI"], missing_skills=[]) is False


def test_validate_grounding_requires_gaps_when_missing_skills_exist() -> None:
    """Verify validator rejects explanation when missing skills exist but LLM returned zero gaps."""
    explanation = MatchExplanation(
        summary="Mức độ phù hợp thấp.",
        strengths=[],
        gaps=[],  # Omitted gaps
        recommendations=[],
    )
    assert validate_grounding(explanation, matched_skills=["Python"], missing_skills=["Docker", "K8s"]) is False


def test_validate_grounding_accepts_valid_subset() -> None:
    """Verify validator passes when returned skills are valid subsets of evaluated data."""
    explanation = MatchExplanation(
        summary="Mức độ phù hợp tốt.",
        strengths=[
            MatchStrength(
                item="Python",
                statement="CV có đề cập kỹ năng Python.",
                evidence_source="cv.skills",
                evidence_text="Python",
            )
        ],
        gaps=[
            MatchGap(
                requirement="Docker",
                statement="Chưa đủ bằng chứng về Docker.",
            )
        ],
        recommendations=[],
    )
    assert (
        validate_grounding(
            explanation,
            matched_skills=["Python", "FastAPI (Preferred)"],
            missing_skills=["Docker", "Kubernetes"],
        )
        is True
    )


def test_critical_missing_skills_must_be_covered_in_gaps() -> None:
    """Verify validate_grounding rejects explanations that omit critical missing required skills."""
    explanation_partial = MatchExplanation(
        summary="Mức độ phù hợp thấp.",
        strengths=[],
        gaps=[
            MatchGap(
                requirement="Python",
                statement="Chưa đủ bằng chứng về kỹ năng bắt buộc Python.",
            )
        ],
        recommendations=[],
    )
    # Required skills missing: ["Python", "FastAPI"]
    # Explanation only reported "Python", omitting critical required "FastAPI"
    assert (
        validate_grounding(
            explanation=explanation_partial,
            matched_skills=[],
            missing_skills=["Python", "FastAPI"],
            missing_required_skills=["Python", "FastAPI"],
        )
        is False
    )

    # When all critical missing required skills are covered in gaps:
    explanation_full = MatchExplanation(
        summary="Mức độ phù hợp thấp.",
        strengths=[],
        gaps=[
            MatchGap(requirement="Python", statement="Chưa đủ bằng chứng về Python."),
            MatchGap(requirement="FastAPI", statement="Chưa đủ bằng chứng về FastAPI."),
        ],
        recommendations=[],
    )
    assert (
        validate_grounding(
            explanation=explanation_full,
            matched_skills=[],
            missing_skills=["Python", "FastAPI"],
            missing_required_skills=["Python", "FastAPI"],
        )
        is True
    )


def test_forbidden_phrase_in_strength_item_caught() -> None:
    """Verify forbidden phrase placed in strength.item is collected and rejected."""
    explanation = MatchExplanation(
        summary="Mức độ phù hợp thấp.",
        strengths=[
            MatchStrength(
                item="Ứng viên mạnh trong Python",
                statement="CV có đề cập Python.",
                evidence_source="cv.skills",
                evidence_text="Python",
            )
        ],
        gaps=[
            MatchGap(
                requirement="Kubernetes",
                statement="Thiếu Kubernetes.",
            )
        ],
        recommendations=[],
    )
    # Even though summary has 'mức độ phù hợp thấp', strength.item contains 'ứng viên mạnh'
    assert validate_explanation_tone(match_score=35, explanation=explanation) is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. Strict Schema Validation & Extra Fields Rejection
# ─────────────────────────────────────────────────────────────────────────────


def test_schema_rejects_invalid_evidence_source() -> None:
    """Verify MatchStrength only permits cv.skills, cv.technologies, cv.projects."""
    # Valid sources succeed
    for valid_source in ("cv.skills", "cv.technologies", "cv.projects"):
        s = MatchStrength(
            item="Python",
            statement="CV có Python.",
            evidence_source=valid_source,  # type: ignore[arg-type]
            evidence_text="Python",
        )
        assert s.evidence_source == valid_source

    # Invalid sources rejected (including legacy cv.experience and cv.education)
    for invalid_source in ("cv.experience", "cv.education", "cv.hobbies", "custom"):
        with pytest.raises(ValidationError):
            MatchStrength(
                item="Python",
                statement="CV có Python.",
                evidence_source=invalid_source,  # type: ignore[arg-type]
                evidence_text="Python",
            )


def test_schema_rejects_extra_fields() -> None:
    """Verify MatchExplanation rejects unexpected fields (extra='forbid')."""
    with pytest.raises(ValidationError):
        MatchExplanation(
            summary="Mức độ phù hợp tốt.",
            strengths=[],
            gaps=[],
            recommendations=[],
            match_score=85,  # Extra forbidden field
        )


def test_schema_does_not_contain_match_score() -> None:
    """Verify match_score is absent from MatchExplanation output schema."""
    assert "match_score" not in MatchExplanation.model_fields


# ─────────────────────────────────────────────────────────────────────────────
# 6. Fallback Mechanics & Formatting
# ─────────────────────────────────────────────────────────────────────────────


def test_deterministic_explanation_fallback_structure_and_tone() -> None:
    """Verify fallback creates valid MatchExplanation without soft invented evidence."""
    fb_low = build_deterministic_structured_explanation(
        final_score=25,
        matched_skills=["Python"],
        missing_required_skills=["Kubernetes", "AWS"],
        missing_preferred_skills=["Docker"],
    )
    assert EXPECTED_BAND_LABELS["low"] in fb_low.summary.casefold()
    assert len(fb_low.strengths) == 1
    assert fb_low.strengths[0].evidence_source == "cv.skills"
    assert fb_low.strengths[0].evidence_text == "Python"
    assert len(fb_low.gaps) == 3

    # High score fallback should be cautious and objective
    fb_high = build_deterministic_structured_explanation(
        final_score=85,
        matched_skills=["Python", "FastAPI"],
        missing_required_skills=[],
        missing_preferred_skills=[],
    )
    assert EXPECTED_BAND_LABELS["strong"] in fb_high.summary.casefold()
    assert "xác minh" in fb_high.summary.casefold()


def test_deterministic_fallback_more_than_ten_missing_skills() -> None:
    """Verify fallback caps gaps at 10 and documents overflow in summary."""
    missing_req = [f"Skill_{i}" for i in range(15)]
    fb = build_deterministic_structured_explanation(
        final_score=20,
        matched_skills=[],
        missing_required_skills=missing_req,
        missing_preferred_skills=[],
    )
    assert len(fb.gaps) == 10
    assert "Ngoài ra còn thiếu 5 kỹ năng bắt buộc khác" in fb.summary


@pytest.mark.asyncio
async def test_low_score_contradiction_triggers_deterministic_fallback() -> None:
    """Verify contradictory praise on low score triggers deterministic fallback."""
    mock_llm = MagicMock(spec=LlmPort)
    mock_llm.provider_name = "gemini"
    mock_llm.model_name = "gemini-2.5-flash-lite"
    mock_llm.generate_structured = AsyncMock(
        return_value=MatchExplanation(
            summary="Ứng viên rất phù hợp và là ứng viên lý tưởng cho công việc.",
            strengths=[],
            gaps=[],
            recommendations=[],
        )
    )

    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")
    res = await service.match(cv=DEMO_CV_LOW, job=DEMO_JOB, generate_explanation=True)

    assert res.match_score < 40
    assert res.meta.explanation_mode == "deterministic-fallback"
    assert "rất phù hợp" not in (res.match_explanation or "")
    assert "ứng viên lý tưởng" not in (res.match_explanation or "")
    assert "Mức độ phù hợp thấp." in (res.match_explanation or "")
    assert res.explanation_details is not None
    assert EXPECTED_BAND_LABELS["low"] in res.explanation_details.summary.casefold()


@pytest.mark.asyncio
async def test_llm_plain_text_or_exception_triggers_deterministic_fallback() -> None:
    """Verify that if LLM returns plain text or raises exception, fallback is triggered."""
    mock_llm = MagicMock(spec=LlmPort)
    mock_llm.provider_name = "gemini"
    mock_llm.model_name = "gemini-2.5-flash-lite"
    # LLM returns plain text string instead of MatchExplanation
    mock_llm.generate_structured = AsyncMock(return_value="Đây là văn bản tự do không phải JSON.")

    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")
    res = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=True)

    assert res.meta.explanation_mode == "deterministic-fallback"
    assert res.explanation_details is not None
    assert EXPECTED_BAND_LABELS["strong"] in res.explanation_details.summary.casefold()


@pytest.mark.asyncio
async def test_explanation_mode_provenance() -> None:
    """Verify explanation_mode accurately reflects deterministic, llm, and deterministic-fallback."""
    # 1. generate_explanation=False -> deterministic
    llm_mock = MagicMock(spec=LlmPort)
    llm_mock.provider_name = "mock"
    llm_mock.model_name = "mock"
    service = MatchingService(llm=llm_mock, matching_algorithm="matching-v0")
    res_no_llm = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=False)
    assert res_no_llm.meta.explanation_mode == "deterministic"
    assert res_no_llm.meta.llm_invoked is False
    assert res_no_llm.explanation_details is not None

    # 2. generate_explanation=True + LLM success -> llm
    llm_mock.generate_structured = AsyncMock(
        return_value=MatchExplanation(
            summary="Mức độ phù hợp cao theo các tiêu chí đã được hệ thống đánh giá.",
            strengths=[
                MatchStrength(
                    item="Python",
                    statement="CV có đề cập kỹ năng Python.",
                    evidence_source="cv.skills",
                    evidence_text="Python",
                )
            ],
            gaps=[
                MatchGap(
                    requirement="Kubernetes",
                    statement="Chưa có thông tin về kỹ năng ưu tiên Kubernetes.",
                )
            ],
            recommendations=["Tiếp tục duy trì và nâng cao các kỹ năng chuyên môn."],
        )
    )
    res_llm = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=True)
    assert res_llm.meta.explanation_mode == "llm"
    assert res_llm.meta.llm_invoked is True
    assert res_llm.explanation_details is not None

    # 3. generate_explanation=True + LLM error -> deterministic-fallback
    llm_mock.generate_structured = AsyncMock(side_effect=RuntimeError("Timeout"))
    res_fallback = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=True)
    assert res_fallback.meta.explanation_mode == "deterministic-fallback"
    assert res_fallback.meta.llm_invoked is True
    assert res_fallback.explanation_details is not None
