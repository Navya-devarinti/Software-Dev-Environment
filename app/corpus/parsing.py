"""Extract useful text from HTML pages and PDF documents."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass
class ParsedDocument:
    title: str
    pages: list[tuple[str, str]]  # (locator, text)


def parse_html(html: str, fallback_title: str = "PNW webpage") -> ParsedDocument:
    soup = BeautifulSoup(html, "html.parser")

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else fallback_title
    )

    for element in soup.select(
        "script, style, nav, footer, header, noscript, "
        "svg, form, aside"
    ):
        element.decompose()

    main = soup.find("main") or soup.find("article") or soup.body or soup

    lines = []
    for element in main.find_all(
        ["h1", "h2", "h3", "h4", "p", "li", "tr"]
    ):
        text = element.get_text(" ", strip=True)
        if text:
            lines.append(text)

    # Avoid duplicate consecutive lines.
    cleaned = []
    for line in lines:
        if not cleaned or cleaned[-1] != line:
            cleaned.append(line)

    text = "\n".join(cleaned).strip()
    if not text:
        raise ValueError("No readable text was extracted from the HTML page")

    return ParsedDocument(
        title=title.strip() or fallback_title,
        pages=[("Webpage content", text)],
    )


def parse_pdf(content: bytes, fallback_title: str = "PNW PDF") -> ParsedDocument:
    reader = PdfReader(BytesIO(content))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((f"PDF page {page_number}", text))

    if not pages:
        raise ValueError(
            "No extractable text found in the PDF. "
            "The PDF may be scanned and require OCR."
        )

    return ParsedDocument(title=fallback_title, pages=pages)
