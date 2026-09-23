# Copilot instructions

## Repository status and source of truth

This is a Python 3.12 FastAPI project for a public Purdue University Northwest (PNW) information chatbot. The runtime is only partially implemented: `app/corpus/models.py` and the package markers exist, while the remaining application and test modules are specified but not yet built. Treat the feature artifacts under `specs/001-pnw-info-chatbot/` as the behavioral source of truth, especially:

- `spec.md` for user-visible requirements and safety boundaries.
- `contracts/openapi.yaml` for the `/v1/chat` request and response contract.
- `data-model.md` for entity meaning and answer eligibility.
- `tasks.md` for the implementation order and intended file/module boundaries.
- `quickstart.md` for required validation scenarios.

There is no README or CONTRIBUTING guide. `.specify/` contains the Speckit workflow and templates; `.agents/skills/` contains the available Speckit skills. The constitution at `.specify/memory/constitution.md` is still an unfilled template, so the feature artifacts—not that template—define the current design constraints.

## Build, test, and run commands

The project metadata and dependencies are in `pyproject.toml`. There are no custom task scripts or configured linter.

```bash
# Install the package and test dependencies
python -m pip install -e '.[test]'

# Run the complete test suite
python -m pytest

# Run one test module
python -m pytest tests/test_foundation.py

# Run one test function or scenario
python -m pytest tests/test_foundation.py::test_name
```

Pytest discovers `tests/test_*.py` and enables `-ra`. API contract tests must validate against `specs/001-pnw-info-chatbot/contracts/openapi.yaml`. The planned local server entry point is `app.main:app`; use `uvicorn app.main:app --reload` after that module exists. There is no application entry point, test suite, lint command, or database initialization command in the current checkout.

## Implementation workflow

Follow the dependency order in `specs/001-pnw-info-chatbot/tasks.md`: database/models and safety primitives first; retrieval and rules next; then response rendering, endpoint wiring, story-specific tests, and cross-cutting validation/documentation. Keep the shared modules `app/corpus/retrieval.py`, `app/api/answers.py`, and `app/api/chat.py` coordinated rather than creating story-specific parallel implementations. When using the Speckit workflow, keep `spec.md`, `plan.md`, `tasks.md`, and the contract synchronized.

## Architecture

Keep the system as one application with four cooperating areas:

- `app/api/` exposes the public HTTP contract. Request/response schemas and routing must stay aligned with the OpenAPI document; the four normal outcomes are `answered`, `needs_context`, `cannot_verify`, and `escalation_required`.
- `app/corpus/` owns the reviewed official-source corpus, relational persistence, extraction, and explicit operator-run refresh. The intended entities are `Source`, `SourceVersion`, `Evidence`, and `OfficeRoute`.
- `app/rules/` makes safety decisions before response rendering: public-context requirements, privacy/student-data rejection, freshness/cadence, citation construction, conflict handling, academic/deadline/policy rules, rapid-update verification, and escalation.
- `app/templates/` is reserved for the minimal public web page; the initial feature is still centered on the API.

The application has one public boundary, `POST /v1/chat`. It should retrieve only from the reviewed corpus, apply safety/routing rules before rendering, and return one of `answered`, `needs_context`, `cannot_verify`, or `escalation_required`. The initial storage is PostgreSQL with pgvector for embedding similarity search through `DATABASE_URL`; Docker Compose provides the local database, and source refresh is an explicit operator-run operation, not a background crawler.

The design deliberately avoids accounts, student records, personalization, chat history, analytics, background crawling, external vector search, and unrestricted web search.

## Domain invariants and conventions

- Only reviewed official PNW sources are eligible. A factual answer may use only `Evidence` attached to a `SourceVersion` with `current` status and matching public context.
- Preserve context with evidence instead of detaching facts: schedules retain term, deadline type, date, and conditions; extracted material retains PDF page/section, HTML heading, table row/header, catalog entry, or linked-source relationship.
- Citations must be constructed from stored source title/URL and evidence locator. Never invent citations or locators in answer text.
- Missing campus, term, program, course, or academic-level context must produce a clarification response rather than a guessed answer. A deadline must retain its term and conditions.
- Stale, incomplete, unreviewed, ambiguous, conflicting, or unconfirmed rapidly changing information must not produce a definitive factual answer. Explain the limitation and use an approved office route where one exists.
- Resolve conflicts only among relevant sources with matching subject/context. Prefer a documented subject-specific authority scope; otherwise report the conflict and escalate instead of silently ranking sources.
- Reject student-specific data and individualized decisions (for example, an individual graduation, registration, PIN, or schedule outcome). The application handles general public information only.
- `OfficeRoute` is the supported escalation mapping; use the documented Dean of Students fallback only when no approved mapping applies.
- Source refresh is explicit and operator-run. Preserve original official URLs as the student-facing source of record, and keep review cadence meaningful: daily for urgent updates, each term for deadlines, and annually for policy/catalog sources.
- Do not add fields or persistence for accounts, student data, sessions, chat history, or analytics. Local configuration belongs in `.env` copied from `.env.example`; never commit credentials or student-specific data.
