---

description: "Implementation tasks for the PNW University Information Chatbot"
---

# Tasks: PNW University Information Chatbot

**Input**: Design documents from `/specs/001-pnw-info-chatbot/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/openapi.yaml`

**Tests**: Required. The feature specification mandates pytest source-processing and answer-safety scenarios plus API contract checks.

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated independently after the shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches a different file and has no unfinished prerequisite in this phase.
- **[Story]**: User story served by the task (`US1` through `US5`).

## Path Conventions

- Application code: `app/`
- Tests and representative public-source fixtures: `tests/`
- API contract: `specs/001-pnw-info-chatbot/contracts/openapi.yaml`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the single Python 3.12 web application and its local development tooling.

- [X] T001 Create the Python 3.12 package metadata and runtime/test dependencies for FastAPI, HTML/PDF extraction, a relational database library, pytest, and API contract validation in pyproject.toml
- [X] T002 [P] Create the application package layout for API, corpus, rules, and templates modules in app/__init__.py
- [X] T003 [P] Configure pytest discovery and test options in pyproject.toml
- [X] T004 [P] Add local environment configuration documentation with no credentials or student-data settings in .env.example

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the reviewed public-corpus storage, refresh pipeline, answer-safety primitives, and public API shell required by every user story.

**⚠️ CRITICAL**: Complete this phase before beginning user-story work.

- [X] T005 Create relational models for Source, SourceVersion, Evidence, and OfficeRoute in app/corpus/models.py; enforce SourceVersion status values `current`, `superseded`, `incomplete`, or `unreviewed`
- [ ] T006 Implement database engine, session lifecycle, and schema initialization in app/corpus/database.py
- [ ] T007 Implement reviewed-source eligibility, source-version currency, and cadence checks in app/rules/freshness.py; preserve `Daily for urgent updates, each term for deadlines, annually for policy/catalog`
- [ ] T008 [P] Implement citation construction from stored Source title/URL and Evidence locator, never answer-text invention, in app/rules/citations.py
- [ ] T009 [P] Implement public-context validation and collection for campus, term, program, courseCode, and academicLevel in app/rules/context.py
- [ ] T010 [P] Implement the student-data rejection rule and individualized-decision detection in app/rules/privacy.py
- [ ] T011 Implement approved OfficeRoute lookup with a Dean of Students fallback in app/rules/escalation.py
- [ ] T012 Implement source-version extraction interfaces that preserve PDF page/section, HTML heading, table row/header, catalog-entry, and linked-source context in app/corpus/extractors.py
- [ ] T013 Implement the explicit operator-run approved-source refresh command, including review state and source-version replacement, in app/corpus/refresh.py
- [ ] T014 Define FastAPI request/response schemas matching the chat contract, including `answered`, `needs_context`, `cannot_verify`, and `escalation_required`, in app/api/schemas.py
- [ ] T015 Create the FastAPI application, `/v1/chat` router registration, and application-level safe error handling in app/main.py
- [ ] T016 [P] Create representative approved public fixtures for schedules, a policy PDF, catalog prerequisites, conflicting sources, timestamped alerts, and office routes in tests/fixtures/corpus.py
- [ ] T017 Add foundational model, freshness, context, privacy, escalation, extractor, and refresh tests in tests/test_foundation.py
- [ ] T018 Add API contract checks against specs/001-pnw-info-chatbot/contracts/openapi.yaml in tests/test_api_contract.py

**Checkpoint**: A local reviewed corpus can be refreshed and queried through a contract-shaped API without retaining student-specific data.

---

## Phase 3: User Story 1 - Find a Current Deadline (Priority: P1) 🎯 MVP

**Goal**: Return only term-specific, reviewed, current deadline information with its conditions and official citation; otherwise request term context or safely refer the student.

**Independent Test**: With the schedule fixtures, a term-qualified add/drop or financial-aid request returns its term, deadline type, date, conditions, and citation; a multi-term request without a term asks for it; stale, incomplete, or unreviewed schedules never yield a deadline.

- [ ] T019 [P] [US1] Add deadline retrieval tests for term/date/type/condition preservation and missing-term clarification in tests/test_deadlines.py
- [ ] T020 [P] [US1] Add stale, incomplete, unreviewed, and expired deadline safety tests in tests/test_deadline_safety.py
- [ ] T021 [US1] Implement term-aware deadline evidence selection that retains each date with its academic term, deadline type, and conditions in app/corpus/retrieval.py
- [ ] T022 [US1] Implement deadline answer decisions that require term context and accept only current reviewed evidence in app/rules/deadlines.py
- [ ] T023 [US1] Implement cited plain-language deadline response rendering and safe schedule-office referral in app/api/answers.py
- [ ] T024 [US1] Wire the deadline question path through POST /v1/chat in app/api/chat.py

**Checkpoint**: User Story 1 independently satisfies all deadline acceptance scenarios through the public endpoint.

---

## Phase 4: User Story 2 - Understand a Policy or Procedure (Priority: P1)

**Goal**: Explain supported policies and procedures in plain language, including relevant linked instructions, while referring individual decisions to authorized staff.

**Independent Test**: A policy or parking-ticket question returns a bounded explanation, next steps, a source citation (including child-page/PDF evidence where needed), and an appropriate office route for an individual outcome request.

- [ ] T025 [P] [US2] Add policy and procedure explanation tests, including linked parking-payment/appeal evidence, in tests/test_policies.py
- [ ] T026 [P] [US2] Add individual-decision boundary and supported-referral tests for policy questions in tests/test_policy_escalation.py
- [ ] T027 [US2] Implement policy/procedure evidence retrieval across reviewed child pages and related documents in app/corpus/retrieval.py
- [ ] T028 [US2] Implement plain-language policy/procedure summarization with material qualifications and next steps in app/rules/policies.py
- [ ] T029 [US2] Add policy-specific answer and escalation rendering in app/api/answers.py
- [ ] T030 [US2] Wire the policy and procedure question path through POST /v1/chat in app/api/chat.py

**Checkpoint**: User Stories 1 and 2 both work independently, with policy answers never replacing authorized decisions.

---

## Phase 5: User Story 3 - Find Course, Program, or Graduation Information (Priority: P1)

**Goal**: Provide coherent, cited general course, program, and graduation information while requiring applicable public context and declining individualized determinations.

**Independent Test**: A prerequisite or program request produces every material citation and requests missing campus/program/course/academic-level context; individualized graduation eligibility is routed to an advisor or supported office without a determination.

- [ ] T031 [P] [US3] Add prerequisite and campus-dependent course retrieval tests in tests/test_academics.py
- [ ] T032 [P] [US3] Add program/graduation context and individualized-determination safety tests in tests/test_graduation_safety.py
- [ ] T033 [US3] Implement catalog evidence retrieval that groups prerequisites, offerings, program requirements, campus tags, and catalog locators in app/corpus/retrieval.py
- [ ] T034 [US3] Implement academic context requirements and general-versus-individual determination rules in app/rules/academics.py
- [ ] T035 [US3] Add cited academic and graduation limitation response rendering in app/api/answers.py
- [ ] T036 [US3] Wire course, program, and graduation question handling through POST /v1/chat in app/api/chat.py

**Checkpoint**: User Stories 1–3 answer supported general questions with required context and safely route individualized academic decisions.

---

## Phase 6: User Story 4 - Reach the Correct Human or Office (Priority: P1)

**Goal**: Route unsupported, ambiguous, conflicting, and staff-authority questions to a supported office, using Dean of Students only when no approved mapping applies.

**Independent Test**: An unsupported or staff-authority question explains the limitation, returns the mapped department/contact source when present, and uses the documented Dean of Students fallback when mapping is absent; unresolved source conflicts never produce a definitive answer.

- [ ] T037 [P] [US4] Add office-mapping, official-contact citation, and Dean of Students fallback tests in tests/test_office_routes.py
- [ ] T038 [P] [US4] Add relevant-source conflict detection and unresolved-conflict referral tests in tests/test_conflicts.py
- [ ] T039 [US4] Implement relevant-source conflict comparison using subject, term, campus, program, and course scope in app/rules/conflicts.py
- [ ] T040 [US4] Implement limitation explanations and actionable supported-referral assembly in app/rules/escalation.py
- [ ] T041 [US4] Add conflict and office-route response rendering in app/api/answers.py
- [ ] T042 [US4] Wire unsupported, conflicting, and routing-only questions through POST /v1/chat in app/api/chat.py

**Checkpoint**: User Stories 1–4 never guess an unsupported fact or escalation recipient and always expose a supported route when available.

---

## Phase 7: User Story 5 - Check a Rapidly Changing University Update (Priority: P2)

**Goal**: State a rapid room/location change only when a current timestamped official alert or responsible-office update confirms it and its context.

**Independent Test**: An unconfirmed update request returns a limitation and official route; adding a current timestamped alert returns its cited, contextualized update without treating unconfirmed changes as fact.

- [ ] T043 [P] [US5] Add confirmed timestamped-alert and unconfirmed-update safety tests in tests/test_rapid_updates.py
- [ ] T044 [US5] Implement current timestamped alert/office-update verification with applicable context checks in app/rules/rapid_updates.py
- [ ] T045 [US5] Add rapid-update cited answer and unverified-update referral rendering in app/api/answers.py
- [ ] T046 [US5] Wire rapid room and location update handling through POST /v1/chat in app/api/chat.py

**Checkpoint**: All five user stories are independently functional and rapid-change claims are only made from current timestamped official evidence.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete safety contract and document operation of the reviewed corpus.

- [ ] T047 [P] Add end-to-end quickstart validation scenarios for citations, context, freshness, conflicts, escalation, and privacy in tests/test_quickstart_scenarios.py
- [ ] T048 [P] Document approved-source review ownership, daily/termly/annual cadence, and operator refresh steps in README.md
- [ ] T049 Add response logging that excludes questions, context values, student data, chat history, and analytics in app/main.py
- [ ] T050 Run and document the full pytest and API contract validation commands in specs/001-pnw-info-chatbot/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → all user stories.
- **US1, US2, US3, and US4** are P1 increments and may begin in parallel after Phase 2, though their shared files (`app/corpus/retrieval.py`, `app/api/answers.py`, and `app/api/chat.py`) require coordinated sequencing.
- **US5** depends on Phase 2 and can proceed independently of US1–US4.
- **Polish (Phase 8)** depends on every desired user story.

### User Story Dependencies

- **US1 (P1)**: Phase 2 only; recommended MVP.
- **US2 (P1)**: Phase 2 only; reuses shared retrieval and answer modules after US1 changes are integrated.
- **US3 (P1)**: Phase 2 only; reuses shared retrieval and answer modules after preceding changes are integrated.
- **US4 (P1)**: Phase 2 only; relies on foundational `OfficeRoute` and escalation primitives.
- **US5 (P2)**: Phase 2 only; its rapid-update rules are separate from other story rules.

### Within Each User Story

- Write the marked tests first and confirm they fail.
- Implement retrieval/rules before response rendering and endpoint wiring.
- Run that story’s tests plus the API contract checks before accepting its checkpoint.

## Parallel Opportunities

- T002–T004 can run in parallel after T001.
- T007–T010 and T016 can run in parallel after T005–T006 where their module prerequisites permit.
- Each story’s `[P]` test tasks can run concurrently.
- T043 can proceed in parallel with any P1 story after Phase 2; `app/rules/rapid_updates.py` has no story-file conflict.
- T047 and T048 can run in parallel after all stories are complete.

## Parallel Example: User Story 1

```text
Task: "Add deadline retrieval tests for term/date/type/condition preservation and missing-term clarification in tests/test_deadlines.py"
Task: "Add stale, incomplete, unreviewed, and expired deadline safety tests in tests/test_deadline_safety.py"
```

## Parallel Example: User Story 4

```text
Task: "Add office-mapping, official-contact citation, and Dean of Students fallback tests in tests/test_office_routes.py"
Task: "Add relevant-source conflict detection and unresolved-conflict referral tests in tests/test_conflicts.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phases 1 and 2.
2. Complete T019–T024 for term-aware deadlines.
3. Validate its acceptance scenarios with `tests/test_deadlines.py`, `tests/test_deadline_safety.py`, and the API contract checks.
4. Demo only the supported deadline flow, missing-term clarification, and safe non-answer behavior.

### Incremental Delivery

1. Deliver US1 for deadlines.
2. Add US2 for policies and procedures.
3. Add US3 for course, program, and graduation information.
4. Add US4 for safe human routing and conflict handling.
5. Add US5 for timestamped rapid university updates.
