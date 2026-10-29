import json

import httpx
from pydantic import BaseModel
import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.infrastructure.llm.providers.openai_provider import OpenAiProvider


def test_mock_provider_metadata():
    """Verify MockLlmProvider returns correct metadata strings."""
    mock_llm = MockLlmProvider()
    assert mock_llm.provider_name == "mock"
    assert mock_llm.model_name == "mock-deterministic"


def test_openai_provider_metadata():
    """Verify OpenAiProvider returns configured model metadata."""
    settings = Settings(OPENAI_API_KEY="sk-test-key", LLM_MODEL="gpt-4o-mini")
    openai_llm = OpenAiProvider(settings=settings)
    assert openai_llm.provider_name == "openai"
    assert openai_llm.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_openai_provider_reuses_client_and_aclose_shuts_it_down():
    """Verify single reusable AsyncClient is maintained and closed via aclose()."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")
    provider = OpenAiProvider(settings=settings)

    client1 = provider._client
    assert client1 is not None
    assert not client1.is_closed

    await provider.aclose()
    assert client1.is_closed


@pytest.mark.asyncio
async def test_openai_retries_transient_500_server_error_and_eventually_fails():
    """Verify 500 error triggers bounded retries using backoff, then raises ProviderError."""
    attempt_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(500, json={"error": "Internal Server Error"})

    mock_transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=mock_transport)

    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client, sleep_func=mock_sleep)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="Test prompt")

    assert "transient error status 500" in str(exc_info.value)
    # Initial attempt + 2 retries = 3 attempts total
    assert attempt_count == 3
    assert len(sleep_calls) == 2


@pytest.mark.asyncio
async def test_openai_retries_transient_429_honoring_retry_after():
    """Verify 429 rate limit error respects Retry-After header and raises RateLimitExceededError."""
    attempt_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(429, headers={"Retry-After": "1.5"}, json={"error": "Rate limit reached"})

    mock_transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=mock_transport)

    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client, sleep_func=mock_sleep)

    with pytest.raises(RateLimitExceededError):
        await provider.generate_text(prompt="Test prompt")

    assert attempt_count == 3
    # Both sleeps should have honored the 1.5s Retry-After header
    assert sleep_calls == [1.5, 1.5]


@pytest.mark.asyncio
async def test_openai_permanent_400_not_retried():
    """Rule: Permanent 400 Bad Request error must fail immediately without retrying."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(400, json={"error": "Invalid request parameters"})

    mock_transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=mock_transport)

    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=3)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="Test prompt")

    assert "permanent error status 400" in str(exc_info.value)
    # Strict assertion: Exactly 1 attempt made, zero retries
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_permanent_401_not_retried():
    """Rule: Permanent 401 Unauthorized error must fail immediately without retrying."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(401, json={"error": "Invalid API key"})

    mock_transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=mock_transport)

    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=3)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="Test prompt")

    assert "permanent error status 401" in str(exc_info.value)
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_network_error_retried_and_recovers():
    """Verify transient network connection failure retries and succeeds on subsequent attempt."""
    attempt_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise httpx.ConnectError("Connection refused by peer")
        return httpx.Response(200, json={"choices": [{"message": {"content": "Successful response"}}]})

    mock_transport = httpx.MockTransport(handler)
    mock_client = httpx.AsyncClient(transport=mock_transport)

    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client, sleep_func=mock_sleep)

    result = await provider.generate_text(prompt="Hello")
    assert result == "Successful response"
    assert attempt_count == 2
    assert len(sleep_calls) == 1


class DummyStructuredOutput(BaseModel):
    summary: str
    score: float


@pytest.mark.asyncio
async def test_openai_200_invalid_json_body_raises_provider_error():
    """Rule 1: HTTP 200 with non-JSON response body raises controlled ProviderError (502) without retries."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(200, text="<html><body>502 Bad Gateway</body></html>")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="test")

    assert exc_info.value.status_code == 502
    assert "Invalid JSON in OpenAI response body" in str(exc_info.value)
    # Malformed 200 is not retryable: exactly 1 attempt
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_200_empty_dict_raises_provider_error():
    """Rule 2: HTTP 200 with empty JSON object {} raises controlled ProviderError."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(200, json={})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="test")

    assert exc_info.value.status_code == 502
    assert "missing or empty 'choices' list" in str(exc_info.value)
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_200_empty_choices_raises_provider_error():
    """Rule 3: HTTP 200 with choices=[] raises controlled ProviderError."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(200, json={"choices": []})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="test")

    assert exc_info.value.status_code == 502
    assert "missing or empty 'choices' list" in str(exc_info.value)
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_200_content_none_raises_provider_error():
    """Rule 4: HTTP 200 with content=None raises controlled ProviderError."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": None}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="test")

    assert exc_info.value.status_code == 502
    assert "'content' field is None" in str(exc_info.value)
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_200_content_non_string_raises_provider_error():
    """Rule 5: HTTP 200 with non-string content (e.g. int/list/object) raises controlled ProviderError."""
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": 123}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test", LLM_MAX_RETRIES=2)
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_text(prompt="test")

    assert exc_info.value.status_code == 502
    assert "expected string content, got int" in str(exc_info.value)
    assert attempt_count == 1


@pytest.mark.asyncio
async def test_openai_structured_content_invalid_json_raises_provider_error():
    """Rule 6: Structured generation with non-JSON content string raises controlled ProviderError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "This is plain text, not JSON"}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test")
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(prompt="test", response_model=DummyStructuredOutput)

    assert exc_info.value.status_code == 502
    assert "not valid JSON" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_structured_content_schema_invalid_raises_provider_error():
    """Rule 7: Structured generation with valid JSON but invalid schema raises controlled ProviderError."""

    def handler(request: httpx.Request) -> httpx.Response:
        # Missing required 'summary' and 'score' fields
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"unknown_field": 42})}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test")
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(prompt="test", response_model=DummyStructuredOutput)

    assert exc_info.value.status_code == 502
    assert "does not match required contract" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_normal_valid_response_still_works():
    """Rule 8: Verify normal valid text and structured generation continue to work flawlessly."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if "response_format" in body:
            content = json.dumps({"summary": "Great match", "score": 98.5})
        else:
            content = "  Hello from OpenAI!  "
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    settings = Settings(OPENAI_API_KEY="sk-test")
    provider = OpenAiProvider(settings=settings, http_client=mock_client)

    # 1. Text generation
    text_result = await provider.generate_text(prompt="Hi")
    assert text_result == "Hello from OpenAI!"

    # 2. Structured generation
    struct_result = await provider.generate_structured(prompt="Analyze", response_model=DummyStructuredOutput)
    assert struct_result.summary == "Great match"
    assert struct_result.score == 98.5
