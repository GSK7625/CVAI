"""Endpoints for Job Matching and Candidate Ranking."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_matching_service, get_ranking_service, verify_internal_api_key
from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.contracts.matching import (
    CandidateRankRequest,
    CandidateRankResponse,
    MatchRequest,
    MatchResult,
)

router = APIRouter(
    tags=["Matching Engine"],
    dependencies=[Depends(verify_internal_api_key)],
)


@router.post(
    "/job/match",
    response_model=MatchResult,
    status_code=status.HTTP_200_OK,
    summary="Match a single structured CV against a Job Description",
)
async def match_cv_to_job(
    req: MatchRequest,
    service: MatchingService = Depends(get_matching_service),
) -> MatchResult:
    """
    Evaluate compatibility between a candidate CV and a job description.
    Uses inspectable multi-criteria scoring (skills, experience, education).
    """
    return await service.match(cv=req.cv, job=req.job)


@router.post(
    "/candidates/rank",
    response_model=CandidateRankResponse,
    status_code=status.HTTP_200_OK,
    summary="Rank multiple candidates for a single Job using the shared Matching Engine",
)
async def rank_candidates(
    req: CandidateRankRequest,
    service: RankingService = Depends(get_ranking_service),
) -> CandidateRankResponse:
    """
    Rank a pool of candidates against a job posting.
    Reuses the single Matching Engine under bounded concurrency, sorted descending by match score.
    """
    return await service.rank_candidates(req)
