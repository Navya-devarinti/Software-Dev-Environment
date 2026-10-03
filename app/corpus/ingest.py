"""Offline RAG corpus ingestion CLI.

Run from the project root with:
    python -m app.corpus.ingest
"""

from __future__ import annotations

import hashlib
from datetime import date
from urllib.parse import urlparse

import httpx
from sqlalchemy import desc, select

from app.corpus.chunking import chunk_text
from app.corpus.database import SessionLocal, init_db
from app.corpus.embeddings import embed_texts
from app.corpus.models import (
    Evidence,
    Source,
    SourceVersion,
    SourceVersionStatus,
)
from app.corpus.parsing import parse_html, parse_pdf


SOURCES = [
    {
        "url": "https://www.pnw.edu/admissions/undergraduate/",
        "title": "PNW Undergraduate Admissions",
        "category": "admissions",
        "owner_office": "Office of Undergraduate Admissions",
    },
    {
        "url": "https://www.pnw.edu/admissions/undergraduate/how-to-apply/",
        "title": "PNW Undergraduate How to Apply",
        "category": "admissions",
        "owner_office": "Office of Undergraduate Admissions",
    },
    {
        "url": "https://www.pnw.edu/bursar/tuition-and-fees/",
        "title": "PNW Tuition and Fees",
        "category": "tuition_and_fees",
        "owner_office": "Office of the Bursar",
    },
]


def fetch_and_parse(client: httpx.Client, source: dict):
    response = client.get(source["url"])
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    is_pdf = (
        "application/pdf" in content_type
        or urlparse(str(response.url)).path.lower().endswith(".pdf")
    )

    if is_pdf:
        return parse_pdf(
            response.content,
            fallback_title=source["title"],
        )

    return parse_html(
        response.text,
        fallback_title=source["title"],
    )


def ingest_source(client: httpx.Client, session, source: dict) -> tuple[int, int]:
    document = fetch_and_parse(client, source)

    chunks = []
    for page_locator, page_text in document.pages:
        chunks.extend(
            chunk_text(
                page_text,
                chunk_size=1200,
                overlap=200,
                locator_prefix=page_locator,
            )
        )

    if not chunks:
        raise ValueError(f"No text chunks produced for {source['url']}")

    # Hash normalized extracted text so unchanged pages can be skipped.
    normalized_text = "\n".join(text for _, text in document.pages)
    content_hash = hashlib.sha256(
        normalized_text.encode("utf-8")
    ).hexdigest()
    source_note = f"sha256:{content_hash}"

    db_source = session.scalar(
        select(Source).where(Source.url == source["url"])
    )

    if db_source is None:
        db_source = Source(
            title=document.title[:500],
            url=source["url"],
            category=source["category"],
            owner_office=source["owner_office"],
            authority_scope="Official public university information",
            review_frequency="Review periodically and before relying on time-sensitive details",
            last_reviewed_on=date.today(),
        )
        session.add(db_source)
        session.flush()
    else:
        db_source.title = document.title[:500]
        db_source.category = source["category"]
        db_source.owner_office = source["owner_office"]
        db_source.last_reviewed_on = date.today()

    versions = session.scalars(
        select(SourceVersion)
        .where(SourceVersion.source_id == db_source.id)
        .order_by(desc(SourceVersion.captured_on), desc(SourceVersion.id))
    ).all()

    if versions and versions[0].source_note == source_note:
        print(f"SKIP unchanged: {source['url']}")
        return 0, 0

    # Preserve older versions but mark previously current versions superseded.
    for old_version in versions:
        if old_version.status == SourceVersionStatus.CURRENT:
            old_version.status = SourceVersionStatus.SUPERSEDED

    version = SourceVersion(
        source_id=db_source.id,
        status=SourceVersionStatus.CURRENT,
        source_note=source_note,
    )
    session.add(version)
    session.flush()

    vectors = embed_texts([chunk["text"] for chunk in chunks])

    for chunk, vector in zip(chunks, vectors, strict=True):
        session.add(
            Evidence(
                source_version_id=version.id,
                text=chunk["text"],
                locator=chunk["locator"],
                context={
                    **chunk["context"],
                    "source_url": source["url"],
                    "source_title": document.title,
                    "category": source["category"],
                    "embedding_model": "BAAI/bge-base-en-v1.5",
                },
                embedding=vector,
            )
        )

    print(
        f"INGESTED: {document.title} | "
        f"{len(chunks)} chunks | {source['url']}"
    )
    return 1, len(chunks)


def main() -> None:
    init_db()
    total_documents = 0
    total_chunks = 0

    headers = {
        "User-Agent": "PNWInformationChatbotCorpusBot/1.0 (educational project)"
    }

    with httpx.Client(
        follow_redirects=True,
        timeout=45,
        headers=headers,
    ) as client:
        with SessionLocal() as session:
            try:
                for source in SOURCES:
                    documents, chunks = ingest_source(
                        client, session, source
                    )
                    total_documents += documents
                    total_chunks += chunks

                session.commit()
            except Exception:
                session.rollback()
                raise

    print("\nIngestion finished.")
    print(f"New source versions: {total_documents}")
    print(f"New evidence chunks: {total_chunks}")


if __name__ == "__main__":
    main()
