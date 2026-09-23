# Implementation Plan: PNW University Information Chatbot

**Branch**: `001-pnw-info-chatbot` | **Date**: 2026-09-23 | **Spec**: [spec.md](spec.md)

## Summary

Build one public PNW information application. It accepts general questions, searches a small reviewed corpus of official PNW pages and documents, and returns a plain-language answer with the supporting official links and locations. Before answering, it checks whether the question needs campus, term, program, course, or academic-level context and whether the available source is current, complete, and non-conflicting. If not, it asks for context or gives a clear limitation and a supported office referral.

## Technical Context

**Language/Version**: Python 3.12

**Frontend**: React

**Backend**: Python 3.12 with FastAPI and explicit Pydantic API models; SQLAlchemy 2 for PostgreSQL ORM; BeautifulSoup4; pypdf

**Database**: PostgreSQL with the pgvector extension for evidence embeddings and similarity search

**Deployment**: Docker and Docker Compose for local development and service orchestration

**Storage**: One PostgreSQL database for the reviewed source list, source versions, extracted evidence, office routes, and pgvector-backed embeddings. Original official URLs remain the student-facing source of record. Retrieval combines vector similarity with structured metadata filters for source status, freshness, and campus/program/term/course context.

**Testing**: pytest with isolated database fixtures for source processing and answer-safety scenarios; `openapi-spec-validator` plus live endpoint contract checks

**Target Platform**: A Dockerized React frontend and FastAPI backend deployed as one public web application with PostgreSQL/pgvector

**Project Type**: RAG-based web application with a React client, FastAPI chat API, PostgreSQL/pgvector retrieval store, and operator-run source refresh command

**Performance Goals**: Correctness, citations, provenance, and safe abstention take priority. Response-time, availability, coverage, and satisfaction targets remain `TBD` until a stakeholder-approved baseline and measurement window exist; do not invent release thresholds.

**Constraints**: No sign-in, student records, personalization, chat history, analytics, or student-specific data. Only reviewed official PNW sources are eligible. Deadlines retain their term and conditions; rapidly changing updates require a current timestamped official source.

**Scale/Scope**: A reviewed set of PNW policies, schedules, catalog pages, procedures, parking information, contacts, and official alerts. The initial design does not assume a complete crawl, background worker, OCR pipeline, or automated source discovery; ingestion remains explicit and operator-run.

## Constitution Check

The project constitution is an unfilled template and defines no ratified gates. The feature gates are: cite factual answers, preserve source context, require relevant campus/term context, decline unsafe answers, and never handle student-specific data.

**Pre-design result: PASS.**

## Project Structure

```text
app/
├── api/                    # Public question/answer endpoint
├── corpus/                 # Source refresh and extraction code
├── rules/                  # Context, freshness, conflict, and escalation checks
└── templates/              # Minimal public web page

frontend/
└── src/                    # React public chat client

infra/
└── docker-compose.yml      # React, FastAPI, and PostgreSQL/pgvector services

tests/
├── fixtures/               # Small representative official-source fixtures
└── test_*.py

specs/001-pnw-info-chatbot/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/openapi.yaml
```

**Structure Decision**: Use a React frontend and one FastAPI backend, with PostgreSQL/pgvector as the shared reviewed-corpus and embedding store. The backend performs retrieval-augmented generation by filtering eligible evidence, retrieving semantically relevant chunks, applying safety rules, and rendering cited answers. Use explicit API schemas separate from SQLAlchemy corpus models. Source refresh is an explicit operator task; no autonomous crawler or separate worker is required initially.

## Complexity Tracking

No constitution violations require justification.

## Post-Design Constitution Check

**PASS.** The reduced model stores only public-source information and office routes. The contract contains no account or student fields, and the validation guide exercises citation, context, freshness, conflict, abstention, and escalation behavior. Quantitative operational targets remain explicitly deferred to stakeholder approval rather than being guessed.
