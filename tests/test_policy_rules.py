from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.main import app
from app.rules.policies import summarize_policy


def policy_evidence(
    text: str = (
        "Students first discuss the grade with the instructor. If unresolved, "
        "submit a written appeal with supporting documentation to the department "
        "chair within 10 working days."
    ),
    *,
    last_reviewed_on: date | None = None,
    status: str = "current",
    category: str = "policy",
    locator: str = "PDF page 3, Appeal procedure",
    url: str = "https://www.pnw.edu/academic-affairs/grade-appeal-policy.pdf",
    incomplete: bool = False,
) -> SimpleNamespace:
    source = SimpleNamespace(
        title="Grade Appeal Policy",
        url=url,
        last_reviewed_on=last_reviewed_on or date.today(),
        review_frequency="annual",
    )
    version = SimpleNamespace(
        status=status,
        effective_from=None,
        effective_to=None,
        source=source,
    )
    metadata = {"category": category}
    if incomplete:
        metadata["incomplete"] = True
    return SimpleNamespace(
        text=text,
        locator=locator,
        source_title="Grade Appeal Policy",
        source_url=url,
        source_version=version,
        metadata=metadata,
    )


def test_supported_general_policy_returns_qualified_facts_steps_and_provenance() -> None:
    result = summarize_policy(
        "What are the steps in the grade appeal process?",
        evidence=[policy_evidence()],
    )

    assert result["outcome"] == "answered"
    assert "If unresolved" in result["message"]
    assert "10 working days" in result["message"]
    assert result["next_steps"] == [
        "Students first discuss the grade with the instructor. If unresolved, "
        "submit a written appeal with supporting documentation to the department "
        "chair within 10 working days."
    ]
    assert result["citations"] == [
        {
            "title": "Grade Appeal Policy",
            "url": "https://www.pnw.edu/academic-affairs/grade-appeal-policy.pdf",
            "locator": "PDF page 3, Appeal procedure",
        }
    ]


def test_individual_policy_outcome_is_not_determined_and_uses_approved_route() -> None:
    result = summarize_policy(
        "Will my parking citation appeal be approved if I submit it today?",
        evidence=[
            policy_evidence(
                text=(
                    "Submit an appeal through the PNW Parking Portal within "
                    "10 calendar days of the citation."
                ),
                category="procedure",
                locator="PDF page 2, Appeal submission",
                url="https://www.pnw.edu/parking/citation-appeal.pdf",
            )
        ],
    )

    assert result["outcome"] == "escalation_required"
    assert "10 calendar days" in result["message"]
    assert "I can't determine an individual outcome." in result["message"]
    assert result["escalation"]["office"] == "Parking Services"
    assert result["escalation"]["contactUrl"] == "https://www.pnw.edu/parking/"
    assert "approved" not in result["message"].lower()


def test_missing_stale_incomplete_or_unofficial_policy_evidence_abstains() -> None:
    stale = policy_evidence(last_reviewed_on=date(2024, 1, 1))
    incomplete = policy_evidence(incomplete=True)
    unreviewed = policy_evidence(status="unreviewed")
    unofficial = policy_evidence(url="https://example.com/policy")

    for evidence in ([], [stale], [incomplete], [unreviewed], [unofficial]):
        result = summarize_policy("How does this policy work?", evidence=evidence)
        assert result["outcome"] == "cannot_verify"
        assert result["citations"] == []
        assert result["next_steps"] == []


def test_unsupported_category_and_missing_citation_locator_abstain() -> None:
    unsupported = policy_evidence(category="alert")
    missing_locator = policy_evidence(locator="")

    for evidence in ([unsupported], [missing_locator]):
        result = summarize_policy("How does this policy work?", evidence=evidence)
        assert result["outcome"] == "cannot_verify"
        assert result["summary"] is None


def test_summary_abstains_instead_of_truncating_material_source_text() -> None:
    result = summarize_policy(
        "What does this policy say?",
        evidence=[policy_evidence(text="Required qualification " * 30)],
    )

    assert result["outcome"] == "cannot_verify"
    assert result["summary"] is None
    assert result["citations"] == []
