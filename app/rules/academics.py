from __future__ import annotations


def requires_academic_context(question: str, context: dict | None = None) -> list[str]:
    del context
    q = (question or "").lower()
    required: list[str] = []
    if any(token in q for token in ["course", "prerequisite", "catalog", "graduation"]):
        required.append("courseCode")
    if any(token in q for token in ["major", "program", "degree"]):
        required.append("program")
    return required
