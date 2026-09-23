from __future__ import annotations

from typing import Any


class EmbeddingProvider:
    """Simple explicit embedding provider used by the retrieval boundary."""

    def __init__(self, *, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        return [0.0 for _ in range(self.dimensions)] if text else []


def generate_embedding(text: str, *, provider: EmbeddingProvider | None = None) -> list[float]:
    provider = provider or EmbeddingProvider()
    return provider.embed(text)


def persist_embeddings(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return records
