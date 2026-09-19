# Feature Specification: PNW University Information Chatbot

**Feature Branch**: `not assigned`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: Student, Dean of Students Office, and corpus-review research for a Purdue University Northwest (PNW) information chatbot.

## Problem Statement

PNW students currently have to assemble answers from search engines, the PNW website, MyPNW, policy documents, the academic catalog, advisors, professors, classmates, and the existing Leo chatbot. Information is fragmented, often linked rather than explained, and may be campus-, program-, or term-specific. Students report difficulty locating direct, current answers and have encountered outdated graduation information with material academic consequences.

The chatbot shall provide a single, understandable entry point for general university information. Its primary value is trustworthy, source-supported answers and safe referral when that trust cannot be established. Correctness takes precedence over coverage, speed, or conversational polish.

## Clarifications

### Session 2026-09-19

- Q: What student-specific data may the chatbot handle? → A: No student-specific data; no sign-in required.
- Q: When official PNW sources conflict, which source should govern the chatbot’s answer? → A: Subject-specific official source prevails; unresolved conflicts require human review.
- Q: How should PNW assign ownership and review timing for source content? → A: Assign an owning office per source category; review urgent updates daily, deadlines each term, and policies/catalog annually.
- Q: How should the chatbot choose a human or office when escalation is required? → A: Use approved category-to-office mappings; use Dean of Students as the documented fallback when no mapping applies.
- Q: Which source may confirm a sudden room or location change before the chatbot states it as fact? → A: A current official PNW alert or responsible office update with a timestamp.

## Target Users and Required Context

### Primary Users

- **PNW students** seeking general information about policies, procedures, deadlines, programs, courses, registration, graduation, parking, and university contacts.
- **University staff** who need a traceable answer or an efficient way to direct recurring questions to an authoritative source or responsible office.

### Context That May Be Needed

The chatbot shall obtain or confirm only the context needed for a reliable answer. Relevant context includes campus (Hammond or Westville), college/program, course, academic level, academic term, question category, and whether the question concerns a general rule or an individual case. It must not infer a campus, term, program, or student-specific status when doing so could change the answer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a Current Deadline (Priority: P1)

A student asks when they may add, drop, or withdraw from a course, or when a financial-aid deadline occurs.

**Why this priority**: Missing a deadline can materially affect enrollment, finances, and academic progress.

**Independent Test**: Ask about a date for a selected term and verify that the answer identifies the applicable term, gives the supported deadline and conditions, cites the official source, and does not present expired dates as current.

**Acceptance Scenarios**:

1. **Given** a student asks for an add/drop deadline and identifies a current academic term, **When** the official schedule contains that term, **Then** the chatbot provides the term-specific date, relevant conditions, and an official citation.
2. **Given** the schedule contains several terms or an expired date, **When** the student does not identify a term, **Then** the chatbot asks for the term or explains the alternatives rather than selecting one.
3. **Given** no current authoritative deadline can be confirmed, **When** the student asks for a deadline, **Then** the chatbot declines to state a deadline and directs the student to the responsible office or official schedule.

---

### User Story 2 - Understand a Policy or Procedure (Priority: P1)

A student asks how registration, academic standing, grade appeals, parking ticket payment/appeals, or another university process works.

**Why this priority**: These are recurring questions reported by both students and the Dean of Students Office.

**Independent Test**: Ask a representative policy question and verify a plain-language, bounded explanation, required next steps, cited official evidence, and an appropriate referral for individual decisions.

**Acceptance Scenarios**:

1. **Given** authoritative policy information supports the question, **When** a student asks for an explanation, **Then** the chatbot summarizes the applicable process in plain language and links to the supporting official source.
2. **Given** payment or appeal instructions are located in a relevant child page or linked document, **When** a student asks about a parking ticket, **Then** the chatbot provides the supported instructions and source rather than only a top-level link.
3. **Given** the question requires an authorized decision about the student's particular situation, **When** the student asks for an outcome, **Then** the chatbot gives only general information and refers the student to the responsible office.

---

### User Story 3 - Find Course, Program, or Graduation Information (Priority: P1)

A student asks about course prerequisites, campus-specific availability, plan-of-study requirements, graduate requirements, or graduation procedures.

**Why this priority**: Incorrect information in this area can delay graduation; students specifically reported difficulty combining scattered requirements.

**Independent Test**: Ask a course or program question requiring campus/program context and verify that the answer requests missing context, consolidates supported information, identifies limitations, and cites every material source.

**Acceptance Scenarios**:

1. **Given** prerequisite information is distributed across catalog elements, **When** a student asks about a course prerequisite, **Then** the chatbot gives a coherent, source-supported prerequisite explanation without inventing a course path.
2. **Given** campus affects course availability, **When** the student's campus is unknown, **Then** the chatbot asks which campus applies rather than guessing.
3. **Given** a student asks whether they personally satisfy graduation or plan-of-study requirements, **When** a staff review or approval is required, **Then** the chatbot describes general published requirements and directs the student to the appropriate advisor or office for an individualized determination.

---

### User Story 4 - Reach the Correct Human or Office (Priority: P1)

A student asks who can resolve an issue, including a registration error, advisor/PIN issue, unclear policy, or question the chatbot cannot support reliably.

**Why this priority**: Students and staff identified accurate routing as a core need and a safe alternative to unsupported answers.

**Independent Test**: Ask a question with no supported answer or requiring staff authority and verify that the chatbot explains why it cannot decide, identifies the best supported department/contact route, and supplies an official contact source when available.

**Acceptance Scenarios**:

1. **Given** a supported department mapping exists, **When** the student asks who handles an issue, **Then** the chatbot identifies the relevant office and provides the official contact source.
2. **Given** sources conflict or lack enough evidence, **When** the chatbot cannot answer reliably, **Then** it explicitly says so, avoids a guess, and offers a supported escalation path.

---

### User Story 5 - Check a Rapidly Changing University Update (Priority: P2)

A student asks about a sudden room or location change.

**Why this priority**: Students expect current information, but rapidly changing updates require particularly strong validation.

**Independent Test**: Ask about an update whose current official status cannot be confirmed and verify that the chatbot does not state an unverified change as fact and directs the student to an appropriate official channel.

**Acceptance Scenarios**:

1. **Given** a current, authoritative update is available, **When** a student asks about a room or location change, **Then** the chatbot communicates the update with its source and applicable context.
2. **Given** the update cannot be validated as current, **When** a student asks about it, **Then** the chatbot states that it cannot confirm the change and points to the applicable official channel or staff contact.

### Edge Cases

- A page lists Fall, Spring, and Summer dates in one table; the chatbot must not separate a date from its term, deadline type, or refund condition.
- A policy PDF and a webpage disagree, or multiple versions of the same policy exist.
- A required section of a PDF, child page, table, or expandable page cannot be extracted completely.
- A question uses an ambiguous college name, campus, course identifier, term, or policy topic.
- A student asks for a personalized registration, PIN, schedule, graduation, or staff-decision outcome.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept natural-language questions about general PNW policies, rules, deadlines, academic processes, course/program requirements, registration, graduation procedures, parking procedures, and appropriate university contacts.
- **FR-002**: The system MUST provide a direct, plain-language answer when authoritative information sufficiently supports one; it MUST NOT respond with links alone when a supported explanation can be provided.
- **FR-003**: The system MUST cite or link the official PNW source or sources supporting each material factual claim in an answer.
- **FR-004**: The system MUST preserve enough source context for a student or staff member to verify the specific policy, procedure, date, requirement, or contact stated.
- **FR-005**: The system MUST identify when campus, program/college, course, academic level, or academic term is necessary to answer accurately and request or present that context instead of guessing.
- **FR-006**: The system MUST use term-aware information for deadlines and schedules, retaining the relationship between a date, its academic term, deadline type, and applicable conditions.
- **FR-007**: The system MUST validate time-sensitive information against the current date and source currency before presenting it as current; expired information MUST be identified as expired or withheld from a current answer.
- **FR-008**: The system MUST retrieve and explain supported course prerequisite information as a coherent set of requirements, including relevant campus context when applicable.
- **FR-009**: The system MUST distinguish general published requirements from an individualized determination of a student's eligibility, schedule, registration, or graduation status.
- **FR-010**: The system MUST identify the appropriate university department, office, or human contact for a supported issue category and provide an official contact source when one is available.
- **FR-011**: The system MUST decline to provide a factual answer when authoritative evidence is unavailable, incomplete, ambiguous, outdated, or conflicting in a way that prevents a reliable conclusion.
- **FR-012**: When declining an answer, the system MUST clearly explain the limitation, distinguish uncertainty from sourced facts, provide the most relevant official source when available, and escalate to an appropriate office or human contact when supported.
- **FR-013**: The system MUST detect and surface conflicts between relevant authoritative sources rather than selecting a result without disclosure.
- **FR-014**: The system MUST avoid inventing policies, deadlines, requirements, procedures, course availability, contacts, exceptions, or university decisions.
- **FR-015**: The system MUST state rapidly changing information only when a current official PNW alert or responsible office update confirms it with a timestamp and applicable context; otherwise it MUST refer students to the applicable official channel.
- **FR-016**: The system MUST communicate answers in understandable language while retaining material qualifications, exceptions, and uncertainty needed to prevent a misleading answer.
- **FR-017**: The system MUST operate without sign-in and MUST NOT collect, access, retain, expose, or use student-specific data.

### Correctness and Safety Requirements

- **CS-001**: Correctness of university information MUST take precedence over broad answer coverage, response fluency, and conversational completion.
- **CS-002**: Every policy, deadline, requirement, procedure, availability statement, and contact recommendation presented as fact MUST be traceable to authoritative evidence.
- **CS-003**: The system MUST not infer missing facts from partial, stale, or loosely related information.
- **CS-004**: The system MUST not make personalized academic, registration, financial-aid, conduct, or graduation decisions and MUST route requests requiring authorized staff judgment to the appropriate human process.
- **CS-005**: The system MUST make the distinction between confirmed information, conditional information, and information it cannot verify understandable to the student.

### Data Ingestion and Corpus Requirements

The source corpus must accommodate differences in document structure because a uniform generic text-splitting approach can lose meaning: it can separate schedule dates from their terms, omit dynamically revealed content, miss linked instructions, or fragment prerequisite relationships.

- **DI-001**: The corpus MUST support full-document processing of authoritative PDF policies and handbooks, preserving headings, sections, page/location context, and source links needed for traceable retrieval.
- **DI-002**: The corpus MUST preserve the relationships in table-heavy HTML, including term, date, deadline type, refund percentage, and other applicable conditions.
- **DI-003**: The corpus MUST include relevant content exposed through click-to-reveal, expandable, or dynamically rendered official pages where that content is required for a complete answer.
- **DI-004**: The corpus MUST follow relevant official child pages, linked PDFs, and related pages where top-level content alone is insufficient, while preserving each source's relationship and avoiding duplicate or contextless material.
- **DI-005**: The corpus MUST represent structured academic catalog information so prerequisites, offerings, program requirements, and campus tags can be retrieved with their applicable context.
- **DI-006**: The corpus MUST retain document identity, official location, publication or update information when available, source type, and relationships to related official sources.
- **DI-007**: Potentially changing sources, including academic schedules and university updates, MUST be identifiable for freshness review before being used as current information.
- **DI-008**: If an authoritative source cannot be completely processed, the system MUST not imply that an answer derived from it is complete; it MUST limit the answer or escalate as appropriate.
- **DI-009**: PNW MUST assign an owning office to each source category. Urgent updates MUST be reviewed daily, deadlines each academic term, and policies and catalog content annually.

### Freshness and Versioning Requirements

- **FV-001**: The system MUST associate time-sensitive content with the applicable academic term, effective period, and source version or update date when available.
- **FV-002**: The system MUST not describe a past deadline as current.
- **FV-003**: When a page has changed, the system MUST use only a current, confirmed version for current guidance or disclose that currency cannot be confirmed.
- **FV-004**: When official sources conflict, the system MUST use the authoritative source specific to the subject; if no applicable authority can be established, it MUST withhold a definitive conclusion pending human resolution.
- **FV-005**: The source corpus MUST support review and replacement of outdated content without losing the traceability necessary to explain what was previously sourced.

### Escalation Requirements

- **ER-001**: The system MUST escalate or direct the student to a human/department when authoritative information is missing, conflicting, incomplete, or stale.
- **ER-002**: The system MUST escalate questions involving highly specific individual circumstances, authorized staff decisions, personalized scheduling, PIN-specific registration actions, individualized graduation determinations, or potential material student harm from an incorrect answer.
- **ER-003**: The system MUST not claim an escalation recipient is correct unless that routing is supported by an official PNW source; otherwise it MUST state the routing limitation and provide the best available official starting point.
- **ER-004**: The system MUST make escalation actionable by explaining why staff help is needed and, when supported, how to reach the relevant office.
- **ER-005**: The system MUST use approved category-to-office mappings for escalation. When no mapping applies, it MUST direct the student to the Dean of Students as the documented fallback.

### Out of Scope

- Making personalized course scheduling decisions.
- Making individualized graduation decisions or certifying graduation eligibility.
- Performing PIN-specific registration actions or accessing/registering on a student's behalf.
- Acting as an academic advisor or replacing an authorized staff decision.
- Making financial-aid, academic-standing, conduct, appeal, or other university determinations for an individual.
- Inventing or inferring policies, exceptions, requirements, deadlines, contacts, or other information not supported by authoritative sources.

### Non-Functional Requirements

- **NFR-001 Accuracy**: The chatbot MUST prioritize source-supported correctness and safe abstention over answer coverage.
- **NFR-002 Reliability**: The chatbot MUST consistently provide citations, limitation notices, and escalation behavior for supported, uncertain, and unsupported queries.
- **NFR-003 Explainability**: Students and staff MUST be able to identify the official source and contextual basis of material answers.
- **NFR-004 Freshness**: Time-sensitive answers MUST be validated for term and currency before presentation as current.
- **NFR-005 Response speed**: The chatbot SHOULD provide prompt answers for simple questions; an acceptable response-time target is an open question.
- **NFR-006 Availability**: Expected availability, support windows, and outage behavior are open questions.
- **NFR-007 Privacy and security**: The chatbot MUST operate without sign-in and MUST not collect, access, retain, expose, or use student-specific information.
- **NFR-008 Maintainability**: Assigned source-category owners MUST be able to review source currency, source conflicts, missing content, and changes to the official corpus according to the required review schedule.

## Key Entities

- **Question**: A student or staff request, including its category and any needed context.
- **Answer**: A plain-language response containing sourced facts, applicable conditions, uncertainty, and escalation guidance where required.
- **Official Source**: A PNW webpage, policy, catalog entry, schedule, PDF, or official update used as evidence.
- **Source Version**: The identifiable current or historical state of an official source, including its effective date or update information when available.
- **Academic Term**: The period that scopes schedules, dates, course information, and other time-sensitive guidance.
- **Campus Context**: The Hammond or Westville context that may affect availability, procedures, or contacts.
- **Program/College Context**: The academic program, department, or college that scopes academic requirements or contacts.
- **Escalation Route**: An official department, office, person, or channel for questions requiring human assistance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a stakeholder-approved evaluation set of answerable policy, deadline, procedure, course, and contact questions, 100% of material factual claims in answers are traceable to cited official sources.
- **SC-002**: In a stakeholder-approved evaluation set of unavailable, ambiguous, stale, or conflicting-source questions, 100% of responses avoid an unsupported definitive answer and provide the required limitation and supported referral where available.
- **SC-003**: In evaluation scenarios where campus or term changes the correct answer, 100% of responses obtain or explicitly present the required context before giving a definitive answer.
- **SC-004**: In evaluation scenarios involving multi-term schedules, no response presents a deadline without its applicable term and conditions.
- **SC-005**: Students can verify every evaluated answer's official basis using the source citation or link supplied by the chatbot.
- **SC-006**: Quantitative targets for response time, deployment accuracy threshold, availability, coverage, and user satisfaction are defined and approved before deployment.

## Assumptions

- The chatbot initially provides general informational guidance, not personalized student-record advice or decisions.
- PNW can identify official sources and responsible content owners before a production release.
- Official source pages and documents may remain distributed; centralization means a unified student-facing discovery experience, not necessarily one underlying source.
- The source corpus will include the relevant PNW website pages, academic catalog information, policies, schedules, and linked authoritative documents within the approved scope.
- Some questions will appropriately end in a human referral because authoritative public information cannot establish an answer.

## Open Questions / Ambiguities

1. What campus, program/college, course, term, and academic-level context must be collected before different answer categories may be answered definitively?
2. What response-time, availability, coverage, accuracy/evaluation, and user-satisfaction thresholds are acceptable before deployment?
3. Which situations, beyond those listed here, require mandatory human escalation because an incorrect answer could materially harm a student?
