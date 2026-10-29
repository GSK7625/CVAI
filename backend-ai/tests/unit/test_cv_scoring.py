"""Unit tests for deterministic CV quality evaluation."""

from app.domain.cv.scoring import evaluate_cv_quality


def test_evaluate_cv_quality_empty_cv():
    """An empty CV should receive low score and list missing components."""
    empty_cv = {}
    result = evaluate_cv_quality(empty_cv)
    assert result.cv_score < 20
    assert len(result.weaknesses) > 0
    assert len(result.improvement_suggestions) > 0


def test_evaluate_cv_quality_full_cv():
    """A rich, complete CV should receive a high score and list strengths."""
    complete_cv = {
        "full_name": "Nguyễn Văn A",
        "email": "a.nguyen@example.com",
        "phone": "0912345678",
        "career_summary": (
            "Senior Fullstack Engineer với hơn 5 năm kinh nghiệm phát triển hệ thống phân tán và ứng dụng cloud-native."
        ),
        "skills": ["C#", ".NET", "React", "TypeScript", "Docker", "PostgreSQL", "CI/CD", "Kubernetes"],
        "work_experience": [
            {
                "job_title": "Senior Dev",
                "company": "Tech Corp",
                "years_of_experience": 3.0,
                "description": "Backend lead",
            },
            {
                "job_title": "Mid Dev",
                "company": "Software Ltd",
                "years_of_experience": 2.0,
                "description": "Fullstack engineer",
            },
        ],
        "education": [
            {"degree": "Bachelor of Computer Science", "institution": "Đại học Bách Khoa", "graduation_year": "2021"},
        ],
        "certificates": ["AWS Certified Solutions Architect"],
        "projects": [
            {
                "name": "E-Commerce Microservices",
                "description": "High throughput order processing",
                "technologies": ["C#", "Docker"],
            },
            {
                "name": "AI CV Parsing System",
                "description": "Automated recruitment matching",
                "technologies": ["Python", "FastAPI"],
            },
        ],
    }

    result = evaluate_cv_quality(complete_cv)
    assert result.cv_score >= 90
    assert len(result.strengths) >= 4
    assert result.cv_score <= 100
