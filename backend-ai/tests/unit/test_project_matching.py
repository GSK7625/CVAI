"""Unit tests for deterministic project domain relevance evaluator."""

from pydantic import ValidationError
import pytest

from app.contracts.cv import ProjectItem
from app.domain.matching.project_match import evaluate_project_relevance
from app.domain.matching.scoring import MATCHING_ALGORITHM_VERSION


def test_project_relevance_matching_technologies():
    """Verify overlapping technologies are identified with alias normalization."""
    projects = [
        ProjectItem(
            name="E-Commerce API",
            technologies=["ReactJS", "FastAPI", "PostgreSQL"],
        ),
        ProjectItem(
            name="Mobile App",
            technologies=["Flutter", "Dart"],
        ),
    ]
    required_skills = ["React", "Python"]
    preferred_skills = ["Docker"]

    res = evaluate_project_relevance(
        projects=projects,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert res.relevant_project_count == 1
    assert res.total_project_count == 2
    assert "React" in res.matched_technologies
    assert "1/2 dự án thực tế" in res.relevance_explanation


def test_project_relevance_no_overlap_honest_explanation():
    """Verify projects with no overlapping technologies honestly state non-relevance."""
    projects = [
        ProjectItem(name="PHP CMS", technologies=["Wordpress", "PHP", "MySQL"]),
    ]
    required_skills = ["Golang", "Kubernetes"]

    res = evaluate_project_relevance(
        projects=projects,
        required_skills=required_skills,
    )

    assert res.relevant_project_count == 0
    assert res.total_project_count == 1
    assert res.matched_technologies == []
    assert "chưa thể hiện sự trùng khớp" in res.relevance_explanation


def test_project_relevance_empty_projects():
    """Verify empty projects list states no project information provided."""
    res = evaluate_project_relevance(
        projects=[],
        required_skills=["Python", "FastAPI"],
    )

    assert res.relevant_project_count == 0
    assert res.total_project_count == 0
    assert "Chưa có thông tin dự án thực tế" in res.relevance_explanation


def test_project_relevance_job_without_skills():
    """Verify job without skills states relevance is N/A (project_score=100.0, no penalty)."""
    # Variant A: Candidate has projects, Job has no targets
    projects = [ProjectItem(name="Sample", technologies=["Python"])]
    res_a = evaluate_project_relevance(
        projects=projects,
        required_skills=[],
        preferred_skills=[],
    )

    assert res_a.project_score == 100.0
    assert res_a.relevant_project_count == 0
    assert "không có yêu cầu kỹ năng cụ thể" in res_a.relevance_explanation

    # Variant B: Candidate has NO projects, Job has no targets
    # No-target criterion takes precedence over no-project penalty
    res_b = evaluate_project_relevance(
        projects=[],
        required_skills=[],
        preferred_skills=[],
    )

    assert res_b.project_score == 100.0
    assert res_b.relevant_project_count == 0
    assert "không có yêu cầu kỹ năng cụ thể" in res_b.relevance_explanation


def test_matching_algorithm_version_is_matching_v0():
    """Verify constant MATCHING_ALGORITHM_VERSION equals 'matching-v0'."""
    assert MATCHING_ALGORITHM_VERSION == "matching-v0"


def test_project_order_invariance():
    """Verify candidate project list ordering does not affect project score or relevant count."""
    proj_a = ProjectItem(name="Backend Service", technologies=["Python", "FastAPI"])
    proj_b = ProjectItem(name="DevOps Setup", technologies=["Docker"])

    job_targets = ["Python", "Docker"]

    res_1 = evaluate_project_relevance(
        projects=[proj_a, proj_b],
        required_skills=job_targets,
    )
    res_2 = evaluate_project_relevance(
        projects=[proj_b, proj_a],
        required_skills=job_targets,
    )

    assert res_1.project_score == res_2.project_score == 100.0
    assert res_1.relevant_project_count == res_2.relevant_project_count == 2
    assert set(res_1.matched_technologies) == set(res_2.matched_technologies)


def test_project_technology_alias_normalization():
    """Verify project matching reuses centralized normalize_skill aliases."""
    projects = [
        ProjectItem(
            name="Cloud Platform",
            technologies=["Postgres", "k8s", "GCP", "VueJS"],
        )
    ]
    required_skills = ["PostgreSQL", "Kubernetes"]
    preferred_skills = ["Google Cloud", "Vue.js"]

    res = evaluate_project_relevance(
        projects=projects,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    assert res.project_score == 100.0
    assert res.relevant_project_count == 1
    assert set(res.matched_technologies) == {"PostgreSQL", "Kubernetes", "Google Cloud", "Vue.js"}


def test_project_duplicate_technologies_deduplication():
    """Verify aliases and duplicate technologies within or across projects do not inflate score."""
    # Project contains 3 aliases of the same technology
    projects = [
        ProjectItem(
            name="Frontend Web",
            technologies=["React", "ReactJS", "react.js"],
        )
    ]
    # Job contains 2 aliases of React
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=["React"],
        preferred_skills=["ReactJS"],
    )

    assert res.project_score == 100.0
    assert res.relevant_project_count == 1
    # Exactly 1 unique canonical target in matched_technologies with required display provenance
    assert res.matched_technologies == ["React"]


def test_project_false_positive_prevention():
    """Verify strict word and key boundaries prevent substring false positives."""
    projects = [
        ProjectItem(
            name="Legacy System",
            technologies=["Java", "C", "React"],
        )
    ]
    # Distinguish Java != JavaScript, C != C++, React != React Native
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=["JavaScript", "C++"],
        preferred_skills=["React Native"],
    )

    assert res.project_score == 0.0
    assert res.relevant_project_count == 0
    assert res.matched_technologies == []
    assert "chưa thể hiện sự trùng khớp" in res.relevance_explanation


def test_project_score_bounds_and_numeric_types():
    """Verify project score is strictly a float bounded in [0.0, 100.0]."""
    test_cases = [
        ([], []),
        ([], ["Python"]),
        ([ProjectItem(name="P", technologies=["Python"])], []),
        ([ProjectItem(name="P", technologies=["Java"])], ["Python"]),
        ([ProjectItem(name="P", technologies=["Python"])], ["Python"]),
        ([ProjectItem(name="P", technologies=["Python", "Go"])], ["Python", "Go", "Docker", "K8s"]),
    ]

    for projs, targets in test_cases:
        res = evaluate_project_relevance(projects=projs, required_skills=targets)
        assert isinstance(res.project_score, float)
        assert 0.0 <= res.project_score <= 100.0
        assert isinstance(res.relevance_explanation, str)
        assert len(res.relevance_explanation) > 0


def test_project_partial_coverage_ratio():
    """Verify project score accurately reflects partial coverage of target skills."""
    projects = [
        ProjectItem(
            name="Backend API",
            technologies=["Python", "FastAPI"],
        )
    ]
    job_targets = ["Python", "FastAPI", "PostgreSQL", "Docker"]

    res = evaluate_project_relevance(
        projects=projects,
        required_skills=job_targets,
    )

    # 2 out of 4 target skills covered -> exactly 50.0%
    assert res.project_score == 50.0
    assert len(res.matched_technologies) == 2
    assert set(res.matched_technologies) == {"Python", "FastAPI"}
    assert res.relevant_project_count == 1
    assert res.total_project_count == 1


def test_project_empty_technologies_handling():
    """Verify projects with empty technology lists are safely evaluated and contract-protected."""
    # Pydantic contract layer prohibits whitespace-only skill items in ProjectItem
    with pytest.raises(ValidationError):
        ProjectItem(name="Invalid Project", technologies=["", "   "])

    # Valid projects with empty technologies list
    projects = [
        ProjectItem(name="Empty Tech Project 1", technologies=[]),
        ProjectItem(name="Empty Tech Project 2", technologies=[]),
    ]
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=["Python", "Docker"],
    )

    assert res.project_score == 0.0
    assert res.relevant_project_count == 0
    assert res.total_project_count == 2
    assert res.matched_technologies == []
    assert "chưa thể hiện sự trùng khớp" in res.relevance_explanation


def test_matching_v1_end_to_end_project_na_no_penalty():
    """Verify under matching-v1 that a perfect candidate achieves 100/100 when Job has no project targets."""
    from app.domain.matching.education_match import EducationMatchResult
    from app.domain.matching.experience_match import ExperienceMatchResult
    from app.domain.matching.scoring import compute_overall_match_score_v1
    from app.domain.matching.skill_match import SkillMatchResult

    proj_res = evaluate_project_relevance(
        projects=[],
        required_skills=[],
        preferred_skills=[],
    )
    assert proj_res.project_score == 100.0

    overall = compute_overall_match_score_v1(
        skill_res=SkillMatchResult(skill_score=100.0),
        exp_res=ExperienceMatchResult(score=100.0, comparison_text="", candidate_years=5.0, required_years=5.0),
        edu_res=EducationMatchResult(score=100.0, comparison_text=""),
        proj_res=proj_res,
        semantic_score=100.0,
    )
    # Score must be exactly 100 (no hidden 5-point penalty)
    assert overall.final_score == 100
    assert overall.project_score == 100.0


def test_target_display_precedence_required_over_preferred():
    """Verify first-canonical-occurrence ensures required skill display string is not overwritten by preferred alias."""
    projects = [ProjectItem(name="Frontend", technologies=["React"])]
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=["React"],
        preferred_skills=["ReactJS"],
    )

    assert res.project_score == 100.0
    assert res.matched_technologies == ["React"]
    assert "React" in res.relevance_explanation
    assert "ReactJS" not in res.relevance_explanation


def test_target_display_preferred_only_retains_display_string():
    """Verify when only preferred skills specify an alias, its display string is preserved."""
    projects = [ProjectItem(name="Frontend", technologies=["React"])]
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=[],
        preferred_skills=["ReactJS"],
    )

    assert res.project_score == 100.0
    assert res.matched_technologies == ["ReactJS"]
    assert "ReactJS" in res.relevance_explanation


def test_target_display_multiple_aliases_deduplication():
    """Verify multiple aliases in targets deduplicate to one canonical target with first display."""
    projects = [ProjectItem(name="Frontend", technologies=["React"])]
    res = evaluate_project_relevance(
        projects=projects,
        required_skills=["React", "ReactJS", "react.js"],
        preferred_skills=["ReactJS"],
    )

    assert res.project_score == 100.0
    assert res.matched_technologies == ["React"]
    assert len(res.matched_technologies) == 1
