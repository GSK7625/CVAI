"""Factory for creating Embedding provider instances based on application settings."""

from app.core.config import Settings, get_settings
from app.infrastructure.embeddings.providers.gemini_provider import GeminiEmbeddingProvider
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.embeddings.providers.openai_provider import OpenAiEmbeddingProvider
from app.ports.embeddings import EmbeddingPort


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingPort:
    """Return the configured EmbeddingPort implementation without silent fallbacks."""
    current_settings = settings or get_settings()
    provider_name = current_settings.embedding_provider

    if provider_name == "mock":
        return MockEmbeddingProvider()

    if provider_name == "openai":
        return OpenAiEmbeddingProvider(current_settings)

    if provider_name == "gemini":
        return GeminiEmbeddingProvider(current_settings)

    raise ValueError(f"Unsupported embedding provider '{provider_name}'")
