from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api import chat
from app.corpus.models import Evidence, Source, SourceVersion, SourceVersionStatus
from app.corpus.retrieval import RetrievalResult
from app.main import app

client = TestClient(app)


@pytest.fixture
def schedule_evidence() -> Evidence:
    source = Source(
        title="Fall 2026 Academic Schedule",
        url="https://www.pnw.edu/academic-calendar/",
        category="schedule",
        owner_office="Registrar",
        review_frequency="term",
        last_reviewed_on=date(2026, 10, 1),
    )
    version = SourceVersion(
        source=source,
        status=SourceVersionStatus.CURRENT,
        effective_from=date(2026, 8, 1),
        effective_to=date(2026, 12, 31),
    )
    return Evidence(
        source_version=version,
        text="Add/drop deadline: September 8, 2026.",
        locator="Fall 2026 schedule, add/drop row",
        context={
            "term": "Fall 2026",
            "deadline_type": "add/drop",
            "date": "2026-09-08",
            "conditions": ["Refund eligibility depends on the withdrawal date."],
        },
    )


def retrieved_schedule(evidence: Evidence) -> RetrievalResult:
    source = evidence.source_version.source
    return RetrievalResult(
        text=evidence.text,
        locator=evidence.locator,
        source_title=source.title,
        source_url=source.url,
        source_version=evidence.source_version,
        metadata={**evidence.context, "category": source.category},
    )


def test_chat_returns_cited_term_specific_deadline(
    monkeypatch: pytest.MonkeyPatch, schedule_evidence: Evidence
) -> None:
    calls: list[tuple[str, dict]] = []

    def retrieve(question: str, *, context: dict) -> list[RetrievalResult]:
        calls.append((question, context))
        return [retrieved_schedule(schedule_evidence)]

    monkeypatch.setattr(chat, "retrieve_evidence", retrieve)

    response = client.post(
        "/v1/chat",
        json={
            "question": "When is the add/drop deadline?",
            "context": {"term": "Fall 2026"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "answered"
    assert "Fall 2026" in payload["message"]
    assert "September 8, 2026" in payload["message"]
    assert "Refund eligibility depends on the withdrawal date." in payload["message"]
    assert payload["citations"] == [
        {
            "title": "Fall 2026 Academic Schedule",
            "url": "https://www.pnw.edu/academic-calendar/",
            "locator": "Fall 2026 schedule, add/drop row",
        }
    ]
    assert calls == [
        ("When is the add/drop deadline?", {"term": "Fall 2026"})
    ]


def test_chat_requests_term_before_retrieving_deadlines(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_retrieved(*_args: object, **_kwargs: object) -> list[object]:
        pytest.fail("deadline retrieval must wait for term context")

    monkeypatch.setattr(chat, "retrieve_evidence", fail_if_retrieved)

    response = client.post(
        "/v1/chat",
        json={"question": "What is the add/drop deadline?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "needs_context"
    assert payload["requiredContext"] == ["term"]
    assert "term" in payload["message"].lower()
    assert payload["citations"] == []


def test_chat_refers_when_deadline_evidence_is_stale(
    monkeypatch: pytest.MonkeyPatch, schedule_evidence: Evidence
) -> None:
    schedule_evidence.source_version.source.last_reviewed_on = date(2026, 5, 1)
    monkeypatch.setattr(
        chat,
        "retrieve_evidence",
        lambda *_args, **_kwargs: [retrieved_schedule(schedule_evidence)],
    )

    response = client.post(
        "/v1/chat",
        json={
            "question": "When is the add/drop deadline?",
            "context": {"term": "Fall 2026"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "escalation_required"
    assert "September 8" not in payload["message"]
    assert payload["citations"] == []
    assert payload["escalation"]["office"] == "Registrar's Office"
    assert payload["escalation"]["contactUrl"] == "https://www.pnw.edu/registrar/"
