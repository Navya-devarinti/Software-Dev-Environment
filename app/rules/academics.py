from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

from app.api.schemas import Context
from app.rules.escalation import resolve_office_route
from app.rules.freshness import is_eligible_source_version

MAX_ACADEMIC_ANSWER_LENGTH = 1600
MAX_ACADEMIC_EVIDENCE_ITEMS = 5
MAX_ACADEMIC_EVIDENCE_LENGTH = 500

_ACADEMIC_TERMS = (
    "academic",
    "catalog",
    "college",
    "course",
    "degree",
    "graduat",
    "major",
    "plan of study",
    "prerequisite",
    "program",
    "requirement",
)

_INDIVIDUAL_PATTERNS = (
    r"\b(?:am|can|could|will|would|should)\s+i\b.{0,160}\b"
    r"(?:graduate|graduation|eligible|qualif\w*|meet|satisf\w*|"
    r"fulfill\w*|complete\w*|on track|requirement)\b",
    r"\b(?:do|did|have)\s+i\b.{0,160}\b"
    r"(?:meet|satisf\w*|fulfill\w*|complete\w*|qualif\w*)\b",
    r"\bwhat\s+is\s+my\s+(?:graduation|degree)\s+status\b",
    r"\bmy\s+(?:graduation|eligibility)\b",
)

_ACADEMIC_CONTEXT_FIELDS = (
    ("campus", r"\b(?:campus|hammond|westville|location|available|offered)\b"),
    ("term", r"\b(?:term|semester|fall|spring|summer|winter|schedule|offering)\b"),
    ("program", r"\b(?:program|major|college|degree|graduation|plan of study)\b"),
    ("courseCode", r"\b(?:course|prerequisite|course code)\b|\b[a-z]{2,5}\s?\d{3,4}\b"),
    ("academicLevel", r"\b(?:graduate|undergraduate|academic level)\b"),
)


def is_individual_academic_question(question: str) -> bool:
    """Identify questions asking for a personal academic or graduation decision."""
    normalized = (question or "").casefold()
    if not any(term in normalized for term in _ACADEMIC_TERMS):
        return False
    return any(re.search(pattern, normalized) for pattern in _INDIVIDUAL_PATTERNS)


def is_general_academic_question(question: str) -> bool:
    """Return whether a question concerns general published academic information."""
    normalized = (question or "").casefold()
    return (
        any(term in normalized for term in _ACADEMIC_TERMS)
        and not is_individual_academic_question(normalized)
    )


def requires_academic_context(
    question: str,
    context: Context | dict | None = None,
) -> list[str]:
    """List public context fields needed to answer an academic question reliably."""
    normalized_context = _normalize_context(context)
    question_text = (question or "").casefold()
    required = []

    for field, pattern in _ACADEMIC_CONTEXT_FIELDS:
        if not re.search(pattern, question_text):
            continue
        value = _context_value(normalized_context, field)
        if not value:
            required.append(field)

    return required


def evaluate_academic_question(
    question: str,
    *,
    evidence: Sequence[Any] | None = None,
    context: Context | dict | None = None,
) -> dict[str, Any]:
    """Decide whether reviewed catalog evidence supports a bounded academic answer."""
    question = (question or "").strip()
    evidence_items = list(evidence or [])

    if is_individual_academic_question(question):
        return _individual_decision(evidence_items, context)

    if not is_general_academic_question(question):
        return _cannot_verify(
            "I can't verify an academic answer because the question is outside "
            "general published academic information."
        )

    required_context = requires_academic_context(question, context)
    if required_context:
        return {
            "outcome": "needs_context",
            "message": "I need a bit more public academic context to answer accurately.",
            "summary": None,
            "required_context": required_context,
            "citations": [],
            "evidence": [],
            "escalation": None,
        }

    eligible = _eligible_catalog_evidence(evidence_items, context)
    if not eligible:
        return _cannot_verify(
            "I can't verify the current published academic information from "
            "complete, reviewed official catalog evidence."
        )

    facts = [_evidence_text(item) for item in eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS]]
    if any(fact is None for fact in facts):
        return _cannot_verify(
            "I can't safely summarize this academic information without losing "
            "material qualifications."
        )

    summary = " ".join(fact for fact in facts if fact)
    if not summary or len(summary) > MAX_ACADEMIC_ANSWER_LENGTH:
        return _cannot_verify(
            "I can't safely present this academic explanation within a bounded "
            "answer while preserving its qualifications."
        )

    citations = _citations(eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS])
    if not citations:
        return _cannot_verify(
            "I can't verify the catalog information because complete source "
            "citations are unavailable."
        )

    return {
        "outcome": "answered",
        "message": summary,
        "summary": summary,
        "required_context": [],
        "citations": citations,
        "evidence": eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS],
        "escalation": None,
    }


def _individual_decision(
    evidence_items: Sequence[Any],
    context: Context | dict | None,
) -> dict[str, Any]:
    eligible = _eligible_catalog_evidence(evidence_items, context)
    relevant = eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS]
    facts = [_evidence_text(item) for item in relevant]
    summary = (
        " ".join(fact for fact in facts if fact)
        if all(fact is not None for fact in facts)
        else ""
    )
    if len(summary) > MAX_ACADEMIC_ANSWER_LENGTH:
        summary = ""

    route = resolve_office_route("graduation")
    citations = _citations(eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS]) if summary else []
    message = (
        "I can't determine an individual graduation or academic outcome from "
        "general public information. Please contact Academic Advising for review."
    )
    return {
        "outcome": "escalation_required",
        "message": message,
        "summary": summary or None,
        "required_context": [],
        "citations": citations,
        "evidence": eligible[:MAX_ACADEMIC_EVIDENCE_ITEMS] if summary else [],
        "escalation": route,
    }


def _eligible_catalog_evidence(
    evidence_items: Sequence[Any],
    context: Context | dict | None,
) -> list[Any]:
    normalized_context = _normalize_context(context)
    eligible = []
    for item in evidence_items:
        metadata = getattr(item, "metadata", None)
        if not isinstance(metadata, Mapping):
            continue
        if (
            str(metadata.get("category", "")).strip().casefold() != "catalog"
            or metadata.get("incomplete") is True
            or metadata.get("extraction_complete") is False
            or any(metadata.get(flag) is True for flag in ("ambiguous", "conflict", "conflicting"))
            or not _matches_context(metadata, normalized_context)
            or not _has_valid_provenance(item)
            or not _nonempty_string(getattr(item, "text", None))
        ):
            continue
        eligible.append(item)
    return eligible


def _has_valid_provenance(item: Any) -> bool:
    title = _nonempty_string(getattr(item, "source_title", None))
    url = _official_pnw_url(getattr(item, "source_url", None))
    locator = _nonempty_string(getattr(item, "locator", None))
    version = getattr(item, "source_version", None)
    source = getattr(version, "source", None)
    if not (title and url and locator and version is not None and source is not None):
        return False
    if title != _nonempty_string(getattr(source, "title", None)):
        return False
    if url != _official_pnw_url(getattr(source, "url", None)):
        return False
    return is_eligible_source_version(version, source=source)


def _matches_context(metadata: Mapping[str, Any], context: Context | None) -> bool:
    if context is None:
        return True
    for field, _pattern in _ACADEMIC_CONTEXT_FIELDS:
        requested = _context_value(context, field)
        available = metadata.get(field)
        if (
            requested
            and isinstance(available, str)
            and available.strip()
            and available.strip().casefold() != requested.casefold()
        ):
            return False
    return True


def _citations(evidence_items: Sequence[Any]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in evidence_items:
        citation = {
            "title": _nonempty_string(getattr(item, "source_title", None)) or "",
            "url": _official_pnw_url(getattr(item, "source_url", None)) or "",
            "locator": _nonempty_string(getattr(item, "locator", None)) or "",
        }
        key = (citation["title"], citation["url"], citation["locator"])
        if all(key) and key not in seen:
            citations.append(citation)
            seen.add(key)
    return citations


def _evidence_text(item: Any) -> str | None:
    text = _nonempty_string(getattr(item, "text", None))
    if not text or len(text) > MAX_ACADEMIC_EVIDENCE_LENGTH:
        return None
    return text


def _normalize_context(context: Context | dict | None) -> Context | None:
    if context is None:
        return None
    if isinstance(context, Context):
        return context
    return Context.model_validate(context)


def _context_value(context: Context | None, field: str) -> str | None:
    if context is None:
        return None
    value = {
        "courseCode": context.course_code,
        "academicLevel": context.academic_level,
    }.get(field, getattr(context, field, None))
    return value.strip() if isinstance(value, str) and value.strip() else None


def _official_pnw_url(value: Any) -> str | None:
    url = _nonempty_string(value)
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "pnw.edu" or host.endswith(".pnw.edu")):
        return None
    return url


def _nonempty_string(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _cannot_verify(message: str) -> dict[str, Any]:
    return {
        "outcome": "cannot_verify",
        "message": message,
        "summary": None,
        "required_context": [],
        "citations": [],
        "evidence": [],
        "escalation": None,
    }
