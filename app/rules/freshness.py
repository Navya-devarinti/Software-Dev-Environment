from __future__ import annotations

from datetime import date


def is_current_status(status: str | None) -> bool:
    return (status or "").lower() == "current"


def is_current_effective_period(
    effective_from: date | str | None,
    effective_to: date | str | None,
    *,
    today: date | None = None,
) -> bool:
    if today is None:
        today = date.today()

    if isinstance(effective_from, str):
        effective_from = date.fromisoformat(effective_from)
    if isinstance(effective_to, str):
        effective_to = date.fromisoformat(effective_to)

    if effective_from is not None and today < effective_from:
        return False
    if effective_to is not None and today > effective_to:
        return False
    return True


def deadline_requires_term(question: str) -> bool:
    q = question.lower()
    return any(token in q for token in ["deadline", "add", "drop", "withdraw", "semester", "term"])
