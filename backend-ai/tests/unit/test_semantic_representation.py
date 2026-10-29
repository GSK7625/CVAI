"""Unit tests for semantic representation builders and honest PII protection (Task D)."""

from app.application.semantic_representation import (
    build_cv_semantic_text,
    build_job_semantic_text,
    sanitize_semantic_text,
)
from app.contracts.cv import ProjectItem, StructuredCv, WorkExperienceItem
from app.contracts.job import StructuredJob


def test_dedicated_pii_fields_strictly_omitted_from_cv_semantic_text():
    """Rule: cv.full_name, cv.email, and cv.phone are NEVER included in semantic text."""
    cv = StructuredCv(
        full_name="Nguyen Van A",
        email="candidate.identity@example.com",
        phone="+84 912 345 678",
        career_summary="Senior Python Engineer with expertise in microservices.",
        skills=["Python", "FastAPI"],
    )

    text = build_cv_semantic_text(cv)

    assert "Nguyen Van A" not in text
    assert "candidate.identity@example.com" not in text
    assert "+84 912 345 678" not in text
    assert "Python" in text
    assert "FastAPI" in text


def test_free_text_email_and_phone_deterministic_redaction():
    """Rule: Email addresses and phone numbers appearing in free text are deterministically redacted."""
    raw_text = (
        "Liên hệ với tôi qua email hidden@example.com hoặc gọi số 0912345678. "
        "Số dự phòng quốc tế: +84 987 654 321 hoặc sếp cũ boss.lead@corp.org."
    )

    sanitized = sanitize_semantic_text(raw_text)

    assert "hidden@example.com" not in sanitized
    assert "boss.lead@corp.org" not in sanitized
    assert "0912345678" not in sanitized
    assert "+84 987 654 321" not in sanitized
    assert "[EMAIL_REDACTED]" in sanitized
    assert "[PHONE_REDACTED]" in sanitized


def test_free_text_pii_in_experience_and_project_descriptions_redacted():
    """Rule: PII injected inside work experience or project descriptions is redacted before embedding."""
    cv = StructuredCv(
        career_summary="Developer summary without PII.",
        skills=["Python"],
        work_experience=[
            WorkExperienceItem(
                job_title="Lead Developer",
                company="Tech Co",
                years_of_experience=3.0,
                description="Managed team. Emergency contact: lead.emergency@mail.com or 0909112233.",
            )
        ],
        projects=[
            ProjectItem(
                name="Customer Portal",
                description="Demo credentials available via demo.contact@app.vn or +84-903-123-456.",
                technologies=["Python", "PostgreSQL"],
            )
        ],
    )

    text = build_cv_semantic_text(cv)

    # Assert raw PII is omitted/redacted
    assert "lead.emergency@mail.com" not in text
    assert "0909112233" not in text
    assert "demo.contact@app.vn" not in text
    assert "+84-903-123-456" not in text
    # Assert redaction markers are present
    assert "[EMAIL_REDACTED]" in text
    assert "[PHONE_REDACTED]" in text


def test_build_job_semantic_text_structure_and_sanitization():
    """Verify job semantic representation structure and free-text sanitization."""
    job = StructuredJob(
        title="Senior Python Backend",
        description="Build scalable APIs. For inquiries contact hr.dept@company.com or 0944556677.",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        minimum_experience_years=4.0,
        education_requirement="Bachelor",
    )

    text = build_job_semantic_text(job)

    assert "Vị trí tuyển dụng: Senior Python Backend" in text
    assert "Python, FastAPI" in text
    assert "Docker" in text
    assert "4.0 năm" in text
    assert "Bachelor" in text
    assert "hr.dept@company.com" not in text
    assert "0944556677" not in text
    assert "[EMAIL_REDACTED]" in text
    assert "[PHONE_REDACTED]" in text


def test_comprehensive_pii_sanitization_across_all_field_categories():
    """
    CRITICAL PROOF (FIX F): Email/phone values in EVERY major included semantic field
    are deterministically redacted, and dedicated identity fields are omitted entirely.
    """
    from app.contracts.cv import EducationItem

    cv = StructuredCv(
        full_name="Secret Candidate Name",
        email="identity.leak@secret.com",
        phone="+84 999 888 777",
        career_summary="Summary text contact career@test.com or 0901111222",
        skills=["Python skill@test.com"],
        technologies=["FastAPI tech@test.com"],
        certificates=["AWS cert@test.com"],
        work_experience=[
            WorkExperienceItem(
                job_title="Lead title@test.com",
                company="Company company@test.com 0902222333",
                description="Work description desc@test.com 0903333444",
                years_of_experience=3.0,
            )
        ],
        education=[
            EducationItem(
                degree="Degree degree@test.com",
                field_of_study="Computer Science cs@test.com",
                institution="Tech University univ@test.com 0904444555",
            )
        ],
        projects=[
            ProjectItem(
                name="Project name proj@test.com",
                description="Project description pdesc@test.com 0905555666",
                technologies=["React ptech@test.com"],
            )
        ],
    )

    cv_text = build_cv_semantic_text(cv)

    # Verify dedicated identity fields are strictly omitted
    assert "cand-secret-uuid-9999" not in cv_text
    assert "Secret Candidate Name" not in cv_text
    assert "identity.leak@secret.com" not in cv_text
    assert "+84 999 888 777" not in cv_text

    # Verify all raw emails in all CV fields are redacted
    for email in [
        "career@test.com",
        "skill@test.com",
        "tech@test.com",
        "cert@test.com",
        "title@test.com",
        "company@test.com",
        "desc@test.com",
        "degree@test.com",
        "cs@test.com",
        "univ@test.com",
        "proj@test.com",
        "pdesc@test.com",
        "ptech@test.com",
    ]:
        assert email not in cv_text

    # Verify all raw phones in all CV fields are redacted
    for phone in ["0901111222", "0902222333", "0903333444", "0904444555", "0905555666"]:
        assert phone not in cv_text

    # Test Job Posting
    job = StructuredJob(
        title="Lead Backend title@job.com",
        description="JD description desc@job.com or call 0906666777",
        required_skills=["Python req@job.com"],
        preferred_skills=["Docker pref@job.com"],
        education_requirement="Master edu@job.com",
        employment_type="Full-time emp@job.com 0907777888",
    )

    job_text = build_job_semantic_text(job)

    # Verify all raw emails in all Job fields are redacted
    for email in [
        "title@job.com",
        "desc@job.com",
        "req@job.com",
        "pref@job.com",
        "edu@job.com",
        "emp@job.com",
    ]:
        assert email not in job_text

    # Verify all raw phones in all Job fields are redacted
    for phone in ["0906666777", "0907777888"]:
        assert phone not in job_text


def test_cv_semantic_representation_name_and_contact_invariance():
    """Rule: Altering candidate full_name, email, or phone produces 100% byte-identical semantic representation."""
    base_kwargs = dict(
        career_summary="Senior Backend Engineer specializing in distributed databases.",
        skills=["Python", "FastAPI", "PostgreSQL"],
        work_experience=[WorkExperienceItem(job_title="Backend Lead", company="Tech Corp", years_of_experience=4.0)],
        projects=[ProjectItem(name="Cloud DB", technologies=["Python", "PostgreSQL"])],
    )

    cv_alice = StructuredCv(
        full_name="Alice Smith",
        email="alice@company.com",
        phone="+1 555 123 4567",
        **base_kwargs,
    )
    cv_bob = StructuredCv(
        full_name="Bob Jones",
        email="bob@startup.io",
        phone="+84 901 234 567",
        **base_kwargs,
    )
    cv_anon = StructuredCv(
        full_name=None,
        email=None,
        phone=None,
        **base_kwargs,
    )

    text_alice = build_cv_semantic_text(cv_alice)
    text_bob = build_cv_semantic_text(cv_bob)
    text_anon = build_cv_semantic_text(cv_anon)

    assert text_alice == text_bob
    assert text_alice == text_anon


def test_cv_semantic_representation_skill_sensitivity():
    """Rule: Changing candidate technical skills alters the semantic representation."""
    cv_python = StructuredCv(skills=["Python", "FastAPI"])
    cv_java = StructuredCv(skills=["Java", "Spring Boot"])

    assert build_cv_semantic_text(cv_python) != build_cv_semantic_text(cv_java)


def test_cv_semantic_representation_experience_sensitivity():
    """Rule: Changing candidate work experience alters the semantic representation."""
    cv_lead = StructuredCv(
        work_experience=[WorkExperienceItem(job_title="Lead Architect", company="Scale Co", years_of_experience=5.0)]
    )
    cv_junior = StructuredCv(
        work_experience=[WorkExperienceItem(job_title="Junior Tester", company="QA Co", years_of_experience=1.0)]
    )

    assert build_cv_semantic_text(cv_lead) != build_cv_semantic_text(cv_junior)


def test_cv_semantic_representation_project_sensitivity():
    """Rule: Changing candidate project content alters the semantic representation."""
    cv_proj_a = StructuredCv(
        projects=[ProjectItem(name="Kubernetes Operator", technologies=["Go", "Docker", "Kubernetes"])]
    )
    cv_proj_b = StructuredCv(projects=[ProjectItem(name="WordPress Blog", technologies=["PHP", "MySQL"])])

    assert build_cv_semantic_text(cv_proj_a) != build_cv_semantic_text(cv_proj_b)


def test_job_semantic_representation_determinism_and_independence():
    """Rule: Job representation is strictly deterministic and depends exclusively on Job fields."""
    job = StructuredJob(
        title="Site Reliability Engineer",
        description="Maintain 99.99% uptime for cloud infrastructure.",
        required_skills=["Linux", "Kubernetes", "Prometheus"],
        preferred_skills=["Golang", "Terraform"],
        minimum_experience_years=3.0,
        education_requirement="Bachelor of Computer Science",
        employment_type="Full-time",
    )

    rep1 = build_job_semantic_text(job)
    rep2 = build_job_semantic_text(job)

    assert rep1 == rep2
    assert "Site Reliability Engineer" in rep1
    assert "99.99% uptime" in rep1
    assert "Linux, Kubernetes, Prometheus" in rep1
    assert "3.0 năm" in rep1
