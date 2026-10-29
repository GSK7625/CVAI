"""Google Gemini Embeddings provider adapter using official google-genai SDK."""

import asyncio
from collections.abc import Callable, Coroutine, Sequence
import math
from typing import Any

from google import genai
from google.genai import errors

from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.observability.logging import get_logger
from app.ports.embeddings import EmbeddingPort

logger = get_logger(__name__)

# Transient HTTP status codes that warrant bounded retries
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Permanent client error status codes that must fail immediately without retrying
PERMANENT_ERROR_CODES = {400, 401, 403, 404}

DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"
MAX_BATCH_SIZE = 100


class GeminiEmbeddingProvider(EmbeddingPort):
    """Google Gemini Embeddings adapter with async client, dimension validation, and bounded retries."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: genai.Client | None = None,
        sleep_func: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        configured_model = self.settings.embedding_model
        if not configured_model or configured_model.startswith("text-embedding-3"):
            self.model = DEFAULT_GEMINI_EMBEDDING_MODEL
        else:
            self.model = configured_model

        self.timeout = float(self.settings.llm_timeout_seconds)
        self.max_retries = self.settings.llm_max_retries
        self._sleep = sleep_func

        if client is not None:
            self._client = client
            self._owns_client = False
        else:
            api_key = self._ensure_api_key()
            self._client = genai.Client(api_key=api_key)
            self._owns_client = True

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "gemini"

    @property
    def model_name(self) -> str:
        """Return configured embedding model identifier."""
        return self.model

    def _ensure_api_key(self) -> str:
        """Ensure GEMINI_EMBEDDING_API_KEY or GEMINI_API_KEY is configured and non-empty."""
        key = self.settings.get_effective_gemini_embedding_key()
        if not key or not key.strip():
            raise ProviderError(
                "GEMINI_API_KEY must be configured for Gemini embedding provider",
                provider="gemini",
            )
        return key.strip()

    async def aclose(self) -> None:
        """Close the underlying client if owned by this provider instance."""
        if self._owns_client and self._client is not None:
            await self._client.aio.aclose()

    def _calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff duration in seconds."""
        backoff = min(1.0 * (2**attempt), 10.0)
        return float(backoff)

    def _extract_embedding_vectors(self, response: Any, expected_count: int) -> list[list[float]]:
        """
        Extract and strictly validate embedding vectors from Gemini API response.

        Validates:
        1. Root embeddings field is a list.
        2. Vector count matches expected count.
        3. Each vector is non-empty with uniform dimensionality across the batch.
        4. Elements are strictly finite numbers (rejects non-numeric, NaN, +/-Inf).
        """
        if isinstance(response, dict):
            raw_embeddings = response.get("embeddings")
        else:
            raw_embeddings = getattr(response, "embeddings", None)

        if not isinstance(raw_embeddings, list):
            raise ProviderError(
                "Malformed response structure from Gemini Embeddings API: missing or non-list 'embeddings' field",
                provider="gemini",
            )

        if len(raw_embeddings) != expected_count:
            raise ProviderError(
                f"Gemini Embeddings returned {len(raw_embeddings)} vectors for {expected_count} input texts",
                provider="gemini",
            )

        vectors: list[list[float]] = []
        expected_dimension: int | None = None

        for pos, item in enumerate(raw_embeddings):
            if isinstance(item, dict):
                values = item.get("values")
            elif hasattr(item, "values"):
                values = getattr(item, "values", None)
            elif isinstance(item, list):
                values = item
            else:
                values = None

            if not isinstance(values, list) or len(values) == 0:
                raise ProviderError(
                    f"Malformed response structure from Gemini Embeddings API: "
                    f"empty or non-list vector at position {pos}",
                    provider="gemini",
                )

            if expected_dimension is None:
                expected_dimension = len(values)
                if expected_dimension == 0:
                    raise ProviderError(
                        "Gemini Embeddings returned zero-dimension embedding vector",
                        provider="gemini",
                    )
            elif len(values) != expected_dimension:
                raise ProviderError(
                    f"Inconsistent embedding dimensions: "
                    f"expected {expected_dimension}, got {len(values)} at position {pos}",
                    provider="gemini",
                )

            float_vec: list[float] = []
            for val in values:
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    raise ProviderError(
                        "Gemini embedding vector contains non-numeric value",
                        provider="gemini",
                    )
                f_val = float(val)
                if math.isnan(f_val) or math.isinf(f_val):
                    raise ProviderError(
                        "Gemini embedding vector contains NaN or Inf values",
                        provider="gemini",
                    )
                float_vec.append(f_val)

            vectors.append(float_vec)

        return vectors

    async def _execute_embed_content(self, texts: list[str]) -> Any:
        """Execute async embed_content with timeout and bounded retries for transient errors."""
        last_error: Exception | None = None
        last_status: int | None = None

        for attempt in range(self.max_retries + 1):
            try:
                coro = self._client.aio.models.embed_content(
                    model=self.model,
                    contents=texts,  # type: ignore[arg-type]
                )
                return await asyncio.wait_for(coro, timeout=self.timeout)

            except errors.APIError as exc:
                last_error = exc
                status_code = getattr(exc, "code", None)
                last_status = status_code

                # Immediate failure for permanent 4xx errors (401, 400, 403, 404)
                if status_code in PERMANENT_ERROR_CODES:
                    logger.error(
                        "Permanent error from Gemini Embeddings (status=%s): %s",
                        status_code,
                        exc,
                    )
                    raise ProviderError(
                        f"Gemini service rejected embedding request with permanent status {status_code}",
                        provider="gemini",
                        details={"status_code": status_code},
                    ) from exc

                # Transient errors - retry if attempts remain
                if status_code in TRANSIENT_STATUS_CODES:
                    if attempt < self.max_retries:
                        backoff = self._calculate_backoff(attempt)
                        logger.warning(
                            "Transient Gemini Embeddings error (status=%s, attempt=%d/%d). Retrying in %.2fs...",
                            status_code,
                            attempt + 1,
                            self.max_retries,
                            backoff,
                        )
                        await self._sleep(backoff)
                        continue

                    if status_code == 429:
                        raise RateLimitExceededError("Gemini embedding rate limit reached after retries") from exc

                    raise ProviderError(
                        f"Gemini service returned transient error status {status_code} "
                        f"after {self.max_retries + 1} attempts",
                        provider="gemini",
                        details={"status_code": status_code},
                    ) from exc

                # Unexpected non-transient status code
                raise ProviderError(
                    f"Gemini service returned error status {status_code}",
                    provider="gemini",
                    details={"status_code": status_code},
                ) from exc

            except TimeoutError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    backoff = self._calculate_backoff(attempt)
                    logger.warning(
                        "Timeout connecting to Gemini Embeddings (attempt %d/%d). Retrying in %.2fs...",
                        attempt + 1,
                        self.max_retries,
                        backoff,
                    )
                    await self._sleep(backoff)
                    continue

                raise ProviderError(
                    f"Gemini embedding request timed out after {self.timeout}s and {self.max_retries + 1} attempts",
                    provider="gemini",
                ) from exc

            except (RateLimitExceededError, ProviderError):
                raise

            except Exception as exc:
                last_error = exc
                logger.error("Unexpected error communicating with Gemini Embeddings: %s", exc)
                raise ProviderError(
                    "Unexpected error communicating with Gemini Embeddings",
                    provider="gemini",
                    details={"error_type": exc.__class__.__name__},
                ) from exc

        raise ProviderError(
            f"Failed to communicate with Gemini Embeddings after {self.max_retries + 1} attempts",
            provider="gemini",
            details={
                "last_error_type": last_error.__class__.__name__ if last_error else "Unknown",
                "last_status": last_status,
            },
        )

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate embedding vectors for sequence of texts.

        Preserves exact input sequence ordering.
        Enforces batch size limit and shields privacy (never logs input text).
        """
        if not texts:
            return []

        if len(texts) > MAX_BATCH_SIZE:
            raise ProviderError(
                f"Embedding batch size {len(texts)} exceeds maximum allowed limit {MAX_BATCH_SIZE}",
                provider="gemini",
            )

        # Privacy invariant: log text count and model, NEVER raw texts (PII protection)
        logger.info("Requesting embeddings from Gemini (count=%d, model=%s)", len(texts), self.model)

        response = await self._execute_embed_content(list(texts))
        return self._extract_embedding_vectors(response, expected_count=len(texts))
