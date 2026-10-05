from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.corpus import retrieval


def source(
    *,
    source_id: int,
    title: str,
    url: str,
    related_source: SimpleNamespace | None = None,
    related_source_id: int | None = None,
) -> SimpleNamespace:
    item = SimpleNamespace(
        id=source_id,
        title=title,
        url=url,
        category="policy",
        related_source_id=related_source_id,
        related_source=related_source,
        related_sources=[],
        last_reviewed_on=date.today(),
        review_frequency="annual",
    )
    if related_source is not None:
        related_source.related_sources.append(item)
    return item


def evidence(
    *,
    evidence_id: int,
    text: str,
    locator: str,
    source: SimpleNamespace,
) -> SimpleNamespace:
    version = SimpleNamespace(
        status="current",
        effective_from=None,
        effective_to=None,
        source=source,
    )
    return SimpleNamespace(
        id=evidence_id,
        text=text,
        locator=locator,
        context={},
        source_version=version,
    )


def test_policy_retrieval_expands_related_sources_and_keeps_source_locators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = source(
        source_id=1,
        title="Parking Services",
        url="https://www.pnw.edu/parking/",
    )
    child = source(
        source_id=2,
        title="Pay a Parking Citation",
        url="https://www.pnw.edu/parking/pay-citation/",
        related_source=parent,
        related_source_id=parent.id,
    )
    pdf = source(
        source_id=3,
        title="Parking Citation Appeal Instructions",
        url="https://www.pnw.edu/parking/citation-appeal.pdf",
        related_source=parent,
        related_source_id=parent.id,
    )
    parent.related_sources = [child, pdf]

    parent_evidence = evidence(
        evidence_id=10,
        text="Parking Services manages parking citations.",
        locator="Parking citations section",
        source=parent,
    )
    child_evidence = evidence(
        evidence_id=11,
        text="Pay online using the citation number.",
        locator="Payment instructions",
        source=child,
    )
    pdf_evidence = evidence(
        evidence_id=12,
        text="Appeal within 10 calendar days.",
        locator="PDF page 2, Appeal submission",
        source=pdf,
    )

    class Session:
        statements: list[object] = []

        def __enter__(self) -> Session:
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def execute(self, statement: object) -> SimpleNamespace:
            self.statements.append(statement)
            if len(self.statements) == 1:
                rows = [(parent_evidence, parent.title, parent.category, 0.1)]
            else:
                rows = [
                    (child_evidence, child.title, child.category, 0.2),
                    (pdf_evidence, pdf.title, pdf.category, 0.3),
                    (parent_evidence, parent.title, parent.category, 0.4),
                ]
            return SimpleNamespace(all=lambda: rows)

    session = Session()
    monkeypatch.setattr(retrieval, "SessionLocal", lambda: session)
    monkeypatch.setattr(retrieval, "embed_texts", lambda _texts: [[0.0] * 768])

    results = retrieval.retrieve_evidence(
        "How do I pay or appeal a parking citation?",
        context={"program": "Computer Science"},
        category="policy",
    )

    assert len(session.statements) == 2
    related_query = session.statements[1]
    compiled_related_query = related_query.compile()
    assert "program" in compiled_related_query.params.values()
    assert "Computer Science" in compiled_related_query.params.values()
    related_query_sql = str(related_query)
    assert "related_source_id" in related_query_sql
    assert "source_versions.status" in related_query_sql
    assert "last_reviewed_on" in related_query_sql
    assert "effective_from" in related_query_sql
    assert "effective_to" in related_query_sql
    assert [(item.source_title, item.locator) for item in results] == [
        ("Parking Services", "Parking citations section"),
        ("Pay a Parking Citation", "Payment instructions"),
        ("Parking Citation Appeal Instructions", "PDF page 2, Appeal submission"),
    ]
    assert results[0].source_url == parent.url
    assert results[0].metadata["related_sources"] == [
        {"title": child.title, "url": child.url},
        {"title": pdf.title, "url": pdf.url},
    ]
    assert results[1].source_url == child.url
    assert results[1].metadata["related_source"] == {
        "title": parent.title,
        "url": parent.url,
    }
