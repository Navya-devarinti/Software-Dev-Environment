from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.corpus import retrieval
from app.rules.citations import make_citation

client = TestClient(app)


@pytest.fixture
def fall_deadline() -> dict:
    return {
        "term": "Fall 2026",
        "deadline_type": "add/drop",
        "date": "2026-09-08",
        "conditions": ["Refund eligibility depends on the date of withdrawal."],
        "source_title": "Fall 2026 Academic Schedule",
        "source_url": "https://www.pnw.edu/academic-calendar/",
        "locator": "Fall 2026 schedule, add/drop row",
    }


def test_retrieved_deadline_keeps_term_date_type_and_conditions(
    monkeypatch: pytest.MonkeyPatch, fall_deadline: dict
) -> None:
    evidence = SimpleNamespace(
        context={
            key: fall_deadline[key]
            for key in ("term", "deadline_type", "date", "conditions")
        },
        text="Add/drop deadline: September 8, 2026.",
        locator=fall_deadline["locator"],
    )

    class Session:
        def __enter__(self) -> Session:
            return self

        def __exit__(self, *_: object) -> None:
            pass

        def execute(self, _statement: object) -> SimpleNamespace:
            return SimpleNamespace(
                all=lambda: [
                    (evidence, fall_deadline["source_title"], "schedule", 0.1)
                ]
            )

    monkeypatch.setattr(retrieval, "embed_texts", lambda _texts: [[0.0] * 768])
    monkeypatch.setattr(retrieval, "SessionLocal", Session)

    results = retrieval.retrieve_evidence(
        "When is the add/drop deadline?",
        context={"term": fall_deadline["term"]},
    )

    assert len(results) == 1
    result = results[0]
    assert result.metadata["term"] == fall_deadline["term"]
    assert result.metadata["deadline_type"] == fall_deadline["deadline_type"]
    assert result.metadata["date"] == fall_deadline["date"]
    assert result.metadata["conditions"] == fall_deadline["conditions"]

    citation = make_citation(
        result.source_title, fall_deadline["source_url"], result.locator
    )
    assert citation == {
        "title": fall_deadline["source_title"],
        "url": fall_deadline["source_url"],
        "locator": fall_deadline["locator"],
    }


def test_retrieval_selects_the_requested_term(
    monkeypatch: pytest.MonkeyPatch, fall_deadline: dict
) -> None:
    spring_deadline = {
        **fall_deadline,
        "term": "Spring 2027",
        "date": "2027-01-25",
    }
    schedule = [fall_deadline, spring_deadline]
    rows = [
        (
            SimpleNamespace(
                context={
                    key: record[key]
                    for key in ("term", "deadline_type", "date", "conditions")
                },
                text=f"{record['term']} add/drop deadline",
                locator=record["locator"],
            ),
            record["source_title"],
            "schedule",
            0.1,
        )
        for record in schedule
    ]

    class Session:
        def __enter__(self) -> Session:
            return self

        def __exit__(self, *_: object) -> None:
            pass

        def execute(self, statement: object) -> SimpleNamespace:
            compiled = statement.compile()
            requested_term = next(
                (
                    value
                    for value in compiled.params.values()
                    if value == fall_deadline["term"]
                ),
                None,
            )
            matching_rows = [
                row
                for row in rows
                if row[0].context["term"] == requested_term
            ]
            return SimpleNamespace(all=lambda: matching_rows or rows)

    monkeypatch.setattr(retrieval, "embed_texts", lambda _texts: [[0.0] * 768])
    monkeypatch.setattr(retrieval, "SessionLocal", Session)

    results = retrieval.retrieve_evidence(
        "When is the add/drop deadline?",
        context={"term": fall_deadline["term"]},
    )

    assert [result.metadata["term"] for result in results] == [
        fall_deadline["term"]
    ]


def test_deadline_without_term_requests_clarification() -> None:
    response = client.post(
        "/v1/chat",
        json={"question": "What is the add/drop deadline?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "needs_context"
    assert "term" in payload["requiredContext"]
