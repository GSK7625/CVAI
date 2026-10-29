"""Contract tests for Candidate Ranking."""

from app.contracts.matching import CandidateRankRequest, CandidateRankResponse


def test_candidate_ranking_contract_fields():
    """Verify CandidateRankRequest and CandidateRankResponse contracts."""
    request_data = {
        "job": {
            "title": "Backend Engineer",
            "required_skills": ["Python"],
        },
        "candidates": [
            {
                "candidate_id": "cand-01",
                "cv": {
                    "full_name": "Nguyen A",
                    "skills": ["Python"],
                },
            }
        ],
    }

    req = CandidateRankRequest.model_validate(request_data)
    assert req.job.title == "Backend Engineer"
    assert len(req.candidates) == 1

    response_data = {
        "job_title": "Backend Engineer",
        "total_evaluated": 1,
        "ranked_candidates": [
            {
                "rank": 1,
                "candidate_id": "cand-01",
                "match_result": {
                    "match_score": 90,
                    "matched_skills": ["Python"],
                    "missing_skills": [],
                    "experience_comparison": "OK",
                    "education_comparison": "OK",
                    "project_domain_relevance": "OK",
                    "match_explanation": "Great fit",
                },
            }
        ],
    }

    resp = CandidateRankResponse.model_validate(response_data)
    dumped = resp.model_dump()
    assert dumped["total_evaluated"] == 1
    assert dumped["ranked_candidates"][0]["rank"] == 1
    assert dumped["ranked_candidates"][0]["candidate_id"] == "cand-01"
