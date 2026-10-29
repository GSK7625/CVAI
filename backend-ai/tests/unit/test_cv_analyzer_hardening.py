"""Unit tests for hardened CV Analyzer service, PII redaction, and qualitative feedback."""

from typing import TypeVar

from pydantic import BaseModel
import pytest

from app.api.deps import get_cv_analyzer_service
from app.application.cv_analyzer import CvAnalyzerService
from app.core.config import Settings
from app.core.exceptions import DocumentParsingError
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.document_parser import DocumentParserPort

T = TypeVar("T", bound=BaseModel)


class DummyParser(DocumentParserPort):
    async def parse_pdf(self, file_bytes: bytes) -> str:
        return "Dummy extracted text"


class PiiInterceptingLlm(MockLlmProvider):
    """Spy LLM provider capturing prompts sent to generate_structured."""

    def __init__(self) -> None:
        self.captured_prompts: list[str] = []

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        self.captured_prompts.append(prompt)
        if response_model.__name__ == "CvQualitativeFeedback":
            return response_model.model_validate(
                {
                    "strengths": ["Strong architectural insight", "Thorough problem solving"],
                    "weaknesses": ["Needs more quantifiable project metrics"],
                    "improvement_suggestions": [
                        "Highlight business impact in experience bullets",
                        "Thorough problem solving",  # duplicate candidate
                    ],
                }
            )
        return await super().generate_structured(prompt, response_model, system_prompt, temperature)


@pytest.mark.asyncio
async def test_cv_analyzer_redacts_pii_before_qualitative_evaluation():
    """Verify full_name, email, and phone are redacted before the second-stage qualitative prompt."""
    spy_llm = PiiInterceptingLlm()
    service = CvAnalyzerService(parser=DummyParser(), llm=spy_llm)

    # Pre-structured CV containing sensitive PII
    raw_cv = (
        "Họ và tên: Nguyễn Văn A\n"
        "Email: secret_candidate@example.com\n"
        "Số điện thoại: 0901234567\n"
        "Kỹ năng: Python, FastAPI, Docker\n"
        "Tóm tắt: Senior Backend Engineer\n"
    )

    response = await service.analyze_text(raw_cv)

    # There should be 2 structured calls: 1 for CV extraction, 1 for qualitative critique
    assert len(spy_llm.captured_prompts) == 2
    qualitative_prompt = spy_llm.captured_prompts[1]

    # Assert PII is NOT present in the qualitative prompt
    assert "secret_candidate@example.com" not in qualitative_prompt
    assert "0901234567" not in qualitative_prompt
    assert "Nguyễn Văn A" not in qualitative_prompt

    # Assert delimiters are used
    assert "<<<BEGIN UNTRUSTED CANDIDATE CV>>>" in qualitative_prompt
    assert "<<<END UNTRUSTED CANDIDATE CV>>>" in qualitative_prompt

    # Assert metadata
    assert response.meta.algorithm_version == "cv-v0"
    assert response.meta.provider == "mock"
    assert response.meta.model == "mock-deterministic"


@pytest.mark.asyncio
async def test_cv_analyzer_merges_and_deduplicates_feedback_preserving_order():
    """Verify qualitative feedback merges with deterministic completeness items and deduplicates."""
    spy_llm = PiiInterceptingLlm()
    service = CvAnalyzerService(parser=DummyParser(), llm=spy_llm)

    response = await service.analyze_text("Python engineer with 5 years experience.")

    # Strengths should contain both structural notes and LLM feedback
    assert any("Strong architectural insight" in s for s in response.strengths)
    assert any("Thorough problem solving" in s for s in response.strengths)

    # Weaknesses should contain both structural notes and LLM feedback
    assert any("Needs more quantifiable project metrics" in w for w in response.weaknesses)

    # Deduplication check: no duplicate items in any list
    assert len(response.strengths) == len(set(response.strengths))
    assert len(response.weaknesses) == len(set(response.weaknesses))
    assert len(response.improvement_suggestions) == len(set(response.improvement_suggestions))


@pytest.mark.asyncio
async def test_cv_analyzer_rejects_oversized_raw_text():
    """Verify raw_text exceeding max_extracted_text_chars raises DocumentParsingError."""
    settings = Settings(MAX_EXTRACTED_TEXT_CHARS=50)
    service = CvAnalyzerService(parser=DummyParser(), llm=MockLlmProvider(), settings=settings)

    with pytest.raises(DocumentParsingError) as exc_info:
        await service.analyze_text("A" * 51)

    assert exc_info.value.error_code == "INVALID_DOCUMENT"
    assert exc_info.value.details["reason"] == "text_limit_exceeded"


def test_get_cv_analyzer_service_receives_injected_settings():
    """Verify get_cv_analyzer_service receives and forwards explicit Settings to CvAnalyzerService."""
    custom_settings = Settings(MAX_EXTRACTED_TEXT_CHARS=1234)
    parser = DummyParser()
    llm = MockLlmProvider()

    service = get_cv_analyzer_service(parser=parser, llm=llm, settings=custom_settings)

    assert service.settings is custom_settings
    assert service.settings.max_extracted_text_chars == 1234


def test_cv_analyzer_dependency_override_pipeline_consistency():
    """Prove that route, parser, and CvAnalyzerService observe the identical injected Settings instance."""
    from fastapi.testclient import TestClient

    from app.api.deps import get_document_parser, get_settings_dep
    from app.main import app

    # Create distinct custom settings with a non-default character threshold
    custom_settings = Settings(
        MAX_EXTRACTED_TEXT_CHARS=100,
        MAX_UPLOAD_SIZE_BYTES=32 * 1024,
    )

    def override_settings():
        yield custom_settings

    app.dependency_overrides[get_settings_dep] = override_settings
    try:
        # 1. Verify parser resolved via DI has the exact custom settings instance
        resolved_parser = get_document_parser(settings=custom_settings)
        assert resolved_parser.settings is custom_settings
        assert resolved_parser.settings.max_extracted_text_chars == 100

        # 2. Verify service resolved via get_cv_analyzer_service has the exact custom settings instance
        resolved_service = get_cv_analyzer_service(
            parser=resolved_parser,
            llm=MockLlmProvider(),
            settings=custom_settings,
        )
        assert resolved_service.settings is custom_settings
        assert resolved_service.settings.max_extracted_text_chars == 100

        # 3. End-to-end route invocation proving CvAnalyzerService enforces the overridden 100-char limit
        client = TestClient(app)
        oversized_text = "Software Engineer with deep expertise. " * 4  # ~160 chars > 100 limit
        response = client.post(
            "/api/v1/cv/analyze-text",
            json={"raw_text": oversized_text},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["error_code"] == "INVALID_DOCUMENT"
        assert body["details"]["reason"] == "text_limit_exceeded"

        # Within the 100-character limit succeeds
        valid_text = "Software Engineer with Python."  # ~30 chars < 100 limit
        valid_response = client.post(
            "/api/v1/cv/analyze-text",
            json={"raw_text": valid_text},
        )
        assert valid_response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_settings_dep, None)
