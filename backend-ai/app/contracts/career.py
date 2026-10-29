"""Contracts for Career Assistant conversational feature."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.contracts.common import ResponseMeta
from app.contracts.cv import StructuredCv
from app.contracts.job import StructuredJob
from app.contracts.matching import MatchResult


class ChatMessage(BaseModel):
    """Single turn in a career conversation."""

    role: Literal["user", "assistant"] = Field(description="Sender role ('user' or 'assistant' only)")
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message text (1 to 4000 characters)",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Reject empty or whitespace-only content."""
        if not v.strip():
            raise ValueError("content cannot be empty or whitespace only")
        return v


class CareerAssistantContext(BaseModel):
    """Context provided by ASP.NET Core for the Career Assistant conversation."""

    candidate_id: str | None = Field(default=None, max_length=256, description="Candidate ID")
    cv: StructuredCv | None = Field(default=None, description="Current candidate structured CV")
    job: StructuredJob | None = Field(default=None, description="Job currently being viewed or targeted")
    match_result: MatchResult | None = Field(default=None, description="Pre-computed match result if available")


class CareerAssistantRequest(BaseModel):
    """Request to generate career guidance based on conversation history and candidate context."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User question or query (1 to 4000 characters)",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Prior conversational messages (maximum 20 turns)",
    )
    context: CareerAssistantContext | None = Field(default=None, description="Candidate profile and job context")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Reject empty or whitespace-only queries."""
        if not v.strip():
            raise ValueError("message cannot be empty or whitespace only")
        return v


class CareerAssistantResponse(BaseModel):
    """Response from Career Assistant containing advisory reply and suggested next questions."""

    reply: str = Field(description="Assistant conversational response")
    suggested_followups: list[str] = Field(default_factory=list, description="Suggested follow-up questions or actions")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Execution metadata")
