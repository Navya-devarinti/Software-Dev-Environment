---

description: "Implementation tasks for the PNW University Information Chatbot"
---

# Tasks: PNW University Information Chatbot

**Input**: Design documents from `/specs/001-pnw-info-chatbot/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/openapi.yaml`

**Tests**: Required by the feature specification. Include source-processing, safe-abstention, privacy, RAG retrieval, frontend, integration, and API contract tests.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an independent increment after the shared foundation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no unfinished prerequisite.
- **[Story]**: User story served by the task (`US1` through `US5`).

## Path Conventions

- Backend application: `app/`
- React application: `frontend/`
- Docker and service configuration: `infra/`, `Dockerfile`, `frontend/Dockerfile`
- Tests and public fixtures: `tests/`
- API contract: `specs/001-pnw-info-chatbot/contracts/openapi.yaml`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the React/FastAPI application, PostgreSQL/pgvector development environment, and shared test tooling.

- [X] T001 Create the Python 3.12 backend package metadata and dependencies for FastAPI, Pydantic, SQLAlchemy 2, psycopg, pgvector, BeautifulSoup4, pypdf, pytest, and OpenAPI validation in `pyproject.toml`
- [X] T002 Create the React frontend with the selected TypeScript-capable build setup and package scripts in `frontend/package.json`
- [X] T003 [P] Create the backend package layout for `api`, `corpus`, `rules`, and `templates` in `app/__init__.py`
- [X] T004 [P] Create the React application shell and source layout in `frontend/src/main.tsx` and `frontend/src/App.tsx`
- [X] T005 [P] Configure pytest discovery and test options in `pyproject.toml`
- [X] T006 [P] Add Dockerfiles for the FastAPI backend and React frontend in `Dockerfile` and `frontend/Dockerfile`
- [X] T007 Create Docker Compose services for React, FastAPI, and PostgreSQL with pgvector, health checks, a persistent local database volume, and network wiring in `infra/docker-compose.yml`
- [X] T008 [P] Document non-secret PostgreSQL, pgvector, backend, and frontend settings in `.env.example`
- [X] T009 [P] Add frontend and backend ignore/build configuration in `frontend/.gitignore` and `.gitignore`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the reviewed-corpus persistence, embedding/retrieval boundary, safety primitives, API shell, and shared UI behavior required by every user story.

**CRITICAL**: Complete this phase before beginning user-story implementation.

- [X] T010 Implement the PostgreSQL engine, short-lived SQLAlchemy session lifecycle, transaction helpers, pgvector extension initialization, and schema initialization in `app/corpus/database.py`
- [X] T011 [P] Extend the relational models for `Source`, `SourceVersion`, `Evidence`, and `OfficeRoute` with PostgreSQL-compatible constraints and a pgvector embedding column in `app/corpus/models.py`
- [ ] T012 [P] Create Alembic configuration and the initial PostgreSQL/pgvector migration in `alembic.ini`, `migrations/env.py`, and `migrations/versions/`
- [X] T013 Implement source-version eligibility, freshness cadence, effective-period, and current-status checks in `app/rules/freshness.py`
- [X] T014 [P] Implement citation construction exclusively from stored source title, URL, and evidence locator in `app/rules/citations.py`
- [X] T015 [P] Implement public context validation for `campus`, `term`, `program`, `courseCode`, and `academicLevel` in `app/rules/context.py`
- [X] T016 [P] Implement student-data rejection and individualized-decision detection in `app/rules/privacy.py`
- [X] T017 [P] Implement approved category-to-office routing and the Dean of Students fallback in `app/rules/escalation.py`
- [X] T018 Implement HTML/PDF/linked-source extraction interfaces that preserve headings, page/section locators, table row/header relationships, catalog entries, and related-source context in `app/corpus/extractors.py`
- [X] T019 Implement embedding generation and pgvector persistence behind an explicit provider interface in `app/corpus/embeddings.py`
- [X] T020 Implement hybrid RAG retrieval that applies source-status, freshness, effective-date, and public-context filters before pgvector similarity ranking in `app/corpus/retrieval.py`
- [X] T021 Implement the explicit operator-run approved-source refresh flow, including version replacement, review state, extraction completeness, and embedding updates in `app/corpus/refresh.py`
- [X] T022 Define Pydantic request/response schemas matching `contracts/openapi.yaml`, including camelCase aliases and the four outcomes, in `app/api/schemas.py`
- [X] T023 Create the FastAPI application, `/v1/chat` router registration, CORS policy for the React origin, and safe error handling in `app/main.py` and `app/api/chat.py`
- [X] T024 [P] Create the shared React API client, typed contract models, and error-state handling in `frontend/src/api/chat.ts`
- [X] T025 [P] Create the shared React chat form, response, citation, required-context, and escalation components in `frontend/src/components/`
- [X] T026 [P] Add foundational PostgreSQL model, freshness, context, privacy, escalation, extractor, embedding, and retrieval tests with isolated database fixtures in `tests/test_foundation.py`
- [X] T027 [P] Add API schema and live `/v1/chat` contract checks against `specs/001-pnw-info-chatbot/contracts/openapi.yaml` in `tests/test_api_contract.py`
- [X] T028 [P] Add Docker Compose health and service connectivity checks in `tests/test_deployment.py`

**Checkpoint**: Docker Compose starts React, FastAPI, and PostgreSQL/pgvector; a reviewed corpus can be refreshed, embedded, filtered, retrieved, and exposed through a contract-shaped API without student-specific data.

---

## Phase 3: User Story 1 - Find a Current Deadline (Priority: P1) 🎯 MVP

**Goal**: Return only term-specific, reviewed, current deadline information with its conditions and official citation; otherwise request term context or safely refer the student.

**Independent Test**: A term-qualified add/drop or financial-aid request returns its term, deadline type, date, conditions, and citation; a missing-term multi-term request returns `needs_context`; stale, incomplete, expired, or unreviewed schedules never produce a definitive deadline.

### Tests for User Story 1

- [ ] T029 [P] [US1] Add term-aware deadline retrieval tests for date, type, conditions, citations, and missing-term clarification in `tests/test_deadlines.py`
- [ ] T030 [P] [US1] Add deadline safety tests for stale, incomplete, unreviewed, superseded, and expired schedule evidence in `tests/test_deadline_safety.py`

### Implementation for User Story 1

- [ ] T031 [US1] Implement term-aware schedule evidence selection that keeps term, deadline type, date, refund conditions, and source locator together in `app/corpus/retrieval.py`
- [ ] T032 [US1] Implement deadline decision rules requiring term context and current reviewed evidence in `app/rules/deadlines.py`
- [ ] T033 [US1] Implement cited plain-language deadline and safe schedule-office referral rendering in `app/api/answers.py`
- [ ] T034 [US1] Wire deadline classification, retrieval, rules, and response rendering through `POST /v1/chat` in `app/api/chat.py`
- [ ] T035 [US1] Render deadline answers, missing-context prompts, citations, and safe referrals in `frontend/src/components/DeadlineAnswer.tsx` and `frontend/src/App.tsx`

**Checkpoint**: User Story 1 satisfies all deadline acceptance scenarios through the API and React client.

---

## Phase 4: User Story 2 - Understand a Policy or Procedure (Priority: P1)

**Goal**: Explain supported policies and procedures in plain language, including relevant linked instructions, while referring individual decisions to authorized staff.

**Independent Test**: A policy or parking-ticket question returns a bounded explanation, next steps, every material citation including child-page/PDF evidence, and an appropriate office route for an individual outcome request.

### Tests for User Story 2

- [ ] T036 [P] [US2] Add policy and procedure RAG tests for linked child pages, linked PDFs, bounded explanations, and parking instructions in `tests/test_policies.py`
- [ ] T037 [P] [US2] Add individual-decision boundary and supported-referral tests in `tests/test_policy_escalation.py`

### Implementation for User Story 2

- [ ] T038 [US2] Implement policy/procedure retrieval across reviewed related sources without losing source relationships or locators in `app/corpus/retrieval.py`
- [ ] T039 [US2] Implement plain-language policy summarization with material qualifications, next steps, and safe abstention in `app/rules/policies.py`
- [ ] T040 [US2] Implement policy answer and individual-decision escalation rendering with stored citations in `app/api/answers.py`
- [ ] T041 [US2] Wire policy/procedure classification and retrieval through `POST /v1/chat` in `app/api/chat.py`
- [ ] T042 [US2] Render policy explanations, linked citations, next steps, and escalation states in `frontend/src/components/PolicyAnswer.tsx` and `frontend/src/App.tsx`

**Checkpoint**: User Stories 1 and 2 both work independently, with policy answers never replacing authorized decisions.

---

## Phase 5: User Story 3 - Find Course, Program, or Graduation Information (Priority: P1)

**Goal**: Provide coherent, cited general course, program, and graduation information while requiring applicable public context and declining individualized determinations.

**Independent Test**: A prerequisite or program request produces all material citations, requests missing campus/program/course/academic-level context, and routes individualized graduation eligibility to an advisor or supported office without a determination.

### Tests for User Story 3

- [ ] T043 [P] [US3] Add catalog prerequisite, offering, campus, and academic-level retrieval tests in `tests/test_academics.py`
- [ ] T044 [P] [US3] Add program/graduation context and individualized-determination safety tests in `tests/test_graduation_safety.py`

### Implementation for User Story 3

- [ ] T045 [US3] Implement catalog evidence retrieval that groups prerequisites, offerings, program requirements, campus tags, and catalog locators in `app/corpus/retrieval.py`
- [ ] T046 [US3] Implement academic context requirements and general-versus-individual determination rules in `app/rules/academics.py`
- [ ] T047 [US3] Implement cited academic explanations and graduation limitation/referral rendering in `app/api/answers.py`
- [ ] T048 [US3] Wire course, program, and graduation classification, retrieval, and rules through `POST /v1/chat` in `app/api/chat.py`
- [ ] T049 [US3] Render prerequisite/program explanations, context requests, citations, and advisor referrals in `frontend/src/components/AcademicAnswer.tsx` and `frontend/src/App.tsx`

**Checkpoint**: User Stories 1–3 answer supported general questions with required context and safely route individualized academic decisions.

---

## Phase 6: User Story 4 - Reach the Correct Human or Office (Priority: P1)

**Goal**: Route unsupported, ambiguous, conflicting, and staff-authority questions to a supported office, using Dean of Students only when no approved mapping applies.

**Independent Test**: An unsupported or staff-authority question explains the limitation, returns the mapped department/contact source when present, and uses the documented fallback when mapping is absent; unresolved conflicts never produce a definitive answer.

### Tests for User Story 4

- [ ] T050 [P] [US4] Add office-mapping, official-contact citation, and Dean of Students fallback tests in `tests/test_office_routes.py`
- [ ] T051 [P] [US4] Add relevant-source conflict detection and unresolved-conflict referral tests in `tests/test_conflicts.py`

### Implementation for User Story 4

- [ ] T052 [US4] Implement conflict comparison across matching subject, term, campus, program, and course scope with authority-scope resolution in `app/rules/conflicts.py`
- [ ] T053 [US4] Implement limitation explanations and actionable supported-referral assembly in `app/rules/escalation.py`
- [ ] T054 [US4] Implement conflict, unsupported-question, and office-route response rendering with contact citations in `app/api/answers.py`
- [ ] T055 [US4] Wire unsupported, conflicting, staff-authority, and routing-only questions through `POST /v1/chat` in `app/api/chat.py`
- [ ] T056 [US4] Render escalation reason, office, contact link, and supporting citation states in `frontend/src/components/EscalationCard.tsx` and `frontend/src/App.tsx`

**Checkpoint**: User Stories 1–4 never guess an unsupported fact or escalation recipient and always expose a supported route when available.

---

## Phase 7: User Story 5 - Check a Rapidly Changing University Update (Priority: P2)

**Goal**: State a rapid room/location change only when a current timestamped official alert or responsible-office update confirms it and its context.

**Independent Test**: An unconfirmed update returns a limitation and official route; a current timestamped alert returns its cited, contextualized update without treating unconfirmed changes as fact.

### Tests for User Story 5

- [ ] T057 [P] [US5] Add confirmed timestamped-alert, context matching, stale-alert, and unconfirmed-update safety tests in `tests/test_rapid_updates.py`

### Implementation for User Story 5

- [ ] T058 [US5] Implement current timestamped alert and responsible-office update verification with applicable context checks in `app/rules/rapid_updates.py`
- [ ] T059 [US5] Implement rapid-update cited answer and unverified-update referral rendering in `app/api/answers.py`
- [ ] T060 [US5] Wire rapid room and location update classification through `POST /v1/chat` in `app/api/chat.py`
- [ ] T061 [US5] Render confirmed rapid updates, timestamps, citations, and unverified-update referrals in `frontend/src/components/RapidUpdateAnswer.tsx` and `frontend/src/App.tsx`

**Checkpoint**: All five user stories are independently functional and rapid-change claims use only current timestamped official evidence.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete RAG safety contract, containerized workflow, privacy boundary, and reviewed-corpus operation.

- [ ] T062 [P] Add end-to-end quickstart scenarios for citations, context, freshness, vector retrieval, conflicts, escalation, privacy, and rapid updates in `tests/test_quickstart_scenarios.py`
- [ ] T063 [P] Add React component and API-client tests for loading, validation errors, `needs_context`, citations, escalation, and safe non-answer states in `frontend/src/**/*.test.tsx`
- [ ] T064 [P] Add backend logging that excludes questions, context values, student data, chat history, and analytics in `app/main.py`
- [ ] T065 [P] Add Docker health/readiness behavior and production-safe CORS/environment validation in `app/main.py` and `infra/docker-compose.yml`
- [ ] T066 [P] Document approved-source ownership, daily/termly/annual review cadence, operator refresh, embedding regeneration, and Docker Compose operation in `README.md`
- [ ] T067 Run the full pytest suite, API contract checks, frontend tests, and Docker Compose quickstart validation and record commands/results in `specs/001-pnw-info-chatbot/quickstart.md`
- [ ] T068 Verify that all RAG answer paths enforce provenance, current reviewed evidence, context matching, citation construction, privacy rejection, conflict handling, and escalation rules in `tests/test_safety_matrix.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; Docker, frontend, backend, and test scaffolding can begin in parallel where marked.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Stories (Phases 3–7)**: Depend on the foundational phase.
- **Polish (Phase 8)**: Depends on the desired user stories and their shared integration points.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; recommended MVP.
- **US2 (P1)**: Can start after Phase 2; reuses the shared retrieval, answer, chat, and React shell.
- **US3 (P1)**: Can start after Phase 2; reuses shared retrieval and answer components.
- **US4 (P1)**: Can start after Phase 2; relies on foundational OfficeRoute and citation primitives.
- **US5 (P2)**: Can start after Phase 2; its rapid-update rule is independent of the other story rules.

### Within Each User Story

- Write story tests first and confirm they fail.
- Implement retrieval and safety rules before response rendering.
- Implement API wiring before frontend integration.
- Run the story tests plus API contract checks at each checkpoint.

## Parallel Opportunities

- Phase 1: T003–T009 can run in parallel after T001/T002 prerequisites; T006 and T008 are independent of application logic.
- Phase 2: T013–T019, T024–T028 can run in parallel where their module dependencies permit; T020–T023 follow the relevant primitives.
- Each story's test tasks can run in parallel with other story test tasks after Phase 2.
- US1: T029 and T030 can run in parallel; T031–T035 then proceed in retrieval/rules/rendering/wiring order.
- US2: T036 and T037 can run in parallel; frontend rendering can proceed separately from policy-rule implementation.
- US3: T043 and T044 can run in parallel; catalog retrieval and academic safety rules are separable.
- US4: T050 and T051 can run in parallel; conflict analysis and office mapping are separate rule surfaces.
- US5: T057 can run in parallel with the other story tests and T058 can proceed independently after foundational retrieval.

## Parallel Example: User Story 1

```text
Task: "Add term-aware deadline retrieval tests in tests/test_deadlines.py"
Task: "Add deadline safety tests in tests/test_deadline_safety.py"
```

## Parallel Example: User Story 4

```text
Task: "Add office-route tests in tests/test_office_routes.py"
Task: "Add conflict-detection tests in tests/test_conflicts.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational PostgreSQL/pgvector, RAG, API, React, and safety work.
3. Complete T029–T035 for term-aware deadlines.
4. Validate the deadline, missing-term, stale-source, citation, privacy, and contract scenarios.
5. Stop for stakeholder review before adding broader story categories.

### Incremental Delivery

1. Deliver US1 for current deadlines.
2. Add US2 for policies and procedures.
3. Add US3 for course, program, and graduation information.
4. Add US4 for safe human routing and conflict handling.
5. Add US5 for timestamped rapid university updates.
6. Complete Phase 8 cross-cutting validation and operational documentation.

### Notes

- Every task starts with `- [ ]`, has a sequential ID, uses `[P]` only for parallelizable work, and includes a story label for user-story tasks.
- Every task names at least one concrete file path.
- pgvector similarity is never sufficient for eligibility; provenance, freshness, context, conflict, privacy, and escalation rules remain mandatory.
- No task adds accounts, student records, personalization, chat history, analytics, unrestricted web search, or autonomous crawling.
