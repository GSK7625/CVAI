"""Contract tests for Job Matching and MatchResult."""

from app.contracts.job import StructuredJob
from app.contracts.matching import MatchRequest, MatchResult


def test_structured_job_contract_fields():
    """Verify StructuredJob fields match expectations."""
    job_data = {
        "title": "Senior .NET Developer",
        "description": "Develop microservices",
        "required_skills": ["C#", ".NET Core"],
        "preferred_skills": ["Docker", "Kubernetes"],
        "minimum_experience_years": 4.0,
        "education_requirement": "Bachelor",
        "location": "Ho Chi Minh City",
        "salary": "2000-3000 USD",
        "employment_type": "Full-time",
    }

    job = StructuredJob.model_validate(job_data)
    dumped = job.model_dump()

    expected_keys = {
        "title",
        "description",
        "required_skills",
        "preferred_skills",
        "minimum_experience_years",
        "education_requirement",
        "location",
        "salary",
        "employment_type",
    }
    assert expected_keys.issubset(dumped.keys())


def test_match_request_contract_fields():
    """Verify MatchRequest validates both cv and job payloads."""
    req_data = {
        "cv": {"skills": ["Python", "FastAPI"]},
        "job": {"title": "Backend Dev", "required_skills": ["Python"]},
    }
    req = MatchRequest.model_validate(req_data)
    assert req.job.title == "Backend Dev"
    assert "Python" in req.cv.skills


def test_match_result_contract_fields():
    """Verify MatchResult properties and serialization format."""
    result_data = {
        "match_score": 88,
        "matched_skills": ["C#", ".NET Core"],
        "missing_skills": [],
        "experience_comparison": "Exceeds requirement",
        "education_comparison": "Meets requirement",
        "project_domain_relevance": "High relevance",
        "match_explanation": "Strong candidate match overall.",
        "meta": {
            "algorithm_version": "1.0.0",
            "correlation_id": "test-cid",
        },
    }

    res = MatchResult.model_validate(result_data)
    dumped = res.model_dump()

    assert dumped["match_score"] == 88
    assert isinstance(dumped["match_score"], int)
    assert dumped["matched_skills"] == ["C#", ".NET Core"]
    assert "experience_comparison" in dumped
    assert "education_comparison" in dumped
    assert "project_domain_relevance" in dumped
    assert "match_explanation" in dumped
