from typing import Literal

from pydantic import BaseModel, Field

ExplanationMode = Literal["llm", "deterministic", "deterministic-fallback"]


class ResponseMeta(BaseModel):
    """Metadata attached to AI service responses."""

    algorithm_version: str = Field(
        default="1.0.0",
        description="Version or identifier of the algorithm (e.g. matching-v0, matching-v1-experimental)",
    )
    algorithm_variant: str | None = Field(
        default=None,
        description="Variant of algorithm (e.g. matching-v0, matching-v1-experimental)",
    )
    contract_version: str | None = Field(
        default=None,
        description="Optional response contract identifier when a feature defines a frozen contract",
    )
    schema_version: str | None = Field(
        default="1.0.0",
        description="Semantic schema/contract version (e.g. 1.0.0)",
    )
    prompt_version: str = Field(default="v1", description="Prompt template version")
    provider: str = Field(
        default="mock",
        description=(
            "Configured AI/LLM provider (e.g. 'mock', 'openai'). See llm_invoked to check if LLM was actually called."
        ),
    )
    model: str = Field(
        default="default",
        description="Configured AI/LLM model identifier used or configured for explanations",
    )
    embedding_provider: str | None = Field(
        default=None,
        description="Embedding provider used for semantic computation",
    )
    embedding_model: str | None = Field(
        default=None,
        description="Embedding model identifier used",
    )
    semantic_similarity: float | None = Field(
        default=None,
        description="Semantic similarity score between CV and Job description",
    )
    semantic_score: int | None = Field(
        default=None,
        description="Semantic score scaled to 0-100",
    )
    semantic_mode: str | None = Field(
        default=None,
        description="Mode of semantic matching: 'advisory', 'integrated', or None",
    )
    semantic_available: bool | None = Field(
        default=None,
        description="Whether semantic embedding was successfully computed and available",
    )
    llm_invoked: bool | None = Field(
        default=None,
        description=(
            "Indicates whether an LLM was actively invoked for this response. None indicates undeclared by service."
        ),
    )
    explanation_mode: ExplanationMode | None = Field(
        default=None,
        description=(
            "Provenance of match explanation: 'llm', 'deterministic', or 'deterministic-fallback'. "
            "None indicates undeclared by service."
        ),
    )
    processing_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    correlation_id: str = Field(default="-", description="Distributed request correlation ID")
