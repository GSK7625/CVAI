"""Regression tests verifying removal of fake fallback data (AI-DEMO-004).

Definition of Done:
1. Empty CV produces no work experiences, no education, no projects, no mock skills, and full_name is None.
2. Fresher CV (no experience section) is never assigned 'Senior Engineer' or fabricated years.
3. CV experience missing dates is not awarded arbitrary 2 years (years_of_experience == 0.0).
4. No placeholders carrying semantic meaning like 'Software Engineer', 'Senior Engineer',
   'Company', 'Enterprise Technology', 'University', 'Project', 'Mock full_name', 'Mock skills item'.
5. Projects without names are omitted.
"""

import pytest

from app.contracts.cv import StructuredCv
from app.domain.cv.heuristic_extractor import (
    extract_education,
    extract_projects,
    extract_skills_heuristically,
    extract_structured_cv_heuristically,
    extract_work_experience,
)
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider


def test_empty_cv_does_not_generate_fake_data():
    """Verify empty CV text produces completely clean StructuredCv with zero placeholders."""
    cv: StructuredCv = extract_structured_cv_heuristically("")

    assert cv.full_name is None
    assert cv.full_name != "Mock full_name"

    assert cv.email is None
    assert cv.phone is None
    assert cv.career_summary is None

    assert cv.skills == []
    assert "Mock skills item 1" not in cv.skills

    assert cv.work_experience == []
    assert cv.education == []
    assert cv.projects == []
    assert cv.certificates == []


def test_whitespace_cv_does_not_generate_fake_data():
    """Verify whitespace-only CV text produces empty collections and no placeholders."""
    cv: StructuredCv = extract_structured_cv_heuristically("   \n\n\t  \n  ")

    assert cv.full_name is None
    assert cv.work_experience == []
    assert cv.education == []
    assert cv.projects == []
    assert cv.skills == []


def test_fresher_cv_never_assigned_senior_engineer_or_fake_experience():
    """Verify fresher CV with only academic background does not fabricate work experience."""
    fresher_cv = """
    NGUYEN VAN AN
    an.nguyen@university.edu.vn | +84 901 112 233

    PROFESSIONAL SUMMARY
    Recent computer science graduate passionate about backend development and cloud technologies.

    CORE SKILLS
    Python, FastAPI, Docker, SQL

    EDUCATION
    Bachelor of Information Technology | Danang University of Science and Technology
    2020 - 2024
    """
    cv: StructuredCv = extract_structured_cv_heuristically(fresher_cv)

    assert cv.full_name == "NGUYEN VAN AN"
    assert len(cv.skills) >= 2
    assert len(cv.education) == 1
    assert "Danang University of Science and Technology" in cv.education[0].institution

    # Critical requirement: MUST NOT fabricate any work experience for a fresher
    assert cv.work_experience == []
    for exp in cv.work_experience:
        assert exp.job_title != "Senior Engineer"
        assert exp.job_title != "Software Engineer"
        assert exp.company != "Company"
        assert exp.company != "Enterprise Technology"


def test_experience_missing_dates_is_not_awarded_two_years():
    """Verify work experience without start/end dates receives 0.0 years, not 2.0."""
    cv_missing_dates = """
    NGUYEN VAN BINH
    binh@test.com | 0912345678

    EXPERIENCE
    Backend Developer | Startup Lab
    Contributed to building internal administrative dashboards and REST endpoints.
    """
    cv: StructuredCv = extract_structured_cv_heuristically(cv_missing_dates)

    assert len(cv.work_experience) == 1
    exp = cv.work_experience[0]
    assert exp.job_title == "Backend Developer"
    assert exp.company == "Startup Lab"
    assert exp.start_date is None
    assert exp.end_date is None
    # Must NOT default to 2.0 years
    assert exp.years_of_experience == 0.0


def test_no_placeholders_when_fields_are_absent():
    """Verify absent company, title, or institution remain empty or None without placeholders."""
    # Experience without '|' separator and no company mentioned
    exp_text = "Junior Programmer\nAssisted with feature development."
    experiences = extract_work_experience(raw_text=exp_text, experience_section=exp_text)
    assert len(experiences) == 1
    assert experiences[0].company == ""
    assert experiences[0].company != "Company"
    assert experiences[0].company != "Enterprise Technology"
    assert experiences[0].job_title != "Software Engineer"
    assert experiences[0].job_title != "Senior Engineer"

    # Education without '|' separator and no institution
    edu_text = "Master of Science\nGraduated with honors in 2022."
    educations = extract_education(education_section=edu_text)
    assert len(educations) == 1
    assert educations[0].institution == ""
    assert educations[0].institution != "University"
    assert educations[0].degree == "Master of Science"


def test_unnamed_projects_are_omitted():
    """Verify projects with missing/empty names are omitted, not named 'Project'."""
    proj_text = """
    - • *
    This project has only bullet points and no title.

    E-Commerce Platform
    Built full-featured ordering system.
    """
    projects = extract_projects(projects_section=proj_text)

    # The empty/symbol-only name block must be omitted
    assert len(projects) == 1
    assert projects[0].name == "E-Commerce Platform"
    assert projects[0].name != "Project"


def test_skills_extraction_returns_empty_list_when_no_skills_present():
    """Verify extract_skills_heuristically returns [] when text contains no tech skills."""
    non_tech_text = "I love hiking in the mountains, cooking Italian pasta, and reading history novels."
    skills = extract_skills_heuristically(non_tech_text)

    assert skills == []
    assert "Mock skills item 1" not in skills
    assert "Mock skills item 2" not in skills


@pytest.mark.asyncio
async def test_mock_llm_provider_structured_cv_with_empty_text():
    """Verify MockLlmProvider produces clean StructuredCv without mock strings on empty prompt."""
    provider = MockLlmProvider()
    result = await provider.generate_structured(
        prompt="",
        response_model=StructuredCv,
    )

    assert isinstance(result, StructuredCv)
    assert result.full_name is None
    assert result.full_name != "Mock full_name"
    assert result.work_experience == []
    assert result.skills == []
    assert result.education == []
    assert result.projects == []
