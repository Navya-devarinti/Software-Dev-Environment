from app.api.answers import render_deadline_answer


def reliable_deadline() -> dict:
    return {
        "outcome": "answered",
        "current": True,
        "term": "Fall 2026",
        "deadline_type": "add/drop",
        "date": "2026-09-08",
        "conditions": ["Refund eligibility depends on the withdrawal date."],
        "source_title": "Fall 2026 Academic Schedule",
        "source_url": "https://www.pnw.edu/academic-calendar/",
        "locator": "Fall 2026 schedule, add/drop row",
        "evidence": object(),
    }


def test_reliable_deadline_renders_plain_language_details_and_citation() -> None:
    response = render_deadline_answer(reliable_deadline())

    assert response.outcome == "answered"
    assert "Fall 2026" in response.message
    assert "add/drop" in response.message
    assert "September 8, 2026" in response.message
    assert "Refund eligibility depends on the withdrawal date." in response.message
    assert [citation.model_dump() for citation in response.citations] == [
        {
            "title": "Fall 2026 Academic Schedule",
            "url": "https://www.pnw.edu/academic-calendar/",
            "locator": "Fall 2026 schedule, add/drop row",
        }
    ]


def test_missing_term_renders_context_clarification_without_citation() -> None:
    response = render_deadline_answer(
        {
            "outcome": "needs_context",
            "requires_context": True,
            "term": None,
            "current": False,
            "evidence": None,
        }
    )

    assert response.outcome == "needs_context"
    assert response.required_context == ["term"]
    assert "term" in response.message.lower()
    assert response.citations == []
    assert response.escalation is None


def test_unreliable_deadline_renders_only_supplied_office_referral() -> None:
    response = render_deadline_answer(
        {
            "outcome": "escalation_required",
            "term": "Fall 2026",
            "current": False,
            "evidence": None,
            "escalation": {
                "office": "Registrar's Office",
                "reason": "Registration and course schedule questions need registrar guidance.",
                "contact_url": "https://www.pnw.edu/registrar/",
            },
        }
    )

    assert response.outcome == "escalation_required"
    assert "September" not in response.message
    assert "contact" in response.message.lower()
    assert response.citations == []
    assert response.escalation is not None
    assert response.escalation.office == "Registrar's Office"
    assert response.escalation.contact_url == "https://www.pnw.edu/registrar/"


def test_unreliable_deadline_does_not_render_claims_from_answer_shaped_result() -> None:
    result = reliable_deadline()
    result.update(current=False, evidence=None)

    response = render_deadline_answer(result)

    assert response.outcome == "cannot_verify"
    assert "September 8" not in response.message
    assert response.citations == []
    assert response.escalation is None
