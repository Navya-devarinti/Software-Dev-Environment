from __future__ import annotations


def detect_conflict(documents: list[dict] | None = None) -> bool:
    docs = documents or []
    return len(docs) > 1 and any(doc.get("source") != docs[0].get("source") for doc in docs[1:])
