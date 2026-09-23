from __future__ import annotations


def validate_rapid_update(question: str, *, timestamped: bool = False, approved: bool = False) -> dict[str, bool]:
    q = (question or "").lower()
    needs_authority = any(token in q for token in ["room", "location", "change", "alert", "update"])
    return {"needs_authority": needs_authority, "timestamped": timestamped, "approved": approved}
