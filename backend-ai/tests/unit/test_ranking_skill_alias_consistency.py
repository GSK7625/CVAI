"""Application-level test verifying Candidate Ranking consistency with skill aliases."""

import pytest

from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider


@pytest.mark.asyncio
async def test_candidate_ranking_alias_consistency():
    """Verify Candidate Ranking sorts alias-matched candidate above missing candidate with exact score parity."""
    matching_service = MatchingService(
        llm=MockLlmProvider(),
        embedding_provider=None,
        matching_algorithm="matching-v0",
    )
    ranking_service = RankingService(matching_service=matching_service)

    job = StructuredJob(
        title="Fullstack Engineer",
        required_skills=["ReactJS", "C#", "C++"],
    )

    # Candidate 1 has alias forms: React, C Sharp, CPP -> 100% skill match
    cand_1_cv = StructuredCv(
        skills=["React", "C Sharp", "CPP"],
        work_experience=[],
        education=[],
    )
    # Candidate 2 lacks skills
    cand_2_cv = StructuredCv(
        skills=["Python", "Java"],
        work_experience=[],
        education=[],
    )

    req = CandidateRankRequest(
        job=job,
        candidates=[
            CandidateItem(candidate_id="cand-alias", cv=cand_1_cv),
            CandidateItem(candidate_id="cand-missing", cv=cand_2_cv),
        ],
    )

    rank_resp = await ranking_service.rank_candidates(req)
    assert rank_resp.total_evaluated == 2
    assert rank_resp.ranked_candidates[0].candidate_id == "cand-alias"
    assert rank_resp.ranked_candidates[0].rank == 1
    assert rank_resp.ranked_candidates[1].candidate_id == "cand-missing"
    assert rank_resp.ranked_candidates[1].rank == 2

    # Single match parity check
    single_match_res = await matching_service.match(cv=cand_1_cv, job=job, generate_explanation=False)
    assert rank_resp.ranked_candidates[0].match_result.match_score == single_match_res.match_score
    assert rank_resp.ranked_candidates[0].match_result.matched_skills == ["ReactJS", "C#", "C++"]
    assert rank_resp.ranked_candidates[0].match_result.missing_skills == []

    # MatchResult v1 shape verification
    assert rank_resp.meta.contract_version == "match-result-v1"
    assert rank_resp.ranked_candidates[0].match_result.meta.contract_version == "match-result-v1"
    dumped = rank_resp.ranked_candidates[0].match_result.model_dump(mode="json")
    expected_keys = {
        "match_score",
        "matched_skills",
        "missing_skills",
        "experience_comparison",
        "education_comparison",
        "project_domain_relevance",
        "match_explanation",
        "explanation_details",
        "status",
        "warning",
        "meta",
    }
    assert set(dumped.keys()) == expected_keys
