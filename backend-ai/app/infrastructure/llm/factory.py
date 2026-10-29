import hashlib
from typing import Any

from app.core.config import Settings, get_settings
from app.infrastructure.llm.providers.gemini_provider import GeminiLlmProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.infrastructure.llm.providers.openai_provider import OpenAiProvider
from app.ports.llm import LlmPort


def get_llm_settings_fingerprint(settings: Settings) -> tuple[Any, ...]:
    """
    Generate an immutable configuration fingerprint for LLM provider reuse.
    Includes model, provider, timeout, retries, and a one-way truncated hash
    of the API key to detect credential changes without logging/leaking secrets.
    """
    key_hash: str | None = None
    gemini_key = settings.get_effective_gemini_llm_key()
    if settings.openai_api_key:
        key_hash = hashlib.sha256(settings.openai_api_key.encode()).hexdigest()[:16]
    elif gemini_key:
        key_hash = hashlib.sha256(gemini_key.encode()).hexdigest()[:16]

    return (
        settings.llm_provider,
        settings.llm_model,
        float(settings.llm_timeout_seconds),
        int(settings.llm_max_retries),
        key_hash,
    )


def get_llm_provider(settings: Settings | None = None) -> LlmPort:
    """Return the configured LlmPort implementation without silent fallbacks."""
    current_settings = settings or get_settings()
    provider_name = current_settings.llm_provider

    if provider_name == "mock":
        return MockLlmProvider()

    if provider_name == "openai":
        return OpenAiProvider(current_settings)

    if provider_name == "gemini":
        return GeminiLlmProvider(current_settings)

    raise ValueError(f"Unsupported LLM provider '{provider_name}'")
