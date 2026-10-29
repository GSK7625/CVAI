"""Unit tests for hardened PDF parsing and bounded upload constraints."""

import fitz
import pytest

from app.core.config import Settings
from app.core.exceptions import (
    DocumentPageLimitExceededError,
    DocumentParsingError,
    DocumentSizeLimitExceededError,
)
from app.infrastructure.documents.pdf_parser import PyMuPdfDocumentParser


def _create_dummy_pdf(num_pages: int = 1, text_per_page: str = "Test candidate CV content") -> bytes:
    """Create a minimal valid in-memory PDF document using PyMuPDF."""
    doc = fitz.open()
    for _ in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), text_per_page)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_valid_pdf_within_limits_parsed_successfully():
    """Verify standard valid PDF document parses cleanly."""
    settings = Settings(MAX_UPLOAD_SIZE_BYTES=5242880, MAX_PDF_PAGES=20, MAX_EXTRACTED_TEXT_CHARS=50000)
    parser = PyMuPdfDocumentParser(settings=settings)

    pdf_bytes = _create_dummy_pdf(num_pages=2, text_per_page="Senior Software Engineer experience")
    extracted = parser._sync_parse(pdf_bytes)

    assert "Senior Software Engineer experience" in extracted
    assert len(extracted) > 0


def test_oversized_payload_raises_document_size_limit_error():
    """Verify document size exceeding max_upload_size_bytes is rejected."""
    settings = Settings(MAX_UPLOAD_SIZE_BYTES=100)
    parser = PyMuPdfDocumentParser(settings=settings)

    large_bytes = b"%PDF-1.4 " + b"X" * 200
    with pytest.raises(DocumentSizeLimitExceededError) as exc_info:
        parser._sync_parse(large_bytes)

    assert exc_info.value.status_code == 413
    assert exc_info.value.error_code == "FILE_TOO_LARGE"


def test_invalid_header_prefix_rejected():
    """Verify files without %PDF- in the initial 1024 bytes are rejected."""
    settings = Settings()
    parser = PyMuPdfDocumentParser(settings=settings)

    non_pdf = b"NOT_A_PDF_FILE" * 50
    with pytest.raises(DocumentParsingError) as exc_info:
        parser._sync_parse(non_pdf)

    assert exc_info.value.error_code == "INVALID_DOCUMENT"
    assert exc_info.value.details["reason"] == "invalid_magic_bytes"


def test_excessive_pages_raises_page_limit_error():
    """Verify document with pages exceeding max_pdf_pages raises DocumentPageLimitExceededError."""
    settings = Settings(MAX_PDF_PAGES=3)
    parser = PyMuPdfDocumentParser(settings=settings)

    four_page_pdf = _create_dummy_pdf(num_pages=4, text_per_page="Page text content")
    with pytest.raises(DocumentPageLimitExceededError) as exc_info:
        parser._sync_parse(four_page_pdf)

    assert exc_info.value.status_code == 422
    assert exc_info.value.error_code == "PAGE_LIMIT_EXCEEDED"


def test_excessive_extracted_text_raises_controlled_error_without_silent_truncation():
    """Verify text exceeding max_extracted_text_chars raises controlled error rather than truncating."""
    settings = Settings(MAX_EXTRACTED_TEXT_CHARS=100)
    parser = PyMuPdfDocumentParser(settings=settings)

    # Create a 2-page PDF with 80 chars on each page -> 160 total chars > 100 char limit
    page_text = "A" * 80
    oversized_text_pdf = _create_dummy_pdf(num_pages=2, text_per_page=page_text)

    with pytest.raises(DocumentParsingError) as exc_info:
        parser._sync_parse(oversized_text_pdf)

    assert exc_info.value.error_code == "INVALID_DOCUMENT"
    assert exc_info.value.details["reason"] == "text_limit_exceeded"
    assert exc_info.value.details["max_chars"] == 100
