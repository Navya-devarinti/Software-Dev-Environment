# Research: PNW University Information Chatbot

## Decisions

### Decision: Use a React client, FastAPI service, and PostgreSQL/pgvector retrieval store

**Rationale**: React provides the public chat interface, FastAPI exposes the stable `/v1/chat` contract, and PostgreSQL with pgvector keeps relational provenance and semantic retrieval in one operational store. The backend can implement RAG by filtering reviewed evidence before similarity search, then applying context, freshness, conflict, privacy, and escalation rules before returning a cited answer.

**Alternatives considered**: A server-rendered-only UI would not satisfy the selected frontend stack. A separate vector database or autonomous crawling service would split provenance and review state without being justified by the initial corpus.

### Decision: Use source-first retrieval, not a generic corpus split

**Rationale**: Store extracted passages with their official URL and locator. Preserve PDF page/section, HTML heading and linked-page relationship, table row/header relationship, and catalog context. For schedules, retain term, deadline type, date, and conditions together. This supports direct citations and avoids detached dates or prerequisites.

**Alternatives considered**: Fixed-size text chunks or bare search snippets lose the context required by DI-001 through DI-006.

### Decision: Refresh and review only approved sources

**Rationale**: Each source has an owner, category, review timing, and official URL. Refresh urgent updates daily, deadlines each term, and policy/catalog sources annually. Mark a source version current only when its review is complete. An incomplete or unreviewed source can support a limitation or referral, not a definitive claim.

**Alternatives considered**: Unrestricted crawling cannot establish authority, ownership, or currency. A background scheduler is not necessary for the initial operator-managed scope.

### Decision: Resolve conflicts at answer time using source category and scope

**Rationale**: Compare only sources relevant to the same subject, term, campus, program, or course. Use the documented subject-specific official source when one is known. Otherwise state the conflict, avoid a conclusion, and direct the student to the supported office. No separate claim graph or automated adjudication is needed.

**Alternatives considered**: A global document ranking or model-generated reconciliation can silently choose the wrong source.

### Decision: Keep answers public, cited, and non-personalized

**Rationale**: The request may include only a general question and optional public context such as campus or term. The application does not request, store, or use student identifiers, records, schedules, or history. Every factual answer includes official source links and locators; unsupported or individualized questions receive a limitation and escalation route.

**Alternatives considered**: Accounts, chat memory, student-system connections, analytics, and personalized recommendations are outside the specification.

### Decision: Test safety cases alongside supported answers

**Rationale**: Representative fixtures can prove the required behavior for multi-term schedules, missing campus context, incomplete extraction, stale sources, conflicts, unconfirmed alerts, and individual-case requests without needing a large production corpus.

**Alternatives considered**: Happy-path-only testing would not establish safe abstention or escalation.

### Decision: Use explicit API schemas separate from corpus models

**Rationale**: FastAPI/Pydantic request and response models keep the public `/v1/chat` contract stable and prevent SQLAlchemy persistence details from leaking into responses. Camel-case contract fields such as `courseCode` and `requiredContext` should use explicit aliases. The four outcome values remain contract-level semantics, while conditional requirements are enforced by application rules and tests.

**Alternatives considered**: Returning untyped dictionaries is shorter but weakens validation, generated documentation, and protection against accidental field disclosure.

### Decision: Use short-lived SQLAlchemy sessions with PostgreSQL and pgvector integrity enabled

**Rationale**: One SQLAlchemy engine and session factory with a short-lived session per operation/request fits the reviewed corpus. PostgreSQL provides the required relational integrity and concurrent access, while pgvector stores embeddings beside source/version/evidence metadata for filtered similarity search. Refresh writes must use explicit commit/rollback boundaries, and Docker Compose should provide a reproducible local PostgreSQL/pgvector service.

**Alternatives considered**: A global session risks leaked transactions and cross-request state; an embedded file database does not satisfy the application database requirement; a separate search database would duplicate provenance and complicate consistency.

### Decision: Use hybrid RAG retrieval with metadata gating

**Rationale**: Embedding similarity finds semantically relevant official passages, but it must never decide eligibility by itself. Query retrieval should first or concurrently apply structured filters for current review status, approved source identity, effective dates, and matching campus, program, course, term, and academic level. The answer generator receives only eligible evidence plus locators and context, and the rules layer can abstain when retrieval is empty, incomplete, stale, ambiguous, or conflicting.

**Alternatives considered**: Pure keyword search misses paraphrased questions; unrestricted vector search can surface stale or context-mismatched facts; model-only answers cannot provide the required provenance.

### Decision: Run the stack with Docker Compose

**Rationale**: Docker Compose provides a repeatable local environment for the React frontend, FastAPI backend, and PostgreSQL image with pgvector. Configuration remains environment-based, and the database volume is local-only. Production deployment may use an equivalent container platform without changing the service boundaries.

**Alternatives considered**: Host-installed services create version drift and make pgvector setup inconsistent; Kubernetes is unnecessary for the initial single-application scope.

### Decision: Extract structural evidence and abstain on incomplete parsing

**Rationale**: HTML extraction must preserve headings, links, and table row/header relationships. PDF extraction should run page-by-page with page/section locators and mark empty or suspicious output incomplete. BeautifulSoup does not execute JavaScript and pypdf does not perform OCR, so dynamically revealed or scanned content must be supplied through an approved capture or withheld/escalated.

**Alternatives considered**: Flattened text or generic chunks lose schedule, policy, and prerequisite context; automatic OCR or unrestricted rendering would add an unreviewed dependency and new quality risks.

### Decision: Keep quantitative operational targets as approval items

**Rationale**: The specification leaves response time, availability, coverage, accuracy, and satisfaction thresholds open. Define the metrics and collect a pilot baseline before stakeholders approve targets; until then, gate implementation on provenance, privacy, contract, freshness, conflict, extraction-integrity, and safe-abstention behavior rather than guessed numbers.

**Alternatives considered**: Arbitrary latency or uptime values would create false release criteria and are not supported by the current requirements.
