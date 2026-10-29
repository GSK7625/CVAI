"""Unit tests for Multimodal Vision OCR fallback in CV Analyzer."""

import pytest

from app.application.cv_analyzer import CvAnalyzerService
from app.core.config import Settings
from app.core.exceptions import DocumentParsingError, ProviderError
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.infrastructure.llm.providers.openai_provider import OpenAiProvider
from app.ports.document_parser import DocumentParserPort


class SufficientTextParser(DocumentParserPort):
    async def parse_pdf(self, file_bytes: bytes) -> str:
        return (
            "Nguyễn Văn A\n"
            "Email: nguyenvana@example.com\n"
            "Kỹ sư phát triển phần mềm với hơn 4 năm kinh nghiệm làm việc với Python và C#.\n"
            "Kỹ năng: Python, C#, FastAPI, Docker, PostgreSQL."
        )


class ScannedPdfParser(DocumentParserPort):
    async def parse_pdf(self, file_bytes: bytes) -> str:
        raise DocumentParsingError(
            "PDF document contains no extractable text (it may be a scanned image)",
            details={"reason": "empty_or_scanned_pdf"},
        )


class ShortTextParser(DocumentParserPort):
    async def parse_pdf(self, file_bytes: bytes) -> str:
        return "Canva Watermark"  # < 50 chars threshold


class TrackingMockLlm(MockLlmProvider):
    def __init__(self, ocr_return_text: str | None = None, fail_ocr: bool = False) -> None:
        self.ocr_called = False
        self.ocr_return_text = ocr_return_text
        self.fail_ocr = fail_ocr

    async def extract_text_from_document(
        self,
        document_bytes: bytes,
        mime_type: str = "application/pdf",
        instruction: str | None = None,
    ) -> str:
        self.ocr_called = True
        if self.fail_ocr:
            raise ProviderError("Gemini OCR simulated failure", provider="gemini")
        if self.ocr_return_text is not None:
            return self.ocr_return_text
        return await super().extract_text_from_document(document_bytes, mime_type, instruction)


@pytest.mark.asyncio
async def test_cv_analyzer_skips_ocr_when_text_layer_is_sufficient():
    """Verify that normal vector PDFs with sufficient text do not trigger OCR."""
    llm = TrackingMockLlm()
    service = CvAnalyzerService(parser=SufficientTextParser(), llm=llm)

    response = await service.analyze_pdf(b"%PDF-valid-digital-content")

    assert response is not None
    assert response.structured_cv is not None
    assert llm.ocr_called is False  # OCR was NOT called for normal PDF


@pytest.mark.asyncio
async def test_cv_analyzer_triggers_ocr_when_pdf_is_scanned_image():
    """Verify that scanned image PDF triggers multimodal OCR fallback and succeeds."""
    llm = TrackingMockLlm()
    service = CvAnalyzerService(parser=ScannedPdfParser(), llm=llm)

    response = await service.analyze_pdf(b"%PDF-scanned-image-content")

    assert response is not None
    assert response.structured_cv is not None
    assert llm.ocr_called is True  # OCR was successfully invoked as fallback


@pytest.mark.asyncio
async def test_cv_analyzer_triggers_ocr_when_extracted_text_below_threshold():
    """Verify that suspicious short text (< 50 chars) triggers OCR and uses longer text."""
    llm = TrackingMockLlm()
    settings = Settings(ENABLE_OCR_FALLBACK=True, OCR_MIN_CHAR_THRESHOLD=50)
    service = CvAnalyzerService(parser=ShortTextParser(), llm=llm, settings=settings)

    response = await service.analyze_pdf(b"%PDF-short-text-content")

    assert response is not None
    assert llm.ocr_called is True
    # The extracted CV has been populated from OCR fallback text
    assert len(response.structured_cv.skills) > 0


@pytest.mark.asyncio
async def test_cv_analyzer_raises_when_ocr_disabled():
    """Verify that when OCR fallback is disabled, scanned PDF raises DocumentParsingError."""
    llm = TrackingMockLlm()
    settings = Settings(ENABLE_OCR_FALLBACK=False)
    service = CvAnalyzerService(parser=ScannedPdfParser(), llm=llm, settings=settings)

    with pytest.raises(DocumentParsingError) as exc_info:
        await service.analyze_pdf(b"%PDF-scanned-content")

    assert exc_info.value.details.get("reason") == "empty_or_scanned_pdf"
    assert llm.ocr_called is False


@pytest.mark.asyncio
async def test_cv_analyzer_raises_when_ocr_fails():
    """Verify that when OCR fails on scanned PDF, an informative DocumentParsingError is raised."""
    llm = TrackingMockLlm(fail_ocr=True)
    service = CvAnalyzerService(parser=ScannedPdfParser(), llm=llm)

    with pytest.raises(DocumentParsingError) as exc_info:
        await service.analyze_pdf(b"%PDF-corrupted-scanned-content")

    assert exc_info.value.details.get("reason") == "empty_or_scanned_pdf"
    assert "ocr_error" in exc_info.value.details
    assert llm.ocr_called is True


@pytest.mark.asyncio
async def test_openai_provider_raises_for_document_ocr():
    """Verify OpenAiProvider explicitly informs that direct document vision OCR is not supported."""
    provider = OpenAiProvider(settings=Settings(OPENAI_API_KEY="test-key"))
    with pytest.raises(ProviderError) as exc_info:
        await provider.extract_text_from_document(b"%PDF-bytes")

    assert "Direct document vision OCR is currently supported via Gemini provider" in str(exc_info.value)
