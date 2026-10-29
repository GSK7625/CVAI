"""
Prompt-capture privacy tests at the provider boundary.

Verifies that raw contact PII (emails and phone numbers) NEVER reaches fake/mock
providers in:
1. Career Assistant
2. Match Explanation
3. Qualitative CV Analysis
4. Semantic Embedding representations
"""

from typing import Any, TypeVar

from pydantic import BaseModel
import pytest

from app.application.career_assistant import CareerAssistantService
from app.application.cv_analyzer import CvAnalyzerService, CvQualitativeFeedback
from app.application.matching_service import MatchingService
from app.application.ranking_service import RankingService
from app.application.text_sanitization import EMAIL_REDACTED_TOKEN, PHONE_REDACTED_TOKEN
from app.contracts.career import CareerAssistantContext, CareerAssistantRequest, ChatMessage
from app.contracts.cv import EducationItem, ProjectItem, StructuredCv, WorkExperienceItem
from app.contracts.job import StructuredJob
from app.contracts.matching import CandidateItem, CandidateRankRequest, MatchResult
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.ports.document_parser import DocumentParserPort

T = TypeVar("T", bound=BaseModel)


class CapturingLlmProvider(MockLlmProvider):
    """Spy LLM provider capturing raw prompt strings dispatched to generate_text and generate_structured."""

    def __init__(self) -> None:
        self.captured_text_calls: list[dict[str, Any]] = []
        self.captured_structured_calls: list[dict[str, Any]] = []

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.captured_text_calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "temperature": temperature,
            }
        )
        return await super().generate_text(prompt, system_prompt, temperature)

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        self.captured_structured_calls.append(
            {
                "prompt": prompt,
                "response_model": response_model,
                "system_prompt": system_prompt,
                "temperature": temperature,
            }
        )
        if response_model == StructuredCv:
            return StructuredCv(  # type: ignore[return-value]
                full_name="Nguyễn Văn B",
                email="candidate.cv@domain.com",
                phone="0988 123 456",
                career_summary="Kỹ sư phần mềm 4 năm kinh nghiệm. Liên hệ: alt.mail@domain.vn hoặc (+84) 912 345 678.",
                skills=["Python", "FastAPI", "Docker", "Liên hệ: extra@domain.com"],
                certificates=["AWS Certified Developer", "Hotline: 024.3825.7888"],
                work_experience=[
                    WorkExperienceItem(
                        job_title="Software Engineer",
                        company="ABC Corp",
                        years_of_experience=4.0,
                    )
                ],
                education=[EducationItem(degree="Bachelor", institution="HUST")],
            )
        return await super().generate_structured(prompt, response_model, system_prompt, temperature)


class CapturingEmbeddingProvider(MockEmbeddingProvider):
    """Spy Embedding provider capturing all text strings submitted for embedding."""

    def __init__(self, dimension: int = 64) -> None:
        super().__init__(dimension=dimension)
        self.captured_texts: list[str] = []

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.captured_texts.extend(texts)
        return await super().embed_texts(texts)


class DummyDocumentParser(DocumentParserPort):
    """Dummy parser returning static text."""

    async def parse_pdf(self, file_bytes: bytes) -> str:
        return "Dummy PDF Text"


# ---------------------------------------------------------------------------
# Test 1: Career Assistant Prompt Capture
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_career_assistant_captures_zero_raw_contact_pii() -> None:
    """Verify Career Assistant sanitizes user message, history, and free-text context before LLM call."""
    spy_llm = CapturingLlmProvider()
    service = CareerAssistantService(llm=spy_llm)

    raw_user_email = "candidate.career@futurecv.vn"
    raw_user_phone = "+84 988 123 456"
    raw_history_email = "old.account@recruitment.com"
    raw_history_phone = "0988123456"
    raw_job_email = "hr.contact@enterprise.com"
    raw_job_phone = "0912 345 678"

    req = CareerAssistantRequest(
        message=f"My email is {raw_user_email} and my phone is {raw_user_phone}. Should I apply?",
        history=[
            ChatMessage(
                role="user",
                content=f"Previous email was {raw_history_email} and phone {raw_history_phone}.",
            ),
            ChatMessage(
                role="assistant",
                content="Understood. Let's look at your target job.",
            ),
        ],
        context=CareerAssistantContext(
            candidate_id="cand-hidden-id-999",
            cv=StructuredCv(
                full_name="Nguyen Van A",
                email="hidden.cv.email@example.com",
                phone="0999888777",
                career_summary="Looking for backend roles. Email me at personal@work.io or call 0907777888.",
                skills=["Python", "FastAPI", "Call: 0906666777"],
                work_experience=[
                    WorkExperienceItem(
                        company="FinTech Ltd",
                        job_title="Engineer",
                        years_of_experience=3.0,
                    )
                ],
            ),
            job=StructuredJob(
                title=f"Backend Lead - Reach {raw_job_email}",
                description=f"Send resume to {raw_job_email} or contact {raw_job_phone}.",
                required_skills=["Python", "Docker"],
                preferred_skills=["Kubernetes"],
            ),
            match_result=MatchResult(
                match_score=85,
                matched_skills=["Python"],
                missing_skills=["Docker"],
                experience_comparison="Has 3.0 years vs 3.0 required. Note: call 0912-345-678.",
                education_comparison="Bachelor degree matches.",
                project_domain_relevance="Relevant e-commerce projects.",
                match_explanation="Overall good match.",
            ),
        ),
    )

    response = await service.chat(req)
    assert response.reply != ""
    assert len(spy_llm.captured_text_calls) == 1

    captured_prompt = spy_llm.captured_text_calls[0]["prompt"]

    # Assert NO raw contact PII reaches provider
    for leaked_item in [
        raw_user_email,
        raw_user_phone,
        raw_history_email,
        raw_history_phone,
        raw_job_email,
        raw_job_phone,
        "hidden.cv.email@example.com",
        "personal@work.io",
        "0999888777",
        "0907777888",
        "0906666777",
        "0912-345-678",
        # Candidate identity fields must never be in prompt
        "Nguyen Van A",
        "cand-hidden-id-999",
    ]:
        assert leaked_item not in captured_prompt

    # Assert redacted tokens are present in prompt
    assert EMAIL_REDACTED_TOKEN in captured_prompt
    assert PHONE_REDACTED_TOKEN in captured_prompt


# ---------------------------------------------------------------------------
# Test 2: Match Explanation Prompt Capture
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_match_explanation_captures_zero_contact_pii() -> None:
    """Verify Match Explanation LLM prompt does not contain candidate contact PII or raw contacts."""
    spy_llm = CapturingLlmProvider()
    service = MatchingService(llm=spy_llm)

    raw_cand_email = "candidate.match@testdomain.com"
    raw_cand_phone = "+84 988 123 456"
    raw_job_email = "jobs.matching@corporation.vn"
    raw_job_phone = "0912 345 678"

    cv = StructuredCv(
        full_name="Do Not Leak Me",
        email=raw_cand_email,
        phone=raw_cand_phone,
        skills=["Python", "FastAPI"],
        work_experience=[
            WorkExperienceItem(
                job_title="Software Engineer",
                company="Tech Co",
                years_of_experience=3.0,
                description=f"Direct questions to {raw_cand_email} or {raw_cand_phone}.",
            )
        ],
        education=[EducationItem(degree="Bachelor", institution="HUST")],
    )

    job = StructuredJob(
        job_id="job-match-001",
        title=f"Python Engineer (Questions: {raw_job_email} / {raw_job_phone})",
        required_skills=["Python", "FastAPI"],
        min_experience_years=2.0,
        required_education_level="bachelor",
    )

    result = await service.match(
        cv=cv,
        job=job,
        generate_explanation=True,
    )
    assert result.match_score > 0
    assert result.meta.llm_invoked is True
    captured_calls = spy_llm.captured_text_calls + spy_llm.captured_structured_calls
    assert len(captured_calls) == 1

    captured_prompt = captured_calls[0]["prompt"]

    # Assert NO contact PII or identity fields reached LLM
    for leaked_item in [
        raw_cand_email,
        raw_cand_phone,
        raw_job_email,
        raw_job_phone,
        "cand-match-001",
        "Do Not Leak Me",
    ]:
        assert leaked_item not in captured_prompt

    # Redacted tokens present for contaminated job title
    assert EMAIL_REDACTED_TOKEN in captured_prompt
    assert PHONE_REDACTED_TOKEN in captured_prompt


# ---------------------------------------------------------------------------
# Test 3: CV Qualitative Analysis Prompt Capture
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cv_qualitative_analysis_captures_zero_contact_pii() -> None:
    """Verify qualitative feedback generation (Stage 2) contains ZERO contact PII."""
    spy_llm = CapturingLlmProvider()
    service = CvAnalyzerService(parser=DummyDocumentParser(), llm=spy_llm)

    raw_cv_text = """
    Nguyễn Văn B
    Email: candidate.cv@domain.com | Phone: 0988 123 456
    Tóm tắt: Kỹ sư phần mềm 4 năm kinh nghiệm. Liên hệ phỏng vấn: alt.mail@domain.vn hoặc (+84) 912 345 678.
    Kỹ năng: Python, FastAPI, Docker, Liên hệ: extra@domain.com
    Chứng chỉ: AWS Certified Developer, Hotline trung tâm: 024.3825.7888
    Kinh nghiệm: 2020-2024 tại Công ty ABC.
    """

    response = await service.analyze_text(raw_cv_text)
    assert response.cv_score > 0
    # Stage 1: Structured extraction (expected exception)
    # Stage 2: Qualitative feedback
    assert len(spy_llm.captured_structured_calls) == 2

    extraction_call = spy_llm.captured_structured_calls[0]
    qualitative_call = spy_llm.captured_structured_calls[1]

    assert extraction_call["response_model"] == StructuredCv
    assert qualitative_call["response_model"] == CvQualitativeFeedback

    qualitative_prompt = qualitative_call["prompt"]

    # Assert NO contact PII or identity in Stage 2 prompt
    for contact_item in [
        "candidate.cv@domain.com",
        "alt.mail@domain.vn",
        "extra@domain.com",
        "0988 123 456",
        "(+84) 912 345 678",
        "024.3825.7888",
        "Nguyễn Văn B",
    ]:
        assert contact_item not in qualitative_prompt


# ---------------------------------------------------------------------------
# Test 4: Embedding Semantic Representations
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_embedding_semantic_representations_contain_zero_raw_contact_pii() -> None:
    """Verify CV and Job semantic texts sent to embedding provider contain ZERO raw contact PII."""
    spy_llm = CapturingLlmProvider()
    spy_embedding = CapturingEmbeddingProvider(dimension=64)
    matching_svc = MatchingService(
        llm=spy_llm,
        embedding_provider=spy_embedding,
        matching_algorithm="matching-v1-experimental",
    )
    ranking_svc = RankingService(matching_service=matching_svc)

    raw_cand_email = "candidate.embed@futurecv.ai"
    raw_cand_phone = "+84 988 123 456"
    raw_job_email = "recruitment.embed@futurecv.ai"
    raw_job_phone = "0912-345-678"

    cv = StructuredCv(
        full_name="Secret Candidate",
        email=raw_cand_email,
        phone=raw_cand_phone,
        career_summary=f"Experienced backend engineer. Email: {raw_cand_email} or call {raw_cand_phone}.",
        skills=["Python", "Docker"],
        work_experience=[
            WorkExperienceItem(
                job_title="Senior Dev",
                company="FinTech Corp",
                years_of_experience=4.0,
                description=f"Led payments backend. Contact: {raw_cand_email}.",
            )
        ],
        projects=[
            ProjectItem(
                name="Payment Gateway",
                description=f"High scale gateway. Inquiries: {raw_cand_email}.",
                technologies=["Python", "PostgreSQL"],
            )
        ],
    )

    job = StructuredJob(
        job_id="job-emb-01",
        title="Senior Python Engineer",
        description=f"Build microservices. Reach recruiter at {raw_job_email} or {raw_job_phone}.",
        required_skills=["Python", "Docker"],
        min_experience_years=3.0,
    )

    await ranking_svc.rank_candidates(
        CandidateRankRequest(job=job, candidates=[CandidateItem(candidate_id="cand-emb-01", cv=cv)])
    )

    assert len(spy_embedding.captured_texts) >= 2

    # Assert NO raw contact PII exists in any captured embedding string
    for text_sample in spy_embedding.captured_texts:
        for pii in [
            raw_cand_email,
            raw_cand_phone,
            raw_job_email,
            raw_job_phone,
            "Secret Candidate",
            "cand-emb-01",
        ]:
            assert pii not in text_sample

    # Redacted tokens must appear in the embedding texts where free text contained PII
    all_embedded = "\n".join(spy_embedding.captured_texts)
    assert EMAIL_REDACTED_TOKEN in all_embedded
    assert PHONE_REDACTED_TOKEN in all_embedded


# ---------------------------------------------------------------------------
# Test 5: Structured Data Excludes Contact Fields in Non-Extraction Operations
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_structured_contact_fields_never_leaked_into_non_extraction_llm_calls() -> None:
    """Explicitly verifies candidate.email and candidate.phone are excluded from all non-extraction prompts."""
    spy_llm = CapturingLlmProvider()
    service = MatchingService(llm=spy_llm)

    cv = StructuredCv(
        full_name="Nguyen Sensitive Name",
        email="very.sensitive@candidate.org",
        phone="+84 988 123 456",
        skills=["React", "TypeScript"],
        work_experience=[
            WorkExperienceItem(
                job_title="Frontend Engineer",
                company="Digital Agency",
                years_of_experience=2.0,
            )
        ],
    )

    job = StructuredJob(
        job_id="job-clean-99",
        title="Frontend Developer",
        required_skills=["React", "TypeScript"],
        min_experience_years=2.0,
    )

    await service.match(cv=cv, job=job, generate_explanation=True)

    captured_calls = spy_llm.captured_text_calls + spy_llm.captured_structured_calls
    assert len(captured_calls) == 1
    prompt = captured_calls[0]["prompt"]

    assert "very.sensitive@candidate.org" not in prompt
    assert "+84 988 123 456" not in prompt
    assert "Nguyen Sensitive Name" not in prompt
    assert "id-sensitive-12345" not in prompt
