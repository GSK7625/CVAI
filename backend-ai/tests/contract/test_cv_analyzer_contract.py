"""Contract tests for CV Analyzer and Structured CV."""

from app.contracts.cv import StructuredCv
from app.contracts.cv_analysis import CvAnalysisResponse


def test_structured_cv_contract_fields():
    """Verify StructuredCv contract matches expected properties and types."""
    data = {
        "full_name": "Nguyễn Văn Test",
        "email": "test@futurecv.com",
        "phone": "0900000000",
        "career_summary": "Summary",
        "skills": ["Python", "FastAPI"],
        "work_experience": [
            {
                "job_title": "Engineer",
                "company": "Company",
                "duration": "2020-2023",
                "years_of_experience": 3.0,
                "description": "Led backend team",
            }
        ],
        "education": [
            {
                "degree": "Bachelor",
                "institution": "University",
                "field_of_study": "IT",
                "graduation_year": "2020",
            }
        ],
        "certificates": ["Cert A"],
        "projects": [
            {
                "name": "Project 1",
                "description": "Desc",
                "technologies": ["Python"],
            }
        ],
        "technologies": ["Python"],
    }

    model = StructuredCv.model_validate(data)
    dumped = model.model_dump()

    expected_keys = {
        "full_name",
        "email",
        "phone",
        "career_summary",
        "skills",
        "work_experience",
        "education",
        "certificates",
        "projects",
        "technologies",
    }
    assert expected_keys.issubset(dumped.keys())


def test_cv_analysis_response_contract_fields():
    """Verify CvAnalysisResponse contract conforms to required schema."""
    response_data = {
        "structured_cv": {
            "full_name": "Candidate A",
            "skills": ["C#"],
        },
        "cv_score": 85,
        "strengths": ["Strong C# background"],
        "weaknesses": ["Needs more project details"],
        "improvement_suggestions": ["Add metrics to project descriptions"],
        "meta": {
            "algorithm_version": "1.0.0",
            "prompt_version": "v1",
            "provider": "MockLlmProvider",
            "model": "default",
            "processing_time_ms": 12.34,
            "correlation_id": "test-cid",
        },
    }

    resp = CvAnalysisResponse.model_validate(response_data)
    dumped = resp.model_dump()

    assert "cv_score" in dumped
    assert isinstance(dumped["cv_score"], int)
    assert "strengths" in dumped
    assert isinstance(dumped["strengths"], list)
    assert "weaknesses" in dumped
    assert isinstance(dumped["weaknesses"], list)
    assert "improvement_suggestions" in dumped
    assert isinstance(dumped["improvement_suggestions"], list)
    assert "meta" in dumped
    assert dumped["meta"]["correlation_id"] == "test-cid"
