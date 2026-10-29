"""Contract tests for Career Assistant and ErrorResponse."""

from app.contracts.career import CareerAssistantRequest, CareerAssistantResponse
from app.contracts.errors import ErrorResponse


def test_career_assistant_contract_fields():
    """Verify CareerAssistantRequest and CareerAssistantResponse shapes."""
    req_data = {
        "message": "Làm sao để cải thiện CV?",
        "history": [{"role": "user", "content": "Hello"}],
        "context": {
            "candidate_id": "cand-001",
        },
    }
    req = CareerAssistantRequest.model_validate(req_data)
    assert req.message == "Làm sao để cải thiện CV?"
    assert len(req.history) == 1

    resp_data = {
        "reply": "Bạn nên bổ sung các dự án thực tế.",
        "suggested_followups": ["Ví dụ dự án nào phù hợp?"],
        "meta": {"correlation_id": "cid-123"},
    }
    resp = CareerAssistantResponse.model_validate(resp_data)
    dumped = resp.model_dump()
    assert dumped["reply"] == "Bạn nên bổ sung các dự án thực tế."
    assert len(dumped["suggested_followups"]) == 1


def test_error_response_contract_fields():
    """Verify ErrorResponse contract matches standardized schema."""
    error_data = {
        "error_code": "INVALID_DOCUMENT",
        "message": "Cannot parse document",
        "details": {"reason": "corrupt_pdf"},
        "correlation_id": "err-cid-999",
    }
    err = ErrorResponse.model_validate(error_data)
    dumped = err.model_dump()
    assert dumped["error_code"] == "INVALID_DOCUMENT"
    assert dumped["correlation_id"] == "err-cid-999"
