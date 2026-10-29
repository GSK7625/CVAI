"""OpenAI Embeddings provider adapter using httpx async client."""

import asyncio
from collections.abc import Callable, Coroutine, Sequence
import math
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.observability.logging import get_logger
from app.ports.embeddings import EmbeddingPort

logger = get_logger(__name__)

# Set of transient HTTP status codes that warrant bounded retries
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Permanent client error status codes that must fail immediately without retrying
PERMANENT_ERROR_CODES = {400, 401, 403, 404}


class OpenAiEmbeddingProvider(EmbeddingPort):
    """OpenAI Embeddings API adapter with reusable async client, resilient timeouts, and bounded retries."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
        sleep_func: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.openai_api_key
        self.model = self.settings.embedding_model or "text-embedding-3-small"
        self.timeout = float(self.settings.llm_timeout_seconds)
        self.max_retries = self.settings.llm_max_retries
        self.base_url = "https://api.openai.com/v1/embeddings"
        self._client = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._owns_client = http_client is None
        self._sleep = sleep_func

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai"

    @property
    def model_name(self) -> str:
        """Return configured embedding model identifier."""
        return self.model

    async def aclose(self) -> None:
        """Close the underlying AsyncClient if owned by this provider instance."""
        if self._owns_client and not self._client.is_closed:
            await self._client.aclose()

    def _ensure_api_key(self) -> str:
        """Validate presence of OpenAI API key."""
        if not self.api_key:
            raise ProviderError("OpenAI API key is not configured in environment", provider="openai")
        return self.api_key

    def _calculate_backoff(self, attempt: int, response: httpx.Response | None = None) -> float:
        """Calculate exponential backoff or honor Retry-After header."""
        max_delay = 10.0
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return float(min(float(retry_after), max_delay))
                except ValueError:
                    pass
        # Exponential backoff: 0.5 * 2^attempt
        return float(min(0.5 * (2**attempt), max_delay))

    def _parse_response_json(self, response: httpx.Response) -> dict[str, Any]:
        """
        Safely decode and validate root JSON object from an HTTP success response.
        Raises ProviderError if response body is invalid JSON or not a JSON object.
        """
        try:
            data = response.json()
        except (ValueError, TypeError) as exc:
            logger.error(
                "OpenAI Embeddings returned non-JSON HTTP %d response (error_type=%s)",
                response.status_code,
                exc.__class__.__name__,
            )
            raise ProviderError(
                "Invalid JSON in OpenAI Embeddings response body",
                provider="openai",
            ) from exc

        if not isinstance(data, dict):
            logger.error(
                "OpenAI Embeddings returned invalid top-level JSON type: expected dict, got %s",
                type(data).__name__,
            )
            raise ProviderError(
                "Malformed OpenAI embeddings response: root payload must be a JSON object",
                provider="openai",
            )
        return data

    def _extract_embedding_vectors(self, data: dict[str, Any], expected_count: int) -> list[list[float]]:
        """
        Safely validate and extract embedding vectors from OpenAI API payload.

        Validates:
        - Root 'data' field is a list with exact expected item count.
        - Each item is an object containing integer 'index' and list 'embedding'.
        - Index sequence integrity: sorted indices must strictly equal [0, 1, ..., expected_count-1].
          Rejects duplicate, missing, negative, gapped, or out-of-range indices.
        - Dimension consistency: every vector has identical non-zero dimensionality.
        - All elements are finite numbers (rejects non-numeric, NaN, +/-Inf).
        """
        raw_data = data.get("data")
        if not isinstance(raw_data, list):
            raise ProviderError(
                "Malformed response structure from OpenAI Embeddings API: missing or non-list 'data' field",
                provider="openai",
            )

        if len(raw_data) != expected_count:
            raise ProviderError(
                f"Malformed response structure from OpenAI Embeddings API: "
                f"returned {len(raw_data)} embeddings for {expected_count} input texts",
                provider="openai",
            )

        # Validate item types and index attributes before sorting
        for pos, item in enumerate(raw_data):
            if not isinstance(item, dict):
                raise ProviderError(
                    f"Malformed response structure from OpenAI Embeddings API: item at position {pos} is not an object",
                    provider="openai",
                )
            if "index" not in item:
                raise ProviderError(
                    f"Malformed response structure from OpenAI Embeddings API: "
                    f"missing 'index' field in item at position {pos}",
                    provider="openai",
                )
            idx_val = item["index"]
            if isinstance(idx_val, bool) or not isinstance(idx_val, int):
                raise ProviderError(
                    f"Malformed response structure from OpenAI Embeddings API: "
                    f"non-integer 'index' ({idx_val!r}) in item",
                    provider="openai",
                )
            if "embedding" not in item:
                raise ProviderError(
                    f"Malformed response structure from OpenAI Embeddings API: "
                    f"missing 'embedding' field in item {idx_val}",
                    provider="openai",
                )

        # Sort items by index to guarantee exact input ordering
        sorted_items = sorted(raw_data, key=lambda item: int(item["index"]))

        # Strict index integrity check (FIX D)
        actual_indices = [item["index"] for item in sorted_items]
        expected_indices = list(range(expected_count))
        if actual_indices != expected_indices:
            raise ProviderError(
                f"Malformed response structure from OpenAI Embeddings API: "
                f"invalid index sequence (got {actual_indices}, expected {expected_indices})",
                provider="openai",
            )

        # Dimension and finite numeric validation (FIX C, E)
        vectors: list[list[float]] = []
        expected_dimension: int | None = None

        for item in sorted_items:
            vec = item.get("embedding")
            if not isinstance(vec, list) or len(vec) == 0:
                raise ProviderError(
                    "Malformed response structure from OpenAI Embeddings API: empty or non-list 'embedding' vector",
                    provider="openai",
                )

            if expected_dimension is None:
                expected_dimension = len(vec)
                if expected_dimension == 0:
                    raise ProviderError(
                        "Malformed response structure from OpenAI Embeddings API: zero-dimension embedding vector",
                        provider="openai",
                    )
            elif len(vec) != expected_dimension:
                raise ProviderError(
                    f"Malformed response structure from OpenAI Embeddings API: "
                    f"inconsistent vector dimension (expected {expected_dimension}, got {len(vec)})",
                    provider="openai",
                )

            float_vec: list[float] = []
            for val in vec:
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    raise ProviderError(
                        "Malformed response structure from OpenAI Embeddings API: vector contains non-numeric value",
                        provider="openai",
                    )
                f_val = float(val)
                if math.isnan(f_val) or math.isinf(f_val):
                    raise ProviderError("OpenAI embedding vector contains NaN or Inf values", provider="openai")
                float_vec.append(f_val)

            vectors.append(float_vec)

        return vectors

    async def _post_embeddings(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute embeddings request with bounded retries for transient errors."""
        api_key = self._ensure_api_key()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        last_status: int | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.post(self.base_url, headers=headers, json=payload)
                last_status = response.status_code

                if response.is_success:
                    return self._parse_response_json(response)

                # Immediate failure for permanent 4xx errors
                if response.status_code in PERMANENT_ERROR_CODES:
                    logger.error(
                        "Permanent error from OpenAI Embeddings (status=%d)",
                        response.status_code,
                    )
                    raise ProviderError(
                        f"OpenAI service rejected embedding request with status {response.status_code}",
                        provider="openai",
                    )

                # Transient errors - retry if attempts remain
                if response.status_code in TRANSIENT_STATUS_CODES:
                    if attempt < self.max_retries:
                        backoff = self._calculate_backoff(attempt, response)
                        logger.warning(
                            "Transient OpenAI Embeddings error (status=%d, attempt=%d/%d). Retrying in %.2fs...",
                            response.status_code,
                            attempt + 1,
                            self.max_retries,
                            backoff,
                        )
                        await self._sleep(backoff)
                        continue

                    # Exhausted retries for transient error
                    if response.status_code == 429:
                        raise RateLimitExceededError("OpenAI embedding rate limit reached after retries")

                    raise ProviderError(
                        f"OpenAI service returned transient error status {response.status_code} "
                        f"after {self.max_retries + 1} attempts",
                        provider="openai",
                    )

                # Any other unexpected non-transient status code
                raise ProviderError(
                    f"OpenAI service returned unexpected status {response.status_code}",
                    provider="openai",
                )

            except (RateLimitExceededError, ProviderError):
                raise
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Network/timeout error connecting to OpenAI Embeddings "
                        "(attempt %d/%d, error=%s). Retrying in %.2fs...",
                        attempt + 1,
                        self.max_retries,
                        exc.__class__.__name__,
                        backoff,
                    )
                    await self._sleep(backoff)
                    continue

        raise ProviderError(
            f"Failed to communicate with OpenAI Embeddings after {self.max_retries + 1} attempts",
            provider="openai",
            details={
                "last_error_type": last_error.__class__.__name__ if last_error else "Unknown",
                "last_status": last_status,
            },
        )

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embedding vectors for sequence of texts preserving original input ordering."""
        if not texts:
            return []

        payload = {
            "model": self.model,
            "input": list(texts),
        }

        # Privacy invariant: log text count and model, NEVER raw texts
        logger.info("Requesting embeddings from OpenAI (count=%d, model=%s)", len(texts), self.model)

        data = await self._post_embeddings(payload)
        return self._extract_embedding_vectors(data, expected_count=len(texts))
