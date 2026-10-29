"""Port interface for document parsing and text extraction."""

from abc import ABC, abstractmethod


class DocumentParserPort(ABC):
    """Abstract interface for parsing and extracting raw text from documents."""

    @abstractmethod
    async def parse_pdf(self, file_bytes: bytes) -> str:
        """
        Extract text from raw PDF file bytes.

        Raises:
            DocumentParsingError: If file is invalid or corrupted.
            DocumentSizeLimitExceededError: If file exceeds maximum size limit.
            DocumentPageLimitExceededError: If page count exceeds maximum allowable pages.
        """
        raise NotImplementedError
