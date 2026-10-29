"""Unit tests for matching-v0 stability, active weight normalization, resilience, and DoD criteria."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.matching_service import MatchingService
from app.contracts.cv import (
    StructuredCv,
)
from app.contracts.job import StructuredJob
from app.contracts.matching import MatchResult
from app.domain.matching.demo_job import (
    DEMO_CV_HIGH,
    DEMO_CV_LOW,
    DEMO_CV_MEDIUM,
    DEMO_JOB,
)
from app.domain.matching.education_match import (
    EducationMatchResult,
    calculate_education_match,
)
from app.domain.matching.experience_match import (
    ExperienceMatchResult,
)
from app.domain.matching.scoring import (
    EDUCATION_WEIGHT,
    EXPERIENCE_WEIGHT,
    SKILL_WEIGHT,
    compute_overall_match_score,
)
from app.domain.matching.skill_match import (
    SkillMatchResult,
)
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.llm import LlmPort
from app.prompts.match_explanation_v1 import MATCH_EXPLANATION_SYSTEM_PROMPT_V1


@pytest.fixture
def mock_llm() -> MockLlmProvider:
    return MockLlmProvider()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Determinism: Same input always produces identical scores
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_matching_v0_deterministic_same_input_same_score(mock_llm: MockLlmProvider) -> None:
    """DoD: Cùng input luôn cho cùng score qua nhiều lần tính toán lặp lại."""
    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")

    scores: list[int] = []
    for _ in range(5):
        res = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=False)
        scores.append(res.match_score)

    assert len(set(scores)) == 1, f"Scores varied across runs: {scores}"
    assert scores[0] >= 90


# ─────────────────────────────────────────────────────────────────────────────
# 2. Zero LLM dependency for scoring
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_matching_v0_no_gemini_needed_for_scoring() -> None:
    """DoD: Matching không cần Gemini để tính score (toàn bộ điểm được tính bằng code tất định)."""
    # LLM mock where generate_text raises if called
    strictly_no_llm = MagicMock(spec=LlmPort)
    strictly_no_llm.provider_name = "mock"
    strictly_no_llm.model_name = "mock"
    strictly_no_llm.generate_text = AsyncMock(side_effect=AssertionError("LLM should not be called!"))

    service = MatchingService(llm=strictly_no_llm, matching_algorithm="matching-v0")
    res = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=False)

    assert isinstance(res.match_score, int)
    assert res.match_score > 0
    strictly_no_llm.generate_text.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Gemini error resilience: Error does not lose score
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_matching_v0_gemini_error_preserves_score() -> None:
    """DoD: Gemini lỗi không làm mất score (tự động chuyển sang deterministic-fallback)."""
    failing_llm = MagicMock(spec=LlmPort)
    failing_llm.provider_name = "gemini"
    failing_llm.model_name = "gemini-2.5-flash-lite"
    failing_llm.generate_text = AsyncMock(side_effect=RuntimeError("Google AI Studio 503 Service Unavailable"))

    service = MatchingService(llm=failing_llm, matching_algorithm="matching-v0")
    res = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=True)

    assert res.match_score >= 90
    assert res.meta.explanation_mode == "deterministic-fallback"
    assert res.match_explanation is not None
    assert "Điểm phù hợp:" in res.match_explanation


# ─────────────────────────────────────────────────────────────────────────────
# 4. Job missing education: Does not award free 20 points
# ─────────────────────────────────────────────────────────────────────────────


def test_job_missing_education_does_not_award_free_twenty_points() -> None:
    """DoD: Job thiếu education không tự tặng 20 điểm."""
    # When Job does not require education:
    edu_res = calculate_education_match(candidate_degrees=[], required_education=None)
    assert edu_res.is_active is False
    assert edu_res.score == 100.0  # internal neutral

    # Candidate with 0 skills and 0 experience
    skill_zero = SkillMatchResult(
        skill_score=0.0,
        matched_required_skills=[],
        missing_required_skills=["Python"],
        is_active=True,
    )
    exp_zero = ExperienceMatchResult(
        score=0.0, candidate_years=0.0, required_years=3.0, comparison_text="", is_active=True
    )

    overall = compute_overall_match_score(skill_res=skill_zero, exp_res=exp_zero, edu_res=edu_res)

    # Inactive education weight is 0.0, active weights are 50/80 and 30/80
    assert overall.education_weight == 0.0
    assert overall.skill_weight == round(0.50 / 0.80, 4)
    assert overall.experience_weight == round(0.30 / 0.80, 4)
    # Final score MUST be 0, NOT 20!
    assert overall.final_score == 0


def test_job_missing_education_normalizes_active_weights() -> None:
    """Verify active weight normalization when education is missing (Skill 50/80, Exp 30/80)."""
    edu_res = calculate_education_match(candidate_degrees=["Kỹ sư"], required_education="")
    assert edu_res.is_active is False

    # Candidate with 80% skills and 60% experience
    skill_res = SkillMatchResult(skill_score=80.0, is_active=True)
    exp_res = ExperienceMatchResult(
        score=60.0, candidate_years=3.0, required_years=5.0, comparison_text="", is_active=True
    )

    overall = compute_overall_match_score(skill_res=skill_res, exp_res=exp_res, edu_res=edu_res)

    # 80.0 * (50/80) + 60.0 * (30/80) = 50.0 + 22.5 = 72.5 -> 72 (round-to-even)
    expected_score = round((80.0 * (0.50 / 0.80)) + (60.0 * (0.30 / 0.80)))
    assert overall.final_score == expected_score
    assert overall.final_score == 72


# ─────────────────────────────────────────────────────────────────────────────
# 5. Dynamic Active Weight Normalization across criteria combinations
# ─────────────────────────────────────────────────────────────────────────────


def test_active_weight_normalization_skill_only() -> None:
    """When only Skill is required (no exp, no edu), Skill weight is normalized to 1.0 (100%)."""
    skill_res = SkillMatchResult(skill_score=75.0, is_active=True)
    exp_res = ExperienceMatchResult(
        score=100.0, candidate_years=1.0, required_years=0.0, comparison_text="", is_active=False
    )
    edu_res = EducationMatchResult(score=100.0, comparison_text="", is_active=False)

    overall = compute_overall_match_score(skill_res=skill_res, exp_res=exp_res, edu_res=edu_res)

    assert overall.skill_weight == 1.0
    assert overall.experience_weight == 0.0
    assert overall.education_weight == 0.0
    assert overall.final_score == 75


def test_active_weight_normalization_experience_only() -> None:
    """When only Experience is required (no skills, no edu), Experience weight is normalized to 1.0 (100%)."""
    skill_res = SkillMatchResult(skill_score=100.0, is_active=False)
    exp_res = ExperienceMatchResult(
        score=80.0, candidate_years=2.4, required_years=3.0, comparison_text="", is_active=True
    )
    edu_res = EducationMatchResult(score=100.0, comparison_text="", is_active=False)

    overall = compute_overall_match_score(skill_res=skill_res, exp_res=exp_res, edu_res=edu_res)

    assert overall.skill_weight == 0.0
    assert overall.experience_weight == 1.0
    assert overall.education_weight == 0.0
    assert overall.final_score == 80


def test_active_weight_normalization_all_active() -> None:
    """When all 3 criteria are required, weights remain standard 0.50, 0.30, 0.20."""
    skill_res = SkillMatchResult(skill_score=100.0, is_active=True)
    exp_res = ExperienceMatchResult(
        score=100.0, candidate_years=3.0, required_years=3.0, comparison_text="", is_active=True
    )
    edu_res = EducationMatchResult(score=100.0, comparison_text="", is_active=True)

    overall = compute_overall_match_score(skill_res=skill_res, exp_res=exp_res, edu_res=edu_res)

    assert overall.skill_weight == SKILL_WEIGHT
    assert overall.experience_weight == EXPERIENCE_WEIGHT
    assert overall.education_weight == EDUCATION_WEIGHT
    assert overall.final_score == 100


# ─────────────────────────────────────────────────────────────────────────────
# 6. Insufficient Job Data Handling
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_insufficient_job_data_warning_and_status(mock_llm: MockLlmProvider) -> None:
    """DoD: JD không đủ thông tin (không có skill và exp requirement) sinh status và warning rõ ràng."""
    insufficient_job = StructuredJob(
        title="Nhân viên thời vụ",
        description="Mô tả công việc chung chung không yêu cầu kỹ năng cụ thể.",
        required_skills=[],
        preferred_skills=[],
        minimum_experience_years=None,
        education_requirement=None,
    )

    cv = StructuredCv(
        full_name="Nguyễn Văn Test",
        skills=["Python"],
    )

    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")
    res = await service.match(cv=cv, job=insufficient_job, generate_explanation=False)

    assert res.status == "insufficient_job_data"
    assert res.warning == "JD chưa có đủ tiêu chí để chấm độ phù hợp đáng tin cậy."
    assert "JD chưa có đủ tiêu chí" in (res.match_explanation or "")


# ─────────────────────────────────────────────────────────────────────────────
# 7. Hierarchy Verification: High CV > Medium CV > Low CV
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_demo_job_produces_strict_hierarchy_high_medium_low(mock_llm: MockLlmProvider) -> None:
    """DoD: High CV > Medium CV > Low CV trên Demo Job chuẩn."""
    service = MatchingService(llm=mock_llm, matching_algorithm="matching-v0")

    high_res = await service.match(cv=DEMO_CV_HIGH, job=DEMO_JOB, generate_explanation=False)
    med_res = await service.match(cv=DEMO_CV_MEDIUM, job=DEMO_JOB, generate_explanation=False)
    low_res = await service.match(cv=DEMO_CV_LOW, job=DEMO_JOB, generate_explanation=False)

    # Strictly descending
    assert high_res.match_score > med_res.match_score > low_res.match_score, (
        f"Hierarchy violated: High={high_res.match_score}, Med={med_res.match_score}, Low={low_res.match_score}"
    )

    # Calibrated ranges
    assert high_res.match_score >= 85, f"High CV score ({high_res.match_score}) below 85"
    assert 50 <= med_res.match_score <= 75, f"Medium CV score ({med_res.match_score}) not in [50, 75]"
    assert low_res.match_score <= 35, f"Low CV score ({low_res.match_score}) above 35"


# ─────────────────────────────────────────────────────────────────────────────
# 8. Terminology: Điểm không được gọi là xác suất trúng tuyển
# ─────────────────────────────────────────────────────────────────────────────


def test_terminology_forbids_probability_of_being_hired() -> None:
    """DoD: Điểm không được gọi là xác suất trúng tuyển."""
    # Prompt rule 8 explicitly bans 'xác suất trúng tuyển'
    assert "xác suất trúng tuyển" in MATCH_EXPLANATION_SYSTEM_PROMPT_V1
    assert "Do NOT refer to the match score as a hiring probability" in MATCH_EXPLANATION_SYSTEM_PROMPT_V1

    # Contract documentation asserts match_score is compatibility index, NOT hiring probability
    field_desc = MatchResult.model_fields["match_score"].description or ""
    assert "NOT a CV quality score, probability of being hired" in field_desc
