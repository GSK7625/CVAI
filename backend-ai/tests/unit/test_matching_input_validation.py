"""Unit tests for matching input validation hardening (AI-MATCH-003).

Covers:
- Skills validation (whitespace, empty, duplicates, special symbols, lengths).
- Experience validation (floats, negative, NaN, Inf, booleans).
- Date validation (chronological order, inverted dates, ongoing tokens, overlaps).
- StructuredJob validation (title, description, required/preferred skills, optional criteria).
- Text and collection boundary limits.
- Candidate ranking validation (empty batch, blank candidate ID, duplicate IDs).
- No-crash fuzz-like edge case matrix.
"""

from pydantic import ValidationError
import pytest

from app.contracts.cv import EducationItem, ProjectItem, StructuredCv, WorkExperienceItem
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest

# =====================================================================
# 1. Skill Validation Tests
# =====================================================================


def test_skills_whitespace_trimming() -> None:
    """Surrounding whitespace must be stripped from skill strings."""
    job = StructuredJob(
        title="Software Engineer",
        required_skills=["  Python  ", " FastAPI ", "\tDocker\t"],
        preferred_skills=["  Kubernetes  "],
    )
    assert job.required_skills == ["Python", "FastAPI", "Docker"]
    assert job.preferred_skills == ["Kubernetes"]

    cv = StructuredCv(
        skills=["  React  ", " TypeScript "],
        technologies=["  Node.js  "],
    )
    assert cv.skills == ["React", "TypeScript"]
    assert cv.technologies == ["Node.js"]


def test_blank_or_whitespace_skills_rejected() -> None:
    """Empty or whitespace-only skill items must raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", required_skills=["Python", "", "Docker"])
    assert "cannot be empty or whitespace-only" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", required_skills=["Python", "   "])
    assert "cannot be empty or whitespace-only" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredCv(skills=["   "])
    assert "cannot be empty or whitespace-only" in str(exc_info.value)


def test_duplicate_skills_deduplication_policy() -> None:
    """Duplicate skills are deduplicated case-insensitively, preserving first-seen casing/order."""
    job = StructuredJob(
        title="Dev",
        required_skills=["React", "react", "REACT", "Python", "PYTHON"],
        preferred_skills=["Docker", "docker", "DOCKER"],
    )
    assert job.required_skills == ["React", "Python"]
    assert job.preferred_skills == ["Docker"]

    cv = StructuredCv(skills=["Go", "go", "GO", "Rust", "rust"])
    assert cv.skills == ["Go", "Rust"]


def test_special_skill_names_preserved() -> None:
    """Special technical notations like C#, .NET, Node.js, CI/CD, and AWS must be preserved."""
    special_skills = [
        "C#",
        ".NET",
        "Node.js",
        "CI/CD",
        "Amazon Web Services (AWS)",
        "C++",
        "React Native",
        "Next.js",
        "Vue.js",
        "TCP/IP",
    ]
    job = StructuredJob(title="Dev", required_skills=special_skills)
    assert job.required_skills == special_skills

    cv = StructuredCv(skills=special_skills)
    assert cv.skills == special_skills


def test_skill_length_limits() -> None:
    """Skill strings up to 200 characters pass; >200 characters raise ValidationError."""
    valid_skill = "A" * 200
    job = StructuredJob(title="Dev", required_skills=[valid_skill])
    assert job.required_skills == [valid_skill]

    invalid_skill = "A" * 201
    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", required_skills=[invalid_skill])
    assert ("200 characters" in str(exc_info.value)) or ("exceeds maximum allowed length" in str(exc_info.value))


# =====================================================================
# 2. Experience Validation Tests
# =====================================================================


def test_experience_valid_numeric_values() -> None:
    """0, positive integer, and float decimals are valid experience values."""
    exp1 = WorkExperienceItem(job_title="Dev", years_of_experience=0)
    assert exp1.years_of_experience == 0.0

    exp2 = WorkExperienceItem(job_title="Dev", years_of_experience=3)
    assert exp2.years_of_experience == 3.0

    exp3 = WorkExperienceItem(job_title="Dev", years_of_experience=2.5)
    assert exp3.years_of_experience == 2.5

    job1 = StructuredJob(title="Dev", minimum_experience_years=0)
    assert job1.minimum_experience_years == 0.0

    job2 = StructuredJob(title="Dev", minimum_experience_years=5)
    assert job2.minimum_experience_years == 5.0


def test_experience_negative_rejected() -> None:
    """Negative experience values must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", years_of_experience=-0.1)
    assert "cannot be negative" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", minimum_experience_years=-2.0)
    assert "cannot be negative" in str(exc_info.value)


def test_experience_nan_and_inf_rejected() -> None:
    """NaN and Infinity values must be rejected."""
    for bad_val in [float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValidationError) as exc_info:
            WorkExperienceItem(job_title="Dev", years_of_experience=bad_val)
        assert "must be a finite number" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            StructuredJob(title="Dev", minimum_experience_years=bad_val)
        assert "must be a finite number" in str(exc_info.value)


def test_experience_booleans_rejected() -> None:
    """Booleans (True/False) must not be silently coerced to 1.0 or 0.0."""
    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", years_of_experience=True)  # type: ignore[arg-type]
    assert "Boolean values are not valid experience numbers" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", years_of_experience=False)  # type: ignore[arg-type]
    assert "Boolean values are not valid experience numbers" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", minimum_experience_years=True)  # type: ignore[arg-type]
    assert "Boolean values are not valid experience numbers" in str(exc_info.value)


def test_experience_max_bound() -> None:
    """Experience values > 60.0 years must be rejected."""
    valid_exp = WorkExperienceItem(job_title="Dev", years_of_experience=60.0)
    assert valid_exp.years_of_experience == 60.0

    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", years_of_experience=60.1)
    assert "exceeds maximum allowed limit" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="Dev", minimum_experience_years=60.1)
    assert "exceeds maximum allowed limit" in str(exc_info.value)


# =====================================================================
# 3. Date Validation Tests
# =====================================================================


def test_date_valid_chronological_order() -> None:
    """Valid start_date <= end_date pairs must pass."""
    exp1 = WorkExperienceItem(job_title="Dev", start_date="2020-01", end_date="2022-01")
    assert exp1.start_date == "2020-01"
    assert exp1.end_date == "2022-01"

    exp2 = WorkExperienceItem(job_title="Dev", start_date="2021-03-01", end_date="2021-03-15")
    assert exp2.start_date == "2021-03-01"
    assert exp2.end_date == "2021-03-15"

    exp3 = WorkExperienceItem(job_title="Dev", start_date="2022-01", end_date="2022-01")
    assert exp3.start_date == "2022-01"
    assert exp3.end_date == "2022-01"


def test_date_inverted_range_rejected() -> None:
    """Reversed date ranges (start > end) must raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", start_date="2025-01", end_date="2024-01")
    assert "cannot be later than end_date" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        WorkExperienceItem(job_title="Dev", start_date="2023-10-15", end_date="2023-10-14")
    assert "cannot be later than end_date" in str(exc_info.value)


def test_date_ongoing_and_none_tokens_accepted() -> None:
    """Ongoing end date tokens (Present, Current, Now, Hiện tại, None) must be accepted."""
    for token in ["Present", "current", "Now", "Hiện tại", None]:
        exp = WorkExperienceItem(job_title="Dev", start_date="2022-01", end_date=token)
        assert exp.start_date == "2022-01"
        assert exp.end_date == token


def test_overlapping_employment_periods_remain_valid() -> None:
    """Overlapping employment entries across different jobs are legitimate and valid."""
    role_1 = WorkExperienceItem(
        job_title="Full Stack Developer",
        company="Company Alpha",
        start_date="2020-01",
        end_date="2023-01",
    )
    role_2 = WorkExperienceItem(
        job_title="Part-time Consultant",
        company="Company Beta",
        start_date="2022-01",
        end_date="2024-01",
    )
    cv = StructuredCv(work_experience=[role_1, role_2])
    assert len(cv.work_experience) == 2


# =====================================================================
# 4. StructuredJob Validation Tests
# =====================================================================


def test_structured_job_valid_minimal() -> None:
    """Minimal job with only title passes."""
    job = StructuredJob(title="Backend Engineer")
    assert job.title == "Backend Engineer"
    assert job.required_skills == []
    assert job.preferred_skills == []
    assert job.minimum_experience_years is None
    assert job.education_requirement is None


def test_structured_job_blank_title_rejected() -> None:
    """Empty or whitespace-only job title must raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="")
    assert "title cannot be empty or whitespace-only" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        StructuredJob(title="   \n\t  ")
    assert "title cannot be empty or whitespace-only" in str(exc_info.value)


def test_structured_job_optional_criteria_semantics() -> None:
    """Optional fields normalize whitespace-only strings to None without error."""
    job = StructuredJob(
        title="QA Engineer",
        education_requirement="   ",
        location="  ",
        salary="   ",
        employment_type="   ",
    )
    assert job.education_requirement is None
    assert job.location is None
    assert job.salary is None
    assert job.employment_type is None


# =====================================================================
# 5. Free-Text and Collection Boundary Limit Tests
# =====================================================================


def test_job_title_boundary_limits() -> None:
    """Job title max 300 chars passes; 301 chars raises ValidationError."""
    job = StructuredJob(title="A" * 300)
    assert len(job.title) == 300

    with pytest.raises(ValidationError):
        StructuredJob(title="A" * 301)


def test_job_description_boundary_limits() -> None:
    """Job description max 20,000 chars passes; 20,001 chars raises ValidationError."""
    job = StructuredJob(title="Dev", description="A" * 20000)
    assert len(job.description) == 20000

    with pytest.raises(ValidationError):
        StructuredJob(title="Dev", description="A" * 20001)


def test_cv_career_summary_boundary_limits() -> None:
    """Career summary max 4,000 chars passes; 4,001 chars raises ValidationError."""
    cv = StructuredCv(career_summary="A" * 4000)
    assert cv.career_summary == "A" * 4000

    with pytest.raises(ValidationError):
        StructuredCv(career_summary="A" * 4001)


def test_work_experience_description_boundary_limits() -> None:
    """Work experience description max 8,000 chars passes; 8,001 chars raises ValidationError."""
    exp = WorkExperienceItem(job_title="Dev", description="A" * 8000)
    assert len(exp.description) == 8000

    with pytest.raises(ValidationError):
        WorkExperienceItem(job_title="Dev", description="A" * 8001)


def test_project_description_boundary_limits() -> None:
    """Project description max 8,000 chars passes; 8,001 chars raises ValidationError."""
    proj = ProjectItem(name="Project", description="A" * 8000)
    assert len(proj.description) == 8000

    with pytest.raises(ValidationError):
        ProjectItem(name="Project", description="A" * 8001)


def test_skills_collection_limits() -> None:
    """Skill collections up to 100 items pass; 101 items raise ValidationError."""
    valid_skills = [f"Skill_{i}" for i in range(100)]
    job = StructuredJob(title="Dev", required_skills=valid_skills)
    assert len(job.required_skills) == 100

    too_many_skills = [f"Skill_{i}" for i in range(101)]
    with pytest.raises(ValidationError):
        StructuredJob(title="Dev", required_skills=too_many_skills)


def test_work_experience_collection_limits() -> None:
    """Work experience collections up to 30 items pass; 31 items raise ValidationError."""
    valid_exps = [WorkExperienceItem(job_title=f"Role_{i}") for i in range(30)]
    cv = StructuredCv(work_experience=valid_exps)
    assert len(cv.work_experience) == 30

    too_many_exps = [WorkExperienceItem(job_title=f"Role_{i}") for i in range(31)]
    with pytest.raises(ValidationError):
        StructuredCv(work_experience=too_many_exps)


def test_education_collection_limits() -> None:
    """Education collections up to 20 items pass; 21 items raise ValidationError."""
    valid_edu = [EducationItem(degree=f"Degree_{i}") for i in range(20)]
    cv = StructuredCv(education=valid_edu)
    assert len(cv.education) == 20

    too_many_edu = [EducationItem(degree=f"Degree_{i}") for i in range(21)]
    with pytest.raises(ValidationError):
        StructuredCv(education=too_many_edu)


# =====================================================================
# 6. Candidate Ranking Validation Tests
# =====================================================================


def test_candidate_ranking_empty_batch_rejected() -> None:
    """Empty candidate batch in CandidateRankRequest must raise ValidationError."""
    job = StructuredJob(title="Dev")
    with pytest.raises(ValidationError):
        CandidateRankRequest(job=job, candidates=[])


def test_candidate_ranking_blank_candidate_id_rejected() -> None:
    """Empty or whitespace-only candidate_id must raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CandidateItem(candidate_id="", cv=StructuredCv())
    assert "candidate_id" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        CandidateItem(candidate_id="   ", cv=StructuredCv())
    assert "candidate_id" in str(exc_info.value)


def test_candidate_ranking_duplicate_candidate_ids_rejected() -> None:
    """Duplicate candidate IDs within a ranking request must be rejected."""
    job = StructuredJob(title="Dev")
    candidates = [
        CandidateItem(candidate_id="cand-123", cv=StructuredCv()),
        CandidateItem(candidate_id="cand-456", cv=StructuredCv()),
        CandidateItem(candidate_id="cand-123", cv=StructuredCv()),
    ]
    with pytest.raises(ValidationError) as exc_info:
        CandidateRankRequest(job=job, candidates=candidates)
    assert "Duplicate candidate_id found" in str(exc_info.value)


def test_candidate_ranking_duplicate_candidate_ids_with_whitespace() -> None:
    """Candidate IDs that differ only by whitespace are stripped and caught as duplicates."""
    job = StructuredJob(title="Dev")
    candidates = [
        CandidateItem(candidate_id="cand-123", cv=StructuredCv()),
        CandidateItem(candidate_id="  cand-123  ", cv=StructuredCv()),
    ]
    with pytest.raises(ValidationError) as exc_info:
        CandidateRankRequest(job=job, candidates=candidates)
    assert "Duplicate candidate_id found" in str(exc_info.value)


def test_candidate_ranking_collection_limits() -> None:
    """Candidate batch size up to 100 is valid; 101 candidates raise ValidationError."""
    job = StructuredJob(title="Dev")
    valid_batch = [CandidateItem(candidate_id=f"c_{i}", cv=StructuredCv()) for i in range(100)]
    req = CandidateRankRequest(job=job, candidates=valid_batch)
    assert len(req.candidates) == 100

    too_large_batch = [CandidateItem(candidate_id=f"c_{i}", cv=StructuredCv()) for i in range(101)]
    with pytest.raises(ValidationError):
        CandidateRankRequest(job=job, candidates=too_large_batch)


# =====================================================================
# 7. No-Crash Fuzz-Like Parameterized Edge Matrix
# =====================================================================


@pytest.mark.parametrize(
    "edge_title,edge_skills,edge_exp",
    [
        ("Kỹ sư phần mềm Cấp cao", ["Python", "FastAPI", "PostgreSQL"], 3.5),
        ("C# / .NET Tech Lead", ["C#", ".NET", "CI/CD", "Docker"], 5.0),
        ("DevOps / SRE Specialist (AWS/GCP)", ["AWS", "Docker", "Kubernetes"], 0.0),
        ("Senior Engineer", ["Python 3.11+", "Node.js", "Vue.js"], 60.0),
    ],
)
def test_no_crash_valid_edge_cases(edge_title: str, edge_skills: list[str], edge_exp: float) -> None:
    """Valid edge case inputs with Unicode, punctuation, and boundaries construct without crashing."""
    job = StructuredJob(
        title=edge_title,
        required_skills=edge_skills,
        minimum_experience_years=edge_exp,
    )
    cv = StructuredCv(
        full_name="Nguyễn Văn A",
        career_summary="Tóm tắt sự nghiệp với các ký tự đặc biệt: & < > ' \"",
        skills=edge_skills,
        work_experience=[
            WorkExperienceItem(
                job_title=edge_title,
                years_of_experience=edge_exp,
                start_date="2020-01",
                end_date="Present",
            )
        ],
    )
    assert job.title == edge_title
    assert cv.work_experience[0].years_of_experience == edge_exp
