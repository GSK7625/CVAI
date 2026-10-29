"""Unit tests for matching-v0 baseline formula, weights, and scoring calculation."""

import pytest

from app.domain.matching.education_match import EducationMatchResult
from app.domain.matching.experience_match import ExperienceMatchResult
from app.domain.matching.scoring import (
    EDUCATION_WEIGHT,
    EXPERIENCE_WEIGHT,
    MATCHING_ALGORITHM_VERSION,
    SKILL_WEIGHT,
    compute_overall_match_score,
)
from app.domain.matching.skill_match import SkillMatchResult


def test_matching_v0_weights_permanent_lock():
    """
    PERMANENT INVARIANT: matching-v0 weights MUST remain:
    Skill: 50% (0.50)
    Experience: 30% (0.30)
    Education: 20% (0.20)
    Sum: exactly 1.0 (100%)
    """
    assert SKILL_WEIGHT == 0.50
    assert EXPERIENCE_WEIGHT == 0.30
    assert EDUCATION_WEIGHT == 0.20

    total = SKILL_WEIGHT + EXPERIENCE_WEIGHT + EDUCATION_WEIGHT
    assert pytest.approx(total, abs=1e-6) == 1.0


def test_compute_overall_match_score_v0_perfect():
    """Verify v0 formula with 100 on all components yields 100."""
    skill_res = SkillMatchResult(skill_score=100.0, matched_required_skills=["Python"], missing_required_skills=[])
    exp_res = ExperienceMatchResult(score=100.0, candidate_years=5.0, required_years=3.0, comparison_text="Valid")
    edu_res = EducationMatchResult(score=100.0, comparison_text="Valid")

    res = compute_overall_match_score(
        skill_res=skill_res,
        exp_res=exp_res,
        edu_res=edu_res,
    )

    assert res.final_score == 100
    assert res.algorithm_version == MATCHING_ALGORITHM_VERSION
    assert res.skill_weight == 0.50
    assert res.experience_weight == 0.30
    assert res.education_weight == 0.20


def test_compute_overall_match_score_v0_weighted_calculation():
    """
    Verify v0 formula: (Skill * 0.50) + (Experience * 0.30) + (Education * 0.20)
    Skill: 80.0 * 0.50 = 40.0
    Experience: 60.0 * 0.30 = 18.0
    Education: 50.0 * 0.20 = 10.0
    Total = 40.0 + 18.0 + 10.0 = 68.0 -> 68
    """
    skill_res = SkillMatchResult(skill_score=80.0, matched_required_skills=["Python"], missing_required_skills=[])
    exp_res = ExperienceMatchResult(score=60.0, candidate_years=3.0, required_years=5.0, comparison_text="Shortage")
    edu_res = EducationMatchResult(score=50.0, comparison_text="Mismatch")

    res = compute_overall_match_score(
        skill_res=skill_res,
        exp_res=exp_res,
        edu_res=edu_res,
    )

    assert res.final_score == 68
    assert res.skill_score == 80.0
    assert res.experience_score == 60.0
    assert res.education_score == 50.0
