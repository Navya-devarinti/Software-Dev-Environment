from __future__ import annotations


def classify_deadline_question(question: str) -> str:
    q = (question or "").lower()
    if any(token in q for token in ["add", "drop", "withdraw", "deadline"]):
        return "deadline"
    return "general"


def evaluate_deadline(question: str, *, term: str | None = None) -> dict[str, str | bool | None]:
    if not term:
        return {"requires_context": True, "term": None, "current": False}
    return {"requires_context": False, "term": term, "current": True}
