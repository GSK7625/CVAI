"""Unit tests for CV analysis stability, prompt grounding, temperature settings, and resilience."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.cv_analyzer import (
    CvAnalyzerService,
    CvQualitativeFeedback,
    _build_education_context,
    _build_experience_context,
    _build_project_context,
)
from app.contracts.cv import (
    EducationItem,
    ProjectItem,
    StructuredCv,
    WorkExperienceItem,
)
from app.core.config import Settings
from app.ports.document_parser import DocumentParserPort
from app.ports.llm import LlmPort


class FakeDocumentParser(DocumentParserPort):
    async def parse_pdf(self, file_bytes: bytes) -> str:
        return "Parsed CV text"


@pytest.fixture
def fake_settings() -> Settings:
    return Settings(
        llm_provider="mock",
        embedding_provider="mock",
        internal_api_key="test-key",
        max_extracted_text_chars=10000,
    )


@pytest.fixture
def sample_structured_cv() -> StructuredCv:
    return StructuredCv(
        full_name="Nguyễn Văn A",
        email="nguyenvana@example.com",
        phone="0912345678",
        career_summary="Senior Backend Engineer with 5 years experience.",
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        work_experience=[
            WorkExperienceItem(
                company="TechCorp VN",
                job_title="Backend Lead",
                start_date="2021-01",
                end_date="2023-12",
                duration="2021 - 2023",
                years_of_experience=3.0,
                description="Designed microservices and improved system throughput by 40%.",
            )
        ],
        education=[
            EducationItem(
                institution="Đại học Bách Khoa",
                degree="Kỹ sư",
                field_of_study="Công nghệ Thông tin",
                graduation_year="2020",
            )
        ],
        certificates=["AWS Certified Solutions Architect"],
        projects=[
            ProjectItem(
                name="FutureCV Platform",
                description="AI-powered CV review and job matching engine.",
                technologies=["FastAPI", "React", "PostgreSQL"],
            )
        ],
        technologies=["Git", "Redis", "Linux"],
    )


@pytest.mark.asyncio
async def test_analyzer_temperatures_and_prompt_grounding(
    fake_settings: Settings,
    sample_structured_cv: StructuredCv,
) -> None:
    """Verify extraction uses temperature=0.0 and feedback uses temperature=0.1 with grounded context."""
    llm = MagicMock(spec=LlmPort)
    llm.provider_name = "mock"
    llm.model_name = "mock-model"

    feedback_response = CvQualitativeFeedback(
        strengths=["Kinh nghiệm backend thực tế tốt"],
        weaknesses=["Chưa nêu rõ chỉ số cho toàn bộ dự án"],
        improvement_suggestions=["Bổ sung chứng chỉ bảo mật"],
    )

    # 1st call returns StructuredCv, 2nd call returns CvQualitativeFeedback
    llm.generate_structured = AsyncMock(side_effect=[sample_structured_cv, feedback_response])

    service = CvAnalyzerService(parser=FakeDocumentParser(), llm=llm, settings=fake_settings)
    result = await service.analyze_text("Some raw cv text")

    assert llm.generate_structured.call_count == 2
    extract_call, feedback_call = llm.generate_structured.call_args_list

    # Step 1: Extraction temperature check
    assert extract_call.kwargs.get("temperature") == 0.0
    assert extract_call.kwargs.get("response_model") == StructuredCv

    # Step 4: Feedback temperature check
    assert feedback_call.kwargs.get("temperature") == 0.1
    assert feedback_call.kwargs.get("response_model") == CvQualitativeFeedback

    # Prompt grounding check: ensure company, job_title, university, project are in prompt
    analysis_prompt = feedback_call.kwargs.get("prompt", "")
    assert "TechCorp VN" in analysis_prompt
    assert "Backend Lead" in analysis_prompt
    assert "Đại học Bách Khoa" in analysis_prompt
    assert "FutureCV Platform" in analysis_prompt

    # PII privacy check: candidate name, email, phone MUST NOT leak into Stage 2 prompt
    assert "Nguyễn Văn A" not in analysis_prompt
    assert "nguyenvana@example.com" not in analysis_prompt
    assert "0912345678" not in analysis_prompt

    # Score integrity
    assert result.cv_score > 0
    assert "Kinh nghiệm backend thực tế tốt" in result.strengths


@pytest.mark.asyncio
async def test_analyzer_resilience_when_qualitative_feedback_fails(
    fake_settings: Settings,
    sample_structured_cv: StructuredCv,
) -> None:
    """Verify that if qualitative feedback LLM call fails, service gracefully degrades to deterministic score."""
    llm = MagicMock(spec=LlmPort)
    llm.provider_name = "mock"
    llm.model_name = "mock-model"

    # Extraction succeeds, qualitative feedback raises an error
    llm.generate_structured = AsyncMock(
        side_effect=[sample_structured_cv, RuntimeError("Gemini 503 Service Unavailable")]
    )

    service = CvAnalyzerService(parser=FakeDocumentParser(), llm=llm, settings=fake_settings)
    result = await service.analyze_text("Raw text")

    # Service should NOT raise exception, must return deterministic evaluation
    assert result.structured_cv.full_name == "Nguyễn Văn A"
    assert result.cv_score > 0
    assert len(result.strengths) >= 1  # Deterministic strengths from evaluate_cv_quality
    assert isinstance(result.improvement_suggestions, list)


def test_context_builder_character_limits() -> None:
    """Verify context builders enforce strict character limits."""
    # Experience context limit
    long_exp = [
        WorkExperienceItem(
            company=f"Company {i}",
            job_title=f"Role {i}",
            start_date="2020",
            end_date="2021",
            duration="1 year",
            years_of_experience=1.0,
            description="A" * 200,
        )
        for i in range(30)
    ]
    exp_ctx = _build_experience_context(long_exp, max_chars=2000)
    assert len(exp_ctx) <= 2000

    # Education context limit
    long_edu = [
        EducationItem(
            institution=f"University of Long Names {i}",
            degree=f"Degree {i}",
            field_of_study="Computer Science and Engineering",
            graduation_year="2020",
        )
        for i in range(30)
    ]
    edu_ctx = _build_education_context(long_edu, max_chars=1000)
    assert len(edu_ctx) <= 1000

    # Project context limit
    long_proj = [
        ProjectItem(
            name=f"Project {i}",
            description="B" * 200,
            technologies=["Python", "FastAPI", "PostgreSQL", "Docker"],
        )
        for i in range(30)
    ]
    proj_ctx = _build_project_context(long_proj, max_chars=2000)
    assert len(proj_ctx) <= 2000


def test_context_builder_empty_fallbacks() -> None:
    """Verify context builders handle empty lists gracefully."""
    assert _build_experience_context([]) == "Chưa có"
    assert _build_education_context([]) == "Chưa có"
    assert _build_project_context([]) == "Chưa có"
