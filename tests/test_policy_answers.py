from __future__ import annotations

from app.api.answers import render_policy_answer

POLICY_CITATION = {
    "title": "Parking Citation Appeal Instructions",
    "url": "https://www.pnw.edu/parking/citation-appeal.pdf",
    "locator": "PDF page 2, Appeal submission",
}


def test_policy_answer_renders_supported_summary_steps_and_all_citations() -> None:
    child_page = {
        "title": "Pay a Parking Citation",
        "url": "https://www.pnw.edu/parking/pay-citation/",
        "locator": "Payment instructions",
    }
    summary = (
        "Pay online through the PNW Parking Portal using the citation number."
    )

    response = render_policy_answer(
        {
            "outcome": "answered",
            "summary": summary,
            "next_steps": ["Pay online through the PNW Parking Portal."],
            "citations": [child_page, POLICY_CITATION],
        }
    )

    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["outcome"] == "answered"
    assert "citation number" in payload["message"]
    assert "Next steps: Pay online through the PNW Parking Portal." in payload["message"]
    assert payload["citations"] == [child_page, POLICY_CITATION]


def test_policy_individual_outcome_renders_general_guidance_and_office_referral() -> None:
    response = render_policy_answer(
        {
            "outcome": "escalation_required",
            "summary": "Submit an appeal within 10 calendar days of the citation.",
            "message": "Your appeal will be approved.",  # Must not be trusted for an individual decision.
            "citations": [POLICY_CITATION],
            "escalation": {
                "office": "Parking Services",
                "reason": "Parking Services handles parking citation appeals.",
                "contactUrl": "https://www.pnw.edu/parking/",
            },
        }
    )

    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["outcome"] == "escalation_required"
    assert "10 calendar days" in payload["message"]
    assert "I can't determine an individual outcome." in payload["message"]
    assert "Your appeal will be approved" not in payload["message"]
    assert payload["escalation"] == {
        "office": "Parking Services",
        "reason": "Parking Services handles parking citation appeals.",
        "contactUrl": "https://www.pnw.edu/parking/",
    }
    assert payload["citations"] == [POLICY_CITATION]


def test_incomplete_policy_decision_abstains_without_factual_claims() -> None:
    response = render_policy_answer(
        {
            "outcome": "answered",
            "summary": "The unsupported deadline is September 1.",
            "citations": [
                {
                    "title": "Schedule",
                    "url": "https://example.com/schedule",
                    "locator": "row 1",
                }
            ],
        }
    )

    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["outcome"] == "cannot_verify"
    assert "September 1" not in payload["message"]
    assert payload["citations"] == []


def test_unsafe_or_incomplete_referral_abstains() -> None:
    response = render_policy_answer(
        {
            "outcome": "escalation_required",
            "summary": "Submit an appeal within 10 calendar days.",
            "citations": [POLICY_CITATION],
            "escalation": {
                "office": "",
                "reason": "A route is required.",
                "contactUrl": "https://www.pnw.edu/parking/",
            },
        }
    )

    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["outcome"] == "cannot_verify"
    assert "10 calendar days" not in payload["message"]


def test_missing_policy_evidence_returns_non_definitive_response() -> None:
    response = render_policy_answer(
        {
            "outcome": "cannot_verify",
            "message": "The current policy could not be verified.",
            "citations": [],
        }
    )

    payload = response.model_dump(by_alias=True, exclude_none=True)
    assert payload["outcome"] == "cannot_verify"
    assert payload["message"] == "The current policy could not be verified."
    assert payload["citations"] == []
