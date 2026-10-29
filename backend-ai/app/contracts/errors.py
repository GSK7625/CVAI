"""Contracts for standardized error responses."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized API error response contract."""

    error_code: str = Field(description="Machine-readable error classification code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional contextual error attributes")
    correlation_id: str = Field(description="Correlation identifier for request tracing")
