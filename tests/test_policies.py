from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import chat
from app.corpus.retrieval import RetrievalResult
from app.main import app

client = TestClient(app)

PARKING_URL = "https://www.pnw.edu/parking/"
PAYMENT_URL = "https://www.pnw.edu/parking/pay-citation/"
APPEAL_PDF_URL = "https://www.pnw.edu/parking/documents/citation-appeal.pdf"
GRADE_APPEAL_URL = "https://www.pnw.edu/academic-affairs/grade-appeal-policy.pdf"


def evidence(
    *,
    text: str,
    title: str,
    url: str,
    locator: str,
    related_source_url: str | None = None,
) -> RetrievalResult:
    metadata: dict[str, str] = {"category": "policy"}
    if related_source_url:
        metadata["related_source_url"] = related_source_url
    source = SimpleNamespace(
        title=title,
        url=url,
        last_reviewed_on=date.today(),
        review_frequency="annual",
    )
    source_version = SimpleNamespace(
        status="current",
        effective_from=None,
        effective_to=None,
        source=source,
    )
    return RetrievalResult(
        text=text,
        locator=locator,
        source_title=title,
        source_url=url,
        source_version=source_version,
        metadata=metadata,
    )


def install_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    results: list[RetrievalResult],
) -> list[str]:
    questions: list[str] = []

    def retrieve(question: str, *, context: dict | None = None) -> list[RetrievalResult]:
        questions.append(question)
        return results

    monkeypatch.setattr(chat, "retrieve_evidence", retrieve)
    return questions


def post_policy_question(question: str) -> dict:
    response = client.post("/v1/chat", json={"question": question})
    assert response.status_code == 200
    return response.json()


def citation_keys(payload: dict) -> set[tuple[str, str, str]]:
    return {
        (citation["title"], citation["url"], citation["locator"])
        for citation in payload["citations"]
    }


def test_policy_answer_retrieves_and_cites_relevant_linked_child_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    questions = install_retrieval(
        monkeypatch,
        [
            evidence(
                text="Parking Services handles parking citations and links to payment instructions.",
                title="Parking Services",
                url=PARKING_URL,
                locator="Parking citations section",
            ),
            evidence(
                text="Pay a parking citation online through the PNW Parking Portal using the citation number.",
                title="Pay a Parking Citation",
                url=PAYMENT_URL,
                locator="Payment instructions",
                related_source_url=PARKING_URL,
            ),
        ],
    )

    payload = post_policy_question("How do I pay a parking citation?")

    assert questions == ["How do I pay a parking citation?"]
    assert payload["outcome"] == "answered"
    assert "Parking Portal" in payload["message"]
    assert "citation number" in payload["message"]
    assert {
        ("Parking Services", PARKING_URL, "Parking citations section"),
        ("Pay a Parking Citation", PAYMENT_URL, "Payment instructions"),
    } <= citation_keys(payload)


def test_policy_answer_preserves_and_cites_linked_pdf_instructions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    questions = install_retrieval(
        monkeypatch,
        [
            evidence(
                text="Parking Services provides information about appealing parking citations.",
                title="Parking Services",
                url=PARKING_URL,
                locator="Citation appeals section",
            ),
            evidence(
                text="Submit an appeal through the PNW Parking Portal within 10 calendar days of the citation.",
                title="Parking Citation Appeal Instructions",
                url=APPEAL_PDF_URL,
                locator="PDF page 2, Appeal submission",
                related_source_url=PARKING_URL,
            ),
        ],
    )

    payload = post_policy_question("How can I appeal a parking citation?")

    assert questions == ["How can I appeal a parking citation?"]
    assert payload["outcome"] == "answered"
    assert "Parking Portal" in payload["message"]
    assert "10 calendar days" in payload["message"]
    assert {
        ("Parking Services", PARKING_URL, "Citation appeals section"),
        (
            "Parking Citation Appeal Instructions",
            APPEAL_PDF_URL,
            "PDF page 2, Appeal submission",
        ),
    } <= citation_keys(payload)


def test_policy_explanation_is_bounded_and_includes_supported_next_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    questions = install_retrieval(
        monkeypatch,
        [
            evidence(
                text=(
                    "Students first discuss the grade with the instructor. If unresolved, "
                    "submit a written appeal with supporting documentation to the "
                    "department chair within 10 working days."
                ),
                title="Grade Appeal Policy",
                url=GRADE_APPEAL_URL,
                locator="PDF page 3, Appeal procedure",
            )
        ],
    )

    payload = post_policy_question("What are the steps in the grade appeal process?")
    message = payload["message"].lower()

    assert questions == ["What are the steps in the grade appeal process?"]
    assert payload["outcome"] == "answered"
    assert "instructor" in message
    assert "written appeal" in message
    assert "supporting documentation" in message
    assert "department chair" in message
    assert "10 working days" in message
    assert "guaranteed approval" not in message
    assert "automatic approval" not in message
    assert citation_keys(payload) == {
        ("Grade Appeal Policy", GRADE_APPEAL_URL, "PDF page 3, Appeal procedure")
    }


def test_parking_ticket_answer_explains_payment_and_appeal_with_each_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    questions = install_retrieval(
        monkeypatch,
        [
            evidence(
                text="Pay online through the PNW Parking Portal using the citation number.",
                title="Pay a Parking Citation",
                url=PAYMENT_URL,
                locator="Payment instructions",
                related_source_url=PARKING_URL,
            ),
            evidence(
                text="Submit an appeal through the PNW Parking Portal within 10 calendar days of the citation.",
                title="Parking Citation Appeal Instructions",
                url=APPEAL_PDF_URL,
                locator="PDF page 2, Appeal submission",
                related_source_url=PARKING_URL,
            ),
        ],
    )

    payload = post_policy_question("How do I pay or appeal a parking ticket?")
    message = payload["message"]

    assert questions == ["How do I pay or appeal a parking ticket?"]
    assert payload["outcome"] == "answered"
    assert "Parking Portal" in message
    assert "citation number" in message
    assert "10 calendar days" in message
    assert {
        ("Pay a Parking Citation", PAYMENT_URL, "Payment instructions"),
        (
            "Parking Citation Appeal Instructions",
            APPEAL_PDF_URL,
            "PDF page 2, Appeal submission",
        ),
    } <= citation_keys(payload)
