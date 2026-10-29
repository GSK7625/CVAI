"""Integration tests for bounded PDF upload stream handling."""

import io

from fastapi.testclient import TestClient
import fitz

from app.api.deps import get_settings_dep
from app.core.config import Settings
from app.main import app


def _create_minimal_pdf() -> bytes:
    """Generate minimal valid PDF bytes."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Nguyen Van D - Python Engineer with 4 years experience.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_cv_analyze_file_upload_success():
    """Verify standard valid PDF file upload is processed and returns 200."""
    client = TestClient(app)
    pdf_bytes = _create_minimal_pdf()

    files = {"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/v1/cv/analyze", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "structured_cv" in data
    assert "cv_score" in data
    assert "strengths" in data


def test_cv_analyze_file_upload_oversized_rejected_before_full_processing():
    """Verify upload exceeding max_upload_size_bytes is aborted with 413 Payload Too Large."""
    # Override settings with a small 10 KB limit for testing
    small_limit_settings = Settings(MAX_UPLOAD_SIZE_BYTES=10 * 1024)

    def get_test_settings():
        return small_limit_settings

    app.dependency_overrides[get_settings_dep] = get_test_settings
    try:
        client = TestClient(app)
        # 100 KB payload exceeding the 10 KB limit
        large_payload = b"%PDF-1.4 " + b"0" * (100 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_payload), "application/pdf")}

        response = client.post("/api/v1/cv/analyze", files=files)
        assert response.status_code == 413
        data = response.json()
        assert data["error_code"] == "FILE_TOO_LARGE"
    finally:
        app.dependency_overrides.pop(get_settings_dep, None)
