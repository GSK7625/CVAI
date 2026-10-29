"""Port interface for text embedding generation."""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingPort(ABC):
    """Abstract interface for text embedding generation and provider lifecycle management."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider (e.g. 'mock', 'openai')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific embedding model used (e.g. 'mock-hash-64', 'text-embedding-3-small')."""
        raise NotImplementedError

    @abstractmethod
    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate embedding vectors for a sequence of texts.

        Preserves exact input sequence ordering: the i-th vector corresponds to texts[i].
        """
        raise NotImplementedError

    async def aclose(self) -> None:
        """Asynchronously close network sessions or underlying clients."""
        return
