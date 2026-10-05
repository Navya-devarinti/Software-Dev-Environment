from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api import chat
from app.corpus.retrieval import RetrievalResult
from app.main import app

client = TestClient(app)

CATALOG_URL = "https://www.pnw.edu/academic-catalog/"
GRADUATION_GUIDANCE = (
    "Students must complete the requirements published for their academic "
    "program before applying for graduation."
)


def catalog_evidence(text: str = GRADUATION_GUIDANCE) -> RetrievalResult:
    source = SimpleNamespace(
        title="PNW Academic Catalog",
        url=CATALOG_URL,
        category="catalog",
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
        locator="2026-2027 Catalog, Graduation Requirements",
        source_title=source.title,
        source_url=source.url,
        source_version=source_version,
        metadata={
            "category": "catalog",
            "program": "Computer Science",
            "academicLevel": "undergraduate",
        },
    )


def install_evidence(
    monkeypatch: pytest.MonkeyPatch,
    evidence: list[RetrievalResult],
) -> None:
    monkeypatch.setattr(
        chat,
        "retrieve_evidence",
        lambda *_args, **_kwargs: evidence,
    )


def ask(question: str, *, context: dict[str, str] | None = None) -> dict:
    request: dict[str, object] = {"question": question}
    if context is not None:
        request["context"] = context
    response = client.post("/v1/chat", json=request)
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize(
    ("question", "required_context"),
    [
        ("What requirements apply to this program?", {"program"}),
        (
            "What are the graduation requirements for my program at this campus?",
            {"program", "campus"},
        ),
        (
            "What are the graduation requirements for the graduate academic level?",
            {"academicLevel"},
        ),
    ],
)
def test_program_and_graduation_questions_request_missing_public_context(
    monkeypatch: pytest.MonkeyPatch,
    question: str,
    required_context: set[str],
) -> None:
    install_evidence(monkeypatch, [catalog_evidence()])

    payload = ask(question)

    assert payload["outcome"] == "needs_context"
    assert required_context <= set(payload["requiredContext"])


def test_individual_graduation_eligibility_is_referred_without_a_determination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_evidence(monkeypatch, [catalog_evidence()])

    payload = ask(
        "Am I eligible to graduate?",
        context={"academicLevel": "undergraduate"},
    )

    assert payload["outcome"] == "escalation_required"
    assert payload["escalation"]["office"] == "Academic Advising"
    assert payload["escalation"]["contactUrl"] == "https://www.pnw.edu/advising/"
    _assert_no_individual_graduation_determination(payload["message"])


def test_general_public_requirements_are_answered_from_catalog_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_evidence(monkeypatch, [catalog_evidence()])
    context = {
        "program": "Computer Science",
        "academicLevel": "undergraduate",
    }

    general = ask(
        "What are the general published graduation requirements for this program?",
        context=context,
    )

    assert general["outcome"] == "answered"
    assert GRADUATION_GUIDANCE in general["message"]
    assert {
        "title": "PNW Academic Catalog",
        "url": CATALOG_URL,
        "locator": "2026-2027 Catalog, Graduation Requirements",
    } in general["citations"]


def test_can_i_graduate_question_is_not_answered_as_a_public_requirement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_evidence(monkeypatch, [catalog_evidence()])

    payload = ask(
        "Can I graduate from this program?",
        context={
            "program": "Computer Science",
            "academicLevel": "undergraduate",
        },
    )

    assert payload["outcome"] == "escalation_required"
    assert payload["escalation"]["office"] == "Academic Advising"
    _assert_no_individual_graduation_determination(payload["message"])


@pytest.mark.parametrize(
    "question",
    [
        "Will I graduate this year?",
        "Do I meet the graduation requirements?",
        "Have I completed enough credits to graduate?",
        "What is my graduation status?",
    ],
)
def test_personal_graduation_determinations_are_referred_before_context_prompts(
    monkeypatch: pytest.MonkeyPatch,
    question: str,
) -> None:
    install_evidence(monkeypatch, [catalog_evidence()])

    payload = ask(question)

    assert payload["outcome"] == "escalation_required"
    assert payload["escalation"]["office"] == "Academic Advising"
    _assert_no_individual_graduation_determination(payload["message"])


@pytest.mark.parametrize(
    "question",
    [
        "What are the Computer Science degree requirements?",
        "What are the graduation requirements for this program?",
    ],
)
def test_public_requirements_are_not_classified_as_individual_determinations(
    question: str,
) -> None:
    assert not chat._is_individual_graduation_question(question)
    assert chat._is_general_public_requirement_question(question)


def test_insufficient_evidence_cannot_establish_individual_graduation_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_evidence(monkeypatch, [])

    payload = ask(
        "Can I graduate if I still need one course?",
        context={
            "courseCode": "CS 400",
            "academicLevel": "undergraduate",
        },
    )

    assert payload["outcome"] in {"cannot_verify", "escalation_required"}
    _assert_no_individual_graduation_determination(payload["message"])


def _assert_no_individual_graduation_determination(message: str) -> None:
    normalized = message.casefold()
    prohibited_claims = (
        "you are eligible",
        "you are not eligible",
        "you can graduate",
        "you cannot graduate",
        "approved to graduate",
        "you are approved",
        "you have been approved",
        "denied graduation",
        "you are denied",
        "you have been denied",
        "waiver granted",
        "waiver denied",
        "your waiver is approved",
        "your waiver was denied",
        "you meet all requirements",
        "you do not meet all requirements",
        "you qualify to graduate",
        "you do not qualify to graduate",
    )
    assert not any(claim in normalized for claim in prohibited_claims)
