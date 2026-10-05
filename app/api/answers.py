from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from urllib.parse import urlparse

from app.api.schemas import ChatResponse, Citation, Escalation
from app.rules.citations import make_citation


def create_response(
    *,
    outcome: str,
    message: str,
    required_context: Sequence[str] | None = None,
    citations: Sequence[dict | Citation] | None = None,
    escalation: dict | Escalation | None = None,
) -> ChatResponse:
    return ChatResponse(
        outcome=outcome,
        message=message,
        requiredContext=list(required_context or []),
        citations=[
            Citation(**c) if isinstance(c, dict) else c for c in (citations or [])
        ],
        escalation=(Escalation(**escalation) if isinstance(escalation, dict) else escalation),
    )


def render_deadline_answer(decision: Mapping[str, object]) -> ChatResponse:
    """Render a deadline decision without adding facts beyond the deadline rules."""
    if decision.get("outcome") == "needs_context" or decision.get("requires_context"):
        return create_response(
            outcome="needs_context",
            message="Which academic term do you mean? I need the term to check the applicable deadline.",
            required_context=["term"],
        )

    if (
        decision.get("outcome") == "answered"
        and decision.get("current") is True
        and decision.get("evidence") is not None
    ):
        term = _nonempty_string(decision.get("term"))
        deadline_type = _nonempty_string(decision.get("deadline_type"))
        deadline_date = _format_deadline_date(decision.get("date"))
        conditions = decision.get("conditions")
        title = _nonempty_string(decision.get("source_title"))
        url = _nonempty_string(decision.get("source_url"))
        locator = _nonempty_string(decision.get("locator"))

        if (
            term
            and deadline_type
            and deadline_date
            and isinstance(conditions, list)
            and all(_nonempty_string(condition) for condition in conditions)
            and title
            and url
            and locator
        ):
            message = (
                f"For {term}, the {deadline_type} deadline is {deadline_date}."
            )
            if conditions:
                label = "condition" if len(conditions) == 1 else "conditions"
                message += f" Applicable {label}: {' '.join(conditions)}"

            return create_response(
                outcome="answered",
                message=message,
                citations=[make_citation(title, url, locator)],
            )

    if decision.get("outcome") == "escalation_required":
        return _render_deadline_referral(decision)

    if decision.get("outcome") == "answered":
        if isinstance(decision.get("escalation"), Mapping):
            return _render_deadline_referral(decision)
        return create_response(
            outcome="cannot_verify",
            message=(
                "I can't verify a current, complete deadline from reliable "
                "schedule information."
            ),
        )

    return create_response(
        outcome="cannot_verify",
        message=(
            "I can't verify a current, complete deadline from reliable "
            "schedule information."
        ),
    )


def render_policy_answer(decision: Mapping[str, object]) -> ChatResponse:
    """Render a policy decision using only its reviewed evidence and safe route."""
    outcome = decision.get("outcome")
    summary = _nonempty_string(decision.get("summary"))
    citations = _policy_citations(decision.get("citations"))

    if outcome == "answered":
        if not summary or not citations:
            return _policy_cannot_verify()

        message = _with_supported_next_steps(
            summary,
            decision.get("next_steps"),
        )
        if len(message) > 1600:
            return _policy_cannot_verify(
                "I can't safely present this policy explanation without losing "
                "material qualifications."
            )
        return create_response(
            outcome="answered",
            message=message,
            citations=citations,
        )

    if outcome == "escalation_required":
        if not summary or not citations:
            return _policy_cannot_verify()

        escalation = decision.get("escalation")
        if not isinstance(escalation, Mapping):
            return _policy_cannot_verify()

        office = _nonempty_string(escalation.get("office"))
        reason = _nonempty_string(escalation.get("reason"))
        contact_url = _official_pnw_contact_url(
            escalation.get("contactUrl", escalation.get("contact_url"))
        )
        if not office or not reason:
            return _policy_cannot_verify()

        message = (
            f"General published guidance: {summary} "
            f"I can't determine an individual outcome. Please contact {office} "
            "for a decision about your situation."
        )
        if len(message) > 1600:
            return _policy_cannot_verify(
                "I can't safely present the general policy guidance without "
                "losing material qualifications. Please contact the responsible office."
            )
        route: dict[str, str] = {"office": office, "reason": reason}
        if contact_url:
            route["contactUrl"] = contact_url
        return create_response(
            outcome="escalation_required",
            message=message,
            citations=citations,
            escalation=route,
        )

    return _policy_cannot_verify(
        _nonempty_string(decision.get("message"))
        or "I can't verify this policy or procedure from current, complete, "
        "reviewed official evidence."
    )


def render_academic_answer(decision: Mapping[str, object]) -> ChatResponse:
    """Render bounded catalog guidance or an individual academic referral."""
    outcome = decision.get("outcome")
    summary = _nonempty_string(decision.get("summary"))
    citations = _academic_citations(decision.get("citations"))

    if outcome == "needs_context":
        required_context = decision.get("required_context")
        if (
            not isinstance(required_context, Sequence)
            or isinstance(required_context, (str, bytes))
            or not required_context
            or any(
                not isinstance(field, str)
                or field not in {
                    "campus",
                    "term",
                    "program",
                    "courseCode",
                    "academicLevel",
                }
                for field in required_context
            )
        ):
            return _academic_cannot_verify()
        return create_response(
            outcome="needs_context",
            message=(
                _nonempty_string(decision.get("message"))
                or "I need more public academic context before I can answer accurately."
            ),
            required_context=required_context,
        )

    if outcome == "answered":
        if (
            not summary
            or len(summary) > 1600
            or _contains_individual_academic_claim(summary)
            or not citations
        ):
            return _academic_cannot_verify()
        return create_response(
            outcome="answered",
            message=summary,
            citations=citations,
        )

    if outcome == "escalation_required":
        escalation = decision.get("escalation")
        if not isinstance(escalation, Mapping):
            return _academic_cannot_verify()

        office = _nonempty_string(escalation.get("office"))
        reason = _nonempty_string(escalation.get("reason"))
        if office != "Academic Advising" or not reason:
            return _academic_cannot_verify()

        safe_summary = (
            summary
            if summary
            and len(summary) <= 1200
            and not _contains_individual_academic_claim(summary)
            and citations
            else None
        )
        contact_url = _official_pnw_contact_url(
            escalation.get("contactUrl", escalation.get("contact_url"))
        )
        message = (
            f"General published academic guidance: {safe_summary} "
            if safe_summary
            else ""
        )
        message += (
            "I can't determine an individual academic or graduation outcome. "
            f"Please contact {office} for review."
        )
        if len(message) > 1600:
            return _academic_cannot_verify()

        route: dict[str, str] = {"office": office, "reason": reason}
        if contact_url:
            route["contactUrl"] = contact_url
        return create_response(
            outcome="escalation_required",
            message=message,
            citations=citations if safe_summary else [],
            escalation=route,
        )

    return _academic_cannot_verify()


def _academic_citations(value: object) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return []

    citations: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            return []
        title = _nonempty_string(item.get("title"))
        url = _official_pnw_contact_url(item.get("url"))
        locator = _nonempty_string(item.get("locator"))
        if not title or not url or not locator:
            return []
        citations.append(make_citation(title, url, locator))
    return citations


def _contains_individual_academic_claim(value: str) -> bool:
    normalized = value.casefold()
    claims = (
        "you will graduate",
        "you won't graduate",
        "you will not graduate",
        "you can graduate",
        "you cannot graduate",
        "you can't graduate",
        "you are eligible",
        "you are not eligible",
        "you qualify to graduate",
        "you do not qualify to graduate",
        "you meet all requirements",
        "you do not meet all requirements",
        "you are approved",
        "you have been approved",
        "you are denied",
        "you have been denied",
        "approved to graduate",
        "denied graduation",
    )
    return any(claim in normalized for claim in claims)


def _academic_cannot_verify(
    message: str = (
        "I can't verify a complete, current academic answer from the available "
        "official catalog evidence."
    ),
) -> ChatResponse:
    return create_response(outcome="cannot_verify", message=message)


def _policy_citations(value: object) -> list[dict[str, str]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return []

    citations: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            return []
        title = _nonempty_string(item.get("title"))
        url = _official_pnw_contact_url(item.get("url"))
        locator = _nonempty_string(item.get("locator"))
        if not title or not url or not locator:
            return []
        citations.append(make_citation(title, url, locator))
    return citations


def _with_supported_next_steps(summary: str, value: object) -> str:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return summary
    steps = [
        step.strip()
        for step in value
        if isinstance(step, str) and step.strip()
    ]
    missing_steps = [step for step in steps if step.casefold() not in summary.casefold()]
    if not missing_steps:
        return summary
    return f"{summary} Next steps: {' '.join(missing_steps)}"


def _official_pnw_contact_url(value: object) -> str | None:
    url = _nonempty_string(value)
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "pnw.edu" or host.endswith(".pnw.edu")):
        return None
    return url


def _policy_cannot_verify(
    message: str = (
        "I can't verify a current, complete policy or procedure from reliable "
        "official evidence."
    ),
) -> ChatResponse:
    return create_response(outcome="cannot_verify", message=message)


def _render_deadline_referral(decision: Mapping[str, object]) -> ChatResponse:
    referral = decision.get("escalation")
    if not isinstance(referral, Mapping):
        return create_response(
            outcome="escalation_required",
            message=(
                "I can't verify a current, complete deadline. Please check the "
                "official schedule or contact the responsible university office."
            ),
        )

    office = _nonempty_string(referral.get("office"))
    if not office:
        return create_response(
            outcome="escalation_required",
            message=(
                "I can't verify a current, complete deadline. Please check the "
                "official schedule or contact the responsible university office."
            ),
        )

    reason = _nonempty_string(referral.get("reason")) or (
        "A current, complete deadline could not be verified."
    )
    contact_url = _nonempty_string(
        referral.get("contact_url", referral.get("contactUrl"))
    )
    escalation: dict[str, str] = {"office": office, "reason": reason}
    if contact_url:
        escalation["contactUrl"] = contact_url

    return create_response(
        outcome="escalation_required",
        message=(
            "I can't verify a current, complete deadline from reliable schedule "
            f"information. Please contact {office} for the official schedule."
        ),
        escalation=escalation,
    )


def _nonempty_string(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _format_deadline_date(value: object) -> str | None:
    if isinstance(value, date):
        deadline_date = value
    elif isinstance(value, str):
        try:
            deadline_date = date.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None

    return f"{deadline_date:%B} {deadline_date.day}, {deadline_date.year}"
