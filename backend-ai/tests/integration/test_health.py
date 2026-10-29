"""Integration tests for health, ready, and correlation ID response headers."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """Verify /health returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health_returns_200():
    """Verify /api/v1/health returns 200 and status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_probe_returns_200():
    """Verify /ready returns readiness structure."""
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "checks" in data


def test_correlation_id_in_response_header():
    """Verify X-Correlation-Id header is propagated or created in response."""
    # Supplied valid correlation ID
    custom_cid = "test-corr-id-12345"
    response = client.get("/health", headers={"X-Correlation-Id": custom_cid})
    assert response.headers.get("X-Correlation-Id") == custom_cid

    # Auto-generated correlation ID when none supplied
    response_auto = client.get("/health")
    assert "X-Correlation-Id" in response_auto.headers
    assert len(response_auto.headers["X-Correlation-Id"]) > 0


def test_readiness_probe_gemini_provider(monkeypatch):
    """Verify /ready probe correctly reflects gemini provider configuration."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123")

    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["llm_provider"] == "gemini"
    assert data["checks"]["provider_key_configured"] is True
    get_settings.cache_clear()
