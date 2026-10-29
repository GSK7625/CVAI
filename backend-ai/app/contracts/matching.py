"""Contracts for Job Matching and Candidate/Job Ranking features."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.contracts.common import ResponseMeta
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob

MATCH_RESULT_CONTRACT_VERSION: str = "match-result-v1"

ShortText = Annotated[str, Field(min_length=1, max_length=500)]


class MatchStrength(BaseModel):
    """Grounded strength item backed by verifiable CV evidence."""

    model_config = ConfigDict(extra="forbid")

    item: ShortText
    statement: ShortText
    evidence_source: Literal["cv.skills", "cv.technologies", "cv.projects"] = Field(
        description="Nguồn bằng chứng xác thực trong CV: cv.skills, cv.technologies hoặc cv.projects",
    )
    evidence_text: str | None = Field(default=None, max_length=500)


class MatchGap(BaseModel):
    """Missing requirement gap identified during matching."""

    model_config = ConfigDict(extra="forbid")

    requirement: ShortText
    statement: ShortText


class MatchExplanation(BaseModel):
    """Structured, verified candidate-job match explanation."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    strengths: list[MatchStrength] = Field(default_factory=list, max_length=5)
    gaps: list[MatchGap] = Field(default_factory=list, max_length=10)
    recommendations: list[ShortText] = Field(default_factory=list, max_length=5)


class MatchRequest(BaseModel):
    """Request payload for matching a single CV against a single Job."""

    cv: StructuredCv = Field(description="Structured CV of the candidate")
    job: StructuredJob = Field(description="Structured Job Posting")


class MatchResult(BaseModel):
    """Evaluation result comparing a candidate CV against a job description."""

    match_score: int = Field(
        description=(
            "Inspectable multi-criteria compatibility index between 0 and 100. Higher indicates a stronger match. "
            "Note: this is NOT a CV quality score, probability of being hired, or automated hiring decision."
        ),
        ge=0,
        le=100,
    )
    matched_skills: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=200,
        description="Skills possessed by candidate required by job",
    )
    missing_skills: list[Annotated[str, Field(max_length=200)]] = Field(
        default_factory=list,
        max_length=200,
        description="Required skills missing from candidate CV",
    )
    experience_comparison: str = Field(
        default="",
        max_length=4000,
        description="Detailed comparison of years of experience",
    )
    education_comparison: str = Field(
        default="",
        max_length=4000,
        description="Comparison of academic qualifications",
    )
    project_domain_relevance: str = Field(
        default="",
        max_length=4000,
        description="Relevance of past projects to job domain",
    )
    match_explanation: str | None = Field(
        default=None,
        max_length=10000,
        description=("Natural language match explanation (optional; None or deterministic summary when unrequested)"),
    )
    explanation_details: MatchExplanation | None = Field(
        default=None,
        description="Structured explanation components adhering to 4-layer defense constraints",
    )
    status: str | None = Field(
        default=None,
        description="Operational status indicator (e.g. 'insufficient_job_data')",
    )
    warning: str | None = Field(
        default=None,
        max_length=1000,
        description="Warning message when job requirements are insufficient for confident matching",
    )
    meta: ResponseMeta = Field(
        default_factory=lambda: ResponseMeta(contract_version=MATCH_RESULT_CONTRACT_VERSION),
        description="Execution metadata",
    )

    @model_validator(mode="after")
    def _ensure_contract_version(self) -> "MatchResult":
        """Ensure MatchResult provenance is stamped with MATCH_RESULT_CONTRACT_VERSION."""
        if self.meta.contract_version is None:
            self.meta.contract_version = MATCH_RESULT_CONTRACT_VERSION
        return self

    @property
    def semantic_similarity(self) -> float | None:
        """Convenience accessor for semantic similarity score from meta."""
        return self.meta.semantic_similarity

    @property
    def semantic_score(self) -> int | None:
        """Convenience accessor for semantic score from meta."""
        return self.meta.semantic_score

    @property
    def semantic_mode(self) -> str | None:
        """Convenience accessor for semantic matching mode from meta."""
        return self.meta.semantic_mode

    @property
    def semantic_available(self) -> bool | None:
        """Convenience accessor for semantic availability from meta."""
        return self.meta.semantic_available


class CandidateItem(BaseModel):
    """Candidate representation in bulk ranking request."""

    candidate_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Unique candidate or application identifier (1 to 256 characters)",
    )
    cv: StructuredCv = Field(description="Candidate's structured CV")

    @field_validator("candidate_id")
    @classmethod
    def validate_candidate_id(cls, v: str) -> str:
        """Strip whitespace and enforce non-empty identifier."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("candidate_id cannot be empty or whitespace only")
        return stripped


class CandidateRankRequest(BaseModel):
    """Request to rank multiple candidates for a single Job posting."""

    job: StructuredJob = Field(description="Target job posting")
    candidates: list[CandidateItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of candidates to evaluate and rank (1 to 100)",
    )

    @model_validator(mode="after")
    def validate_unique_candidate_ids(self) -> "CandidateRankRequest":
        """Reject ranking requests containing duplicate candidate IDs."""
        seen_ids: set[str] = set()
        duplicates: list[str] = []
        for candidate in self.candidates:
            cid = candidate.candidate_id
            if cid in seen_ids:
                duplicates.append(cid)
            seen_ids.add(cid)

        if duplicates:
            raise ValueError(f"Duplicate candidate_id found in ranking request: {list(set(duplicates))}")
        return self


class RankedCandidateItem(BaseModel):
    """Ranked candidate entry with match result and rank position."""

    rank: int = Field(description="Ordinal position (1-based, 1 is best match)")
    candidate_id: str = Field(description="Candidate identifier")
    match_result: MatchResult = Field(description="Underlying match result")


class CandidateRankResponse(BaseModel):
    """Response containing ranked candidates sorted descending by match score."""

    job_title: str = Field(description="Title of evaluated job")
    total_evaluated: int = Field(description="Number of candidates evaluated")
    ranked_candidates: list[RankedCandidateItem] = Field(description="Candidates sorted by MatchScore descending")
    meta: ResponseMeta = Field(
        default_factory=lambda: ResponseMeta(contract_version=MATCH_RESULT_CONTRACT_VERSION),
        description="Execution metadata",
    )

    @model_validator(mode="after")
    def _ensure_contract_version(self) -> "CandidateRankResponse":
        """Ensure CandidateRankResponse provenance is stamped with MATCH_RESULT_CONTRACT_VERSION."""
        if self.meta.contract_version is None:
            self.meta.contract_version = MATCH_RESULT_CONTRACT_VERSION
        return self
