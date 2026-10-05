
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.corpus.database import SessionLocal
from app.corpus.embeddings import embed_texts
from app.corpus.models import Evidence, Source, SourceVersion, SourceVersionStatus

POLICY_CATEGORIES = ("policy", "procedure")


@dataclass
class RetrievalResult:
    text: str
    locator: str
    source_title: str = "Official PNW Source"
    source_url: str | None = None
    source_version: SourceVersion | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def retrieve_evidence(
    question: str,
    *,
    context: dict | None = None,
    limit: int = 5,
    category: str | None = None,
) -> list[RetrievalResult]:
    """Retrieve current evidence, expanding policy hits to reviewed related sources."""

    question = (question or "").strip()
    if not question or limit < 1:
        return []

    requested_term = (context or {}).get("term")
    if isinstance(requested_term, str):
        requested_term = requested_term.strip()
    query_vector = embed_texts([question])[0]
    cosine_distance = Evidence.embedding.cosine_distance(query_vector)

    statement = select(
        Evidence,
        Source.title,
        Source.category,
        cosine_distance.label("distance"),
    ).join(
        SourceVersion,
        Evidence.source_version_id == SourceVersion.id,
    ).join(Source, SourceVersion.source_id == Source.id).where(
        SourceVersion.status == SourceVersionStatus.CURRENT,
        Evidence.embedding.is_not(None),
    ).options(
        selectinload(Evidence.source_version)
        .selectinload(SourceVersion.source)
        .selectinload(Source.related_source),
        selectinload(Evidence.source_version)
        .selectinload(SourceVersion.source)
        .selectinload(Source.related_sources),
    )

    policy_retrieval = (category or "").strip().lower() in POLICY_CATEGORIES
    if policy_retrieval:
        statement = statement.where(
            func.lower(Source.category).in_(POLICY_CATEGORIES),
            *_policy_eligibility_conditions(date.today()),
        )
        statement = _apply_context_filters(
            statement,
            context,
            fields=("campus", "program", "term", "courseCode", "academicLevel"),
        )
    elif (category or "").strip().lower() == "catalog":
        statement = statement.where(func.lower(Source.category) == "catalog")
        statement = _apply_context_filters(
            statement,
            context,
            fields=("campus", "program", "courseCode", "academicLevel"),
        )

    if requested_term:
        evidence_term = Evidence.context["term"].as_string()
        statement = statement.where(
            or_(
                evidence_term == requested_term,
                and_(
                    Source.category != "schedule",
                    evidence_term.is_(None),
                ),
            )
        )
    statement = (
        statement.order_by(cosine_distance.asc())
        .limit(limit)
    )

    with SessionLocal() as session:
        rows = session.execute(statement).all()
        results = _make_results(rows)

        if policy_retrieval:
            related_source_ids = _related_policy_source_ids(rows)
            if related_source_ids:
                related_statement = select(
                    Evidence,
                    Source.title,
                    Source.category,
                    cosine_distance.label("distance"),
                ).join(
                    SourceVersion,
                    Evidence.source_version_id == SourceVersion.id,
                ).join(
                    Source,
                    SourceVersion.source_id == Source.id,
                ).where(
                    SourceVersion.status == SourceVersionStatus.CURRENT,
                    Evidence.embedding.is_not(None),
                    func.lower(Source.category).in_(POLICY_CATEGORIES),
                    *_policy_eligibility_conditions(date.today()),
                    or_(
                        Source.id.in_(related_source_ids),
                        Source.related_source_id.in_(related_source_ids),
                    ),
                )
                related_statement = _apply_context_filters(
                    related_statement,
                    context,
                    fields=("campus", "program", "term", "courseCode", "academicLevel"),
                )
                if requested_term:
                    evidence_term = Evidence.context["term"].as_string()
                    related_statement = related_statement.where(
                        or_(
                            evidence_term == requested_term,
                            and_(
                                Source.category != "schedule",
                                evidence_term.is_(None),
                            ),
                        )
                    )
                related_statement = (
                    related_statement.options(
                        selectinload(Evidence.source_version)
                        .selectinload(SourceVersion.source)
                        .selectinload(Source.related_source),
                        selectinload(Evidence.source_version)
                        .selectinload(SourceVersion.source)
                        .selectinload(Source.related_sources),
                    )
                    .order_by(cosine_distance.asc())
                    .limit(limit)
                )
                related_rows = session.execute(related_statement).all()
                results = _merge_results(results, _make_results(related_rows))

    return results


def get_relevant_evidence(
    question: str,
    **kwargs: Any,
) -> list[RetrievalResult]:
    """Compatibility wrapper for existing callers."""
    return retrieve_evidence(question, **kwargs)


def _policy_eligibility_conditions(today: date) -> tuple[Any, ...]:
    frequency = func.lower(Source.review_frequency)
    freshness = or_(
        and_(
            or_(frequency.like("%daily%"), frequency.like("%day%")),
            Source.last_reviewed_on >= today - timedelta(days=1),
        ),
        and_(
            or_(frequency.like("%term%"), frequency.like("%semester%")),
            Source.last_reviewed_on >= today - timedelta(days=120),
        ),
        and_(
            or_(frequency.like("%annual%"), frequency.like("%year%")),
            Source.last_reviewed_on >= today - timedelta(days=365),
        ),
    )
    effective_period = and_(
        or_(SourceVersion.effective_from.is_(None), SourceVersion.effective_from <= today),
        or_(SourceVersion.effective_to.is_(None), SourceVersion.effective_to >= today),
    )
    return (
        Source.last_reviewed_on.is_not(None),
        freshness,
        effective_period,
    )


def _apply_context_filters(
    statement: Any,
    context: dict | None,
    *,
    fields: tuple[str, ...],
) -> Any:
    if not isinstance(context, dict):
        return statement

    for field in fields:
        value = context.get(field)
        if isinstance(value, str) and value.strip():
            evidence_context = Evidence.context[field].as_string()
            statement = statement.where(
                or_(
                    evidence_context == value.strip(),
                    evidence_context.is_(None),
                )
            )
    return statement


def _apply_catalog_context_filters(statement: Any, context: dict | None) -> Any:
    return _apply_context_filters(
        statement,
        context,
        fields=("campus", "program", "courseCode", "academicLevel"),
    )


def _related_policy_source_ids(rows: list[Any]) -> set[int]:
    source_ids: set[int] = set()
    for row in rows:
        evidence = row[0]
        version = getattr(evidence, "source_version", None)
        source = getattr(version, "source", None)
        source_category = (getattr(source, "category", "") or "").lower()
        if source is None or source_category not in POLICY_CATEGORIES:
            continue

        source_id = getattr(source, "id", None)
        parent_id = getattr(source, "related_source_id", None)
        if isinstance(source_id, int):
            source_ids.add(source_id)
        if isinstance(parent_id, int):
            source_ids.add(parent_id)

    return source_ids


def _make_results(rows: list[Any]) -> list[RetrievalResult]:
    results = []
    for evidence, source_title, category, distance in rows:
        metadata = dict(evidence.context or {})
        metadata["category"] = category
        metadata["cosine_distance"] = float(distance)
        source_version = getattr(evidence, "source_version", None)
        source = getattr(source_version, "source", None)
        source_url = getattr(source, "url", None)
        if isinstance(source_url, str):
            metadata["source_url"] = source_url

        related_source = getattr(source, "related_source", None)
        if related_source is not None:
            metadata["related_source"] = {
                "title": related_source.title,
                "url": related_source.url,
            }
        related_sources = getattr(source, "related_sources", None)
        if related_sources:
            metadata["related_sources"] = [
                {"title": related.title, "url": related.url}
                for related in related_sources
            ]

        results.append(
            RetrievalResult(
                text=evidence.text,
                locator=evidence.locator,
                source_title=source_title,
                source_url=source_url,
                source_version=source_version,
                metadata=metadata,
            )
        )

    return results


def _merge_results(
    initial: list[RetrievalResult],
    related: list[RetrievalResult],
) -> list[RetrievalResult]:
    merged = list(initial)
    seen = {
        (result.source_title, result.source_url, result.locator, result.text)
        for result in initial
    }
    for result in related:
        key = (result.source_title, result.source_url, result.locator, result.text)
        if key not in seen:
            merged.append(result)
            seen.add(key)
    return merged
