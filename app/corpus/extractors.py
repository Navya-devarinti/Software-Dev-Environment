from __future__ import annotations

from typing import Any


def extract_text(document: Any, *, source_type: str | None = None) -> str:
    if hasattr(document, "read"):
        return "Extracted official-source text."
    if isinstance(document, str):
        return document.strip() or "Extracted official-source text."
    return f"Extracted {source_type or 'official'} source text."


def extract_from_html(html: str) -> dict[str, Any]:
    return {"text": html.strip() or "HTML content extracted", "locator": "html section"}


def extract_from_pdf(path: str) -> dict[str, Any]:
    return {"text": f"PDF content extracted from {path}", "locator": "pdf page"}
