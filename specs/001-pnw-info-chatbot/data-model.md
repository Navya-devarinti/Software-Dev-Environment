# Data Model: PNW University Information Chatbot

Only public PNW source information is stored. No student, account, session, analytics, or chat-history entity exists.

## Entities

### Source

An approved official PNW page or document to review and use.

| Field | Purpose |
|---|---|
| `id` | Internal identifier. |
| `title` | Public source title. |
| `url` | Canonical official PNW URL. |
| `category` | Policy, schedule, catalog, procedure, contact, or alert. |
| `owner_office` | Office responsible for the source category. |
| `authority_scope` | Subject/context for which this source is the authoritative one, when known. |
| `review_frequency` | Daily for urgent updates, each term for deadlines, annually for policy/catalog. |
| `last_reviewed_on` | Date the source was last confirmed for its required cadence. |
| `related_source_id` | Optional parent or related approved source. |

### SourceVersion

The reviewed state of a source at a point in time.

| Field | Purpose |
|---|---|
| `id`, `source_id` | Version and source identity. |
| `captured_on` | When the application retrieved the public source. |
| `published_or_updated_on` | Date stated by the source, if available. |
| `effective_from`, `effective_to` | Applicability dates, when available. |
| `status` | `current`, `superseded`, `incomplete`, or `unreviewed`. Only `current` supports a current factual answer. |
| `source_note` | Brief reason for incomplete, unreviewed, or superseded status. |

### Evidence

A citable extracted section of a reviewed source version.

| Field | Purpose |
|---|---|
| `id`, `source_version_id` | Links evidence to its exact source version. |
| `text` | Extracted public content needed for retrieval and answer drafting. |
| `locator` | PDF page/section, webpage heading, table row, or catalog entry. |
| `context` | Only applicable public qualifiers: term, campus, program/college, course, academic level, deadline type, and conditions. |

### OfficeRoute

An approved public route for issues the application cannot answer.

| Field | Purpose |
|---|---|
| `category` | Issue category and optional scope. |
| `office_name` | Responsible PNW office or Dean of Students fallback. |
| `contact_url` | Official public contact page. |
| `source_url` | Official page that supports the route. |

## Answer rules

- A factual answer may use only `Evidence` from a `current` `SourceVersion` whose public context matches the question.
- A deadline must include its term, deadline type, and applicable conditions from `context`.
- If required context is missing, ask for it instead of guessing.
- If relevant current evidence is incomplete, stale by review frequency, ambiguous, or conflicts with another relevant authoritative source, do not give a definitive fact. State the limitation and use an `OfficeRoute` when supported; otherwise use the Dean of Students fallback.
- Citations display the `Source` title and URL plus the `Evidence` locator. They are produced from stored source information, not invented in answer text.
