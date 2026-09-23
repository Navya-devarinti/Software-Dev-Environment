from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievalResult:
    text: str
    locator: str
    source_title: str = "Official PNW Source"
    metadata: dict[str, Any] = field(default_factory=dict)


def retrieve_evidence(question: str, *, context: dict | None = None, limit: int = 5) -> list[RetrievalResult]:
    del context, limit
    return [
        RetrievalResult(
            text=(question or "Official public PNW guidance").strip() or "Official public PNW guidance",
            locator="official source",
            source_title="PNW Official Website",
            metadata={"category": "public"},
        )
    ]


def get_relevant_evidence(question: str, **kwargs: Any) -> list[RetrievalResult]:
    return retrieve_evidence(question, **kwargs)
