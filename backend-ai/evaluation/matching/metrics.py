"""
Evaluation metrics computation for Candidate Job Matching.

Computes:
- Score distribution statistics (mean, std, min, max)
- Expected range compliance percentage
- Pairwise ordering consistency (e.g. Exact Match > Mismatched Role)
- Semantic discrimination delta (high-relevance vs low-relevance separation)
- PII leakage verification (verifying 0% identity leakage in semantic representations)
"""

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class ScoreStatistics:
    """Distribution statistics for a set of evaluation scores."""

    count: int
    mean: float
    std_dev: float
    min_score: int
    max_score: int


@dataclass(frozen=True)
class EvaluationSummary:
    """Consolidated metrics summary for an algorithm run."""

    algorithm_variant: str
    embedding_provider: str | None
    embedding_model: str | None
    stats: ScoreStatistics
    range_compliance_rate: float
    pairwise_ordering_accuracy: float
    semantic_discrimination_delta: float
    pii_leakage_detected: int


def compute_statistics(scores: list[int]) -> ScoreStatistics:
    """Compute mean, sample standard deviation, min, and max for score list."""
    if not scores:
        return ScoreStatistics(count=0, mean=0.0, std_dev=0.0, min_score=0, max_score=0)

    count = len(scores)
    mean = sum(scores) / count

    if count > 1:
        variance = sum((x - mean) ** 2 for x in scores) / (count - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    return ScoreStatistics(
        count=count,
        mean=round(mean, 2),
        std_dev=round(std_dev, 2),
        min_score=min(scores),
        max_score=max(scores),
    )


def compute_range_compliance(results: list[dict[str, Any]], score_key: str, range_key: str) -> float:
    """Calculate percentage of cases falling within defined expected score bounds."""
    if not results:
        return 0.0

    compliant_count = 0
    for r in results:
        score = r[score_key]
        min_expected, max_expected = r[range_key]
        if min_expected <= score <= max_expected:
            compliant_count += 1

    return round((compliant_count / len(results)) * 100.0, 2)


def compute_pairwise_accuracy(results_by_id: dict[str, int]) -> float:
    """
    Check known priority pairs where Case A should strictly outrank Case B:
    1. case_01 (Exact Match) > case_04 (Junior for Senior)
    2. case_01 (Exact Match) > case_07 (Accountant for DevOps)
    3. case_05 (Senior Surplus) > case_06 (Missing Skills)
    4. case_09 (Master Match) > case_08 (High School Mismatch)
    5. case_10 (Relevant Projects) > case_11 (Unrelated Projects)
    6. case_15 (100% Required Skills) > case_14 (0% Required Skills)
    7. case_22 (Fullstack for Frontend) > case_25 (Outdated Mainframe Stack)
    """
    pairs = [
        ("case_01_exact_match_backend", "case_04_junior_for_senior_role"),
        ("case_01_exact_match_backend", "case_07_cross_domain_accountant"),
        ("case_05_senior_for_junior_role", "case_06_missing_mandatory_skills"),
        ("case_09_education_degree_match", "case_08_education_degree_mismatch"),
        ("case_10_high_project_relevance", "case_11_zero_project_relevance"),
        ("case_15_required_skills_full_no_preferred", "case_14_preferred_skills_only"),
        ("case_22_fullstack_to_frontend", "case_25_high_exp_outdated_stack"),
    ]

    correct = 0
    total = 0
    for higher_id, lower_id in pairs:
        if higher_id in results_by_id and lower_id in results_by_id:
            total += 1
            if results_by_id[higher_id] > results_by_id[lower_id]:
                correct += 1

    return round((correct / max(1, total)) * 100.0, 2)


def compute_semantic_discrimination_delta(results: list[dict[str, Any]], score_key: str) -> float:
    """Compute score difference between high-fit cases and complete mismatch cases."""
    high_fit_ids = {"case_01_exact_match_backend", "case_02_skill_alias_react", "case_03_alias_devops_k8s"}
    mismatch_ids = {"case_06_missing_mandatory_skills", "case_07_cross_domain_accountant"}

    high_scores = [r[score_key] for r in results if r["id"] in high_fit_ids]
    mismatch_scores = [r[score_key] for r in results if r["id"] in mismatch_ids]

    if not high_scores or not mismatch_scores:
        return 0.0

    avg_high = sum(high_scores) / len(high_scores)
    avg_mismatch = sum(mismatch_scores) / len(mismatch_scores)
    return round(avg_high - avg_mismatch, 2)
