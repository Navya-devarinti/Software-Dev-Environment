"""Real dense text embeddings using FastEmbed."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

MODEL_NAME = "BAAI/bge-base-en-v1.5"
EMBEDDING_DIMENSIONS = 768


@lru_cache(maxsize=1)
def _load_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Cannot embed empty text")

    vectors = [
        vector.tolist()
        for vector in _load_model().embed(texts)
    ]

    if len(vectors) != len(texts):
        raise RuntimeError("Embedding model returned an unexpected result count")

    for vector in vectors:
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"Expected {EMBEDDING_DIMENSIONS} dimensions, "
                f"received {len(vector)}"
            )

    return vectors


class EmbeddingProvider:
    """Compatibility wrapper for callers using the original provider class."""

    def __init__(
        self,
        *,
        dimensions: int = EMBEDDING_DIMENSIONS,
    ) -> None:
        if dimensions != EMBEDDING_DIMENSIONS:
            raise ValueError(
                f"This database schema requires {EMBEDDING_DIMENSIONS}-dimensional vectors"
            )
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        if not text.strip():
            return []
        return embed_texts([text])[0]


def generate_embedding(
    text: str,
    *,
    provider: EmbeddingProvider | None = None,
) -> list[float]:
    provider = provider or EmbeddingProvider()
    return provider.embed(text)


def persist_embeddings(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Retain the existing compatibility interface."""
    return records
