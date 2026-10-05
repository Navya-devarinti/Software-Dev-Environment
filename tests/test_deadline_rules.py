from datetime import date

import pytest

import app.main
from app.corpus.models import Evidence, Source, SourceVersion, SourceVersionStatus
from app.rules.deadlines import evaluate_deadline

TODAY = date(2026, 10, 4)


@pytest.fixture
def schedule_evidence_factory():
    def create(
        *,
        term: str = "Fall 2026",
        status: SourceVersionStatus = SourceVersionStatus.CURRENT,
        last_reviewed_on: date = date(2026, 10, 1),
        effective_to: date | None = date(2026, 12, 31),
        context_overrides: dict | None = None,
    ) -> Evidence:
        source = Source(
            title="Fall 2026 Academic Schedule",
            url="https://www.pnw.edu/academic-calendar/",
            category="schedule",
            owner_office="Registrar",
            review_frequency="term",
            last_reviewed_on=last_reviewed_on,
        )
        version = SourceVersion(
            source=source,
            status=status,
            effective_from=date(2026, 8, 1),
            effective_to=effective_to,
        )
        context = {
            "term": term,
            "deadline_type": "add/drop",
            "date": "2026-09-08",
            "conditions": ["Refund eligibility depends on the withdrawal date."],
        }
        context.update(context_overrides or {})
        return Evidence(
            source_version=version,
            text="Add/drop deadline: September 8, 2026.",
            locator="Fall 2026 schedule, add/drop row",
            context=context,
        )

    return create


def test_missing_term_requires_context(schedule_evidence_factory) -> None:
    result = evaluate_deadline(
        "When is the add/drop deadline?",
        evidence=schedule_evidence_factory(),
    )

    assert result["outcome"] == "needs_context"
    assert result["requires_context"] is True
    assert result["term"] is None
    assert result["evidence"] is None


def test_current_recent_term_evidence_preserves_deadline_and_locator(
    schedule_evidence_factory,
) -> None:
    evidence = schedule_evidence_factory()

    result = evaluate_deadline(
        "When is the add/drop deadline?",
        term="Fall 2026",
        evidence=evidence,
        today=TODAY,
    )

    assert result["outcome"] == "answered"
    assert result["current"] is True
    assert result["term"] == evidence.context["term"]
    assert result["deadline_type"] == evidence.context["deadline_type"]
    assert result["date"] == evidence.context["date"]
    assert result["conditions"] == evidence.context["conditions"]
    assert result["source_title"] == evidence.source_version.source.title
    assert result["source_url"] == evidence.source_version.source.url
    assert result["locator"] == evidence.locator
    assert result["evidence"] is evidence


@pytest.mark.parametrize(
    ("question", "evidence_kwargs", "context_overrides"),
    [
        (
            "When is the add/drop deadline?",
            {"last_reviewed_on": date(2026, 5, 1)},
            None,
        ),
        (
            "When is the add/drop deadline?",
            {"effective_to": date(2026, 10, 3)},
            None,
        ),
        (
            "When is the add/drop deadline?",
            {"status": SourceVersionStatus.INCOMPLETE},
            None,
        ),
        (
            "When is the add/drop deadline?",
            {},
            {"date": None},
        ),
        (
            "When is the add/drop deadline?",
            {},
            {"conditions": None},
        ),
        (
            "When is the add/drop deadline?",
            {},
            {"deadline_type": None},
        ),
    ],
)
def test_unreliable_or_incomplete_evidence_refers_safely(
    schedule_evidence_factory,
    question: str,
    evidence_kwargs: dict,
    context_overrides: dict | None,
) -> None:
    evidence = schedule_evidence_factory(
        **evidence_kwargs,
        context_overrides=context_overrides,
    )

    result = evaluate_deadline(
        question,
        term="Fall 2026",
        evidence=evidence,
        today=TODAY,
    )

    assert result["outcome"] == "escalation_required"
    assert result["current"] is False
    assert result["evidence"] is None
    assert result["escalation"]["office"] == "Registrar's Office"
    assert result["escalation"]["contact_url"] == "https://www.pnw.edu/registrar/"


def test_evidence_for_another_term_is_never_used(
    schedule_evidence_factory,
) -> None:
    evidence = schedule_evidence_factory(term="Spring 2027")

    result = evaluate_deadline(
        "When is the add/drop deadline?",
        term="Fall 2026",
        evidence=evidence,
        today=TODAY,
    )

    assert result["outcome"] == "escalation_required"
    assert result["evidence"] is None


def test_missing_reliable_evidence_refers_financial_aid_question() -> None:
    result = evaluate_deadline(
        "What is the financial aid deadline?",
        term="Fall 2026",
        today=TODAY,
    )

    assert result["outcome"] == "escalation_required"
    assert result["escalation"]["office"] == "Financial Aid Office"
    assert result["escalation"]["contact_url"] == "https://www.pnw.edu/financial-aid/"
