from app.api.answers import render_academic_answer


CATALOG_CITATION = {
    "title": "PNW Academic Catalog",
    "url": "https://www.pnw.edu/academic-catalog/",
    "locator": "2026-2027 Catalog, Computer Science requirements",
}


def test_academic_answer_renders_bounded_evidence_with_citation() -> None:
    response = render_academic_answer(
        {
            "outcome": "answered",
            "summary": "Computer Science students must complete the published program requirements.",
            "citations": [CATALOG_CITATION],
        }
    )

    assert response.outcome == "answered"
    assert response.message.startswith("Computer Science students")
    assert [citation.model_dump() for citation in response.citations] == [
        CATALOG_CITATION
    ]


def test_academic_answer_abstains_without_supported_summary_or_citation() -> None:
    for decision in (
        {
            "outcome": "answered",
            "summary": "The degree requires 120 credits.",
            "citations": [],
        },
        {
            "outcome": "answered",
            "summary": "You are eligible to graduate.",
            "citations": [CATALOG_CITATION],
        },
        {
            "outcome": "answered",
            "summary": "A valid response.",
            "citations": [
                {**CATALOG_CITATION, "url": "https://example.com/catalog"}
            ],
        },
    ):
        response = render_academic_answer(decision)
        assert response.outcome == "cannot_verify"
        assert response.citations == []


def test_academic_answer_renders_only_valid_context_clarifications() -> None:
    response = render_academic_answer(
        {
            "outcome": "needs_context",
            "message": "Which program do you mean?",
            "required_context": ["program", "academicLevel"],
        }
    )

    assert response.outcome == "needs_context"
    assert response.required_context == ["program", "academicLevel"]
    assert response.citations == []

    invalid = render_academic_answer(
        {
            "outcome": "needs_context",
            "message": "Please provide a student ID.",
            "required_context": ["studentId"],
        }
    )
    assert invalid.outcome == "cannot_verify"
    assert invalid.required_context == []


def test_individual_academic_answer_limits_claims_and_renders_advising_referral() -> None:
    response = render_academic_answer(
        {
            "outcome": "escalation_required",
            "summary": "Students must complete published program requirements.",
            "citations": [CATALOG_CITATION],
            "escalation": {
                "office": "Academic Advising",
                "reason": "An advisor must review individual graduation eligibility.",
                "contactUrl": "https://www.pnw.edu/advising/",
            },
        }
    )

    assert response.outcome == "escalation_required"
    assert "Students must complete published program requirements." in response.message
    assert "can't determine an individual" in response.message
    assert "you are eligible" not in response.message.casefold()
    assert [citation.model_dump() for citation in response.citations] == [
        CATALOG_CITATION
    ]
    assert response.escalation is not None
    assert response.escalation.office == "Academic Advising"
    assert response.escalation.contact_url == "https://www.pnw.edu/advising/"


def test_referral_does_not_forward_unsupported_or_unsafe_summary() -> None:
    response = render_academic_answer(
        {
            "outcome": "escalation_required",
            "summary": "You will graduate and are approved.",
            "citations": [CATALOG_CITATION],
            "escalation": {
                "office": "Academic Advising",
                "reason": "A personal decision is required.",
                "contactUrl": "https://example.com/advising",
            },
        }
    )

    assert response.outcome == "escalation_required"
    assert "You will graduate" not in response.message
    assert response.citations == []
    assert response.escalation is not None
    assert response.escalation.contact_url is None


def test_invalid_referral_and_unknown_decision_abstain() -> None:
    missing_route = render_academic_answer(
        {
            "outcome": "escalation_required",
            "escalation": {
                "office": "",
                "reason": "Advisor review is needed.",
            },
        }
    )
    assert missing_route.outcome == "cannot_verify"

    unsupported = render_academic_answer(
        {
            "outcome": "unknown",
            "message": "No approved factual decision is available.",
        }
    )
    assert unsupported.outcome == "cannot_verify"
    assert unsupported.citations == []

    unverifiable = render_academic_answer(
        {
            "outcome": "cannot_verify",
            "message": "You will graduate and are approved.",
        }
    )
    assert unverifiable.outcome == "cannot_verify"
    assert "You will graduate" not in unverifiable.message
