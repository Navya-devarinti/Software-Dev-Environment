
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select

from app.corpus.database import SessionLocal
from app.corpus.embeddings import embed_texts
from app.corpus.models import Evidence, Source, SourceVersion, SourceVersionStatus


@dataclass
class RetrievalResult:
    text: str
    locator: str
    source_title: str = "Official PNW Source"
    metadata: dict[str, Any] = field(default_factory=dict)


def retrieve_evidence(
    question: str,
    *,
    context: dict | None = None,
    limit: int = 5,
) -> list[RetrievalResult]:
    """Retrieve relevant evidence from PostgreSQL using vector similarity."""
    del context  # Metadata filtering can be added later.

    question = (question or "").strip()
    if not question or limit < 1:
        return []

    query_vector = embed_texts([question])[0]
    cosine_distance = Evidence.embedding.cosine_distance(query_vector)

    statement = (
        select(
            Evidence,
            Source.title,
            Source.category,
            cosine_distance.label("distance"),
        )
        .join(
            SourceVersion,
            Evidence.source_version_id == SourceVersion.id,
        )
        .join(Source, SourceVersion.source_id == Source.id)
        .where(
            SourceVersion.status == SourceVersionStatus.CURRENT,
            Evidence.embedding.is_not(None),
        )
        .order_by(cosine_distance.asc())
        .limit(limit)
    )

    with SessionLocal() as session:
        rows = session.execute(statement).all()

    results = []
    for evidence, source_title, category, distance in rows:
        metadata = dict(evidence.context or {})
        metadata["category"] = category
        metadata["cosine_distance"] = float(distance)

        results.append(
            RetrievalResult(
                text=evidence.text,
                locator=evidence.locator,
                source_title=source_title,
                metadata=metadata,
            )
        )

    return results


def get_relevant_evidence(
    question: str,
    **kwargs: Any,
) -> list[RetrievalResult]:
    """Compatibility wrapper for existing callers."""
    return retrieve_evidence(question, **kwargs)
