from __future__ import annotations


def refresh_source_version(*, source_url: str, review_status: str = "current") -> dict[str, str]:
    return {
        "source_url": source_url,
        "review_status": review_status,
        "status": "reviewed",
    }
