"""Unit tests for MockEmbeddingProvider and embedding factory (Task C)."""

import math

from app.core.config import Settings
from app.infrastructure.embeddings.factory import get_embedding_provider
from app.infrastructure.embeddings.providers.mock_provider import MockEmbeddingProvider


async def test_mock_embedding_provider_metadata():
    """Verify mock embedding provider identifiers."""
    provider = MockEmbeddingProvider(dimension=64)
    assert provider.provider_name == "mock"
    assert provider.model_name == "mock-hash-64"


async def test_mock_embedding_determinism_and_normalization():
    """Verify deterministic hashing and unit normalization across calls."""
    provider = MockEmbeddingProvider(dimension=64)

    text = "Python FastAPI Backend Developer"
    vectors_1 = await provider.embed_texts([text])
    vectors_2 = await provider.embed_texts([text])

    assert len(vectors_1) == 1
    assert len(vectors_2) == 1
    vec1 = vectors_1[0]
    vec2 = vectors_2[0]

    # Deterministic: identical output for identical input
    assert vec1 == vec2
    assert len(vec1) == 64

    # Unit-normalized (Euclidean norm ~ 1.0)
    norm = math.sqrt(sum(x * x for x in vec1))
    assert math.isclose(norm, 1.0, rel_tol=1e-4)


async def test_mock_embedding_preserves_batch_ordering():
    """Verify batch embed_texts returns vectors matching input sequence."""
    provider = MockEmbeddingProvider(dimension=64)
    texts = [
        "Backend Python",
        "Frontend React",
        "DevOps Kubernetes",
    ]

    batch_vectors = await provider.embed_texts(texts)
    assert len(batch_vectors) == 3

    # Independent single calls must produce identical vectors at each position
    for idx, text in enumerate(texts):
        single_vector = (await provider.embed_texts([text]))[0]
        assert batch_vectors[idx] == single_vector


async def test_mock_embedding_distinct_inputs_differ():
    """Verify distinct inputs produce distinct embedding vectors."""
    provider = MockEmbeddingProvider(dimension=64)
    vectors = await provider.embed_texts(["Python", "Kubernetes"])
    assert vectors[0] != vectors[1]


def test_embedding_factory_returns_mock_provider():
    """Verify factory returns MockEmbeddingProvider when configured."""
    settings = Settings(ENV="development", EMBEDDING_PROVIDER="mock")
    provider = get_embedding_provider(settings)
    assert isinstance(provider, MockEmbeddingProvider)
    assert provider.provider_name == "mock"
