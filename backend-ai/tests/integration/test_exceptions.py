"""Integration tests for exception handling and error sanitization."""

from fastapi.testclient import TestClient

from app.core.exceptions import DocumentParsingError
from app.main import app

client = TestClient(app)


def test_404_not_found_returns_sanitized_json():
    """Verify 404 response returns sanitized error structure with correlation_id."""
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert data["error_code"] == "NOT_FOUND"
    assert "message" in data
    assert "correlation_id" in data


def test_custom_domain_exception_handled():
    """Verify custom domain exception is transformed into structured error response."""

    # Temporarily attach a test route that raises custom exception
    @app.get("/test-raise-domain-error")
    def raise_error():
        raise DocumentParsingError("Corrupt PDF file header", details={"reason": "bad_magic_bytes"})

    response = client.get("/test-raise-domain-error")
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INVALID_DOCUMENT"
    assert data["message"] == "Corrupt PDF file header"
    assert data["details"]["reason"] == "bad_magic_bytes"
    assert "correlation_id" in data
