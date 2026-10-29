"""Unit tests for OpenAiEmbeddingProvider resilience, retries, and order preservation (Task C)."""

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider


def test_openai_embedding_provider_metadata():
    """Verify OpenAiEmbeddingProvider returns configured model metadata."""
    settings = Settings(OPENAI_API_KEY="sk-test-key", EMBEDDING_MODEL="text-embedding-3-small")
    provider = OpenAiEmbeddingProvider(settings=settings)
    assert provider.provider_name == "openai"
    assert provider.model_name == "text-embedding-3-small"


async def test_openai_embedding_provider_reuses_client_and_aclose_shuts_it_down():
    """Verify client lifecycle: client is maintained and cleanly closed via aclose()."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")
    provider = OpenAiEmbeddingProvider(settings=settings)

    client = provider._client
    assert client is not None
    assert not client.is_closed

    await provider.aclose()
    assert client.is_closed


async def test_openai_embedding_provider_success_preserves_order():
    """Verify successful response restores exact sequence order based on item index."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    # Return items intentionally out of order to verify sorting by index
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.2, 0.3]},
                    {"index": 0, "embedding": [0.0, 0.1]},
                ]
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    vectors = await provider.embed_texts(["first", "second"])
    assert len(vectors) == 2
    # Verify index 0 vector is first, index 1 vector is second
    assert vectors[0] == [0.0, 0.1]
    assert vectors[1] == [0.2, 0.3]


async def test_openai_embedding_provider_retries_transient_500_and_succeeds():
    """Verify transient 500 error triggers retry and recovers on subsequent attempt."""
    settings = Settings(OPENAI_API_KEY="sk-test-key", LLM_MAX_RETRIES=2)
    attempt_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            return httpx.Response(500, json={"error": "Server Error"})
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.5, 0.5]}]},
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client, sleep_func=mock_sleep)

    vectors = await provider.embed_texts(["test"])
    assert attempt_count == 2
    assert len(sleep_calls) == 1
    assert len(vectors) == 1
    assert vectors[0] == [0.5, 0.5]


async def test_openai_embedding_provider_retries_429_honoring_retry_after():
    """Verify 429 rate limit error retries and honors Retry-After header."""
    settings = Settings(OPENAI_API_KEY="sk-test-key", LLM_MAX_RETRIES=1)
    attempt_count = 0
    sleep_calls: list[float] = []

    async def mock_sleep(duration: float) -> None:
        sleep_calls.append(duration)

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(429, headers={"Retry-After": "2.5"}, json={"error": "Rate limit exceeded"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client, sleep_func=mock_sleep)

    with pytest.raises(RateLimitExceededError) as exc_info:
        await provider.embed_texts(["test"])

    assert attempt_count == 2
    assert sleep_calls == [2.5]
    assert "rate limit reached" in str(exc_info.value).lower()


async def test_openai_embedding_provider_permanent_400_not_retried():
    """Verify permanent 400 client error fails immediately without retrying."""
    settings = Settings(OPENAI_API_KEY="sk-test-key", LLM_MAX_RETRIES=2)
    attempt_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(400, json={"error": "Bad Request: Invalid Model"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])

    # Strict invariant: exactly 1 attempt for permanent errors
    assert attempt_count == 1
    assert "rejected embedding request with status 400" in str(exc_info.value)


async def test_openai_embedding_provider_malformed_response_raises_provider_error():
    """Verify malformed JSON payload raises controlled ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected_key": []})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])

    assert "Malformed response structure from OpenAI Embeddings API" in str(exc_info.value)


async def test_openai_embedding_provider_missing_api_key_raises_provider_error():
    """Verify missing API key raises controlled ProviderError without network call."""
    settings = Settings(OPENAI_API_KEY="")
    provider = OpenAiEmbeddingProvider(settings=settings)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])

    assert "OpenAI API key is not configured" in str(exc_info.value)


async def test_openai_embedding_provider_200_invalid_json_body():
    """HTTP 200 with invalid/unparseable JSON body raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"invalid-not-json{")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "Invalid JSON in OpenAI Embeddings response body" in str(exc_info.value)


async def test_openai_embedding_provider_200_root_not_dict():
    """HTTP 200 with root JSON not an object raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["unexpected", "list"])

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "root payload must be a JSON object" in str(exc_info.value)


async def test_openai_embedding_provider_200_missing_data():
    """HTTP 200 missing 'data' field raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"model": "text-embedding-3-small"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "missing or non-list 'data' field" in str(exc_info.value)


async def test_openai_embedding_provider_200_data_not_list():
    """HTTP 200 with 'data' not a list raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": "not a list"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "missing or non-list 'data' field" in str(exc_info.value)


async def test_openai_embedding_provider_200_item_not_dict():
    """HTTP 200 with item in 'data' not a dict raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": ["not-a-dict"]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "is not an object" in str(exc_info.value)


async def test_openai_embedding_provider_200_duplicate_indices():
    """
    CRITICAL PROOF (FIX D): Length matches texts count but indices are duplicate.
    Must be rejected by index integrity check.
    """
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [0.1, 0.2]},
                    {"index": 0, "embedding": [0.3, 0.4]},
                ]
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["text0", "text1"])
    assert "invalid index sequence" in str(exc_info.value)


async def test_openai_embedding_provider_200_missing_or_negative_or_gapped_index():
    """Indices must be contiguous [0..N-1]. Negative or gapped indices raise ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    # Negative index
    def handler_neg(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": -1, "embedding": [0.1, 0.2]}]})

    mock_client_neg = httpx.AsyncClient(transport=httpx.MockTransport(handler_neg))
    provider_neg = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_neg)
    with pytest.raises(ProviderError) as exc_info:
        await provider_neg.embed_texts(["test"])
    assert "invalid index sequence" in str(exc_info.value)

    # Gapped index (index 1 for 1 item)
    def handler_gap(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 1, "embedding": [0.1, 0.2]}]})

    mock_client_gap = httpx.AsyncClient(transport=httpx.MockTransport(handler_gap))
    provider_gap = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_gap)
    with pytest.raises(ProviderError) as exc_info:
        await provider_gap.embed_texts(["test"])
    assert "invalid index sequence" in str(exc_info.value)


async def test_openai_embedding_provider_200_non_integer_index():
    """Non-integer or boolean index in item raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": "zero", "embedding": [0.1, 0.2]}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["test"])
    assert "non-integer 'index'" in str(exc_info.value)


async def test_openai_embedding_provider_200_missing_or_empty_embedding():
    """Missing or empty embedding array raises ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    # Missing embedding
    def handler_missing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0}]})

    mock_client_m = httpx.AsyncClient(transport=httpx.MockTransport(handler_missing))
    provider_m = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_m)
    with pytest.raises(ProviderError) as exc_info:
        await provider_m.embed_texts(["test"])
    assert "missing 'embedding' field" in str(exc_info.value)

    # Empty embedding
    def handler_empty(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": []}]})

    mock_client_e = httpx.AsyncClient(transport=httpx.MockTransport(handler_empty))
    provider_e = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_e)
    with pytest.raises(ProviderError) as exc_info:
        await provider_e.embed_texts(["test"])
    assert "empty or non-list 'embedding' vector" in str(exc_info.value)


async def test_openai_embedding_provider_200_mixed_dimensions():
    """
    CRITICAL PROOF (FIX E): Vectors with differing dimensions in a single response raise ProviderError.
    Must NOT flow into cosine similarity and become zero score silently.
    """
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                    {"index": 1, "embedding": [0.1, 0.2]},  # Length 2 instead of 3
                ]
            },
        )

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["text0", "text1"])
    assert "inconsistent vector dimension" in str(exc_info.value)


async def test_openai_embedding_provider_200_nan_and_inf_values():
    """Vectors containing NaN or +/-Inf values raise ProviderError."""
    settings = Settings(OPENAI_API_KEY="sk-test-key")

    # NaN value (in raw HTTP JSON bytes)
    def handler_nan(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b'{"data": [{"index": 0, "embedding": [NaN, 0.5]}]}',
            headers={"Content-Type": "application/json"},
        )

    mock_client_nan = httpx.AsyncClient(transport=httpx.MockTransport(handler_nan))
    provider_nan = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_nan)
    with pytest.raises(ProviderError) as exc_info:
        await provider_nan.embed_texts(["test"])
    assert "NaN or Inf values" in str(exc_info.value)

    # Inf value (in raw HTTP JSON bytes)
    def handler_inf(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b'{"data": [{"index": 0, "embedding": [Infinity, 0.5]}]}',
            headers={"Content-Type": "application/json"},
        )

    mock_client_inf = httpx.AsyncClient(transport=httpx.MockTransport(handler_inf))
    provider_inf = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client_inf)
    with pytest.raises(ProviderError) as exc_info:
        await provider_inf.embed_texts(["test"])
    assert "NaN or Inf values" in str(exc_info.value)


async def test_openai_embedding_provider_no_raw_response_text_logged(caplog: pytest.LogCaptureFixture):
    """
    CRITICAL PROOF (FIX G): Permanent error responses MUST NOT log response.text or response bodies.
    """
    settings = Settings(OPENAI_API_KEY="sk-test-key", LLM_MAX_RETRIES=0)
    error_body_sample = '{"error": {"message": "confidential_internal_detail_12345"}}'

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, content=error_body_sample.encode())

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAiEmbeddingProvider(settings=settings, http_client=mock_client)

    with pytest.raises(ProviderError):
        await provider.embed_texts(["test"])

    # Ensure the error body is nowhere in log output
    assert "confidential_internal_detail_12345" not in caplog.text
