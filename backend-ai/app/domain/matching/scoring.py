"""Comprehensive match score aggregation with centralized, inspectable weights.

DISCLAIMER / CALIBRATION NOTE:
The weights configured below (Skill 50%, Experience 30%, Education 20%) represent
an initial heuristic engineering baseline ('matching-v0'). They are engineering
assumptions, NOT final product-approved rules or statistically calibrated parameters.
Systematic calibration against labeled recruitment outcome datasets is required
in subsequent phases.
"""

from dataclasses import dataclass

from app.domain.matching.education_match import EducationMatchResult
from app.domain.matching.experience_match import ExperienceMatchResult
from app.domain.matching.project_match import ProjectRelevanceResult
from app.domain.matching.skill_match import SkillMatchResult

# Matching Engine algorithm version identifier
MATCHING_ALGORITHM_VERSION: str = "matching-v0"

# Centralized, inspectable baseline weights for Matching Engine (matching-v0)
SKILL_WEIGHT: float = 0.50
EXPERIENCE_WEIGHT: float = 0.30
EDUCATION_WEIGHT: float = 0.20


@dataclass(frozen=True)
class OverallMatchScore:
    """Consolidated match scoring calculation."""

    final_score: int
    skill_score: float
    experience_score: float
    education_score: float
    algorithm_version: str = MATCHING_ALGORITHM_VERSION
    skill_weight: float = SKILL_WEIGHT
    experience_weight: float = EXPERIENCE_WEIGHT
    education_weight: float = EDUCATION_WEIGHT


def compute_overall_match_score(
    skill_res: SkillMatchResult,
    exp_res: ExperienceMatchResult,
    edu_res: EducationMatchResult,
) -> OverallMatchScore:
    """
    Compute weighted total match score (0-100) combining skills, experience, and education.

    Formula (matching-v0):
    Base weights: Skill 0.50, Experience 0.30, Education 0.20.
    Active Weight Normalization:
    - Criteria without requirements in the job posting are inactive (is_active=False).
    - If a criterion is inactive, its weight is excluded and remaining active weights
      are normalized to sum to 1.0 (100%).
    - If all criteria are inactive (insufficient job data), the score is 0.
    """
    active_weights: dict[str, float] = {}
    if getattr(skill_res, "is_active", True):
        active_weights["skill"] = SKILL_WEIGHT
    if getattr(exp_res, "is_active", True):
        active_weights["experience"] = EXPERIENCE_WEIGHT
    if getattr(edu_res, "is_active", True):
        active_weights["education"] = EDUCATION_WEIGHT

    total_active_weight = sum(active_weights.values())

    if total_active_weight <= 0.0:
        return OverallMatchScore(
            final_score=0,
            skill_score=skill_res.skill_score,
            experience_score=exp_res.score,
            education_score=edu_res.score,
            algorithm_version=MATCHING_ALGORITHM_VERSION,
            skill_weight=0.0,
            experience_weight=0.0,
            education_weight=0.0,
        )

    norm_skill_weight = active_weights.get("skill", 0.0) / total_active_weight
    norm_exp_weight = active_weights.get("experience", 0.0) / total_active_weight
    norm_edu_weight = active_weights.get("education", 0.0) / total_active_weight

    weighted_total = (
        (skill_res.skill_score * norm_skill_weight)
        + (exp_res.score * norm_exp_weight)
        + (edu_res.score * norm_edu_weight)
    )

    final_score = round(max(0.0, min(100.0, weighted_total)))

    return OverallMatchScore(
        final_score=final_score,
        skill_score=skill_res.skill_score,
        experience_score=exp_res.score,
        education_score=edu_res.score,
        algorithm_version=MATCHING_ALGORITHM_VERSION,
        skill_weight=round(norm_skill_weight, 4),
        experience_weight=round(norm_exp_weight, 4),
        education_weight=round(norm_edu_weight, 4),
    )


# ─────────────────────────────────────────────────────────────────────────────
# matching-v1-experimental (UNCALIBRATED EXPERIMENTAL WEIGHTS)
# ─────────────────────────────────────────────────────────────────────────────
# DISCLAIMER / CALIBRATION NOTE:
# The weights configured below (Skill 40%, Experience 20%, Education 10%,
# Project 10%, Semantic 20%) represent an experimental hypothesis ('matching-v1-experimental').
# These are UNCALIBRATED EXPERIMENTAL WEIGHTS and must NOT be described as statistically
# validated, optimal, or production-calibrated. Component scores are heuristic and are
# not statistically independent.
# ─────────────────────────────────────────────────────────────────────────────

MATCHING_V1_ALGORITHM_VERSION: str = "matching-v1-experimental"

V1_SKILL_WEIGHT: float = 0.40
V1_EXPERIENCE_WEIGHT: float = 0.20
V1_EDUCATION_WEIGHT: float = 0.10
V1_PROJECT_WEIGHT: float = 0.10
V1_SEMANTIC_WEIGHT: float = 0.20


@dataclass(frozen=True)
class OverallMatchScoreV1:
    """Consolidated match scoring calculation for matching-v1-experimental."""

    final_score: int
    skill_score: float
    experience_score: float
    education_score: float
    project_score: float
    semantic_score: float
    algorithm_version: str = MATCHING_V1_ALGORITHM_VERSION
    skill_weight: float = V1_SKILL_WEIGHT
    experience_weight: float = V1_EXPERIENCE_WEIGHT
    education_weight: float = V1_EDUCATION_WEIGHT
    project_weight: float = V1_PROJECT_WEIGHT
    semantic_weight: float = V1_SEMANTIC_WEIGHT


def compute_overall_match_score_v1(
    skill_res: SkillMatchResult,
    exp_res: ExperienceMatchResult,
    edu_res: EducationMatchResult,
    proj_res: ProjectRelevanceResult,
    semantic_score: float,
) -> OverallMatchScoreV1:
    """
    Compute weighted total match score (0-100) under matching-v1-experimental.

    Formula (matching-v1-experimental, UNCALIBRATED EXPERIMENTAL WEIGHTS):
    Score = (Skill * 0.40) + (Experience * 0.20) + (Education * 0.10) + (Project * 0.10) + (Semantic * 0.20)
    """
    weighted_total = (
        (skill_res.skill_score * V1_SKILL_WEIGHT)
        + (exp_res.score * V1_EXPERIENCE_WEIGHT)
        + (edu_res.score * V1_EDUCATION_WEIGHT)
        + (proj_res.project_score * V1_PROJECT_WEIGHT)
        + (semantic_score * V1_SEMANTIC_WEIGHT)
    )

    final_score = round(max(0.0, min(100.0, weighted_total)))

    return OverallMatchScoreV1(
        final_score=final_score,
        skill_score=skill_res.skill_score,
        experience_score=exp_res.score,
        education_score=edu_res.score,
        project_score=proj_res.project_score,
        semantic_score=semantic_score,
        algorithm_version=MATCHING_V1_ALGORITHM_VERSION,
    )
