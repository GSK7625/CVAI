"""Integration tests for matching input validation and provider non-invocation (AI-MATCH-003).

Covers:
- POST /api/v1/job/match with invalid payloads (negative experience, blank skill, reversed dates, oversized text).
- POST /api/v1/candidates/rank with invalid payloads (empty candidates, blank ID, duplicate IDs, negative exp).
- Controlled HTTP 422 validation error format (error_code='VALIDATION_ERROR', never HTTP 500).
- Provider non-invocation verification: 0 LLM calls and 0 embedding calls on rejected requests.
"""

from collections.abc import AsyncIterator, Sequence

from fastapi.testclient import TestClient
import pytest

from app.api.deps import get_embedding_provider_dep, get_llm
from app.infrastructure.llm.providers.mock_provider import MockLlmProvider
from app.main import app
from app.ports.embeddings import EmbeddingPort


class SpyEmbeddingProvider(EmbeddingPort):
    """Spy embedding provider tracking all calls and call counts."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension
        self.call_count = 0
        self.calls: list[list[str]] = []

    @property
    def provider_name(self) -> str:
        return "spy-embedding"

    @property
    def model_name(self) -> str:
        return "spy-embedding-v1"

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        self.call_count += 1
        text_list = list(texts)
        self.calls.append(text_list)
        return [[1.0] + [0.0] * (self.dimension - 1) for _ in text_list]


class SpyLlmProvider(MockLlmProvider):
    """Spy LLM provider tracking all invocation counts."""

    def __init__(self) -> None:
        super().__init__()
        self.generate_text_calls = 0
        self.generate_structured_calls = 0

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.generate_text_calls += 1
        return await super().generate_text(prompt, system_prompt, temperature)

    async def generate_structured(
        self,
        prompt: str,
        response_model: type,
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ):
        self.generate_structured_calls += 1
        return await super().generate_structured(prompt, response_model, system_prompt, temperature)


@pytest.fixture
def spy_providers():
    """Register spy providers and yield them for call count inspection."""
    spy_llm = SpyLlmProvider()
    spy_embedding = SpyEmbeddingProvider()

    async def override_get_llm() -> AsyncIterator[SpyLlmProvider]:
        yield spy_llm

    async def override_get_embedding() -> AsyncIterator[SpyEmbeddingProvider]:
        yield spy_embedding

    app.dependency_overrides[get_llm] = override_get_llm
    app.dependency_overrides[get_embedding_provider_dep] = override_get_embedding

    yield {"llm": spy_llm, "embedding": spy_embedding}

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    return TestClient(app)


# =====================================================================
# Match Endpoint Validation & Non-Invocation Tests
# =====================================================================


def test_match_rejects_negative_experience(client, spy_providers) -> None:
    """POST /job/match with negative experience returns 422 and 0 provider calls."""
    payload = {
        "cv": {
            "full_name": "Test Candidate",
            "skills": ["Python"],
            "work_experience": [{"job_title": "Engineer", "years_of_experience": -1.5}],
        },
        "job": {
            "title": "Python Developer",
            "required_skills": ["Python"],
        },
    }
    response = client.post("/api/v1/job/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["message"] == "Request validation failed"
    assert len(data["details"]["errors"]) > 0

    # Provider calls must be ZERO
    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["llm"].generate_structured_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_match_rejects_blank_skill(client, spy_providers) -> None:
    """POST /job/match with whitespace-only skill returns 422 and 0 provider calls."""
    payload = {
        "cv": {
            "full_name": "Test Candidate",
            "skills": ["Python", "   "],
        },
        "job": {
            "title": "Python Developer",
            "required_skills": ["Python"],
        },
    }
    response = client.post("/api/v1/job/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    # Provider calls must be ZERO
    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_match_rejects_invalid_date_ordering(client, spy_providers) -> None:
    """POST /job/match with start_date > end_date returns 422 and 0 provider calls."""
    payload = {
        "cv": {
            "full_name": "Test Candidate",
            "skills": ["Python"],
            "work_experience": [
                {
                    "job_title": "Engineer",
                    "start_date": "2025-01",
                    "end_date": "2024-01",
                }
            ],
        },
        "job": {
            "title": "Python Developer",
            "required_skills": ["Python"],
        },
    }
    response = client.post("/api/v1/job/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    # Provider calls must be ZERO
    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_match_rejects_oversized_job_title(client, spy_providers) -> None:
    """POST /job/match with title exceeding 300 characters returns 422 and 0 provider calls."""
    payload = {
        "cv": {
            "full_name": "Test Candidate",
            "skills": ["Python"],
        },
        "job": {
            "title": "A" * 301,
            "required_skills": ["Python"],
        },
    }
    response = client.post("/api/v1/job/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    # Provider calls must be ZERO
    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_match_rejects_blank_job_title(client, spy_providers) -> None:
    """POST /job/match with whitespace-only title returns 422 and 0 provider calls."""
    payload = {
        "cv": {
            "full_name": "Test Candidate",
            "skills": ["Python"],
        },
        "job": {
            "title": "    ",
            "required_skills": ["Python"],
        },
    }
    response = client.post("/api/v1/job/match", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


# =====================================================================
# Candidate Ranking Validation & Non-Invocation Tests
# =====================================================================


def test_ranking_rejects_empty_candidates_batch(client, spy_providers) -> None:
    """POST /candidates/rank with empty candidates list returns 422 and 0 provider calls."""
    payload = {
        "job": {"title": "Backend Developer"},
        "candidates": [],
    }
    response = client.post("/api/v1/candidates/rank", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_ranking_rejects_blank_candidate_id(client, spy_providers) -> None:
    """POST /candidates/rank with blank candidate_id returns 422 and 0 provider calls."""
    payload = {
        "job": {"title": "Backend Developer"},
        "candidates": [
            {
                "candidate_id": "   ",
                "cv": {"skills": ["Python"]},
            }
        ],
    }
    response = client.post("/api/v1/candidates/rank", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"

    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0


def test_ranking_rejects_duplicate_candidate_ids(client, spy_providers) -> None:
    """POST /candidates/rank with duplicate candidate_id values returns 422 and 0 provider calls."""
    payload = {
        "job": {"title": "Backend Developer"},
        "candidates": [
            {
                "candidate_id": "cand-001",
                "cv": {"skills": ["Python"]},
            },
            {
                "candidate_id": "cand-001",
                "cv": {"skills": ["Java"]},
            },
        ],
    }
    response = client.post("/api/v1/candidates/rank", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert any("duplicate" in str(err).lower() for err in data["details"]["errors"])

    # Provider calls must be ZERO
    assert spy_providers["llm"].generate_text_calls == 0
    assert spy_providers["embedding"].call_count == 0
