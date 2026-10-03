"""Split extracted document text into overlapping chunks."""

from __future__ import annotations


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1200,
    overlap: int = 200,
    locator_prefix: str = "Document",
) -> list[dict]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and less than chunk_size")

    text = " ".join(text.split())
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer ending at a word boundary when possible.
        if end < len(text):
            boundary = text.rfind(" ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(
                {
                    "text": chunk,
                    "locator": f"{locator_prefix}; characters {start}-{end}",
                    "context": {
                        "chunk_index": len(chunks),
                        "character_start": start,
                        "character_end": end,
                    },
                }
            )

        if end >= len(text):
            break

        start = end - overlap

    return chunks
