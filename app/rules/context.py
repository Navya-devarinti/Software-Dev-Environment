from __future__ import annotations

from typing import Literal

from app.api.schemas import Context

ALLOWED_CAMPUSES = {"Hammond", "Westville"}
ALLOWED_LEVELS = {"undergraduate", "graduate"}


def normalize_context(context: Context | dict | None) -> Context | None:
    if context is None:
        return None
    if isinstance(context, Context):
        return context
    return Context.model_validate(context)


def missing_context_fields(question: str, context: Context | dict | None = None) -> list[str]:
    normalized = normalize_context(context)
    q = question.lower()
    required: list[str] = []

    if any(token in q for token in ["campus", "westville", "hammond", "location"]) and (
        not normalized or not normalized.campus
    ):
        required.append("campus")

    if any(token in q for token in ["term", "semester", "deadline", "add/drop", "withdraw"]) and (
        not normalized or not normalized.term
    ):
        required.append("term")

    if any(token in q for token in ["program", "major", "college", "degree"] ) and (
        not normalized or not normalized.program
    ):
        required.append("program")

    if any(token in q for token in ["course", "prerequisite", "catalog"] ) and (
        not normalized or not normalized.course_code
    ):
        required.append("courseCode")

    if any(token in q for token in ["graduate", "undergraduate", "academic level"] ) and (
        not normalized or not normalized.academic_level
    ):
        required.append("academicLevel")

    return list(dict.fromkeys(required))
