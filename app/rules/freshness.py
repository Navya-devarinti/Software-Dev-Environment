from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def _coerce_date(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return date.fromisoformat(text)
    return None


def _coerce_status(value: str | None) -> str:
    return (value or "").strip().lower()


def is_current_status(status: str | None) -> bool:
    return _coerce_status(status) == "current"


def is_current_effective_period(
    effective_from: date | str | None,
    effective_to: date | str | None,
    *,
    today: date | None = None,
) -> bool:
    if today is None:
        today = date.today()

    effective_from = _coerce_date(effective_from)
    effective_to = _coerce_date(effective_to)

    if effective_from is not None and today < effective_from:
        return False
    if effective_to is not None and today > effective_to:
        return False
    return True


def is_reviewed_recently(
    last_reviewed_on: date | str | None,
    review_frequency: str | None,
    *,
    today: date | None = None,
) -> bool:
    if today is None:
        today = date.today()

    reviewed_on = _coerce_date(last_reviewed_on)
    if reviewed_on is None:
        return False

    normalized_frequency = (review_frequency or "").strip().lower()
    if not normalized_frequency:
        return False

    if "daily" in normalized_frequency or "day" in normalized_frequency:
        max_age = timedelta(days=1)
    elif "term" in normalized_frequency or "semester" in normalized_frequency:
        max_age = timedelta(days=120)
    elif "annual" in normalized_frequency or "year" in normalized_frequency:
        max_age = timedelta(days=365)
    else:
        return False

    return today - reviewed_on <= max_age


def is_eligible_source_version(
    version: Any,
    *,
    source: Any | None = None,
    today: date | None = None,
) -> bool:
    if version is None:
        return False

    if today is None:
        today = date.today()

    if not is_current_status(getattr(version, "status", None)):
        return False

    if not is_current_effective_period(
        getattr(version, "effective_from", None),
        getattr(version, "effective_to", None),
        today=today,
    ):
        return False

    source_obj = source or getattr(version, "source", None)
    if source_obj is None:
        return False

    last_reviewed_on = getattr(source_obj, "last_reviewed_on", None)
    review_frequency = getattr(source_obj, "review_frequency", None)
    return is_reviewed_recently(
        last_reviewed_on,
        review_frequency,
        today=today,
    )


def deadline_requires_term(question: str) -> bool:
    q = question.lower()
    return any(
        token in q
        for token in [
            "deadline",
            "add",
            "drop",
            "withdraw",
            "semester",
            "term",
        ]
    )
