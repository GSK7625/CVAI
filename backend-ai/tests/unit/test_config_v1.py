"""Unit tests for configuration validation of matching algorithm and embedding settings."""

from pydantic import ValidationError
import pytest

from app.core.config import Settings


def test_default_matching_and_embedding_settings():
    """1. Verify default values for matching algorithm and embedding provider."""
    settings = Settings()
    assert settings.matching_algorithm == "matching-v0"
    assert settings.embedding_provider == "mock"
    assert settings.embedding_model == "text-embedding-3-small"


def test_production_allows_matching_v0_with_mock_embedding():
    """2. Verify production environment permits matching-v0 with mock embedding."""
    settings = Settings(
        ENV="production",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-valid-key",
        INTERNAL_API_KEY="internal-secret-key",
        MATCHING_ALGORITHM="matching-v0",
        EMBEDDING_PROVIDER="mock",
    )
    assert settings.is_production is True
    assert settings.matching_algorithm == "matching-v0"
    assert settings.embedding_provider == "mock"


def test_development_allows_matching_v0_with_openai_embedding_and_no_key():
    """3. Verify matching-v0 does not require OPENAI_API_KEY even if EMBEDDING_PROVIDER=openai."""
    settings = Settings(
        ENV="development",
        LLM_PROVIDER="mock",
        MATCHING_ALGORITHM="matching-v0",
        EMBEDDING_PROVIDER="openai",
        OPENAI_API_KEY=None,
    )
    assert settings.matching_algorithm == "matching-v0"
    assert settings.embedding_provider == "openai"


def test_matching_v1_with_openai_embedding_missing_key_rejected():
    """4. Rule: When matching-v1 is active and EMBEDDING_PROVIDER=openai, OPENAI_API_KEY is strictly required."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="development",
            LLM_PROVIDER="mock",
            MATCHING_ALGORITHM="matching-v1-experimental",
            EMBEDDING_PROVIDER="openai",
            OPENAI_API_KEY=None,
        )
    assert (
        "OPENAI_API_KEY must be configured when EMBEDDING_PROVIDER is 'openai' and matching-v1-experimental is active"
        in str(exc_info.value)
    )


def test_production_rejects_matching_v1_with_mock_embedding():
    """5. Rule: Production environment must not permit mock embedding provider when matching-v1 is active."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="production",
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="sk-valid-key",
            INTERNAL_API_KEY="internal-secret-key",
            MATCHING_ALGORITHM="matching-v1-experimental",
            EMBEDDING_PROVIDER="mock",
        )
    assert "Mock embedding provider is not permitted in production when matching-v1-experimental is active" in str(
        exc_info.value
    )


def test_production_allows_matching_v1_with_openai_embedding():
    """Verify valid production settings with matching-v1 and real OpenAI embedding."""
    settings = Settings(
        ENV="production",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-valid-key",
        INTERNAL_API_KEY="internal-secret-key",
        MATCHING_ALGORITHM="matching-v1-experimental",
        EMBEDDING_PROVIDER="openai",
    )
    assert settings.is_production is True
    assert settings.matching_algorithm == "matching-v1-experimental"
    assert settings.embedding_provider == "openai"


def test_unsupported_matching_algorithm_rejected():
    """6. Rule: Algorithms outside Literal['matching-v0', 'matching-v1-experimental'] are rejected."""
    with pytest.raises(ValidationError):
        Settings(MATCHING_ALGORITHM="matching-v2")


def test_unsupported_embedding_provider_rejected():
    """7. Rule: Embedding providers outside Literal['mock', 'openai', 'gemini'] are rejected."""
    with pytest.raises(ValidationError):
        Settings(EMBEDDING_PROVIDER="cohere")

    # gemini is now supported
    settings = Settings(EMBEDDING_PROVIDER="gemini", GEMINI_API_KEY="test-key")
    assert settings.embedding_provider == "gemini"


def test_matching_v1_with_gemini_embedding_missing_key_rejected():
    """Rule: When matching-v1 is active and EMBEDDING_PROVIDER=gemini, GEMINI_API_KEY is strictly required."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENV="development",
            LLM_PROVIDER="mock",
            MATCHING_ALGORITHM="matching-v1-experimental",
            EMBEDDING_PROVIDER="gemini",
            GEMINI_API_KEY=None,
        )
    assert (
        "GEMINI_API_KEY must be configured when EMBEDDING_PROVIDER is 'gemini' and matching-v1-experimental is active"
        in str(exc_info.value)
    )


def test_matching_config_environment_aliases():
    """8. Verify environment variable aliases correctly populate Settings fields."""
    settings = Settings(
        MATCHING_ALGORITHM="matching-v1-experimental",
        EMBEDDING_PROVIDER="openai",
        EMBEDDING_MODEL="text-embedding-3-large",
        OPENAI_API_KEY="sk-test-key",
    )
    assert settings.matching_algorithm == "matching-v1-experimental"
    assert settings.embedding_provider == "openai"
    assert settings.embedding_model == "text-embedding-3-large"


def test_env_casing_behavior():
    """9. Document and test exact ENV value casing behavior."""
    # Lowercase matches Literal and succeeds
    settings = Settings(
        ENV="production",
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-key",
        INTERNAL_API_KEY="secret",
    )
    assert settings.env == "production"

    # Title-case and Upper-case fail Literal validation (case_sensitive=False applies only to field names)
    with pytest.raises(ValidationError):
        Settings(
            ENV="Production",
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="sk-key",
            INTERNAL_API_KEY="secret",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENV="PRODUCTION",
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="sk-key",
            INTERNAL_API_KEY="secret",
        )

    # Abbreviations are rejected
    with pytest.raises(ValidationError):
        Settings(
            ENV="prod",
            LLM_PROVIDER="openai",
            OPENAI_API_KEY="sk-key",
            INTERNAL_API_KEY="secret",
        )
