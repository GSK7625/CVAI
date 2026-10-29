"""Unit tests for OpenAI LLM HTTP client lifecycle, connection reuse, and concurrency safety."""

import asyncio
import json
from typing import Any

from fastapi import Depends
from fastapi.testclient import TestClient
import httpx
import pytest

from app.api.deps import get_llm, get_settings_dep
from app.core.config import Settings
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.infrastructure.llm.providers.openai_provider import OpenAiProvider
from app.main import create_application
from app.ports.llm import LlmPort


@pytest.mark.asyncio
async def test_llm_provider_and_client_reused_across_requests():
    """Verify that multiple requests to the API reuse the exact same OpenAiProvider and AsyncClient."""
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-test-key",
        LLM_TIMEOUT_SECONDS=10,
    )

    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Processed response content",
                        }
                    }
                ]
            },
        )

    from app.infrastructure.llm.factory import get_llm_settings_fingerprint

    transport = httpx.MockTransport(handler)
    shared_client = httpx.AsyncClient(transport=transport)
    custom_provider = OpenAiProvider(settings=settings, http_client=shared_client)

    test_app = create_application()
    test_app.state.llm_provider = custom_provider
    test_app.state.llm_provider_fingerprint = get_llm_settings_fingerprint(settings)
    test_app.dependency_overrides[get_settings_dep] = lambda: settings

    observed_providers: list[LlmPort] = []

    @test_app.get("/test-llm-call")
    async def sample_endpoint(llm: LlmPort = Depends(get_llm)) -> dict[str, Any]:
        observed_providers.append(llm)
        text = await llm.generate_text("Hello test")
        return {"text": text}

    with TestClient(test_app) as client:
        # Send 3 distinct requests
        resp1 = client.get("/test-llm-call")
        resp2 = client.get("/test-llm-call")
        resp3 = client.get("/test-llm-call")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp3.status_code == 200

        # 1. Assert exactly one provider instance was used across all requests
        assert len(observed_providers) == 3
        assert observed_providers[0] is custom_provider
        assert observed_providers[1] is custom_provider
        assert observed_providers[2] is custom_provider

        # 2. Assert client was reused across all 3 calls
        assert call_count == 3
        assert not shared_client.is_closed

    await shared_client.aclose()


@pytest.mark.asyncio
async def test_different_settings_does_not_reuse_app_scoped_provider():
    """
    CRITICAL PROOF (FIX H): When settings differ in model, timeout, or credentials,
    app-scoped provider is NOT reused; a temporary provider is used and closed.
    """
    from app.infrastructure.llm.factory import get_llm_settings_fingerprint

    base_settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-key-a",
        LLM_MODEL="gpt-4o-mini",
        LLM_TIMEOUT_SECONDS=60,
    )
    overridden_settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-key-b",
        LLM_MODEL="gpt-4o",
        LLM_TIMEOUT_SECONDS=10,
    )

    base_client = httpx.AsyncClient()
    app_provider = OpenAiProvider(settings=base_settings, http_client=base_client)

    test_app = create_application()
    test_app.state.llm_provider = app_provider
    test_app.state.llm_provider_fingerprint = get_llm_settings_fingerprint(base_settings)

    # Request with overridden settings
    yielded_providers: list[LlmPort] = []
    mock_request = type("MockRequest", (), {"app": test_app})()
    async for prov in get_llm(request=mock_request, settings=overridden_settings):  # type: ignore[arg-type]
        # Even with request present, it must NOT reuse app_provider because fingerprint differs
        assert prov is not app_provider
        assert prov.model_name == "gpt-4o"
        yielded_providers.append(prov)

    # Temporary provider must have been closed
    assert len(yielded_providers) == 1
    assert isinstance(yielded_providers[0], OpenAiProvider)
    assert yielded_providers[0]._client.is_closed

    # App provider must remain unclosed
    assert not base_client.is_closed
    await base_client.aclose()


def test_lifespan_closes_client_once_at_application_shutdown():
    """Verify application lifespan creates provider on startup and closes client on shutdown."""
    test_app = create_application()

    # Run application within lifespan context
    with TestClient(test_app) as client:
        provider = test_app.state.llm_provider
        assert provider is not None
        assert provider.provider_name == "mock"  # default test/dev provider

        response = client.get("/health")
        assert response.status_code == 200

    # Test explicit client closing on shutdown with OpenAiProvider
    mock_transport = httpx.MockTransport(lambda req: httpx.Response(200, json={}))
    raw_client = httpx.AsyncClient(transport=mock_transport)
    openai_provider = OpenAiProvider(
        settings=Settings(OPENAI_API_KEY="sk-test"),
        http_client=raw_client,
    )
    openai_provider._owns_client = True

    test_app2 = create_application()
    test_app2.state.llm_provider = openai_provider

    with TestClient(test_app2):
        assert not raw_client.is_closed

    assert raw_client.is_closed


@pytest.mark.asyncio
async def test_no_client_leaked_in_standalone_dependency_calls():
    """Verify fallback ephemeral get_llm invocation cleans up client in finally block."""
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-standalone-test",
    )

    created_provider: OpenAiProvider | None = None

    # Call get_llm without an active request / app.state
    async for provider in get_llm(request=None, settings=settings):
        created_provider = provider
        assert isinstance(created_provider, OpenAiProvider)
        assert not created_provider._client.is_closed

    # Exiting async iterator must close the created client
    assert created_provider is not None
    assert created_provider._client.is_closed


def test_dependency_override_remains_functional_with_app_scoped_provider():
    """Verify test dependency overrides take precedence over app.state provider."""
    test_app = create_application()

    class SpyCustomProvider(MockLlmProvider):
        @property
        def model_name(self) -> str:
            return "spy-model-v99"

    spy = SpyCustomProvider()

    test_app.dependency_overrides[get_llm] = lambda: spy

    observed: list[LlmPort] = []

    @test_app.get("/check-override")
    def check_override(llm: LlmPort = Depends(get_llm)) -> dict[str, str]:
        observed.append(llm)
        return {"model": llm.model_name}

    client = TestClient(test_app)
    resp = client.get("/check-override")

    assert resp.status_code == 200
    assert resp.json()["model"] == "spy-model-v99"
    assert observed[0] is spy


@pytest.mark.asyncio
async def test_concurrent_calls_do_not_share_mutable_request_data():
    """Verify concurrent requests using the same OpenAiProvider do not cross-contaminate state."""
    settings = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-concurrent-test",
    )

    async def concurrent_handler(request: httpx.Request) -> httpx.Response:
        json_bytes = request.read()
        payload = json.loads(json_bytes.decode("utf-8"))
        user_content = payload["messages"][-1]["content"]

        # Simulate variable network latency
        await asyncio.sleep(0.02)

        return httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": f"Echo: {user_content}",
                        }
                    }
                ]
            },
        )

    transport = httpx.MockTransport(concurrent_handler)
    shared_client = httpx.AsyncClient(transport=transport)
    provider = OpenAiProvider(settings=settings, http_client=shared_client)

    try:
        prompts = [f"Unique Task #{i}" for i in range(10)]
        tasks = [provider.generate_text(prompt=p) for p in prompts]

        results = await asyncio.gather(*tasks)

        for i, res in enumerate(results):
            assert res == f"Echo: Unique Task #{i}"

        assert not hasattr(provider, "prompt")
        assert not hasattr(provider, "messages")
        assert not hasattr(provider, "response")
    finally:
        await shared_client.aclose()


def test_llm_settings_fingerprint_distinguishes_keys_without_leaking_plaintext():
    """
    CRITICAL PROOF (VERIFICATION 2):
    1. Two Settings with different API keys produce DIFFERENT fingerprints.
    2. Two Settings with identical API keys produce IDENTICAL fingerprints.
    3. Plaintext API key values do NOT appear in the fingerprint tuple or its string representation.
    """
    from app.infrastructure.llm.factory import get_llm_settings_fingerprint

    key_a = "sk-live-credential-alpha"
    key_b = "sk-live-credential-beta"

    settings_a = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY=key_a,
        LLM_MODEL="gpt-4o-mini",
    )
    settings_b = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY=key_b,
        LLM_MODEL="gpt-4o-mini",
    )
    settings_a2 = Settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY=key_a,
        LLM_MODEL="gpt-4o-mini",
    )

    fp_a = get_llm_settings_fingerprint(settings_a)
    fp_b = get_llm_settings_fingerprint(settings_b)
    fp_a2 = get_llm_settings_fingerprint(settings_a2)

    # 1. Distinct keys -> distinct fingerprints
    assert fp_a != fp_b

    # 2. Same keys -> identical fingerprints
    assert fp_a == fp_a2

    # 3. Plaintext API keys must NEVER appear in the fingerprint
    fp_str = str(fp_a)
    assert key_a not in fp_str
    assert key_b not in fp_str
    assert not any(key_a in str(item) for item in fp_a if item is not None)
    assert not any(key_b in str(item) for item in fp_b if item is not None)
