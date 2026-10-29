"""Contracts for CV Analysis feature."""

from pydantic import BaseModel, Field, field_validator

from app.contracts.common import ResponseMeta
from app.contracts.cv import StructuredCv


class CvAnalysisContentRequest(BaseModel):
    """Request payload when sending trusted raw text or pre-extracted content instead of PDF file."""

    raw_text: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Raw extracted text of the CV document (1 to 50,000 characters)",
    )
    candidate_id: str | None = Field(
        default=None,
        max_length=256,
        description="Optional candidate identifier for tracking",
    )

    @field_validator("raw_text")
    @classmethod
    def validate_raw_text(cls, v: str) -> str:
        """Ensure raw_text is not whitespace-only."""
        if not v.strip():
            raise ValueError("raw_text cannot be empty or whitespace only")
        return v


class CvAnalysisResponse(BaseModel):
    """Result of CV analysis containing structured extraction and quality evaluation."""

    structured_cv: StructuredCv = Field(description="Extracted structured CV information")
    cv_score: int = Field(description="Overall CV quality score between 0 and 100", ge=0, le=100)
    strengths: list[str] = Field(default_factory=list, description="Key structural and content strengths identified")
    weaknesses: list[str] = Field(default_factory=list, description="Weaknesses or missing critical components")
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable suggestions to improve CV quality and impact",
    )
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Execution metadata")
    raw_text: str | None = Field(default=None, description="Raw extracted text of the CV document")
