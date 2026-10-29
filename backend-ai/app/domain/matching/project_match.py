"""Deterministic project domain relevance evaluation via normalized technology intersection."""

from dataclasses import dataclass, field

from app.contracts.cv import ProjectItem
from app.domain.cv.normalization import normalize_skill


@dataclass(frozen=True)
class ProjectRelevanceResult:
    """
    Evaluation of candidate projects against job technology requirements.

    NOTE ON STATISTICAL INDEPENDENCE:
    Observed feature correlation is preserved for compatibility. Candidate project
    technologies may contribute to both SkillScore and ProjectScore in matching-v1.
    The effect will be evaluated during calibration.
    """

    matched_technologies: list[str] = field(default_factory=list)
    relevant_project_count: int = 0
    total_project_count: int = 0
    relevance_explanation: str = ""
    project_score: float = 0.0


def evaluate_project_relevance(
    projects: list[ProjectItem],
    required_skills: list[str],
    preferred_skills: list[str] | None = None,
) -> ProjectRelevanceResult:
    """
    Evaluate candidate projects against job skills using canonical alias normalization.

    NOTE: Informational only in matching-v0. Not factored into overall Match Score.
    """
    total_projects = len(projects)
    target_skills = [s.strip() for s in (required_skills + (preferred_skills or [])) if s.strip()]

    # Case 1: Job does not specify target skills to evaluate against (N/A -> 100.0, no penalty)
    if not target_skills:
        return ProjectRelevanceResult(
            matched_technologies=[],
            relevant_project_count=0,
            total_project_count=total_projects,
            relevance_explanation=(
                "Vị trí tuyển dụng không có yêu cầu kỹ năng cụ thể để đánh giá độ liên quan của dự án."
            ),
            project_score=100.0,
        )

    # Case 2: Candidate has no projects listed
    if total_projects == 0:
        return ProjectRelevanceResult(
            matched_technologies=[],
            relevant_project_count=0,
            total_project_count=0,
            relevance_explanation="Chưa có thông tin dự án thực tế trong hồ sơ.",
            project_score=0.0,
        )

    # Build normalized lookup for target skills (first canonical occurrence wins display provenance)
    norm_targets: dict[str, str] = {}
    for s in target_skills:
        canonical = normalize_skill(s)
        if canonical not in norm_targets:
            norm_targets[canonical] = s

    matched_tech_set: list[str] = []
    relevant_count = 0

    for proj in projects:
        proj_has_match = False
        for tech in proj.technologies:
            clean_tech = tech.strip()
            if not clean_tech:
                continue
            norm_tech = normalize_skill(clean_tech)
            if norm_tech in norm_targets:
                proj_has_match = True
                canonical_target = norm_targets[norm_tech]
                if canonical_target not in matched_tech_set:
                    matched_tech_set.append(canonical_target)

        if proj_has_match:
            relevant_count += 1

    # Case 3: Projects exist and technologies overlap
    if relevant_count > 0:
        explanation = (
            f"Ứng viên có {relevant_count}/{total_projects} dự án thực tế ứng dụng công nghệ phù hợp: "
            f"{', '.join(matched_tech_set)}."
        )
        # Compute ratio of matched project technologies to target skills (capped at 100)
        calculated_score = round(min(100.0, (len(matched_tech_set) / max(1, len(norm_targets))) * 100.0), 2)
    else:
        # Case 4: Projects exist but no technology overlap
        explanation = (
            f"Ứng viên có {total_projects} dự án thực tế nhưng các công nghệ sử dụng "
            f"chưa thể hiện sự trùng khớp với yêu cầu của vị trí này."
        )
        calculated_score = 0.0

    return ProjectRelevanceResult(
        matched_technologies=matched_tech_set,
        relevant_project_count=relevant_count,
        total_project_count=total_projects,
        relevance_explanation=explanation,
        project_score=calculated_score,
    )
