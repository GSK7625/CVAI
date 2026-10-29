"""Port interface for Large Language Model generation and structured extraction."""

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LlmPort(ABC):
    """Abstract interface for LLM operations and provider lifecycle management."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider (e.g. 'mock', 'openai')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the specific LLM model used (e.g. 'mock-deterministic', 'gpt-4o-mini')."""
        raise NotImplementedError

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate unstructured natural language text from a prompt."""
        raise NotImplementedError

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate validated, structured output conforming to a Pydantic model."""
        raise NotImplementedError

    async def extract_text_from_document(
        self,
        document_bytes: bytes,
        mime_type: str = "application/pdf",
        instruction: str | None = None,
    ) -> str:
        """
        Extract readable text from a document using multimodal vision capabilities.

        Raises:
            ProviderError: If the provider does not support document extraction or extraction fails.
            NotImplementedError: If not implemented by the underlying provider.
        """
        raise NotImplementedError("Multimodal document extraction is not supported by this provider")

    async def aclose(self) -> None:
        """Asynchronously close network sessions or underlying clients."""
        return
