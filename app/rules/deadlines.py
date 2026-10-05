from __future__ import annotations

from datetime import date
from typing import Any

from app.rules.escalation import resolve_office_route
from app.rules.freshness import is_eligible_source_version


def classify_deadline_question(question: str) -> str:
    q = (question or "").lower()
    if any(token in q for token in ["add", "drop", "withdraw", "deadline"]):
        return "deadline"
    return "general"


def _evidence_value(evidence: Any, key: str) -> Any:
    metadata = getattr(evidence, "metadata", None)
    if isinstance(metadata, dict):
        return metadata.get(key)
    context = getattr(evidence, "context", None)
    if isinstance(context, dict):
        return context.get(key)
    return None


def _source_title(evidence: Any) -> str | None:
    title = getattr(evidence, "source_title", None)
    if isinstance(title, str) and title.strip():
        return title.strip()

    version = getattr(evidence, "source_version", None)
    source = getattr(version, "source", None)
    title = getattr(source, "title", None)
    return title.strip() if isinstance(title, str) and title.strip() else None


def _source_url(evidence: Any, source: Any | None) -> str | None:
    url = getattr(evidence, "source_url", None)
    if not isinstance(url, str):
        metadata = getattr(evidence, "metadata", None)
        url = metadata.get("source_url") if isinstance(metadata, dict) else None
    if not isinstance(url, str):
        url = getattr(source, "url", None)
    return url.strip() if isinstance(url, str) and url.strip() else None


def _source_version_and_source(
    evidence: Any,
    source_version: Any | None,
    source: Any | None,
) -> tuple[Any | None, Any | None]:
    version = source_version or getattr(evidence, "source_version", None)
    source_obj = source or getattr(version, "source", None)
    return version, source_obj


def _has_complete_deadline(evidence: Any) -> bool:
    deadline_type = _evidence_value(evidence, "deadline_type")
    deadline_date = _evidence_value(evidence, "date")
    conditions = _evidence_value(evidence, "conditions")
    locator = getattr(evidence, "locator", None)

    if not isinstance(deadline_type, str) or not deadline_type.strip():
        return False
    if isinstance(deadline_date, date):
        pass
    elif isinstance(deadline_date, str):
        try:
            date.fromisoformat(deadline_date)
        except ValueError:
            return False
    else:
        return False
    if not isinstance(conditions, list) or any(
        not isinstance(condition, str) or not condition.strip()
        for condition in conditions
    ):
        return False
    return isinstance(locator, str) and bool(locator.strip())


def _referral(question: str) -> dict[str, str]:
    normalized = (question or "").lower()
    category = (
        "financial_aid"
        if any(token in normalized for token in ("financial aid", "fafsa"))
        else "registration"
    )
    route = resolve_office_route(category)
    return {
        "office": route["office"],
        "reason": route["reason"],
        "contact_url": route["contactUrl"],
    }


def evaluate_deadline(
    question: str,
    *,
    term: str | None = None,
    evidence: Any | None = None,
    source_version: Any | None = None,
    source: Any | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Decide whether term-matched, fresh schedule evidence can support an answer."""
    requested_term = term.strip() if isinstance(term, str) else ""
    if not requested_term:
        return {
            "outcome": "needs_context",
            "requires_context": True,
            "term": None,
            "current": False,
            "evidence": None,
        }

    if evidence is None or _evidence_value(evidence, "term") != requested_term:
        return {
            "outcome": "escalation_required",
            "requires_context": False,
            "term": requested_term,
            "current": False,
            "evidence": None,
            "escalation": _referral(question),
        }

    version, source_obj = _source_version_and_source(
        evidence, source_version, source
    )
    if (
        not _has_complete_deadline(evidence)
        or _source_title(evidence) is None
        or _source_url(evidence, source_obj) is None
        or not is_eligible_source_version(version, source=source_obj, today=today)
    ):
        return {
            "outcome": "escalation_required",
            "requires_context": False,
            "term": requested_term,
            "current": False,
            "evidence": None,
            "escalation": _referral(question),
        }

    return {
        "outcome": "answered",
        "requires_context": False,
        "term": requested_term,
        "current": True,
        "deadline_type": _evidence_value(evidence, "deadline_type"),
        "date": _evidence_value(evidence, "date"),
        "conditions": _evidence_value(evidence, "conditions"),
        "source_title": _source_title(evidence),
        "source_url": _source_url(evidence, source_obj),
        "locator": evidence.locator,
        "evidence": evidence,
    }
