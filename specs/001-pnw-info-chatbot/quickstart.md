# Quickstart: PNW University Information Chatbot Validation

This guide validates the planned behavior with a small set of representative public-source fixtures. Do not use student data.

## Prerequisites

- A local database populated with approved fixture sources and office routes.
- Fixtures for: a multi-term schedule table, a policy PDF, a catalog prerequisite, two conflicting sources, and a timestamped official alert.
- The application running locally.

## Validation scenarios

Use the request format in [contracts/openapi.yaml](contracts/openapi.yaml) and verify citations against the fixture source URLs and locators described in [data-model.md](data-model.md).

1. Ask for an add/drop deadline with a term. Expect a plain-language answer with the term, deadline conditions, and an official citation.
2. Ask the same question without a term where fixtures include several terms. Expect `needs_context`; no date is selected.
3. Mark the relevant schedule version `unreviewed`, `incomplete`, or past its required review. Expect `cannot_verify` or `escalation_required`, not a deadline.
4. Ask a campus-dependent course question without campus. Expect a campus clarification before a definitive availability answer.
5. Provide two conflicting current sources with no applicable authority scope. Expect a stated conflict and referral, not a selected result. Where a subject-specific authority scope is documented, verify that source is cited.
6. Ask about a room change without a current timestamped official alert. Expect a limitation and official route. Add the alert fixture and verify its citation and context are included.
7. Ask for an individual graduation, PIN, registration, or schedule decision. Expect no individualized outcome and an approved office route or Dean of Students fallback.

## Available checks

Once implementation exists, run its pytest suite and API contract checks. Before deployment, run the stakeholder-approved evaluation set and obtain the unresolved SC-006 quantitative release thresholds.
