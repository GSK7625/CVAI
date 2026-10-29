"""Contract hardening tests for Gemini LLM structured outputs and data contracts.

Verifies AI-DEMO-003 requirements:
1. Structured output with JSON Schema and application/json MIME type.
2. Rejection of unknown/extra fields (model_config = ConfigDict(extra="forbid"))
   for StructuredCv, WorkExperienceItem, EducationItem, ProjectItem, CvQualitativeFeedback.
3. No fake/spoofed data fallbacks (company remains "" or None, never invented).
4. Strict handling of:
   - Valid JSON
   - Missing required fields
   - Wrong data types
   - Extra/unrecognized fields
   - Score out of [0, 100] bounds
   - Markdown code fences (```json ... ```)
   - Plain text responses instead of JSON
"""

from unittest.mock import AsyncMock, MagicMock

from pydantic import BaseModel, ConfigDict, Field, ValidationError
import pytest

from app.application.cv_analyzer import CvQualitativeFeedback
from app.contracts.cv import (
    EducationItem,
    ProjectItem,
    StructuredCv,
    WorkExperienceItem,
)
from app.contracts.cv_analysis import CvAnalysisResponse
from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.domain.cv.heuristic_extractor import extract_structured_cv_heuristically
from app.infrastructure.llm.providers.gemini_provider import (
    GeminiLlmProvider,
    _clean_json_text,
)


def _make_gemini_provider(mock_response_text: str | None) -> tuple[GeminiLlmProvider, MagicMock]:
    """Helper creating a GeminiLlmProvider with a mocked generate_content response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = mock_response_text
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    settings = Settings(GEMINI_API_KEY="mock-gemini-key")
    provider = GeminiLlmProvider(settings=settings, client=mock_client)
    return provider, mock_client


# ============================================================================
# 1. JSON hợp lệ (Valid JSON)
# ============================================================================


@pytest.mark.asyncio
async def test_contract_valid_json_for_structured_cv():
    """Verify GeminiLlmProvider successfully deserializes valid StructuredCv JSON."""
    valid_payload = """
    {
        "full_name": "Tran Van B",
        "email": "tranvanb@example.com",
        "phone": "+84 901 234 567",
        "career_summary": "Senior Backend Developer with 5 years experience.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "work_experience": [
            {
                "job_title": "Backend Engineer",
                "company": "Tech Corp",
                "duration": "2021 - Present",
                "start_date": "2021-01",
                "end_date": null,
                "years_of_experience": 3.0,
                "description": "Building microservices"
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Engineering",
                "institution": "HUST",
                "field_of_study": "Computer Science",
                "graduation_year": "2020"
            }
        ],
        "certificates": ["AWS Solutions Architect"],
        "projects": [
            {
                "name": "E-Commerce Microservices",
                "description": "High-throughput ordering system",
                "technologies": ["FastAPI", "Redis"]
            }
        ],
        "technologies": ["Python", "Docker", "Redis"]
    }
    """
    provider, mock_client = _make_gemini_provider(valid_payload)

    result = await provider.generate_structured(
        prompt="Extract CV",
        response_model=StructuredCv,
        system_prompt="Extract JSON",
    )

    assert isinstance(result, StructuredCv)
    assert result.full_name == "Tran Van B"
    assert result.email == "tranvanb@example.com"
    assert len(result.work_experience) == 1
    assert result.work_experience[0].company == "Tech Corp"
    assert result.work_experience[0].years_of_experience == 3.0
    assert len(result.projects) == 1
    assert result.projects[0].name == "E-Commerce Microservices"

    # Verify JSON Schema was sent in config
    call_args = mock_client.aio.models.generate_content.call_args
    config = call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is not None


@pytest.mark.asyncio
async def test_contract_valid_json_for_cv_qualitative_feedback():
    """Verify GeminiLlmProvider successfully deserializes valid CvQualitativeFeedback JSON."""
    valid_payload = """
    {
        "strengths": ["Solid foundation in backend architecture", "Clear project achievements"],
        "weaknesses": ["Missing quantitative metrics in experience"],
        "improvement_suggestions": ["Add measurable KPIs (e.g. latency reduced by 30%)"]
    }
    """
    provider, _ = _make_gemini_provider(valid_payload)

    result = await provider.generate_structured(
        prompt="Analyze CV",
        response_model=CvQualitativeFeedback,
    )

    assert isinstance(result, CvQualitativeFeedback)
    assert len(result.strengths) == 2
    assert len(result.weaknesses) == 1
    assert len(result.improvement_suggestions) == 1


# ============================================================================
# 2. JSON thiếu required field (Missing required field)
# ============================================================================


@pytest.mark.asyncio
async def test_contract_missing_required_field_rejected():
    """Verify response is rejected when a required field is missing (e.g. ProjectItem.name)."""
    # ProjectItem requires 'name' (non-empty string)
    invalid_payload = """
    {
        "full_name": "Nguyen Van C",
        "skills": ["Python"],
        "projects": [
            {
                "description": "Missing project name field",
                "technologies": ["Python"]
            }
        ]
    }
    """
    provider, _ = _make_gemini_provider(invalid_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract CV",
            response_model=StructuredCv,
        )

    err = exc_info.value
    assert "contract validation failed" in str(err)
    assert err.details.get("reason") == "validation_failed"
    assert err.details.get("model_name") == "StructuredCv"
    # Ensure validation errors detail points to the missing field
    val_errors = str(err.details.get("validation_errors", []))
    assert "name" in val_errors or "Field required" in val_errors


# ============================================================================
# 3. Sai kiểu dữ liệu (Wrong data type)
# ============================================================================


@pytest.mark.asyncio
async def test_contract_wrong_data_type_rejected():
    """Verify response is rejected when field has an incompatible type."""
    # years_of_experience should be a float, not an arbitrary unparseable string or nested object
    invalid_payload = """
    {
        "full_name": "Nguyen Van D",
        "skills": ["Python"],
        "work_experience": [
            {
                "job_title": "Developer",
                "company": "Some Corp",
                "years_of_experience": "ten years"
            }
        ]
    }
    """
    provider, _ = _make_gemini_provider(invalid_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract CV",
            response_model=StructuredCv,
        )

    err = exc_info.value
    assert "contract validation failed" in str(err)
    assert err.details.get("reason") == "validation_failed"


# ============================================================================
# 4. Có field lạ (Extra unexpected field rejected due to extra="forbid")
# ============================================================================


def test_extra_field_forbid_on_cv_contracts_direct():
    """Directly verify Pydantic forbids extra fields on all 5 key LLM models."""
    # 1. StructuredCv
    with pytest.raises(ValidationError) as exc:
        StructuredCv(full_name="Alice", unexpected_cv_field="hallucinated")
    assert "Extra inputs are not permitted" in str(exc.value)

    # 2. WorkExperienceItem
    with pytest.raises(ValidationError) as exc:
        WorkExperienceItem(job_title="Dev", salary_expectation=10000)
    assert "Extra inputs are not permitted" in str(exc.value)

    # 3. EducationItem
    with pytest.raises(ValidationError) as exc:
        EducationItem(institution="MIT", gpa_score=4.0)
    assert "Extra inputs are not permitted" in str(exc.value)

    # 4. ProjectItem
    with pytest.raises(ValidationError) as exc:
        ProjectItem(name="App", client_budget="50k")
    assert "Extra inputs are not permitted" in str(exc.value)

    # 5. CvQualitativeFeedback
    with pytest.raises(ValidationError) as exc:
        CvQualitativeFeedback(strengths=[], personality_type="INTJ")
    assert "Extra inputs are not permitted" in str(exc.value)


@pytest.mark.asyncio
async def test_contract_gemini_response_with_extra_field_rejected():
    """Verify Gemini structured output with hallucinated extra fields is rejected."""
    hallucinated_payload = """
    {
        "full_name": "Alice Wonderland",
        "skills": ["Python"],
        "salary_expectation": 100000,
        "favorite_editor": "Neovim"
    }
    """
    provider, _ = _make_gemini_provider(hallucinated_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract CV",
            response_model=StructuredCv,
        )

    err = exc_info.value
    assert "contract validation failed" in str(err)
    val_errors = str(err.details.get("validation_errors", []))
    assert "extra_forbidden" in val_errors


# ============================================================================
# 5. Score ngoài 0-100 (Score out of [0, 100] bounds)
# ============================================================================


class SampleScoredOutput(BaseModel):
    """Model with score bounded between 0 and 100."""

    model_config = ConfigDict(extra="forbid")
    category: str
    score: int = Field(ge=0, le=100)


@pytest.mark.asyncio
async def test_contract_score_outside_0_100_rejected():
    """Verify values outside [0, 100] are rejected by contract validation."""
    # Test score > 100
    invalid_high_payload = '{"category": "Python Mastery", "score": 105}'
    provider, _ = _make_gemini_provider(invalid_high_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Score candidate",
            response_model=SampleScoredOutput,
        )
    assert "contract validation failed" in str(exc_info.value)
    val_errors = str(exc_info.value.details.get("validation_errors", []))
    assert "less_than_equal" in val_errors

    # Test score < 0
    invalid_low_payload = '{"category": "Python Mastery", "score": -10}'
    provider, _ = _make_gemini_provider(invalid_low_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Score candidate",
            response_model=SampleScoredOutput,
        )
    assert "contract validation failed" in str(exc_info.value)
    val_errors = str(exc_info.value.details.get("validation_errors", []))
    assert "greater_than_equal" in val_errors


def test_cv_analysis_response_score_bounds():
    """Verify CvAnalysisResponse contract enforces cv_score in [0, 100]."""
    cv = StructuredCv(full_name="Valid Candidate")

    # Valid score
    resp = CvAnalysisResponse(structured_cv=cv, cv_score=85)
    assert resp.cv_score == 85

    # Out of bounds high
    with pytest.raises(ValidationError):
        CvAnalysisResponse(structured_cv=cv, cv_score=101)

    # Out of bounds low
    with pytest.raises(ValidationError):
        CvAnalysisResponse(structured_cv=cv, cv_score=-1)


# ============================================================================
# 6. Gemini trả markdown code fence (Markdown code fence handling)
# ============================================================================


def test_clean_json_text_helper():
    """Verify _clean_json_text helper properly strips various markdown fences."""
    # Clean JSON
    assert _clean_json_text('{"a": 1}') == '{"a": 1}'

    # ```json fence
    fenced_1 = '```json\n{"a": 1}\n```'
    assert _clean_json_text(fenced_1) == '{"a": 1}'

    # ``` fence without json
    fenced_2 = '```\n{"a": 1}\n```'
    assert _clean_json_text(fenced_2) == '{"a": 1}'

    # Fenced JSON with surrounding conversational commentary
    fenced_3 = 'Here is the requested output:\n```json\n{"a": 1}\n```\nHope it helps!'
    assert _clean_json_text(fenced_3) == '{"a": 1}'


@pytest.mark.asyncio
async def test_contract_gemini_markdown_code_fence_parsed_successfully():
    """Verify markdown code fences returned by LLM are cleaned and parsed correctly."""
    fenced_payload = """```json
    {
        "strengths": ["Strong architectural vision"],
        "weaknesses": ["Limited cloud experience"],
        "improvement_suggestions": ["Acquire AWS or GCP associate certification"]
    }
    ```"""
    provider, _ = _make_gemini_provider(fenced_payload)

    result = await provider.generate_structured(
        prompt="Analyze CV",
        response_model=CvQualitativeFeedback,
    )

    assert isinstance(result, CvQualitativeFeedback)
    assert result.strengths == ["Strong architectural vision"]
    assert result.weaknesses == ["Limited cloud experience"]


# ============================================================================
# 7. Gemini trả text thay vì JSON (Plain text response rejected)
# ============================================================================


@pytest.mark.asyncio
async def test_contract_gemini_plain_text_rejected():
    """Verify natural language text response is rejected with invalid JSON error."""
    plain_text = (
        "Based on my analysis, this candidate has extensive experience in software development. "
        "They have worked with Python, Django, and PostgreSQL for over 4 years."
    )
    provider, _ = _make_gemini_provider(plain_text)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract CV",
            response_model=StructuredCv,
        )

    err = exc_info.value
    assert "invalid JSON" in str(err)
    assert err.details.get("reason") == "invalid_json"


@pytest.mark.asyncio
async def test_contract_gemini_json_array_instead_of_object_rejected():
    """Verify JSON array response is rejected when a JSON object (BaseModel) is expected."""
    array_payload = '["item1", "item2", "item3"]'
    provider, _ = _make_gemini_provider(array_payload)

    with pytest.raises(ProviderError) as exc_info:
        await provider.generate_structured(
            prompt="Extract CV",
            response_model=StructuredCv,
        )

    err = exc_info.value
    assert "expected JSON object" in str(err)
    assert err.details.get("reason") == "not_an_object"


# ============================================================================
# 8. Không sửa dữ liệu để “cứu” response (No fake data fallbacks)
# ============================================================================


def test_no_data_spoofing_in_work_experience_and_education():
    """Verify contracts default missing values to empty string or None without inventing fake names."""
    # WorkExperienceItem: missing company defaults to "" (not "Company" or fake name)
    item = WorkExperienceItem(job_title="Software Engineer")
    assert item.company == ""
    assert item.company != "Company"

    # EducationItem: missing institution defaults to "" (not "University")
    edu = EducationItem(degree="Bachelor")
    assert edu.institution == ""
    assert edu.institution != "University"
    assert edu.field_of_study == ""


def test_heuristic_extractor_does_not_spoof_company_or_institution():
    """Verify heuristic extractor leaves company and institution empty when not in CV text."""
    minimal_cv = """
    NGUYEN VAN MINH
    minh@test.com | 0912345678

    EXPERIENCE
    Frontend Engineer
    01/2023 - 01/2024
    Built UI components with React.

    EDUCATION
    Bachelor of Science
    2019 - 2023
    """
    cv = extract_structured_cv_heuristically(minimal_cv)

    assert len(cv.work_experience) >= 1
    # Company was not specified in the CV header (no '|' separator), so it should be empty
    assert cv.work_experience[0].company == ""
    assert cv.work_experience[0].company != "Company"

    assert len(cv.education) >= 1
    # Institution was not specified (no '|' separator), so it should be empty
    assert cv.education[0].institution == ""
    assert cv.education[0].institution != "University"
