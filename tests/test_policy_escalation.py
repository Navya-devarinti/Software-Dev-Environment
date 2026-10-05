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
APPEAL_PDF_URL = "https://www.pnw.edu/parking/documents/citation-appeal.pdf"


@pytest.fixture
def parking_policy_evidence() -> RetrievalResult:
    source = SimpleNamespace(
        title="Parking Citation Appeal Instructions",
        url=APPEAL_PDF_URL,
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
        text=(
            "Submit a parking citation appeal through the PNW Parking Portal "
            "within 10 calendar days of the citation."
        ),
        locator="PDF page 2, Appeal submission",
        source_title="Parking Citation Appeal Instructions",
        source_url=APPEAL_PDF_URL,
        source_version=source_version,
        metadata={
            "category": "policy",
            "related_source_url": PARKING_URL,
        },
    )


def test_individual_parking_appeal_outcome_is_not_determined_and_is_referred(
    monkeypatch: pytest.MonkeyPatch,
    parking_policy_evidence: RetrievalResult,
) -> None:
    monkeypatch.setattr(
        chat,
        "retrieve_evidence",
        lambda *_args, **_kwargs: [parking_policy_evidence],
    )

    response = client.post(
        "/v1/chat",
        json={
            "question": (
                "Will my parking citation appeal be approved if I submit it today?"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "escalation_required"
    assert "10 calendar days" in payload["message"]
    assert not any(
        definitive in payload["message"].lower()
        for definitive in (
            "your appeal will be approved",
            "your appeal is approved",
            "your appeal will be denied",
            "your appeal is denied",
        )
    )
    assert {
        "title": "Parking Citation Appeal Instructions",
        "url": APPEAL_PDF_URL,
        "locator": "PDF page 2, Appeal submission",
    } in payload["citations"]
    assert payload["escalation"]["office"] == "Parking Services"
    assert payload["escalation"]["contactUrl"] == PARKING_URL


def test_personal_policy_question_routes_to_supported_office_without_guessing(
    monkeypatch: pytest.MonkeyPatch,
    parking_policy_evidence: RetrievalResult,
) -> None:
    monkeypatch.setattr(
        chat,
        "retrieve_evidence",
        lambda *_args, **_kwargs: [parking_policy_evidence],
    )

    response = client.post(
        "/v1/chat",
        json={
            "question": (
                "Can Parking Services waive my ticket because the sign was obscured?"
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["outcome"] == "escalation_required"
    assert payload["escalation"]["office"] == "Parking Services"
    assert payload["escalation"]["contactUrl"] == PARKING_URL
    assert "waive my ticket" not in payload["message"].lower()
    assert "sign was obscured" not in payload["message"].lower()
