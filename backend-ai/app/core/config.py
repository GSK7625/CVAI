"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="FutureCV Backend AI", alias="APP_NAME")
    env: Literal["development", "test", "staging", "production"] = Field(
        default="development",
        alias="ENV",
    )

    # Server
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # LLM Provider Configuration
    # Supported providers: "mock" (offline/deterministic) | "openai" | "gemini"
    llm_provider: Literal["mock", "openai", "gemini"] = Field(
        default="mock",
        alias="LLM_PROVIDER",
    )
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    # Matching Algorithm Configuration
    # Supported: "matching-v0" (heuristic baseline) | "matching-v1-experimental" (uncalibrated weights + semantic)
    matching_algorithm: Literal["matching-v0", "matching-v1-experimental"] = Field(
        default="matching-v0",
        alias="MATCHING_ALGORITHM",
    )

    # Embedding Provider Configuration
    # Supported providers: "mock" (offline/deterministic) | "openai" | "gemini"
    embedding_provider: Literal["mock", "openai", "gemini"] = Field(
        default="mock",
        alias="EMBEDDING_PROVIDER",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="EMBEDDING_MODEL",
    )

    # Semantic Matching Mode
    # Supported: "disabled" | "advisory" (shadow mode) | "integrated" (v1 formula)
    semantic_mode: Literal["disabled", "advisory", "integrated"] = Field(
        default="advisory",
        alias="SEMANTIC_MODE",
    )

    # Provider API keys
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    gemini_api_key: SecretStr | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_llm_api_key: SecretStr | None = Field(default=None, alias="GEMINI_LLM_API_KEY")
    gemini_embedding_api_key: SecretStr | None = Field(default=None, alias="GEMINI_EMBEDDING_API_KEY")

    def get_effective_gemini_llm_key(self) -> str | None:
        """
        Return effective Gemini API key for LLM:
        1. GEMINI_LLM_API_KEY if configured and non-empty.
        2. Fallback to GEMINI_API_KEY if configured and non-empty.
        3. None otherwise.
        """
        if self.gemini_llm_api_key:
            val = self.gemini_llm_api_key.get_secret_value().strip()
            if val:
                return val
        if self.gemini_api_key:
            val = self.gemini_api_key.get_secret_value().strip()
            if val:
                return val
        return None

    def get_effective_gemini_embedding_key(self) -> str | None:
        """
        Return effective Gemini API key for Embedding:
        1. GEMINI_EMBEDDING_API_KEY if configured and non-empty.
        2. Fallback to GEMINI_API_KEY if configured and non-empty.
        3. None otherwise.
        """
        if self.gemini_embedding_api_key:
            val = self.gemini_embedding_api_key.get_secret_value().strip()
            if val:
                return val
        if self.gemini_api_key:
            val = self.gemini_api_key.get_secret_value().strip()
            if val:
                return val
        return None

    @model_validator(mode="before")
    @classmethod
    def resolve_gemini_keys(cls, data: Any) -> Any:
        """Resolve GEMINI_API_KEY from dedicated LLM or Embedding keys if primary is unset."""
        if isinstance(data, dict):
            llm_key = data.get("GEMINI_LLM_API_KEY") or data.get("gemini_llm_api_key")
            emb_key = data.get("GEMINI_EMBEDDING_API_KEY") or data.get("gemini_embedding_api_key")
            main_key = data.get("GEMINI_API_KEY") or data.get("gemini_api_key")
            if not main_key:
                fallback = llm_key or emb_key
                if fallback:
                    data["GEMINI_API_KEY"] = fallback
        return data

    # Internal Service Authentication (ASP.NET Core -> FastAPI)
    internal_api_key: str = Field(default="", alias="INTERNAL_API_KEY")

    # LLM Resilience
    llm_timeout_seconds: int = Field(default=25, alias="LLM_TIMEOUT_SECONDS", ge=5, le=300)
    llm_max_retries: int = Field(default=1, alias="LLM_MAX_RETRIES", ge=0, le=5)

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # Security & Document Constraints
    max_upload_size_bytes: int = Field(
        default=5 * 1024 * 1024,  # 5 MB (5,242,880 bytes)
        alias="MAX_UPLOAD_SIZE_BYTES",
    )
    max_pdf_pages: int = Field(default=20, alias="MAX_PDF_PAGES", ge=1, le=100)
    max_extracted_text_chars: int = Field(default=50_000, alias="MAX_EXTRACTED_TEXT_CHARS")

    # Multimodal OCR Fallback
    enable_ocr_fallback: bool = Field(default=True, alias="ENABLE_OCR_FALLBACK")
    ocr_min_char_threshold: int = Field(default=50, alias="OCR_MIN_CHAR_THRESHOLD", ge=0, le=1000)

    @property
    def is_production(self) -> bool:
        """Return True if running in production environment."""
        return self.env == "production"

    @property
    def is_test(self) -> bool:
        """Return True if running in test environment."""
        return self.env == "test"

    @field_validator("internal_api_key")
    @classmethod
    def validate_internal_api_key(cls, v: str) -> str:
        """Strip whitespace from internal API key."""
        return v.strip()

    @model_validator(mode="after")
    def validate_environment_and_providers(self) -> "Settings":
        """Enforce production invariants and provider credential requirements."""
        # 1. Production + mock provider -> configuration error
        if self.is_production and self.llm_provider == "mock":
            raise ValueError("Mock LLM provider is not permitted in production environment")

        # 2. Production without INTERNAL_API_KEY -> configuration error
        if self.is_production and not self.internal_api_key:
            raise ValueError("INTERNAL_API_KEY must be configured in production environment")

        # 3. LLM_PROVIDER=openai without OPENAI_API_KEY -> configuration error
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be configured when LLM_PROVIDER is 'openai'")

        # 4. LLM_PROVIDER=gemini without GEMINI_API_KEY -> configuration error
        if self.llm_provider == "gemini" and not self.get_effective_gemini_llm_key():
            raise ValueError("GEMINI_API_KEY must be configured when LLM_PROVIDER is 'gemini'")

        # 4. Production + matching-v1-experimental + mock embedding -> configuration error
        if (
            self.is_production
            and self.matching_algorithm == "matching-v1-experimental"
            and self.embedding_provider == "mock"
        ):
            raise ValueError(
                "Mock embedding provider is not permitted in production when matching-v1-experimental is active"
            )

        # 5. EMBEDDING_PROVIDER=openai without OPENAI_API_KEY when matching-v1 is active -> configuration error
        if (
            self.matching_algorithm == "matching-v1-experimental"
            and self.embedding_provider == "openai"
            and not self.openai_api_key
        ):
            raise ValueError(
                "OPENAI_API_KEY must be configured when EMBEDDING_PROVIDER is 'openai' "
                "and matching-v1-experimental is active"
            )

        # 6. EMBEDDING_PROVIDER=gemini without GEMINI_API_KEY when matching-v1 is active -> configuration error
        if (
            self.matching_algorithm == "matching-v1-experimental"
            and self.embedding_provider == "gemini"
            and not self.get_effective_gemini_embedding_key()
        ):
            raise ValueError(
                "GEMINI_API_KEY must be configured when EMBEDDING_PROVIDER is 'gemini' "
                "and matching-v1-experimental is active"
            )

        # 7. Production + EMBEDDING_PROVIDER=gemini without GEMINI_API_KEY -> configuration error
        if self.is_production and self.embedding_provider == "gemini" and not self.get_effective_gemini_embedding_key():
            raise ValueError("GEMINI_API_KEY must be configured when EMBEDDING_PROVIDER is 'gemini' in production")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
