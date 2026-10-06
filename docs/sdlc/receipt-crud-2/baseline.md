# Requirements baseline: receipt-crud-2 — Receipt create, read, update, delete

Branch: `receipt-crud-2`, based on `master`. Source documents for this run, all under `docs/sdlc/receipt-crud-2/`: `00-triage/change_brief#50.md`, `01-problem/problem_brief#75.md`, `02-concept/solution_concept#90.md`, `03-requirements/requirement#115.md`, `03-requirements/quality_attribute#116.md`, `04-acceptance/acceptance_spec#131.md`.

## Purpose

This document is the requirements baseline for the receipt CRUD feature: the four operations the receipts API is missing (create, read one, update, delete) added to the existing `backend/app/routers/receipts.py` router. Design and implementation are committed against this baseline; a change to scope, requirement wording, thresholds or scenarios after this point is a change to the baseline, not a quiet drift.

It commits to: four additive endpoints reusing the module's existing ownership check and uniform not-found, deletion taking the receipt's photo with it, and the existing list endpoint answering exactly as it does today.

## Scope

**In scope** (from the goal, the problem brief and the concept, all cited above):

- Create, read-one, update (amount and/or description) and delete endpoints in `backend/app/routers/receipts.py`, reusing `_get_owned_receipt` and `_NOT_FOUND_DETAIL` (backend/app/routers/receipts.py lines 23, 35–42).
- Deletion removing the receipt's attached `ReceiptPhoto` via the already-declared cascade (backend/app/models.py lines 66–72).
- Amount validation refusing negative and over-precise values (RCR-7).
- Backend only: FastAPI, SQLAlchemy, pytest — the stack already in the repository.

**Out of scope**:

- No frontend work — `ReceiptsStore` and `api/client.ts` untouched.
- No migration — the `receipts` table is used exactly as it stands; nothing in `backend/app/models.py` moves (no soft-delete column, no audit table).
- The existing list endpoint's response shape is frozen (RCR-8); `list_receipts` is untouched.
- No bulk import. No currency handling beyond the `Numeric(12,2)` the column already has.
- No photo-on-create; the existing one-photo-per-receipt upload endpoint (RCP-15, settled by the prior `docs/sdlc/receipts6/` run) remains the only way to attach a photo. No change to the photo endpoints beyond what deleting a receipt requires of them.
- No change to `_get_owned_receipt`'s contract or `_NOT_FOUND_DETAIL`.
- No multi-user or admin semantics beyond the existing owner-only rule.

Note on prior scope: the prior run `docs/sdlc/receipts6/` deliberately scoped receipt CRUD out (its `baseline.md` line 27). This goal reverses that decision, confirmed deliberate by the person at chosen-direction (settled_question#94). That question is closed, not carried open.

## Definitions

- **Authenticated caller** — a request that passes the router's existing `get_current_active_user` dependency (`backend/app/routers/receipts.py` line 10, from `..deps`). The requirement set does not state the failure status for an unauthenticated request; that is an open question (see below). Used in RCR-1 through RCR-6.
- **Uniform not-found** — defined inside RCR-6 itself, not referenced: HTTP 404 with detail "Receipt not found", identically in status code and body whether the receipt does not exist or belongs to another caller. This is what `_NOT_FOUND_DETAIL` (line 23) and `_get_owned_receipt` (lines 35–42) already produce for the photo endpoints.
- **Optional description / no description** — a description field the caller may omit on create (RCR-1). Whether an omitted description reads back as null, empty string, or field-absent, and whether an explicit null on update clears a description, is undecided — open question.
- **Success status and simple-message form** (RCR-4) — assumed to be the module's existing `MessageResponse` idiom, the form `upload_receipt_photo` answers with (`return MessageResponse(message="Photo attached")`, backend/app/routers/receipts.py line 111). The exact status code (200 with body, or 204 without) is assumed, not decided — open question.
- **Normal operating load** (RCR-NFR-1) — has no settled content; its only meaning is the measure's conditions row, which is itself proposed and unconfirmed. See open questions.

## Functional requirements

All eight are `must`, matching the must-have answer (settled_question#110), which named exactly this set and nothing more.

**RCR-1 — Create a receipt** (priority: must; verification: test)

> When an authenticated caller submits a new receipt with an amount and an optional description, the receipts router shall create a receipt owned by that caller with a unique identifier and a creation timestamp it did not take from the request.

**RCR-2 — Read one receipt** (priority: must; verification: test)

> When an authenticated caller requests a receipt by identifier, the receipts router shall return that receipt's id, amount, description and creation timestamp if the receipt exists and belongs to the caller, and not return any other receipt.

**RCR-3 — Update a receipt's amount or description** (priority: must; verification: test)

> When an authenticated caller submits a new value for an existing receipt's amount or description, the receipts router shall apply exactly the submitted changes to the caller's receipt, leave every field not submitted unchanged, and change no other field.

**RCR-4 — Delete a receipt** (priority: must; verification: test)

> When an authenticated caller requests deletion of a receipt that belongs to the caller, the receipts router shall delete that receipt and answer with a success status and a body in the module's existing simple-message form, as the photo-upload endpoint answers.

**RCR-5 — Deleting a receipt takes its photo with it** (priority: must; verification: test)

> When a receipt is deleted through the API, the receipts router shall remove that receipt's attached photo in the same operation.

**RCR-6 — Uniform not-found for foreign or missing receipts** (priority: must; verification: test)

> If a receipt identifier names a receipt that does not exist or does not belong to the authenticated caller, then the receipts router shall answer with HTTP 404 and the detail "Receipt not found", identically in status code and body for both cases.

**RCR-7 — Amount validation refuses negative or over-precise values** (priority: must; verification: test)

> If a create or update submits an amount that is negative or carries more than two decimal places, then the receipts router shall refuse it with an answer that names the rule broken, without creating or changing any receipt.

**RCR-8 — The existing list endpoint answers as it does today** (priority: must; verification: inspection)

> The receipts router shall return from GET /api/v1/receipts the authenticated caller's receipts as objects with id, amount as a number, description, created_at and has_photo, ordered by creation time descending.

All eight statements above are copied verbatim from `docs/sdlc/receipt-crud-2/03-requirements/requirement#115.md` (verified word-for-word for RCR-1, RCR-6 and RCR-8 during assembly).

## Quality attributes

**RCR-NFR-1 — Endpoint latency under normal load** (category: performance; priority: should)

> While the receipts router serves the four new endpoints under normal operating load, each request that changes state shall complete within 200 ms at the 95th percentile.

- Metric: p95 wall-clock time for POST /api/v1/receipts and GET/PATCH/DELETE /api/v1/receipts/{receipt_id}
- Threshold: 200 ms
- Conditions: single authenticated user, database as deployed by backend/Dockerfile, 10 requests/second sustained over 5 minutes, 1,000 receipts for the caller
- Method: test
- **Every figure here is proposed, not confirmed** — the person's own thresholds answer (settled_question#111) was "No latency number has been settled. Propose what the existing receipts endpoints already meet and mark it unconfirmed". Bohdan must confirm or replace before this attribute is used to accept the work.

**RCR-NFR-2 — Indistinguishable failure for foreign receipts** (category: security; priority: must)

> If a request names a receipt the caller does not own, then the receipts router shall respond to that request indistinguishably from the response to a request for a nonexistent receipt, in status code, body and response size.

- Metric: set equality of (status code, response body, content-length) between nonexistent-id and foreign-id requests, across read, update and delete
- Threshold: 3 of 3 endpoint pairs identical in all three dimensions
- Conditions: two accounts in the test database, the foreign receipt existing under the second account, asserted by automated test in backend/tests/test_receipts.py
- Method: test
- The property is demanded by the goal; the quantified form (including content-length) is the maker's construction, recorded as an assumption.

**RCR-NFR-3 — Change stays inside one router file** (category: maintainability; priority: must)

> The receipts CRUD change shall be implemented without modifying any file other than backend/app/routers/receipts.py and tests under backend/tests/.

- Metric: files changed in the pull request, outside backend/app/routers/receipts.py and backend/tests/
- Threshold: 0
- Conditions: measured on the final diff of branch receipt-crud-2 against master, by inspection of git diff --stat
- Method: inspection
- This bound is derived from the concept's Option B choice, not stated by the person; if RCR-7's validation needs a shared helper outside the router, it must be relaxed to 1 by bohdan. Assumption, recorded as open.

## Acceptance scenarios

The Gherkin below is lifted verbatim from `docs/sdlc/receipt-crud-2/04-acceptance/acceptance_spec#131.md` (the only `.feature`-grade artifact this run has, matching its single acceptance artifact one-for-one). Nothing added. The quality attributes have no Gherkin: RCR-NFR-1 has no scenario of the required shape (flagged in the audit, settled_question#142, and listed under open questions), RCR-NFR-2's coverage by the RCR-6 scenario does not extend to content-length identity (same flag), and RCR-NFR-3 is verified by inspection of the diff, so no scenario applies.

```gherkin
Feature: Receipt create, read, update, delete

  Background:
    Given Sam is signed in to the API

  Scenario: A receipt is created [RCR-1]
    When Sam submits a new receipt with amount 12.50 and description "lunch"
    Then the receipt is created with the submitted amount and description
    And the receipt is owned by Sam
    And the receipt carries a unique identifier and a creation time Sam did not supply

  Scenario: A receipt can be created without a description [RCR-1]
    When Sam submits a new receipt with amount 12.50 and no description
    Then the receipt is created with the submitted amount and no description

  Scenario: A created receipt appears at the top of Sam's list [RCR-1]
    Given Sam already has receipts from earlier
    When Sam submits a new receipt
    Then the new receipt is the first entry in Sam's receipt list

  Scenario: A receipt is read back by identifier [RCR-2]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam reads that receipt by its identifier
    Then Sam sees its identifier, amount, description and creation time

  Scenario: An amount is corrected without disturbing anything else [RCR-3]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam submits 13.25 as the receipt's amount
    Then the receipt's amount is 13.25
    And the receipt's description is still "lunch"
    And the receipt's identifier and creation time are unchanged

  Scenario: A field not submitted is left alone [RCR-3]
    Given Sam has a receipt for 12.50 described as "lunch"
    When Sam submits only a new description "dinner"
    Then the receipt's description is "dinner"
    And the receipt's amount is still 12.50

  Scenario: A receipt is deleted [RCR-4]
    Given Sam has a receipt
    When Sam deletes that receipt
    Then Sam is told the receipt was deleted
    And reading that receipt by its identifier says it is not found

  Scenario: Deleting a receipt takes its photo with it [RCR-5]
    Given Sam has a receipt with a photo attached
    When Sam deletes that receipt
    Then the receipt's photo is no longer retrievable

  Scenario Outline: A foreign or missing receipt is the same not-found [RCR-6]
    Given Sam has a receipt
    But the receipt named is <a receipt that does not exist|another account's receipt|a receipt that was already deleted>
    When Sam <operation> that receipt by identifier
    Then Sam is told the receipt is not found

    Examples:
      | operation |
      | reads      |
      | updates    |
      | deletes    |

  Scenario Outline: A bad amount is refused and changes nothing [RCR-7]
    When Sam submits a receipt with an amount of <amount>
    Then Sam is told the amount is <why>
    And no receipt exists with that amount

    Examples:
      | amount  | why                        |
      | -5.00   | negative                   |
      | 12.505  | more precise than two decimals |

  Scenario Outline: A bad amount is refused on update too [RCR-7]
    Given Sam has a receipt for 12.50
    When Sam submits an amount of <amount> for that receipt
    Then Sam is told the amount is <why>
    And the receipt's amount is still 12.50

    Examples:
      | amount  | why                        |
      | -5.00   | negative                   |
      | 12.505  | more precise than two decimals |

  Scenario: The list endpoint answers as it always has [RCR-8]
    Given Sam has a receipt with a photo and one without, created before it
    When Sam asks for Sam's receipt list
    Then each entry carries an identifier, amount as a number, description, creation time and a photo flag
    And the entries are newest first
```

Twelve scenarios in total (9 plain scenarios plus 2 scenario outlines with 3 examples each, and the RCR-6 outline with 3), matching the per-requirement counts in the matrix below.

## Traceability matrix

The `[[…]]` concept ids are the numbered items inside the approved concept, `docs/sdlc/receipt-crud-2/02-concept/solution_concept#90.md` (chosen approach §, failure behaviour, risks and constraints sections respectively). The problem brief is `docs/sdlc/receipt-crud-2/01-problem/problem_brief#75.md`. Requirements are `docs/sdlc/receipt-crud-2/03-requirements/requirement#115.md`, quality attributes `docs/sdlc/receipt-crud-2/03-requirements/quality_attribute#116.md`, scenarios `docs/sdlc/receipt-crud-2/04-acceptance/acceptance_spec#131.md`. The scenario column points at the acceptance artifact and names the scenarios there — those scenario titles are the only scenario-level identifiers the run has.

| Requirement | Traces up to | Priority | Verification | Scenarios |
|---|---|---|---|---|
| RCR-1 | [[prob-1/concept-1]] → problem_brief#75 | must | test | acceptance_spec#131 (3 scenarios: "A receipt is created", "A receipt can be created without a description", "A created receipt appears at the top of Sam's list") |
| RCR-2 | [[prob-1/concept-1]] → problem_brief#75 | must | test | acceptance_spec#131 (1 scenario: "A receipt is read back by identifier") |
| RCR-3 | [[prob-1/concept-1]] → problem_brief#75 | must | test | acceptance_spec#131 (2 scenarios: "An amount is corrected without disturbing anything else", "A field not submitted is left alone") |
| RCR-4 | [[prob-1/concept-1]] → problem_brief#75 | must | test | acceptance_spec#131 (1 scenario: "A receipt is deleted") |
| RCR-5 | [[prob-1/concept-1]] → problem_brief#75 | must | test | acceptance_spec#131 (1 scenario: "Deleting a receipt takes its photo with it") |
| RCR-6 | [[prob-1/concept-1]], [[prob-1/concept-2]] → problem_brief#75 | must | test | acceptance_spec#131 (1 scenario outline, 3 operations × 3 receipt cases) |
| RCR-7 | [[prob-1/concept-2]], [[prob-1/concept-3]] → problem_brief#75 | must | test | acceptance_spec#131 (2 scenario outlines: create and update, 2 examples each) |
| RCR-8 | [[prob-1/concept-4]] → problem_brief#75 | must | inspection | acceptance_spec#131 (1 scenario: "The list endpoint answers as it always has") |
| RCR-NFR-1 | [[prob-1/concept-1]] → problem_brief#75 | should | test | none — no load-test scenario exists in the acceptance spec (audit finding, settled_question#142); must be verified by a performance test outside the Gherkin set or waved through (open question 11) |
| RCR-NFR-2 | [[prob-1/concept-1]], [[prob-1/concept-2]] → problem_brief#75 | must | test | partially covered — the RCR-6 scenario asserts the same not-found answer but never asserts byte/content-length identity; the content-length dimension needs an extended assertion or its own scenario (open question 12) |
| RCR-NFR-3 | [[prob-1/concept-4]] → problem_brief#75 | must | inspection | none — verified by `git diff --stat master...receipt-crud-2`; correctly scenario-free |

Counted against the artifacts, not estimated: 8 approved `requirement` entries → 8 functional rows; 3 approved `quality_attribute` entries → 3 NFR rows; 1 acceptance artifact → its 12 scenarios are reproduced whole above; every functional requirement has at least one scenario. 11 matrix rows, none missing, none extra.

## Open questions and assumptions

Everything still unresolved, gathered from every stage (problem brief, concept, requirements, quality attributes, acceptance audit). Nothing here is settled silently.

1. **RCR-2's read-one body** — id, amount, description, created_at, *without* has_photo — was proposed from the list-entry shape (backend/app/routers/receipts.py lines 57–64), not decided. Bohdan to confirm whether read-one carries has_photo. If it changes, only RCR-2 changes.
2. **Clearing a description** — RCR-3 states partial-update semantics (a field not submitted stays). Whether an explicit null clears a description, or clearing is out of scope for this change, is undecided. Bohdan to say.
3. **RCR-4's success body and status** — assumed to be the module's `MessageResponse` form (as `upload_receipt_photo` answers at backend/app/routers/receipts.py line 111) with a consistent success status. A bare 204 is the alternative; if preferred, only RCR-4 changes.
4. **RCR-7's two-decimal ceiling** — proposed from the failure-behaviour answer ("over-precise") and the `Numeric(12,2)` column (backend/app/models.py line 60); bohdan has not confirmed it. If it changes, only RCR-7 changes.
5. **Amount upper bound** — no maximum is named anywhere. Whether 99999999999.99 is valid and 100000000000.00 refused (`Numeric(12,2)`'s implied ceiling) is a boundary the requirement set does not decide (settled_question#128).
6. **Client-supplied created_at or user_id in a create body** — silently ignored or refused? Undecided (settled_question#130); both readings are defensible.
7. **Unauthenticated requests** — every requirement says "authenticated caller" but nothing states the 401. Acknowledged as an unwritten gap, presumably carried by the existing `get_current_active_user` dependency (settled_question#129/#130).
8. **RCR-NFR-1's figures are entirely unconfirmed** — the 200 ms p95 threshold and the whole load condition set (single user, 10 req/s over 5 minutes, 1,000 receipts) are proposed, never measured or agreed (settled_question#111, settled_question#144). Bohdan must confirm or replace them before the attribute is used to accept the work.
9. **RCR-NFR-3's 0-file bound** may need relaxing to 1 if the RCR-7 validation needs a shared helper outside the router (for example in `deps.py`); assumed not to, because the module keeps its validation local today.
10. **Volume/frequency** — how often receipts would be created was answered qualitatively only; no estimate was ever given (problem_brief#75).
11. **RCR-NFR-1 has no acceptance scenario** — flagged in the baseline audit (settled_question#142): a load test of that shape exists nowhere in the acceptance spec. It must be verified by a performance test outside the Gherkin set, or explicitly waved through.
12. **RCR-NFR-2's coverage is partial** — the RCR-6 scenario never asserts response size / content-length identity between a missing and a foreign receipt; an extended assertion or its own scenario is needed (settled_question#142).

Closed on the record (listed so it is not re-litigated): the reversal of `docs/sdlc/receipts6/`'s exclusion of receipt CRUD (its `baseline.md` line 27) was confirmed deliberate by the person at chosen-direction (settled_question#94).

Assumptions committed to by baselining this document: no migration is needed (`Receipt`, backend/app/models.py lines 55–72, is complete as-is); the delete cascade removes the photo through the ORM path the HTTP handler uses (pinned at the model layer by `test_deleting_receipt_takes_its_photo_with_it`, backend/tests/test_receipts.py line 310); create accepts amount and optional description and nothing else; exactly one account exercises this through the API only; and compliance obligations are none (settled_question#112), the question having been asked on the record.
