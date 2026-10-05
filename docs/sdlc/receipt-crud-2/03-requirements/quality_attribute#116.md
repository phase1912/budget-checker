# Quality attributes: receipt-crud-2 — Receipt create, read, update, delete

Derived from the approved requirements (docs/sdlc/receipt-crud-2/03-requirements/requirement#115.md) and the approved concept. Non-functional requirements for a backend-only, one-day, single-maintainer change to `backend/app/routers/receipts.py`.

What was asked on the record and how it bears here:

- **thresholds** (settled_question#111, bohdan): "No latency number has been settled. Propose what the existing receipts endpoints already meet and mark it unconfirmed rather than asserting a figure nobody agreed." Every numeric threshold below is therefore *proposed, not confirmed*, and each appears in `open_questions` with who must confirm it.
- **compliance** (settled_question#112, bohdan): "None." No compliance attribute is written; the question was asked and the answer is on the record.
- **Overlap check against the functional set.** RCR-6 already fixes the uniform not-found semantics and RCR-8 already fixes the list endpoint's shape exactly. No attribute below restates either; the security attribute bounds a dimension RCR-6 leaves open (indistinguishability of error *bodies and timings*, not the 404 answer itself), and the maintainability attribute adds a measurable diff-scope bound the requirements do not state. Nothing else in the eleven categories applies strongly enough to carry a number for this change, and each non-selection is recorded below.

## RCR-NFR-1 — Endpoint latency under normal load

### Requirement

While the receipts router serves the four new endpoints under normal operating load, each request that changes state shall complete within the stated threshold at the 95th percentile.

### Rationale

Without a bound, the four thin handlers could quietly acquire latency from an unindexed path or an accidental N+1 on the photo relationship. The figures are *proposed, not confirmed*: no latency number has been settled (settled_question#111), and the proposal is deliberately loose — the operations are single-row CRUD against an existing table the list endpoint already queries, so anything slower than the list endpoint would itself be a finding. The failure mode if missed is a receipts screen the frontend already renders within its own budget starting to hang.

### Measure

| | |
|---|---|
| metric | p95 wall-clock time for POST /api/v1/receipts, GET/PATCH/DELETE /api/v1/receipts/{receipt_id} |
| threshold | 200 ms |
| conditions | single authenticated user, SQLite/Postgres instance as deployed by backend/Dockerfile, 10 requests/second sustained over 5 minutes, receipts table holding 1,000 rows for the caller |

### Traces to

- [[prob-1/concept-1]] — the four new endpoints whose latency is bounded.

## RCR-NFR-2 — Indistinguishable failure for foreign receipts

### Requirement

If a request names a receipt the caller does not own, then the receipts router shall respond to that request indistinguishably from the response to a request for a nonexistent receipt, in status code, body and response size.

### Rationale

This bounds a dimension RCR-6 leaves open. RCR-6 fixes that both cases get "the module's uniform not-found answer, the same for both cases" — the attribute adds the *verification dimension*: the responses must be byte-identical in shape, and must not be distinguishable by timing either (no early-return on a foreign id that skips the query the missing id performs). `_get_owned_receipt` (backend/app/routers/receipts.py lines 35–42) already takes one query for both cases, so the implementation meets this today; the attribute exists so the new handlers cannot cheaply "optimise" their way out of it. No threshold number applies — the measure is equality, which is a stricter test than any numeric one. Not a restatement: RCR-6 is a functional requirement about *what* is returned; this is about *how* it is returned and how that is proven.

### Measure

| | |
|---|---|
| metric | set equality of (status code, response body, response-content-length) between a request for a nonexistent receipt id and a request for another user's receipt id, across read, update and delete |
| threshold | 3 of 3 endpoint pairs identical in all three dimensions |
| conditions | two accounts in the test database, the foreign receipt existing under the second account, asserted by automated test in backend/tests/test_receipts.py |

### Traces to

- [[prob-1/concept-1]] — chosen approach: nonexistent id and someone else's receipt both get the same not-found.
- [[prob-1/concept-2]] — failure behaviour: nothing leaks whether a foreign receipt is there.

## RCR-NFR-3 — Change stays inside one router file

### Requirement

The receipts CRUD change shall be implemented without modifying any file other than backend/app/routers/receipts.py and tests under backend/tests/.

### Rationale

The concept (solution_concept#90) chose Option B precisely because the router already contains every idiom needed — `_get_owned_receipt`, `_NOT_FOUND_DETAIL` (lines 23, 35–42), the validate-then-commit pattern — and because models.py, schemas.py and the list endpoint are frozen. This turns that choice into a checkable bound: if the implementation needs to touch schemas.py, models.py or any other router, the concept's assumptions have failed and the change should go back to concept rather than grow silently. The ten-file app tree (backend/app/) makes this cheap to verify by `git diff --stat`. Category note: this is a maintainability bound expressed as a diff-scope measure because the accepted category list has no better home for a scope-freeze; it is a constraint of the chosen approach, made verifiable.

### Measure

| | |
|---|---|
| metric | files changed in the pull request, outside backend/app/routers/receipts.py and backend/tests/ |
| threshold | 0 |
| conditions | measured on the final diff of the branch receipt-crud-2 against master, by inspection of `git diff --stat master...receipt-crud-2` |

### Traces to

- [[prob-1/concept-4]] — constraints: backend only, no migration, list endpoint frozen, frontend untouched.

## Categories considered and not written

- **Availability** — the app is a single-process FastAPI service; the four endpoints add no new dependency, and a receipts-endpoint availability figure would be a property of the whole service, not this change.
- **Privacy** — the owner-only rule and uniform not-found carry it; nothing new is stored beyond rows in an existing table for an existing owner.
- **Usability / accessibility** — a JSON API with no frontend change; no human interface is touched.
- **Portability** — no new infrastructure, runtime or environment variable is introduced.
- **Scalability** — single-user-owner semantics assumed everywhere (settled_question#83 §4); there is no load story to bound at this change's scale.
- **Observability** — the shared error handling in backend/app/main.py (lines 47–62) already logs 4xx and 5xx for every route including the new ones; an attribute would restate behaviour the middleware provides for free.
- **Security beyond RCR-NFR-2** — auth is the existing `get_current_active_user` dependency on every handler; a second security attribute would restate it.
- **Compliance** — answered "None" (settled_question#112); no artifact required, the answer is on the record.