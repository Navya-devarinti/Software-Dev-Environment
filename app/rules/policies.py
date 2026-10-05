from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any
from urllib.parse import urlparse

from app.rules.escalation import resolve_office_route
from app.rules.freshness import is_eligible_source_version

MAX_POLICY_ANSWER_LENGTH = 1600
MAX_POLICY_EVIDENCE_ITEMS = 5
MAX_EVIDENCE_TEXT_LENGTH = 500

_INDIVIDUAL_DECISION_PHRASES = (
    "my appeal",
    "my ticket",
    "my case",
    "my situation",
    "my eligibility",
    "my standing",
    "will i be approved",
    "will my",
    "can i get an exception",
    "can you approve",
    "can you waive",
    "should i be allowed",
    "am i allowed",
    "do i qualify",
    "do i meet",
    "does my",
)

_NEXT_STEP_MARKERS = (
    "submit",
    "contact",
    "complete",
    "file",
    "send",
    "pay",
    "schedule",
    "meet",
    "provide",
    "request",
    "appeal",
)


def summarize_policy(
    question: str,
    *,
    evidence: Sequence[Any] | None = None,
    supported: bool | None = None,
    today: date | None = None,
) -> dict[str, object]:
    """Evaluate reviewed policy evidence without deciding an individual outcome."""
    question = (question or "").strip()
    evidence_items = list(evidence or [])
    if any(_is_ambiguous_or_conflicting(item) for item in evidence_items):
        return _cannot_verify(
            "I can't give a definitive policy answer because the available "
            "official sources are incomplete, ambiguous, or conflicting."
        )
    eligible = [
        item for item in evidence_items if _is_eligible_policy_evidence(item, today=today)
    ]
    individually_decided = _requires_individual_decision(question)
    category = _issue_category(question, evidence_items)

    if supported is False or not eligible:
        return _cannot_verify(
            "I can't verify this policy or procedure from current, complete, "
            "reviewed official evidence."
        )

    facts = [_evidence_text(item) for item in eligible[:MAX_POLICY_EVIDENCE_ITEMS]]
    facts = [fact for fact in facts if fact]
    if not facts:
        return _cannot_verify(
            "I can't verify this policy or procedure because the reviewed source "
            "does not contain complete readable guidance."
        )

    answer = " ".join(facts)
    if len(answer) > MAX_POLICY_ANSWER_LENGTH:
        return _cannot_verify(
            "I can't safely summarize this policy because the relevant source "
            "material is too extensive to present without losing qualifications."
        )

    next_steps = _supported_next_steps(facts)
    citations = [_citation(item) for item in eligible[:MAX_POLICY_EVIDENCE_ITEMS]]

    if individually_decided:
        route = resolve_office_route(category)
        message = (
            f"General published guidance: {answer} "
            f"I can't determine an individual outcome. Please contact "
            f"{route['office']} for a decision about your situation."
        )
        if len(message) > MAX_POLICY_ANSWER_LENGTH:
            return _cannot_verify(
                "I can't safely summarize this policy without losing its "
                "qualifications. Please contact the responsible office."
            )
        return {
            "outcome": "escalation_required",
            "message": message,
            "summary": answer,
            "next_steps": next_steps,
            "citations": citations,
            "escalation": route,
        }

    return {
        "outcome": "answered",
        "message": answer,
        "summary": answer,
        "next_steps": next_steps,
        "citations": citations,
        "evidence": eligible[:MAX_POLICY_EVIDENCE_ITEMS],
    }


def _is_eligible_policy_evidence(item: Any, *, today: date | None) -> bool:
    metadata = getattr(item, "metadata", None)
    if isinstance(metadata, Mapping):
        if metadata.get("incomplete") is True or metadata.get("extraction_complete") is False:
            return False
        category = str(metadata.get("category", "")).strip().lower()
        if category and category not in {"policy", "procedure"}:
            return False

    title = _nonempty_string(getattr(item, "source_title", None))
    url = _official_pnw_url(getattr(item, "source_url", None))
    locator = _nonempty_string(getattr(item, "locator", None))
    text = _evidence_text(item)
    version = getattr(item, "source_version", None)
    if not (title and url and locator and text and version is not None):
        return False

    source = getattr(version, "source", None)
    if source is None or not _official_pnw_url(getattr(source, "url", None)):
        return False
    if title != _nonempty_string(getattr(source, "title", None)):
        return False
    if url != _official_pnw_url(getattr(source, "url", None)):
        return False
    return is_eligible_source_version(version, source=source, today=today)


def _is_ambiguous_or_conflicting(item: Any) -> bool:
    metadata = getattr(item, "metadata", None)
    return isinstance(metadata, Mapping) and any(
        metadata.get(flag) is True
        for flag in ("ambiguous", "conflicting", "conflict")
    )


def _official_pnw_url(value: Any) -> str | None:
    url = _nonempty_string(value)
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "pnw.edu" or host.endswith(".pnw.edu")):
        return None
    return url


def _evidence_text(item: Any) -> str | None:
    text = _nonempty_string(getattr(item, "text", None))
    if not text:
        return None
    if len(text) > MAX_EVIDENCE_TEXT_LENGTH:
        return None
    return text


def _citation(item: Any) -> dict[str, str]:
    return {
        "title": _nonempty_string(getattr(item, "source_title", None)) or "",
        "url": _official_pnw_url(getattr(item, "source_url", None)) or "",
        "locator": _nonempty_string(getattr(item, "locator", None)) or "",
    }


def _supported_next_steps(facts: Sequence[str]) -> list[str]:
    return [
        fact
        for fact in facts
        if any(marker in fact.lower() for marker in _NEXT_STEP_MARKERS)
    ]


def _requires_individual_decision(question: str) -> bool:
    normalized = question.lower()
    return any(phrase in normalized for phrase in _INDIVIDUAL_DECISION_PHRASES)


def _issue_category(question: str, evidence: Sequence[Any]) -> str | None:
    normalized = question.lower()
    for category, terms in {
        "parking": ("parking", "ticket", "citation"),
        "registration": ("registration", "register", "course schedule"),
        "graduation": ("graduation", "degree", "program requirement"),
        "financial_aid": ("financial aid", "scholarship", "aid eligibility"),
    }.items():
        if any(term in normalized for term in terms):
            return category

    for item in evidence:
        metadata = getattr(item, "metadata", None)
        if isinstance(metadata, Mapping):
            category = _nonempty_string(metadata.get("route_category"))
            if category:
                return category
    return None


def _cannot_verify(message: str) -> dict[str, object]:
    return {
        "outcome": "cannot_verify",
        "message": message,
        "summary": None,
        "next_steps": [],
        "citations": [],
        "evidence": [],
    }


def _nonempty_string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
