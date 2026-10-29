"""Unit tests for Career Assistant prompt hardening and PII minimization."""

import pytest

from app.application.career_assistant import CareerAssistantService
from app.contracts.career import CareerAssistantContext, CareerAssistantRequest, ChatMessage
from app.contracts.cv import StructuredCv, WorkExperienceItem
from app.contracts.job import StructuredJob
from app.contracts.matching import MatchResult
from app.domain.matching.experience_match import calculate_total_experience_years
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider


class CareerPromptInterceptingLlm(MockLlmProvider):
    """Spy LLM provider capturing career assistant prompts."""

    def __init__(self) -> None:
        self.captured_prompts: list[str] = []

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.captured_prompts.append(prompt)
        return await super().generate_text(prompt, system_prompt, temperature)


@pytest.mark.asyncio
async def test_career_assistant_omits_candidate_id_and_pii_from_prompt():
    """Verify candidate_id, full_name, email, and phone are excluded from Career Assistant context."""
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    cv = StructuredCv(
        full_name="Le Van Secret",
        email="candidate_secret@futurecv.vn",
        phone="0988776655",
        career_summary="Looking for Cloud Architect role",
        skills=["AWS", "Docker", "Terraform"],
        work_experience=[{"job_title": "DevOps Lead", "years_of_experience": 5.0}],
    )
    job = StructuredJob(
        title="Senior Cloud Engineer",
        required_skills=["AWS", "Kubernetes"],
    )
    context = CareerAssistantContext(
        candidate_id="SECRET_CANDIDATE_ID_9999",
        cv=cv,
        job=job,
        match_result=MatchResult(
            match_score=75,
            matched_skills=["AWS"],
            missing_skills=["Kubernetes"],
            experience_comparison="Meets 5 years requirement",
            education_comparison="N/A",
            project_domain_relevance="Relevant cloud experience",
            match_explanation="Good match overall",
        ),
    )

    req = CareerAssistantRequest(
        message="What skills should I learn first to improve my score?",
        history=[
            ChatMessage(role="user", content="Hello assistant"),
            ChatMessage(role="assistant", content="Hello, how can I help?"),
        ],
        context=context,
    )

    response = await service.chat(req)

    assert len(spy_llm.captured_prompts) == 1
    prompt = spy_llm.captured_prompts[0]

    # Verify candidate_id and sensitive PII are absent
    assert "SECRET_CANDIDATE_ID_9999" not in prompt
    assert "candidate_secret@futurecv.vn" not in prompt
    assert "0988776655" not in prompt
    assert "Le Van Secret" not in prompt

    # Verify untrusted delimiters exist
    assert "<<<BEGIN UNTRUSTED CAREER CONTEXT>>>" in prompt
    assert "<<<END UNTRUSTED CAREER CONTEXT>>>" in prompt
    assert "<<<BEGIN UNTRUSTED CONVERSATION HISTORY>>>" in prompt
    assert "<<<END UNTRUSTED CONVERSATION HISTORY>>>" in prompt
    assert "<<<BEGIN UNTRUSTED USER QUERY>>>" in prompt
    assert "<<<END UNTRUSTED USER QUERY>>>" in prompt

    # Verify metadata
    assert response.meta.algorithm_version == "career-v0"
    assert response.meta.provider == "mock"
    assert response.meta.model == "mock-deterministic"


@pytest.mark.asyncio
async def test_career_assistant_experience_non_overlapping():
    """
    FIX 1: Sequential non-overlapping roles are summed correctly via canonical helper.
    Role 1: 2020-01 to 2021-01 (1.0 year)
    Role 2: 2022-01 to 2024-01 (2.0 years)
    Expected: 3.0 years
    """
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    experiences = [
        WorkExperienceItem(
            job_title="Junior Engineer",
            start_date="2020-01",
            end_date="2021-01",
            years_of_experience=1.0,
        ),
        WorkExperienceItem(
            job_title="Senior Engineer",
            start_date="2022-01",
            end_date="2024-01",
            years_of_experience=2.0,
        ),
    ]
    canonical_years = calculate_total_experience_years(experiences)
    assert canonical_years == 3.0

    cv = StructuredCv(
        career_summary="Software engineer with continuous learning mindset.",
        skills=["Python", "FastAPI"],
        work_experience=experiences,
    )
    req = CareerAssistantRequest(
        message="Review my experience.",
        context=CareerAssistantContext(cv=cv),
    )

    await service.chat(req)

    prompt = spy_llm.captured_prompts[0]
    assert f"Tổng số năm kinh nghiệm: {canonical_years:.1f} năm" in prompt
    assert "Tổng số năm kinh nghiệm: 3.0 năm" in prompt


@pytest.mark.asyncio
async def test_career_assistant_experience_overlapping_roles_deduplicated():
    """
    CRITICAL PROOF (FIX 1): Overlapping concurrent roles are NOT double-counted.
    Role A: 2022-01 -> 2024-01 (2.0 years)
    Role B: 2022-01 -> 2024-01 (2.0 years)
    Previous naive sum: 4.0 years.
    Canonical Matching helper: 2.0 years.
    Career Assistant MUST use canonical helper and report 2.0 years, NOT 4.0 years.
    """
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    experiences = [
        WorkExperienceItem(
            job_title="Backend Developer",
            company="Company Alpha",
            start_date="2022-01",
            end_date="2024-01",
            years_of_experience=2.0,
        ),
        WorkExperienceItem(
            job_title="Freelance Developer",
            company="Freelance Client",
            start_date="2022-01",
            end_date="2024-01",
            years_of_experience=2.0,
        ),
    ]
    canonical_years = calculate_total_experience_years(experiences)
    assert canonical_years == 2.0

    cv = StructuredCv(
        career_summary="Fullstack engineer.",
        skills=["Python"],
        work_experience=experiences,
    )
    req = CareerAssistantRequest(
        message="What career path fits my background?",
        context=CareerAssistantContext(cv=cv),
    )

    await service.chat(req)

    prompt = spy_llm.captured_prompts[0]
    # Verify canonical 2.0 years is reported, NOT 4.0 years
    assert f"Tổng số năm kinh nghiệm: {canonical_years:.1f} năm" in prompt
    assert "Tổng số năm kinh nghiệm: 2.0 năm" in prompt
    assert "Tổng số năm kinh nghiệm: 4.0 năm" not in prompt


@pytest.mark.asyncio
async def test_career_assistant_experience_mixed_dated_and_undated():
    """
    FIX 1: Conservative dated-timeline policy matches calculate_total_experience_years exactly.
    Dated role (2022-01 -> 2024-01 = 2.0 years) is authoritative over undated scalar role.
    """
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    experiences = [
        WorkExperienceItem(
            job_title="Backend Developer",
            start_date="2022-01",
            end_date="2024-01",
            years_of_experience=2.0,
        ),
        WorkExperienceItem(
            job_title="Part-time Consultant",
            years_of_experience=1.5,
        ),
    ]
    canonical_years = calculate_total_experience_years(experiences)
    assert canonical_years == 2.0

    cv = StructuredCv(work_experience=experiences)
    req = CareerAssistantRequest(
        message="How many years of experience do I have?",
        context=CareerAssistantContext(cv=cv),
    )

    await service.chat(req)

    prompt = spy_llm.captured_prompts[0]
    assert f"Tổng số năm kinh nghiệm: {canonical_years:.1f} năm" in prompt
    assert "Tổng số năm kinh nghiệm: 3.5 năm" not in prompt


@pytest.mark.asyncio
async def test_career_assistant_experience_no_experience():
    """FIX 1: When no experience is provided, experience line is safely omitted."""
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    cv = StructuredCv(
        career_summary="Fresh graduate.",
        skills=["Python"],
        work_experience=[],
    )
    req = CareerAssistantRequest(
        message="Can I apply for junior jobs?",
        context=CareerAssistantContext(cv=cv),
    )

    await service.chat(req)

    prompt = spy_llm.captured_prompts[0]
    assert "Tổng số năm kinh nghiệm:" not in prompt


@pytest.mark.asyncio
async def test_career_assistant_free_text_pii_redaction():
    """
    CRITICAL PROOF (FIX 2): Free-text fields with synthetic emails and phone numbers
    are deterministically redacted before entering the Career Assistant LLM prompt.
    """
    spy_llm = CareerPromptInterceptingLlm()
    service = CareerAssistantService(llm=spy_llm)

    synthetic_email_cv = "candidate.career@synthetic-test.vn"
    synthetic_phone_cv = "0912345678"
    synthetic_email_skill = "skill.author@opensource.org"
    synthetic_phone_skill = "+84 987 654 321"

    synthetic_email_job = "recruiter@hiring-company.com"
    synthetic_email_req_skill = "contact.req@company.com"
    synthetic_phone_pref_skill = "0901234567"

    synthetic_email_match = "evaluator@matching-service.internal"
    synthetic_phone_match = "0933445566"

    cv = StructuredCv(
        # Dedicated identity fields (MUST remain absent)
        full_name="Secret Identity Person",
        email="personal.untrusted@real-domain.com",
        phone="0999888777",
        # Free-text fields containing PII (MUST be redacted)
        career_summary=f"Experienced dev. Reach me at {synthetic_email_cv} or call {synthetic_phone_cv}.",
        skills=[
            f"Python (maintained by {synthetic_email_skill})",
            f"Docker (hotline {synthetic_phone_skill})",
        ],
        work_experience=[
            WorkExperienceItem(
                job_title="Lead Developer",
                company="Tech Co",
                description="Built core backend systems.",
                years_of_experience=3.0,
            )
        ],
    )

    job = StructuredJob(
        title=f"Backend Lead - inquiries to {synthetic_email_job}",
        required_skills=[f"FastAPI (questions to {synthetic_email_req_skill})"],
        preferred_skills=[f"Kubernetes (support line {synthetic_phone_pref_skill})"],
    )

    match_result = MatchResult(
        match_score=85,
        matched_skills=["Python"],
        missing_skills=["Kubernetes"],
        experience_comparison=f"Qualified 3 years. Verified by {synthetic_email_match}.",
        education_comparison=f"CS degree confirmed via phone {synthetic_phone_match}.",
    )

    context = CareerAssistantContext(
        candidate_id="SECRET_ID_XYZ",
        cv=cv,
        job=job,
        match_result=match_result,
    )

    req = CareerAssistantRequest(
        message="How should I prepare for interview?",
        history=[
            ChatMessage(role="user", content="Hi counselor"),
            ChatMessage(role="assistant", content="Hello, let's look at your profile."),
        ],
        context=context,
    )

    await service.chat(req)

    assert len(spy_llm.captured_prompts) == 1
    prompt = spy_llm.captured_prompts[0]

    # 1. Dedicated identity fields MUST NOT appear anywhere
    assert "Secret Identity Person" not in prompt
    assert "personal.untrusted@real-domain.com" not in prompt
    assert "0999888777" not in prompt
    assert "SECRET_ID_XYZ" not in prompt

    # 2. Raw synthetic email values inside free text MUST NOT appear
    assert synthetic_email_cv not in prompt
    assert synthetic_email_skill not in prompt
    assert synthetic_email_job not in prompt
    assert synthetic_email_req_skill not in prompt
    assert synthetic_email_match not in prompt

    # 3. Raw synthetic phone values inside free text MUST NOT appear
    assert synthetic_phone_cv not in prompt
    assert synthetic_phone_skill not in prompt
    assert synthetic_phone_pref_skill not in prompt
    assert synthetic_phone_match not in prompt

    # 4. Redaction tokens MUST be present in the prompt
    assert "[EMAIL_REDACTED]" in prompt
    assert "[PHONE_REDACTED]" in prompt
