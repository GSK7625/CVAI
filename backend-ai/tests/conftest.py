"""Pytest configuration and global fixtures for backend-ai test suite."""

from collections.abc import Generator

import pytest

from app.api.deps import verify_internal_api_key
from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture(autouse=True, scope="session")
def isolate_test_environment() -> Generator[None, None, None]:
    """Ensure test suite runs in an isolated environment without picking up local developer .env."""
    original_env_file = Settings.model_config.get("env_file")
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    try:
        yield
    finally:
        Settings.model_config["env_file"] = original_env_file
        get_settings.cache_clear()


@pytest.fixture(autouse=True)
def bypass_internal_auth_in_general_tests() -> Generator[None, None, None]:
    """
    Bypass internal API key dependency for general feature tests.
    Auth-specific tests can clear app.dependency_overrides to test actual auth rules.
    """
    app.dependency_overrides[verify_internal_api_key] = lambda: None
    try:
        yield
    finally:
        app.dependency_overrides.pop(verify_internal_api_key, None)
