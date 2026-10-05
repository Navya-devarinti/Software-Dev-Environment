from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import chat
from app.corpus.retrieval import RetrievalResult
from app.main import app

client = TestClient(app)

CATALOG_URL = "https://www.pnw.edu/academic-catalog/"
GUIDANCE = "Computer Science students must complete the published program requirements."


def catalog_evidence(
    *,
    text: str = GUIDANCE,
    metadata: dict[str, str] | None = None,
) -> RetrievalResult:
    source = SimpleNamespace(
        title="PNW Academic Catalog",
        url=CATALOG_URL,
        last_reviewed_on=date.today(),
        review_frequency="annual",
    )
    version = SimpleNamespace(
        status="current",
        effective_from=None,
        effective_to=None,
        source=source,
    )
    return RetrievalResult(
        text=text,
        locator="2026-2027 Catalog, Computer Science requirements",
        source_title=source.title,
        source_url=source.url,
        source_version=version,
        metadata={"category": "catalog", **(metadata or {})},
    )


def install_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    results: list[RetrievalResult],
) -> list[tuple[str, dict[str, Any] | None, str | None]]:
    calls: list[tuple[str, dict[str, Any] | None, str | None]] = []

    def retrieve(
        question: str,
        *,
        context: dict[str, Any] | None = None,
        category: str | None = None,
    ) -> list[RetrievalResult]:
        calls.append((question, context, category))
        return results

    monkeypatch.setattr(chat, "retrieve_evidence", retrieve)
    return calls


def ask(question: str, context: dict[str, str] | None = None) -> dict[str, Any]:
    request: dict[str, Any] = {"question": question}
    if context is not None:
        request["context"] = context
    response = client.post("/v1/chat", json=request)
    assert response.status_code == 200
    return response.json()


def test_course_offering_route_passes_all_context_and_catalog_category(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = {
        "courseCode": "CS 101",
        "campus": "Hammond",
        "term": "Fall 2026",
        "academicLevel": "undergraduate",
    }
    calls = install_retrieval(
        monkeypatch,
        [
            catalog_evidence(
                text="CS 101 is offered at Hammond in Fall 2026.",
                metadata={
                    "courseCode": "CS 101",
                    "campus": "Hammond",
                    "term": "Fall 2026",
                    "academicLevel": "undergraduate",
                },
            )
        ],
    )

    payload = ask("Where is the course CS 101 offered in Fall 2026?", context)

    assert calls == [
        (
            "Where is the course CS 101 offered in Fall 2026?",
            context,
            "catalog",
        )
    ]
    assert payload["outcome"] == "answered"
    assert payload["message"] == "CS 101 is offered at Hammond in Fall 2026."
    assert payload["citations"] == [
        {
            "title": "PNW Academic Catalog",
            "url": CATALOG_URL,
            "locator": "2026-2027 Catalog, Computer Science requirements",
        }
    ]


def test_general_program_question_uses_academic_rules_and_catalog_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = {"program": "Computer Science"}
    calls = install_retrieval(
        monkeypatch,
        [
            catalog_evidence(
                metadata={"program": "Computer Science"},
            )
        ],
    )

    payload = ask("What are the Computer Science degree requirements?", context)

    assert calls[0][1:] == (context, "catalog")
    assert payload["outcome"] == "answered"
    assert payload["message"] == GUIDANCE
    assert payload["citations"][0]["url"] == CATALOG_URL


def test_individual_graduation_question_reaches_academic_rule_and_refers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = install_retrieval(monkeypatch, [catalog_evidence()])

    payload = ask("Will I graduate?")

    assert calls == [("Will I graduate?", None, "catalog")]
    assert payload["outcome"] == "escalation_required"
    assert payload["escalation"]["office"] == "Academic Advising"
    assert payload["escalation"]["contactUrl"] == "https://www.pnw.edu/advising/"
    assert "can't determine an individual" in payload["message"]
    assert "you will graduate" not in payload["message"].casefold()


def test_academic_missing_context_and_evidence_abstain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_retrieval(monkeypatch, [catalog_evidence()])

    missing = ask("What are the graduation requirements for this program?")
    assert missing["outcome"] == "needs_context"
    assert missing["requiredContext"] == ["program"]

    absent_calls = install_retrieval(monkeypatch, [])
    unsupported = ask(
        "What are the Computer Science degree requirements?",
        {"program": "Computer Science"},
    )
    assert absent_calls
    assert unsupported["outcome"] == "cannot_verify"
    assert unsupported["citations"] == []
