# Research: PNW University Information Chatbot

## Decisions

### Decision: Start with one application and a reviewed source list

**Rationale**: The feature needs reliable answers from a known set of public PNW material, not independent web, ingestion, vector-search, and worker services. One application can expose the public interface and run an operator-invoked refresh for the approved source list.

**Alternatives considered**: Separate frontend/API/worker services, automated crawling, and external vector stores add deployment and review work without evidence that the available corpus requires them.

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
