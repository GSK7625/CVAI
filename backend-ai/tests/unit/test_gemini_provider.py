"""Unit tests for GeminiLlmProvider adapter and integration."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from google.genai import errors
from pydantic import BaseModel, Field
import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.infrastructure.llm.factory import get_llm_provider, get_llm_settings_fingerprint
from app.infrastructure.llm.providers.gemini_provider import (
    DEFAULT_GEMINI_MODEL,
    GeminiLlmProvider,
)


class SampleProfile(BaseModel):
    name: str = Field(description="Name of candidate")
    skills: list[str] = Field(default_factory=list)


def test_gemini_provider_metadata():
    """Verify GeminiLlmProvider returns correct provider and model metadata."""
    settings = Settings(
        GEMINI_API_KEY="test-key",
        LLM_PROVIDER="gemini",
        LLM_MODEL="gemini-2.5-flash",
    )
    provider = GeminiLlmProvider(settings=settings)
    assert provider.provider_name == "gemini"
    assert provider.model_name == "gemini-2.5-flash"


def test_gemini_provider_defaults_to_gemini_flash_if_model_is_openai_default():
    """Verify provider replaces default gpt-4o-mini with DEFAULT_GEMINI_MODEL."""
    settings = Settings(
        GEMINI_API_KEY="test-key",
        LLM_PROVIDER="gemini",
        LLM_MODEL="gpt-4o-mini",
    )
    provider = GeminiLlmProvider(settings=settings)
    assert provider.provider_name == "gemini"
    assert provider.model_name == DEFAULT_GEMINI_MODEL


@pytest.mark.asyncio
async def test_gemini_provider_aclose_lifecycle():
    """Verify client.aio.aclose() is called when closing an owned provider."""
    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.aclose = AsyncMock()

    settings = Settings(GEMINI_API_KEY="test-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)
    # Set _owns_client to True to test closing behavior
    provider._owns_client = True

    await provider.aclose()
    mock_client.aio.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_generate_text_success():
    """Verify successful natural language text generation."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Xin chào, đây là nhận xét từ Gemini."
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    settings = Settings(GEMINI_API_KEY="test-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    result = await provider.generate_text("Hãy nhận xét CV", system_prompt="Bạn là HR", temperature=0.2)
    assert result == "Xin chào, đây là nhận xét từ Gemini."
    mock_client.aio.models.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_generate_text_empty_raises_provider_error():
    """Verify empty response text raises ProviderError."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = None
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    settings = Settings(GEMINI_API_KEY="test-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text("Test prompt")
    assert "Gemini returned empty response text" in str(exc_info.value)
    assert exc_info.value.details.get("provider") == "gemini"


@pytest.mark.asyncio
async def test_gemini_generate_structured_success():
    """Verify structured response parsing into Pydantic model."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"name": "Nguyen Van A", "skills": ["Python", "FastAPI"]}'
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    settings = Settings(GEMINI_API_KEY="test-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    result = await provider.generate_structured(
        prompt="Extract profile",
        response_model=SampleProfile,
        system_prompt="Extract JSON",
    )
    assert isinstance(result, SampleProfile)
    assert result.name == "Nguyen Van A"
    assert result.skills == ["Python", "FastAPI"]


@pytest.mark.asyncio
async def test_gemini_generate_structured_malformed_json_raises_provider_error():
    """Verify unparseable response raises ProviderError."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "This is not valid json at all {"
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    settings = Settings(GEMINI_API_KEY="test-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract profile",
            response_model=SampleProfile,
        )
    assert "could not be parsed into SampleProfile" in str(exc_info.value)
    assert exc_info.value.details.get("provider") == "gemini"


@pytest.mark.asyncio
async def test_gemini_permanent_401_error_raises_provider_error_without_retries():
    """Verify permanent 401 error fails immediately without retrying."""
    call_count = 0

    def raise_401(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise errors.APIError(401, {"error": "API key not valid"})

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=raise_401)

    settings = Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=2)
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text("Prompt")

    assert "permanent error status 401" in str(exc_info.value)
    assert call_count == 1  # No retries on permanent 401


@pytest.mark.asyncio
async def test_gemini_rate_limit_429_raises_rate_limit_exceeded_error():
    """Verify 429 quota error raises RateLimitExceededError after retries."""
    call_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def raise_429(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise errors.APIError(429, {"error": "Resource has been exhausted"})

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=raise_429)

    settings = Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=2)
    provider = GeminiLlmProvider(settings=settings, client=mock_client, sleep_func=mock_sleep)

    with pytest.raises(RateLimitExceededError) as exc_info:
        await provider.generate_text("Prompt")

    assert "rate limit" in str(exc_info.value).lower()
    assert call_count == 3  # 1 initial + 2 retries
    assert len(sleep_calls) == 2


@pytest.mark.asyncio
async def test_gemini_timeout_raises_provider_error():
    """Verify timeout triggers retries and eventually raises ProviderError."""
    call_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    async def slow_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.5)

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=slow_call)

    # Short timeout 0.05s to trigger timeout immediately
    settings = Settings(
        GEMINI_API_KEY="test-key",
        LLM_TIMEOUT_SECONDS=5,
        LLM_MAX_RETRIES=1,
    )
    provider = GeminiLlmProvider(settings=settings, client=mock_client, sleep_func=mock_sleep)
    provider.timeout = 0.05  # Override for fast test

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text("Prompt")

    assert "timed out" in str(exc_info.value).lower()
    assert call_count == 2  # 1 initial + 1 retry


def test_gemini_api_key_not_leaked_in_logs_or_errors():
    """Verify API key is never placed into error messages or error details."""
    secret_key = "AIzaSySecretSpecialKey999"  # noqa: S105
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(
        side_effect=errors.APIError(403, {"error": "Permission denied"})
    )

    settings = Settings(GEMINI_API_KEY=secret_key)
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        asyncio.run(provider.generate_text("Prompt"))

    # Assert the secret key is NOT in message or details
    err_str = str(exc_info.value)
    assert secret_key not in err_str
    assert secret_key not in str(exc_info.value.details)


def test_factory_creates_gemini_provider():
    """Verify get_llm_provider creates GeminiLlmProvider when LLM_PROVIDER=gemini."""
    settings = Settings(
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="test-key-123",
        LLM_MODEL="gemini-2.5-flash",
    )
    provider = get_llm_provider(settings)
    assert isinstance(provider, GeminiLlmProvider)
    assert provider.provider_name == "gemini"
    assert provider.model_name == "gemini-2.5-flash"


def test_factory_fingerprint_includes_gemini_key_hash():
    """Verify settings fingerprint produces different hashes for different Gemini keys."""
    settings_1 = Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="key-one")
    settings_2 = Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="key-two")

    fp_1 = get_llm_settings_fingerprint(settings_1)
    fp_2 = get_llm_settings_fingerprint(settings_2)

    assert fp_1 != fp_2
    # Verify key itself is not in fingerprint (only truncated hash)
    assert "key-one" not in str(fp_1)
    assert "key-two" not in str(fp_2)


@pytest.mark.asyncio
async def test_cv_analyzer_meta_contains_gemini_provider_and_model():
    """Verify CvAnalyzerService returns provider='gemini' and model in ResponseMeta."""
    from app.application.cv_analyzer import CvAnalyzerService
    from app.ports.document_parser import DocumentParserPort

    mock_client = MagicMock()
    mock_resp_struct = MagicMock()
    mock_resp_struct.text = (
        '{"full_name": "Test Candidate", "email": "test@example.com", "phone": "0123456789", '
        '"skills": ["Python"], "work_experience": [], "education": [], "projects": [], '
        '"certificates": [], "technologies": []}'
    )
    mock_resp_eval = MagicMock()
    mock_resp_eval.text = '{"strengths": ["Strong core skills"], "weaknesses": [], "improvement_suggestions": []}'

    mock_client.aio.models.generate_content = AsyncMock(side_effect=[mock_resp_struct, mock_resp_eval])

    settings = Settings(
        GEMINI_API_KEY="test-key",
        LLM_PROVIDER="gemini",
        LLM_MODEL="gemini-2.5-flash",
    )
    provider = GeminiLlmProvider(settings=settings, client=mock_client)

    mock_parser = MagicMock(spec=DocumentParserPort)
    service = CvAnalyzerService(parser=mock_parser, llm=provider, settings=settings)

    result = await service.analyze_text("Sample CV Text")
    assert result.meta.provider == "gemini"
    assert result.meta.model == "gemini-2.5-flash"


def test_gemini_llm_provider_prefers_dedicated_llm_key():
    """Verify GeminiLlmProvider uses GEMINI_LLM_API_KEY over GEMINI_API_KEY."""
    mock_client = MagicMock()
    settings = Settings(
        GEMINI_LLM_API_KEY="dedicated-llm-key",
        GEMINI_API_KEY="common-fallback-key",
        LLM_PROVIDER="gemini",
    )
    provider = GeminiLlmProvider(settings=settings, client=mock_client)
    assert provider._ensure_api_key() == "dedicated-llm-key"


def test_gemini_llm_provider_falls_back_to_common_gemini_api_key():
    """Verify GeminiLlmProvider falls back to GEMINI_API_KEY when GEMINI_LLM_API_KEY is empty."""
    mock_client = MagicMock()
    settings = Settings(
        GEMINI_LLM_API_KEY="",
        GEMINI_API_KEY="common-fallback-key",
        LLM_PROVIDER="gemini",
    )
    provider = GeminiLlmProvider(settings=settings, client=mock_client)
    assert provider._ensure_api_key() == "common-fallback-key"
