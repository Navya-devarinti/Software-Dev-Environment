# Implementation Plan: PNW University Information Chatbot

**Branch**: `001-pnw-info-chatbot` | **Date**: 2026-09-19 | **Spec**: [spec.md](spec.md)

## Summary

Build one public PNW information application. It accepts general questions, searches a small reviewed corpus of official PNW pages and documents, and returns a plain-language answer with the supporting official links and locations. Before answering, it checks whether the question needs campus, term, program, course, or academic-level context and whether the available source is current, complete, and non-conflicting. If not, it asks for context or gives a clear limitation and a supported office referral.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI; a standard HTML/PDF extraction library; a relational database library

**Storage**: One relational database for the reviewed source list, source versions, extracted evidence, and office routes. Original official URLs remain the student-facing source of record; no object store or separate search/vector database is required for the initial scope.

**Testing**: pytest for source processing and answer-safety scenarios; API contract checks

**Target Platform**: One HTTPS-hosted public web application

**Project Type**: Single web application with a public chat endpoint and an operator-run source refresh command

**Performance Goals**: Correctness, citations, and safe abstention take priority. The quantitative response-time and availability targets remain approval items from the specification and must be set before deployment.

**Constraints**: No sign-in, student records, personalization, chat history, analytics, or student-specific data. Only reviewed official PNW sources are eligible. Deadlines retain their term and conditions; rapidly changing updates require a current timestamped official source.

**Scale/Scope**: A reviewed set of PNW policies, schedules, catalog pages, procedures, parking information, contacts, and official alerts. The initial design does not assume a complete crawl, background worker, OCR pipeline, or automated source discovery.

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

**Structure Decision**: Keep the public interface, corpus refresh, and answer-safety checks in one application. Source refresh is an explicit operator task; separate services are not justified by the current corpus or feature scope.

## Complexity Tracking

No constitution violations require justification.

## Post-Design Constitution Check

**PASS.** The reduced model stores only public-source information and office routes. The contract contains no account or student fields, and the validation guide exercises citation, context, freshness, conflict, abstention, and escalation behavior.
