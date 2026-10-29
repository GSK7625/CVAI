"""OpenAI LLM provider adapter using httpx async client."""

import asyncio
from collections.abc import Callable, Coroutine
import json
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.observability.logging import get_logger
from app.ports.llm import LlmPort

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# Set of transient HTTP status codes that warrant bounded retries
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Permanent client error status codes that must fail immediately without retrying
PERMANENT_ERROR_CODES = {400, 401, 403, 404}


class OpenAiProvider(LlmPort):
    """OpenAI API provider adapter with reusable async client, resilient timeouts, and bounded retries."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
        sleep_func: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.openai_api_key
        self.model = self.settings.llm_model or "gpt-4o-mini"
        self.timeout = float(self.settings.llm_timeout_seconds)
        self.max_retries = self.settings.llm_max_retries
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self._client = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._owns_client = http_client is None
        self._sleep = sleep_func

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "openai"

    @property
    def model_name(self) -> str:
        """Return configured model identifier."""
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
                "OpenAI returned non-JSON HTTP %d response (error_type=%s)",
                response.status_code,
                exc.__class__.__name__,
            )
            raise ProviderError(
                "Invalid JSON in OpenAI response body",
                provider="openai",
            ) from exc

        if not isinstance(data, dict):
            logger.error(
                "OpenAI returned invalid top-level JSON type: expected dict, got %s",
                type(data).__name__,
            )
            raise ProviderError(
                "Malformed OpenAI response: root payload must be a JSON object",
                provider="openai",
            )
        return data

    def _extract_text_content(self, data: dict[str, Any]) -> str:
        """
        Safely validate and extract text string from OpenAI chat completion payload.
        Expected structure: choices[0].message.content (str)
        """
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise ProviderError(
                "Malformed OpenAI response: missing or empty 'choices' list",
                provider="openai",
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ProviderError(
                "Malformed OpenAI response: 'choices[0]' must be an object",
                provider="openai",
            )

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ProviderError(
                "Malformed OpenAI response: missing or invalid 'message' object in choice",
                provider="openai",
            )

        content = message.get("content")
        if content is None:
            raise ProviderError(
                "Malformed OpenAI response: 'content' field is None",
                provider="openai",
            )

        if not isinstance(content, str):
            raise ProviderError(
                f"Malformed OpenAI response: expected string content, got {type(content).__name__}",
                provider="openai",
            )

        return content

    async def _post_chat_completion(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute chat completion request with bounded retries for transient errors."""
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
                        "Permanent error from OpenAI (status=%d)",
                        response.status_code,
                    )
                    raise ProviderError(
                        f"OpenAI service rejected request with permanent error status {response.status_code}",
                        provider="openai",
                    )

                # Transient errors - retry if attempts remain
                if response.status_code in TRANSIENT_STATUS_CODES:
                    if attempt < self.max_retries:
                        backoff = self._calculate_backoff(attempt, response)
                        logger.warning(
                            "Transient OpenAI error (status=%d, attempt=%d/%d). Retrying in %.2fs...",
                            response.status_code,
                            attempt + 1,
                            self.max_retries,
                            backoff,
                        )
                        await self._sleep(backoff)
                        continue

                    # Exhausted retries for transient error
                    if response.status_code == 429:
                        raise RateLimitExceededError("OpenAI rate limit reached after retries")

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
                        "Network/timeout error connecting to OpenAI (attempt %d/%d, error=%s). Retrying in %.2fs...",
                        attempt + 1,
                        self.max_retries,
                        exc.__class__.__name__,
                        backoff,
                    )
                    await self._sleep(backoff)
                    continue

        raise ProviderError(
            f"Failed to communicate with OpenAI after {self.max_retries + 1} attempts",
            provider="openai",
            details={
                "last_error_type": last_error.__class__.__name__ if last_error else "Unknown",
                "last_status": last_status,
            },
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate unstructured text from OpenAI."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        data = await self._post_chat_completion(payload)
        content = self._extract_text_content(data)
        return content.strip()

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """
        Generate structured JSON and validate using Pydantic.

        NOTE & ARCHITECTURAL TODO:
        We currently use OpenAI JSON Object mode ({"type": "json_object"}) combined with strict
        Pydantic schema validation. JSON object mode guarantees syntactically valid JSON, but
        does NOT provide formal schema compliance guarantees by itself. Pydantic validation
        remains mandatory at this application boundary.
        Evaluation of OpenAI Structured Outputs (response_format with strict json_schema)
        should be conducted in a dedicated provider integration and benchmarking pass.
        """
        schema_json = json.dumps(response_model.model_json_schema())
        augmented_system = (
            (system_prompt or "") + f"\nYou MUST output strictly valid JSON matching this schema:\n{schema_json}"
        ).strip()

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        data = await self._post_chat_completion(payload)
        content = self._extract_text_content(data)

        try:
            parsed_json = json.loads(content)
        except (ValueError, TypeError) as exc:
            logger.warning("Failed to decode OpenAI structured output JSON: %s", exc.__class__.__name__)
            raise ProviderError(
                "OpenAI response content is not valid JSON",
                provider="openai",
            ) from exc

        if not isinstance(parsed_json, dict):
            logger.warning(
                "OpenAI structured output is not a JSON object: %s",
                type(parsed_json).__name__,
            )
            raise ProviderError(
                "OpenAI structured output must be a JSON object",
                provider="openai",
            )

        try:
            return response_model.model_validate(parsed_json)
        except ValidationError as exc:
            logger.warning(
                "Failed to validate OpenAI output against schema %s: %d validation error(s)",
                response_model.__name__,
                len(exc.errors()),
            )
            raise ProviderError(
                "AI model generated output that does not match required contract",
                provider="openai",
            ) from exc

    async def extract_text_from_document(
        self,
        document_bytes: bytes,
        mime_type: str = "application/pdf",
        instruction: str | None = None,
    ) -> str:
        """Extract readable text from document bytes."""
        raise ProviderError(
            "Direct document vision OCR is currently supported via Gemini provider",
            provider="openai",
        )

