"""Unit tests for internal API key authentication."""

from unittest.mock import patch

from fastapi import HTTPException
import pytest

from app.api.middleware.internal_auth import verify_internal_api_key
from app.core.config import Settings


def test_verify_internal_api_key_valid():
    """Valid API key matches and does not raise."""
    test_settings = Settings(INTERNAL_API_KEY="my-secret-token", ENV="development")
    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        # Should not raise exception
        verify_internal_api_key(x_internal_api_key="my-secret-token")


def test_verify_internal_api_key_invalid():
    """Invalid API key raises 401 HTTPException."""
    test_settings = Settings(INTERNAL_API_KEY="my-secret-token", ENV="development")
    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_api_key(x_internal_api_key="wrong-token")
        assert exc_info.value.status_code == 401


def test_verify_internal_api_key_missing():
    """Missing API key raises 401 HTTPException when key is required."""
    test_settings = Settings(INTERNAL_API_KEY="my-secret-token", ENV="development")
    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_api_key(x_internal_api_key=None)
        assert exc_info.value.status_code == 401


def test_verify_internal_api_key_dev_unconfigured():
    """Unconfigured key in development mode permits requests."""
    test_settings = Settings(INTERNAL_API_KEY="", ENV="development")
    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        verify_internal_api_key(x_internal_api_key=None)


def test_verify_internal_api_key_prod_unconfigured_fails_closed():
    """Unconfigured key in production mode rejects with 500 configuration error."""
    test_settings = Settings.model_construct(internal_api_key="", env="production")
    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        with pytest.raises(HTTPException) as exc_info:
            verify_internal_api_key(x_internal_api_key=None)
        assert exc_info.value.status_code == 500


def test_endpoint_authentication_requires_valid_internal_api_key():
    """DoD: FastAPI endpoints reject missing/invalid keys with 401, and accept valid key."""
    from fastapi.testclient import TestClient

    from app.api.deps import verify_internal_api_key as dep_verify
    from app.main import app

    # Temporarily remove conftest bypass for this test
    app.dependency_overrides.pop(dep_verify, None)
    client = TestClient(app)

    test_settings = Settings(
        INTERNAL_API_KEY="futurecv-demo-local-2026",
        ENV="development",
        LLM_PROVIDER="mock",
    )

    sample_payload = {
        "raw_text": "Software Engineer with Python skills",
        "candidate_id": "c1",
    }

    with patch("app.api.middleware.internal_auth.get_settings", return_value=test_settings):
        # 1. Missing header -> 401
        res_missing = client.post("/api/v1/cv/analyze-text", json=sample_payload)
        assert res_missing.status_code == 401
        assert "Missing internal service API key" in res_missing.text

        # 2. Invalid header -> 401
        res_invalid = client.post(
            "/api/v1/cv/analyze-text",
            json=sample_payload,
            headers={"X-Internal-API-Key": "wrong-secret-key"},
        )
        assert res_invalid.status_code == 401
        assert "Invalid internal service API key" in res_invalid.text

        # 3. Valid header -> 200
        res_valid = client.post(
            "/api/v1/cv/analyze-text",
            json=sample_payload,
            headers={"X-Internal-API-Key": "futurecv-demo-local-2026"},
        )
        assert res_valid.status_code == 200
