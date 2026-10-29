"""PyMuPDF-based secure document parser implementing DocumentParserPort."""

import anyio
import fitz  # PyMuPDF

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    DocumentPageLimitExceededError,
    DocumentParsingError,
    DocumentSizeLimitExceededError,
)
from app.observability.logging import get_logger
from app.ports.document_parser import DocumentParserPort

logger = get_logger(__name__)


class PyMuPdfDocumentParser(DocumentParserPort):
    """Secure PDF text extraction using PyMuPDF executed in background threadpool."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _sync_parse(self, file_bytes: bytes) -> str:
        """Synchronous CPU-bound PDF extraction with security validation."""
        # 1. Size constraint
        byte_len = len(file_bytes)
        if byte_len > self.settings.max_upload_size_bytes:
            raise DocumentSizeLimitExceededError(
                max_size_bytes=self.settings.max_upload_size_bytes,
                actual_size_bytes=byte_len,
            )

        # 2. PDF signature check within initial prefix (prevent non-PDF masquerading)
        header_prefix = file_bytes[:1024]
        if b"%PDF-" not in header_prefix:
            raise DocumentParsingError(
                "Invalid PDF format: file does not contain a valid %PDF- header in the initial 1024 bytes",
                details={"reason": "invalid_magic_bytes"},
            )

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            raise DocumentParsingError(
                f"Failed to open PDF document: {e!s}",
                details={"reason": "corrupt_pdf"},
            ) from e

        try:
            # 3. Page limit check (prevent denial of service)
            if doc.page_count > self.settings.max_pdf_pages:
                raise DocumentPageLimitExceededError(
                    max_pages=self.settings.max_pdf_pages,
                    actual_pages=doc.page_count,
                )

            # 4. Extract text page by page with incremental character limit validation
            extracted_pages: list[str] = []
            accumulated_chars = 0

            for page_idx in range(doc.page_count):
                page = doc.load_page(page_idx)
                page_text = page.get_text("text") or ""
                separator_len = 2 if extracted_pages else 0
                accumulated_chars += len(page_text) + separator_len

                if accumulated_chars > self.settings.max_extracted_text_chars:
                    raise DocumentParsingError(
                        f"Extracted CV text exceeds the maximum allowable limit of "
                        f"{self.settings.max_extracted_text_chars} characters",
                        details={
                            "reason": "text_limit_exceeded",
                            "max_chars": self.settings.max_extracted_text_chars,
                            "processed_pages": page_idx + 1,
                        },
                    )

                extracted_pages.append(page_text)

            full_text = "\n\n".join(extracted_pages).strip()

            if not full_text:
                raise DocumentParsingError(
                    "PDF document contains no extractable text (it may be a scanned image)",
                    details={"reason": "empty_or_scanned_pdf"},
                )

            logger.info("Successfully extracted text from PDF (%d pages, %d chars)", doc.page_count, len(full_text))
            return full_text
        finally:
            doc.close()

    async def parse_pdf(self, file_bytes: bytes) -> str:
        """Asynchronously parse PDF by offloading to anyio thread pool."""
        return await anyio.to_thread.run_sync(self._sync_parse, file_bytes)
