"""Unit tests for GeminiEmbeddingProvider adapter, validation rules, and error handling."""

import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from google.genai import errors, types
import pytest

from app.core.config import Settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.infrastructure.embeddings.providers.gemini_provider import (
    DEFAULT_GEMINI_EMBEDDING_MODEL,
    MAX_BATCH_SIZE,
    GeminiEmbeddingProvider,
)


def _make_mock_client(return_embeddings: list[list[float]] | None = None) -> MagicMock:
    """Helper to build a mock genai.Client with an async embed_content endpoint."""
    mock_client = MagicMock()
    mock_client.aio = MagicMock()

    if return_embeddings is not None:
        emb_objects = [types.ContentEmbedding(values=vec) for vec in return_embeddings]
        mock_response = types.EmbedContentResponse(embeddings=emb_objects)
        mock_client.aio.models.embed_content = AsyncMock(return_value=mock_response)
    else:
        mock_client.aio.models.embed_content = AsyncMock()

    mock_client.aio.aclose = AsyncMock()
    return mock_client


def _make_api_error(message: str, code: int) -> errors.APIError:
    """Helper to construct google.genai errors.APIError with given HTTP status code."""
    return errors.APIError(code, {"error": message})


# =============================================================================
# 1. Initialization and Provider Metadata
# =============================================================================


def test_gemini_embedding_provider_initialization_defaults():
    """Verify GeminiEmbeddingProvider initializes with default model and settings."""
    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        GEMINI_API_KEY="AIzaSyValidEmbeddingKey",
        LLM_TIMEOUT_SECONDS=25,
        LLM_MAX_RETRIES=2,
    )
    mock_client = _make_mock_client()
    provider = GeminiEmbeddingProvider(settings=settings, client=mock_client)

    assert provider.provider_name == "gemini"
    assert provider.model_name == DEFAULT_GEMINI_EMBEDDING_MODEL
    assert provider.timeout == 25.0
    assert provider.max_retries == 2


def test_gemini_embedding_provider_custom_model():
    """Verify configured custom model overrides default model."""
    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        EMBEDDING_MODEL="text-embedding-004",
        GEMINI_API_KEY="AIzaSyValidEmbeddingKey",
    )
    mock_client = _make_mock_client()
    provider = GeminiEmbeddingProvider(settings=settings, client=mock_client)

    assert provider.model_name == "text-embedding-004"


def test_gemini_embedding_provider_missing_key_raises_error():
    """Verify missing GEMINI_API_KEY raises ProviderError when client is not injected."""
    settings = Settings(
        EMBEDDING_PROVIDER="gemini",
        GEMINI_API_KEY=None,
    )
    with pytest.raises(ProviderError) as exc_info:
        GeminiEmbeddingProvider(settings=settings)

    assert "GEMINI_API_KEY must be configured" in str(exc_info.value)
    assert exc_info.value.details.get("provider") == "gemini"


# =============================================================================
# 2. Sequence Ordering & Empty Input
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_empty_sequence_returns_empty_list():
    """Verify empty input texts returns empty list without calling API."""
    mock_client = _make_mock_client()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    result = await provider.embed_texts([])
    assert result == []
    mock_client.aio.models.embed_content.assert_not_called()


@pytest.mark.asyncio
async def test_embed_texts_preserves_exact_order():
    """Verify input texts return embeddings in the exact corresponding order."""
    expected_vectors = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]
    mock_client = _make_mock_client(return_embeddings=expected_vectors)
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    inputs = ["Senior Python Developer", "PostgreSQL database optimization", "Docker Kubernetes"]
    vectors = await provider.embed_texts(inputs)

    assert len(vectors) == 3
    assert vectors[0] == [0.1, 0.2, 0.3]
    assert vectors[1] == [0.4, 0.5, 0.6]
    assert vectors[2] == [0.7, 0.8, 0.9]


# =============================================================================
# 3. Validation Rule 1: Vector Count == Text Count
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_cardinality_mismatch_too_few_vectors():
    """Rule 1: ProviderError raised if API returns fewer vectors than requested."""
    mock_client = _make_mock_client(return_embeddings=[[0.1, 0.2]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Text 1", "Text 2"])

    assert "returned 1 vectors for 2 input texts" in str(exc_info.value)
    assert exc_info.value.details.get("provider") == "gemini"


@pytest.mark.asyncio
async def test_embed_texts_cardinality_mismatch_too_many_vectors():
    """Rule 1: ProviderError raised if API returns more vectors than requested."""
    mock_client = _make_mock_client(return_embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Text 1", "Text 2"])

    assert "returned 3 vectors for 2 input texts" in str(exc_info.value)


# =============================================================================
# 4. Validation Rule 2: Non-empty Vectors & Uniform Dimensionality
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_empty_vector_rejected():
    """Rule 2: Reject empty vector in API response."""
    mock_client = _make_mock_client(return_embeddings=[[]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Valid text"])

    assert "empty or non-list vector" in str(exc_info.value)


@pytest.mark.asyncio
async def test_embed_texts_inconsistent_dimension_rejected():
    """Rule 2: Reject vectors with inconsistent dimensions across the batch."""
    mock_client = _make_mock_client(return_embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Text 1", "Text 2"])

    assert "Inconsistent embedding dimensions: expected 3, got 2" in str(exc_info.value)


# =============================================================================
# 5. Validation Rule 3: Finite Numeric Values (No NaN, +/-Inf)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_val", [float("nan"), float("inf"), float("-inf")])
async def test_embed_texts_nan_or_inf_rejected(bad_val: float):
    """Rule 3: Reject vectors containing NaN or +/-Infinity."""
    mock_client = _make_mock_client(return_embeddings=[[0.1, bad_val, 0.3]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert "contains NaN or Inf values" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_element", ["invalid_str", True, False, None, [1.0]])
async def test_embed_texts_non_numeric_element_rejected(bad_element: Any):
    """Rule 3: Reject vectors containing non-numeric elements."""
    mock_client = _make_mock_client()
    # Construct raw dict response with non-numeric value
    mock_client.aio.models.embed_content.return_value = {"embeddings": [{"values": [0.1, bad_element, 0.3]}]}
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert "contains non-numeric value" in str(exc_info.value)


# =============================================================================
# 6. Validation Rule 4: Privacy Invariance (Zero PII Logged)
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_zero_pii_logging(caplog: pytest.LogCaptureFixture):
    """Rule 4: CV and JD text must NEVER be logged to console or logger."""
    sensitive_cv_text = "Nguyen Van A - Secret Candidate Summary with PII phone 0901234567"
    sensitive_jd_text = "Confidential Employer Internal Job Description salary 10000 USD"

    mock_client = _make_mock_client(return_embeddings=[[0.1, 0.2], [0.3, 0.4]])
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    with caplog.at_level(logging.DEBUG):
        await provider.embed_texts([sensitive_cv_text, sensitive_jd_text])

    for record in caplog.records:
        assert sensitive_cv_text not in record.message
        assert sensitive_jd_text not in record.message
        assert "0901234567" not in record.message
        assert "Nguyen Van A" not in record.message


# =============================================================================
# 7. Validation Rule 5: 401 Fails Immediately Without Retrying
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_401_fails_fast_without_retrying():
    """Rule 5: HTTP 401 must fail immediately with ProviderError and zero retries."""
    mock_client = _make_mock_client()
    mock_client.aio.models.embed_content.side_effect = _make_api_error("Unauthorized", code=401)

    sleep_mock = AsyncMock()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="invalid-key", LLM_MAX_RETRIES=3),
        client=mock_client,
        sleep_func=sleep_mock,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert "permanent status 401" in str(exc_info.value)
    assert mock_client.aio.models.embed_content.call_count == 1
    sleep_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 403, 404])
async def test_embed_texts_permanent_4xx_errors_fail_fast(status_code: int):
    """Rule 5: Other permanent 4xx errors (400, 403, 404) fail immediately without retrying."""
    mock_client = _make_mock_client()
    mock_client.aio.models.embed_content.side_effect = _make_api_error("Client error", code=status_code)

    sleep_mock = AsyncMock()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=3),
        client=mock_client,
        sleep_func=sleep_mock,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert f"permanent status {status_code}" in str(exc_info.value)
    assert mock_client.aio.models.embed_content.call_count == 1
    sleep_mock.assert_not_called()


# =============================================================================
# 8. Validation Rule 6: 429 & 5xx Bounded Retries with Backoff
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_429_retries_and_raises_rate_limit_exceeded():
    """Rule 6: HTTP 429 retries with backoff and raises RateLimitExceededError when exhausted."""
    mock_client = _make_mock_client()
    mock_client.aio.models.embed_content.side_effect = _make_api_error("Resource Exhausted", code=429)

    sleep_mock = AsyncMock()
    max_retries = 2
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=max_retries),
        client=mock_client,
        sleep_func=sleep_mock,
    )

    with pytest.raises(RateLimitExceededError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert "rate limit reached after retries" in str(exc_info.value)
    assert mock_client.aio.models.embed_content.call_count == max_retries + 1
    assert sleep_mock.call_count == max_retries


@pytest.mark.asyncio
async def test_embed_texts_503_retries_then_succeeds():
    """Rule 6: Transient 503 error retries with exponential backoff and succeeds on subsequent attempt."""
    mock_client = _make_mock_client()
    success_resp = types.EmbedContentResponse(embeddings=[types.ContentEmbedding(values=[0.1, 0.2, 0.3])])
    mock_client.aio.models.embed_content.side_effect = [
        _make_api_error("Service Unavailable", code=503),
        success_resp,
    ]

    sleep_mock = AsyncMock()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=2),
        client=mock_client,
        sleep_func=sleep_mock,
    )

    vectors = await provider.embed_texts(["Sample text"])

    assert vectors == [[0.1, 0.2, 0.3]]
    assert mock_client.aio.models.embed_content.call_count == 2
    assert sleep_mock.call_count == 1
    sleep_mock.assert_awaited_with(1.0)  # attempt 0: 1.0 * (2^0) = 1.0s


@pytest.mark.asyncio
async def test_embed_texts_500_exhausts_retries_raises_provider_error():
    """Rule 6: Persistent 500 error raises ProviderError when max retries are exhausted."""
    mock_client = _make_mock_client()
    mock_client.aio.models.embed_content.side_effect = _make_api_error("Internal Error", code=500)

    sleep_mock = AsyncMock()
    max_retries = 1
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key", LLM_MAX_RETRIES=max_retries),
        client=mock_client,
        sleep_func=sleep_mock,
    )

    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(["Sample text"])

    assert "transient error status 500 after 2 attempts" in str(exc_info.value)
    assert mock_client.aio.models.embed_content.call_count == 2


# =============================================================================
# 9. Validation Rule 7: Batch Size Limit Enforcement (MAX_BATCH_SIZE = 100)
# =============================================================================


@pytest.mark.asyncio
async def test_embed_texts_batch_size_exceeding_limit_raises_error():
    """Rule 7: Reject batch requests exceeding MAX_BATCH_SIZE (100) without calling API."""
    mock_client = _make_mock_client()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )

    texts = [f"Text item {i}" for i in range(MAX_BATCH_SIZE + 1)]
    with pytest.raises(ProviderError) as exc_info:
        await provider.embed_texts(texts)

    assert f"exceeds maximum allowed limit {MAX_BATCH_SIZE}" in str(exc_info.value)
    mock_client.aio.models.embed_content.assert_not_called()


# =============================================================================
# 10. Lifecycle Cleanup (aclose)
# =============================================================================


@pytest.mark.asyncio
async def test_gemini_embedding_provider_aclose_owned_client():
    """Verify provider closes underlying genai client when owned."""
    settings = Settings(GEMINI_API_KEY="test-key")
    with patch("app.infrastructure.embeddings.providers.gemini_provider.genai.Client") as mock_genai_cls:
        mock_instance = MagicMock()
        mock_instance.aio.aclose = AsyncMock()
        mock_genai_cls.return_value = mock_instance

        provider = GeminiEmbeddingProvider(settings=settings)
        await provider.aclose()

        mock_instance.aio.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_embedding_provider_aclose_injected_client_not_closed():
    """Verify provider does NOT close an injected external client."""
    mock_client = _make_mock_client()
    provider = GeminiEmbeddingProvider(
        settings=Settings(GEMINI_API_KEY="test-key"),
        client=mock_client,
    )
    await provider.aclose()

    mock_client.aio.aclose.assert_not_called()


def test_gemini_embedding_provider_prefers_dedicated_embedding_key():
    """Verify GeminiEmbeddingProvider uses GEMINI_EMBEDDING_API_KEY over GEMINI_API_KEY."""
    mock_client = MagicMock()
    settings = Settings(
        GEMINI_EMBEDDING_API_KEY="dedicated-embedding-key",
        GEMINI_API_KEY="common-fallback-key",
        EMBEDDING_PROVIDER="gemini",
    )
    provider = GeminiEmbeddingProvider(settings=settings, client=mock_client)
    assert provider._ensure_api_key() == "dedicated-embedding-key"


def test_gemini_embedding_provider_falls_back_to_common_gemini_api_key():
    """Verify GeminiEmbeddingProvider falls back to GEMINI_API_KEY when GEMINI_EMBEDDING_API_KEY is empty."""
    mock_client = MagicMock()
    settings = Settings(
        GEMINI_EMBEDDING_API_KEY="",
        GEMINI_API_KEY="common-fallback-key",
        EMBEDDING_PROVIDER="gemini",
    )
    provider = GeminiEmbeddingProvider(settings=settings, client=mock_client)
    assert provider._ensure_api_key() == "common-fallback-key"
