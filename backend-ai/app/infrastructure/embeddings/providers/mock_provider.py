"""Deterministic mock embedding provider for offline development, testing, and CI."""

from collections.abc import Sequence
import hashlib
import math
import struct

from app.ports.embeddings import EmbeddingPort


class MockEmbeddingProvider(EmbeddingPort):
    """
    Deterministic offline embedding provider using cryptographic SHA-256 token hashing.

    Produces fixed-dimension, unit-normalized vectors stable across Python processes
    without network calls or external dependencies.

    NOTE: Intended strictly for unit tests, CI, and deterministic regression testing.
    Must NOT be used to claim semantic retrieval quality over baseline.
    """

    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "mock"

    @property
    def model_name(self) -> str:
        """Return mock model identifier."""
        return f"mock-hash-{self._dimension}"

    async def aclose(self) -> None:
        """No-op cleanup for mock provider."""
        return

    def _embed_single(self, text: str) -> list[float]:
        """Compute a deterministic, unit-normalized vector for a single string."""
        normalized = text.strip().lower()
        if not normalized:
            normalized = "__empty__"

        # Generate deterministic float components using sequential SHA-256 blocks
        raw_values: list[float] = []
        block_idx = 0
        while len(raw_values) < self._dimension:
            seed_bytes = f"{block_idx}:{normalized}".encode()
            digest = hashlib.sha256(seed_bytes).digest()  # 32 bytes
            # Unpack 16 signed 16-bit integers per block
            ints = struct.unpack("<16h", digest)
            for val in ints:
                if len(raw_values) < self._dimension:
                    raw_values.append(float(val))
            block_idx += 1

        # Normalize to unit length (L2 norm = 1.0)
        norm = math.sqrt(sum(x * x for x in raw_values))
        if norm == 0.0:
            return [0.0] * self._dimension

        return [round(x / norm, 6) for x in raw_values]

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embedding vectors for sequence of texts preserving input ordering."""
        return [self._embed_single(t) for t in texts]
