"""Embedding infrastructure package and provider implementations."""

from app.infrastructure.embeddings.factory import get_embedding_provider

__all__ = ["get_embedding_provider"]
