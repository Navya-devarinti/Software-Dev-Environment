from __future__ import annotations


def summarize_policy(question: str, *, supported: bool = True) -> dict[str, object]:
    return {
        "supported": supported,
        "summary": f"The question about '{question}' can be answered using the publicly posted official policy guidance and source references.",
    }
