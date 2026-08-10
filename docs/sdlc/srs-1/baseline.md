## Purpose

This is the requirements baseline for Budget Checker's "foundation" feature: the architectural skeleton (a decoupled FastAPI backend and a React+MobX frontend), a public static landing page, and a draft database schema (users, receipts, budgets). It is the frozen reference that architecture/design and implementation are built and verified against. Nothing in this document is invented — every requirement, quality attribute, and scenario here is carried forward verbatim from the approved artifacts of the problem, concept, requirements, and acceptance stages of this SDLC process. This is the third SDLC run for this same feature (proc-3): proc-1 completed under the original 5-stage template; proc-2 reproduced the same content under the newly-extended 9-stage template but was aborted at the implementation stage because its check commands (build-v1, typecheck-v1, etc.) were hardcoded to Meridian's own repo layout rather than budget-checker's; the founder fixed the check commands (now parameterized via a maker-answered build-command question) and added an sdlc_abort capability to unblock this restart.

## Scope

**In scope**, per the approved problem brief ([[prob-1]]) and solution concept ([[prob-1/concept-1]]):
- The architectural skeleton: a FastAPI backend and a React+MobX frontend, deployed as two independent services, able to reach each other.
- A public static landing page describing the product, requiring no authentication.
- A draft database schema defining `users`, `receipts`, and `budgets` as entities, designed so a user's data can be deleted without leaving orphaned records (GDPR-adjacent).
- Basic failure handling for the backend: invalid input, database unavailability, and request timeouts each produce a generic error response and a server-side log entry.
- Two backend performance/availability targets (warm response time, cold-start recovery time).

**Out of scope**, carried forward from [[prob-1]] and [[prob-1/concept-1]]:
- Receipt-photo recognition (OCR), text parsing of receipts, automatic purchase categorization, duplicate-photo detection.
- A real user registration/authentication flow — the schema defines a `users` entity, but no login/signup is wired up in this feature.
- A single-server SSR architecture — excluded because the concept chose a decoupled frontend/backend architecture.
- Non-PostgreSQL databases — excluded because PostgreSQL was the founder's stated preference for this stage.

## Definitions

| Term | Meaning in this baseline |
|---|---|
| Invalid input | Input that fails validation on a given field or endpoint. Which specific values are invalid per field/endpoint is not yet defined and is deferred to design. |
| Generic error message | An error response that communicates that a request failed without exposing internal implementation details — no stack traces, no internal identifiers, no framework/library-specific error text. |
| Database unavailable | The database is unreachable (e.g. connection refused) or fails to respond to a query. Both cases are treated identically by every requirement in this baseline. |
| Dependent table | A table holding rows that reference a `users` row. Currently: `receipts` and `budgets`. |
| Orphaned record | A row in a dependent table whose referenced user no longer exists. |
| Configured timeout | A timeout duration applied to backend request processing. The specific value is not yet chosen. |
| Warm (backend) | The backend service instance is already running and is not resuming from a free-tier idle sleep. |
| Resuming from idle sleep / cold start | Recovering from a free-tier hosting provider's practice of stopping an inactive service instance and restarting it on the next request. The specific timing cited in AVAIL-NFR-1 (15-minute inactivity threshold, 30–60s restart) is Render's documented free-tier behavior; it may not directly apply if a different provider is ultimately chosen. |

## Functional requirements

### LAND-1 — Public landing page access
**Statement:** When an anonymous visitor requests the landing page, the frontend application shall display the product description without requiring authentication.
**Priority:** must · **Verification:** demonstration · **Source:** [[prob-1/concept-1/req-1]]

### SKEL-1 — Backend reachable from frontend
**Statement:** When the frontend requests the backend's health-check endpoint, the backend service shall respond indicating it is available.
**Priority:** must · **Verification:** test · **Source:** [[prob-1/concept-1/req-2]]

### DATA-1 — Draft DB schema defines core entities
**Statement:** The database schema shall define entities for users, receipts, and budgets.
**Priority:** must · **Verification:** inspection · **Source:** [[prob-1/concept-1/req-3]]

### DATA-2 — DB schema supports deleting a user's data
**Statement:** The database schema shall support deletion of a user's data without leaving orphaned records in dependent tables.
**Priority:** must · **Verification:** analysis · **Source:** [[prob-1/concept-1/req-4]]

### ERR-1 — Invalid input produces a generic error response
**Statement:** If the backend receives invalid input on an API request, then the backend service shall respond with a generic error message.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-5]]

### ERR-2 — Database unavailability produces a generic error response
**Statement:** If the database is unavailable when the backend processes a request, then the backend service shall respond with a generic error message.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-6]]

### ERR-3 — Timeout produces a generic error response
**Statement:** If a request to the backend exceeds the configured timeout, then the backend service shall respond with a generic error message.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-7]]

### ERR-4 — Invalid input is logged server-side
**Statement:** If the backend receives invalid input on an API request, then the backend service shall record the failure in its server-side logs.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-8]]

### ERR-5 — Database unavailability is logged server-side
**Statement:** If the database is unavailable when the backend processes a request, then the backend service shall record the failure in its server-side logs.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-9]]

### ERR-6 — Timeout is logged server-side
**Statement:** If a request to the backend exceeds the configured timeout, then the backend service shall record the failure in its server-side logs.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/req-10]]

## Quality attributes

### PERF-NFR-1 — Backend warm response time
**Statement:** While the backend service is warm (not in a cold-start state), the backend service shall respond to a health-check request within 300 ms.
**Measure:** metric = response time for `GET /health`; threshold = 300 ms; conditions = single request, instance already warm, free-tier hosting.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/qa-1]] — threshold proposed by the maker in proc-1, confirmed by the founder there, reconfirmed unchanged across proc-2 and this run.

### AVAIL-NFR-1 — Backend cold-start recovery time
**Statement:** While the backend service is resuming from a free-tier idle sleep, the backend service shall become responsive to a health-check request within 60 seconds.
**Measure:** metric = time to first successful health-check response after idle sleep; threshold = 60 seconds; conditions = after at least 15 minutes of inactivity on the free-tier host.
**Priority:** should · **Verification:** test · **Source:** [[prob-1/concept-1/qa-2]] — threshold proposed by the maker in proc-1 from researched Render free-tier behavior, confirmed by the founder there, reconfirmed unchanged across proc-2 and this run.

## Acceptance scenarios

Each functional requirement's scenarios are lifted verbatim into a standalone `.feature` file, registered alongside this document:

| Requirement | Feature file |
|---|---|
| LAND-1 | `features/LAND-1.feature` (2 scenarios) |
| SKEL-1 | `features/SKEL-1.feature` (1 scenario) |
| DATA-1 | `features/DATA-1.feature` (2 scenarios) |
| DATA-2 | `features/DATA-2.feature` (2 scenarios) |
| ERR-1 | `features/ERR-1.feature` (1 scenario outline, 3 examples) |
| ERR-2 | `features/ERR-2.feature` (2 scenarios) |
| ERR-3 | `features/ERR-3.feature` (2 scenarios) |
| ERR-4 | `features/ERR-4.feature` (2 scenarios) |
| ERR-5 | `features/ERR-5.feature` (2 scenarios) |
| ERR-6 | `features/ERR-6.feature` (3 scenarios) |

PERF-NFR-1 and AVAIL-NFR-1 have no `.feature` file — see Open questions and assumptions.

## Traceability matrix

See `traceability-matrix.md` for the full table.

| Requirement | Traces up to | Priority | Verification | Scenarios |
|---|---|---|---|---|
| LAND-1 [[prob-1/concept-1/req-1]] | [[prob-1/concept-1]] → [[prob-1]] | must | demonstration | [[prob-1/concept-1/req-1/feature-1]] (2 scenarios) |
| SKEL-1 [[prob-1/concept-1/req-2]] | [[prob-1/concept-1]] → [[prob-1]] | must | test | [[prob-1/concept-1/req-2/feature-1]] (1 scenario) |
| DATA-1 [[prob-1/concept-1/req-3]] | [[prob-1/concept-1]] → [[prob-1]] | must | inspection | [[prob-1/concept-1/req-3/feature-1]] (2 scenarios) |
| DATA-2 [[prob-1/concept-1/req-4]] | [[prob-1/concept-1]] → [[prob-1]] | must | analysis | [[prob-1/concept-1/req-4/feature-1]] (2 scenarios) |
| ERR-1 [[prob-1/concept-1/req-5]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-5/feature-1]] (1 outline, 3 examples) |
| ERR-2 [[prob-1/concept-1/req-6]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-6/feature-1]] (2 scenarios) |
| ERR-3 [[prob-1/concept-1/req-7]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-7/feature-1]] (2 scenarios) |
| ERR-4 [[prob-1/concept-1/req-8]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-8/feature-1]] (2 scenarios) |
| ERR-5 [[prob-1/concept-1/req-9]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-9/feature-1]] (2 scenarios) |
| ERR-6 [[prob-1/concept-1/req-10]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | [[prob-1/concept-1/req-10/feature-1]] (3 scenarios) |
| PERF-NFR-1 [[prob-1/concept-1/qa-1]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | none — see Open questions |
| AVAIL-NFR-1 [[prob-1/concept-1/qa-2]] | [[prob-1/concept-1]] → [[prob-1]] | should | test | none — see Open questions |

## Open questions and assumptions

- **No numeric thresholds beyond PERF-NFR-1 and AVAIL-NFR-1 exist.** Treat them as maker-proposed-and-founder-confirmed assumptions, not independently-derived targets.
- **PERF-NFR-1 and AVAIL-NFR-1 have no acceptance scenario.** Not yet backed by any concrete test artifact — to be picked up during implementation/verification.
- **The founder's AWS free-tier eligibility is unverified.** Only the founder can check their own AWS Billing/Free Tier dashboard.
- **The specific DB/hosting provider is still open.** PostgreSQL was chosen as the engine; exact provider (Supabase, Render, Neon, or AWS RDS free tier) deferred to the implementation stage.
- **Frontend behavior when the backend is completely unreachable is not specified.** SKEL-1 only requires the backend to respond when it can be reached.
- **Per-field/per-endpoint validation rules ("what counts as invalid input") do not exist yet.**
- **The cold-start definition (AVAIL-NFR-1) is tied to Render's specific free-tier behavior.** May need revisiting if a different provider is chosen.
- **This baseline reproduces two prior completed/aborted processes under the now-corrected 9-stage template.** proc-1 completed under the original 5-stage template; proc-2 reached this same baseline stage under the extended template but was aborted when its implementation-stage checks (build-v1, typecheck-v1, etc.) proved to be hardcoded to Meridian's own repo layout rather than budget-checker's. The founder fixed those check commands (now parameterized via a maker-answered `build-command` question, confirmed empirically against a fresh index showing zero code exists yet) and added an `sdlc_abort` capability specifically to unblock this restart (proc-3).
