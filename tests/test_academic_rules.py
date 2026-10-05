from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

import app.main
from app.rules.academics import (
    evaluate_academic_question,
    is_general_academic_question,
    is_individual_academic_question,
    requires_academic_context,
)


CATALOG_URL = "https://www.pnw.edu/academic-catalog/"
GUIDANCE = (
    "Students must complete the requirements published for their academic "
    "program before applying for graduation."
)


def catalog_evidence(
    text: str = GUIDANCE,
    *,
    context: dict[str, str] | None = None,
    locator: str = "2026-2027 Catalog, Graduation Requirements",
    url: str = CATALOG_URL,
    status: str = "current",
    category: str = "catalog",
) -> SimpleNamespace:
    source = SimpleNamespace(
        title="PNW Academic Catalog",
        url=url,
        last_reviewed_on=date.today(),
        review_frequency="annual",
    )
    version = SimpleNamespace(
        status=status,
        effective_from=None,
        effective_to=None,
        source=source,
    )
    return SimpleNamespace(
        text=text,
        locator=locator,
        source_title=source.title,
        source_url=source.url,
        source_version=version,
        metadata={"category": category, **(context or {})},
    )


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (
            "Where is CS 101 offered in Fall 2026?",
            ["campus", "term", "courseCode"],
        ),
        ("What are the degree requirements for this program?", ["program"]),
        ("What are graduate program requirements?", ["program", "academicLevel"]),
    ],
)
def test_required_academic_context_is_question_specific(
    question: str,
    expected: list[str],
) -> None:
    assert requires_academic_context(question) == expected


def test_provided_context_satisfies_only_requested_fields() -> None:
    assert requires_academic_context(
        "Where is CS 101 offered in Fall 2026?",
        {
            "campus": "Hammond",
            "term": "Fall 2026",
            "courseCode": "CS 101",
        },
    ) == []


@pytest.mark.parametrize(
    "question",
    [
        "Will I graduate?",
        "Do I meet the graduation requirements?",
        "Have I completed enough credits to graduate?",
        "What is my graduation status?",
        "Am I eligible to graduate?",
    ],
)
def test_individual_graduation_questions_are_classified_as_personal(
    question: str,
) -> None:
    assert is_individual_academic_question(question)
    assert not is_general_academic_question(question)


@pytest.mark.parametrize(
    "question",
    [
        "What are the Computer Science degree requirements?",
        "What are the graduation requirements for this program?",
    ],
)
def test_public_academic_requirements_are_not_individual_determinations(
    question: str,
) -> None:
    assert not is_individual_academic_question(question)
    assert is_general_academic_question(question)


def test_general_requirements_need_context_then_answer_from_cited_catalog_evidence() -> None:
    question = "What are the graduation requirements for this program?"
    missing = evaluate_academic_question(question)
    assert missing["outcome"] == "needs_context"
    assert missing["required_context"] == ["program"]

    answer = evaluate_academic_question(
        question,
        context={"program": "Computer Science"},
        evidence=[
            catalog_evidence(
                context={"program": "Computer Science", "academicLevel": "undergraduate"}
            )
        ],
    )

    assert answer["outcome"] == "answered"
    assert answer["summary"] == GUIDANCE
    assert answer["citations"] == [
        {
            "title": "PNW Academic Catalog",
            "url": CATALOG_URL,
            "locator": "2026-2027 Catalog, Graduation Requirements",
        }
    ]
    assert answer["evidence"][0].source_version.source.url == CATALOG_URL


def test_conflicting_context_or_unverifiable_evidence_cannot_support_answer() -> None:
    question = "What are the Computer Science degree requirements?"
    evidence = catalog_evidence(context={"program": "Mathematics"})

    result = evaluate_academic_question(
        question,
        context={"program": "Computer Science"},
        evidence=[evidence],
    )

    assert result["outcome"] == "cannot_verify"
    assert result["citations"] == []

    for invalid in (
        catalog_evidence(status="superseded"),
        catalog_evidence(url="https://example.com/catalog"),
        catalog_evidence(locator=""),
        catalog_evidence(category="policy"),
    ):
        result = evaluate_academic_question(
            question,
            context={"program": "Computer Science"},
            evidence=[invalid],
        )
        assert result["outcome"] == "cannot_verify"
        assert result["citations"] == []


def test_individual_outcome_always_escalates_without_deciding_eligibility() -> None:
    result = evaluate_academic_question(
        "Do I meet the graduation requirements?",
        evidence=[catalog_evidence()],
    )

    assert result["outcome"] == "escalation_required"
    assert result["escalation"]["office"] == "Academic Advising"
    assert result["escalation"]["contactUrl"] == "https://www.pnw.edu/advising/"
    assert "can't determine an individual" in result["message"]
    assert "approved" not in result["message"].casefold()


def test_individual_outcome_escalates_even_without_evidence() -> None:
    result = evaluate_academic_question("Will I graduate?")

    assert result["outcome"] == "escalation_required"
    assert result["escalation"]["office"] == "Academic Advising"
    assert result["summary"] is None
    assert result["citations"] == []


def test_missing_or_oversized_evidence_cannot_produce_a_partial_answer() -> None:
    result = evaluate_academic_question(
        "What are the Computer Science degree requirements?",
        context={"program": "Computer Science"},
    )
    assert result["outcome"] == "cannot_verify"

    result = evaluate_academic_question(
        "What are the Computer Science degree requirements?",
        context={"program": "Computer Science"},
        evidence=[
            catalog_evidence(context={"program": "Computer Science"}),
            catalog_evidence(
                text="Material qualification " * 30,
                context={"program": "Computer Science"},
                locator="Additional requirements",
            ),
        ],
    )
    assert result["outcome"] == "cannot_verify"
    assert result["citations"] == []
