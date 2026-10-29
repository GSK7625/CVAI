"""Google Gemini LLM provider adapter using official google-genai SDK."""

import asyncio
from collections.abc import Callable, Coroutine
import copy
import json
import re
from typing import Any, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import ProviderError, RateLimitExceededError
from app.observability.logging import get_logger
from app.ports.llm import LlmPort

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)

# Transient status codes that warrant bounded retries
TRANSIENT_STATUS_CODES = {408, 429, 500, 502, 503, 504}

# Permanent client error status codes that must fail immediately without retrying
PERMANENT_ERROR_CODES = {400, 401, 403, 404}

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


def _clean_json_text(text: str) -> str:
    """Strip markdown code fence if present in model response."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    else:
        # Match fenced code block inside surrounding commentary if any
        fence_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", cleaned, re.DOTALL)
        if fence_match:
            cleaned = fence_match.group(1).strip()
    return cleaned


def _convert_to_gemini_schema(raw_schema: dict[str, Any]) -> dict[str, Any]:
    """Convert a Pydantic JSON schema to Gemini OpenAPI 3.0 compatible schema subset."""
    schema = copy.deepcopy(raw_schema)
    defs = schema.pop("$defs", {})

    def convert(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref_key = node["$ref"].split("/")[-1]
                target = copy.deepcopy(defs.get(ref_key, {}))
                return convert(target)

            res: dict[str, Any] = {}
            if "anyOf" in node:
                non_null = [t for t in node["anyOf"] if t.get("type") != "null"]
                if non_null:
                    res = convert(non_null[0])
                    res["nullable"] = True
                    return res

            for k, v in node.items():
                if k in (
                    "additionalProperties",
                    "additional_properties",
                    "title",
                    "maxLength",
                    "maxItems",
                    "minLength",
                    "default",
                ):
                    continue
                res[k] = convert(v)
            return res
        if isinstance(node, list):
            return [convert(x) for x in node]
        return node

    return convert(schema)


class GeminiLlmProvider(LlmPort):
    """Google Gemini LLM provider adapter using official google-genai SDK with async support and retries."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: genai.Client | None = None,
        sleep_func: Callable[[float], Coroutine[Any, Any, None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        # Default to gemini-2.5-flash if model is unset or remains default OpenAI gpt-4o-mini
        configured_model = self.settings.llm_model
        if not configured_model or configured_model.startswith("gpt-"):
            self.model = DEFAULT_GEMINI_MODEL
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
        """Return configured model identifier."""
        return self.model

    def _ensure_api_key(self) -> str:
        """Ensure GEMINI_LLM_API_KEY or GEMINI_API_KEY is configured and non-empty."""
        key = self.settings.get_effective_gemini_llm_key()
        if not key or not key.strip():
            raise ProviderError(
                "GEMINI_API_KEY must be configured for Gemini provider",
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

    async def _execute_generate_content(
        self,
        contents: Any,
        config: types.GenerateContentConfig,
    ) -> Any:
        """Execute async generate_content with timeout and bounded retries for transient errors."""
        last_error: Exception | None = None
        last_status: int | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Wrap generation in timeout
                coro = self._client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                return await asyncio.wait_for(coro, timeout=self.timeout)

            except errors.APIError as exc:
                last_error = exc
                status_code = getattr(exc, "code", None)
                last_status = status_code

                # Immediate failure for permanent 4xx errors
                if status_code in PERMANENT_ERROR_CODES:
                    logger.error(
                        "Permanent error from Gemini (status=%s): %s",
                        status_code,
                        exc,
                    )
                    raise ProviderError(
                        f"Gemini service rejected request with permanent error status {status_code}",
                        provider="gemini",
                        details={"status_code": status_code},
                    ) from exc

                # Transient errors - retry if attempts remain
                if status_code in TRANSIENT_STATUS_CODES:
                    if attempt < self.max_retries:
                        backoff = self._calculate_backoff(attempt)
                        logger.warning(
                            "Transient Gemini error (status=%s, attempt=%d/%d). Retrying in %.2fs...",
                            status_code,
                            attempt + 1,
                            self.max_retries,
                            backoff,
                        )
                        await self._sleep(backoff)
                        continue

                    if status_code == 429:
                        raise RateLimitExceededError("Gemini rate limit reached after retries") from exc

                    raise ProviderError(
                        f"Gemini service returned transient error status {status_code} "
                        f"after {self.max_retries + 1} attempts",
                        provider="gemini",
                        details={"status_code": status_code},
                    ) from exc

                # Any other unexpected non-transient status code
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
                        "Timeout connecting to Gemini (attempt %d/%d). Retrying in %.2fs...",
                        attempt + 1,
                        self.max_retries,
                        backoff,
                    )
                    await self._sleep(backoff)
                    continue

                raise ProviderError(
                    f"Gemini request timed out after {self.timeout}s and {self.max_retries + 1} attempts",
                    provider="gemini",
                ) from exc

            except (RateLimitExceededError, ProviderError):
                raise

            except Exception as exc:
                last_error = exc
                logger.error("Unexpected error communicating with Gemini: %s", exc)
                raise ProviderError(
                    "Unexpected error communicating with Gemini",
                    provider="gemini",
                    details={"error_type": exc.__class__.__name__},
                ) from exc

        raise ProviderError(
            f"Failed to communicate with Gemini after {self.max_retries + 1} attempts",
            provider="gemini",
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
        """Generate unstructured natural language text from Gemini."""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
        )

        response = await self._execute_generate_content(
            contents=prompt,
            config=config,
        )

        raw_text = getattr(response, "text", None)
        if raw_text is None:
            raise ProviderError(
                "Gemini returned empty response text",
                provider="gemini",
            )

        return str(raw_text).strip()

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate structured data conforming to a Pydantic model using Gemini structured outputs."""
        schema = _convert_to_gemini_schema(response_model.model_json_schema())
        schema_json = json.dumps(response_model.model_json_schema())
        instruction = (
            (system_prompt or "")
            + f"\nYou MUST output strictly valid JSON matching this JSON schema:\n{schema_json}"
        ).strip()

        config = types.GenerateContentConfig(
            system_instruction=instruction,
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )

        response = await self._execute_generate_content(
            contents=prompt,
            config=config,
        )

        raw_text = getattr(response, "text", None)
        if not raw_text or not str(raw_text).strip():
            raise ProviderError(
                "Gemini returned empty structured response text",
                provider="gemini",
            )

        cleaned_text = _clean_json_text(str(raw_text))

        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            logger.error(
                "Gemini response content is not valid JSON for %s: %s",
                response_model.__name__,
                exc,
            )
            raise ProviderError(
                f"Gemini response could not be parsed into {response_model.__name__}: invalid JSON",
                provider="gemini",
                details={"model_name": response_model.__name__, "reason": "invalid_json"},
            ) from exc

        if not isinstance(parsed_json, dict):
            logger.error(
                "Gemini response is not a JSON object for %s (type=%s)",
                response_model.__name__,
                type(parsed_json).__name__,
            )
            raise ProviderError(
                f"Gemini response could not be parsed into {response_model.__name__}: expected JSON object",
                provider="gemini",
                details={"model_name": response_model.__name__, "reason": "not_an_object"},
            )

        try:
            return response_model.model_validate(parsed_json)
        except ValidationError as exc:
            logger.error(
                "Failed to validate Gemini response against %s: %s",
                response_model.__name__,
                exc,
            )
            raise ProviderError(
                f"Gemini response could not be parsed into {response_model.__name__}: contract validation failed",
                provider="gemini",
                details={
                    "model_name": response_model.__name__,
                    "reason": "validation_failed",
                    "validation_errors": exc.errors(include_url=False),
                },
            ) from exc

    async def extract_text_from_document(
        self,
        document_bytes: bytes,
        mime_type: str = "application/pdf",
        instruction: str | None = None,
    ) -> str:
        """Extract all readable text from raw document bytes using Gemini Multimodal Vision."""
        prompt = (
            instruction
            or (
                "Trích xuất nguyên văn toàn bộ nội dung văn bản từ tài liệu này mà không tóm tắt, "
                "không chỉnh sửa và không bỏ sót bất kỳ thông tin nào. "
                "Giữ nguyên cấu trúc tự nhiên, thông tin liên hệ, tiêu đề, ngày tháng, các gạch đầu dòng, "
                "kinh nghiệm làm việc, học vấn, kỹ năng, dự án và chứng chỉ. "
                "Chỉ trả về nội dung văn bản đã trích xuất, không thêm lời bình luận mở đầu hay kết thúc."
            )
        )

        part = types.Part.from_bytes(data=document_bytes, mime_type=mime_type)
        config = types.GenerateContentConfig(
            temperature=0.0,
        )

        response = await self._execute_generate_content(
            contents=[prompt, part],
            config=config,
        )

        raw_text = getattr(response, "text", None)
        if not raw_text or not str(raw_text).strip():
            raise ProviderError(
                "Gemini vision OCR returned empty text from document",
                provider="gemini",
            )

        return str(raw_text).strip()

