# Baseline — Receipt photos on expenses

## Purpose

This document is the baseline for the feature **Receipt photos on expenses** ([[prob-1]] → goal: "Let a person attach a receipt photo to an expense in the budget tracker, and open that photo again from the expense later."). It assembles the accepted artifacts of the run so far — problem brief [[prob-1]], solution concept [[concept-1]], requirements [[concept-1/req]] (requirement#112), quality attributes [[qa]] (quality_attribute#113), acceptance scenarios [[feature-1]] (acceptance_spec#133) — into one document. Design and implementation are committed against it; requirements are copied verbatim from the accepted artifacts, not restated.

Verification pass on this assembly (verify-baseline-v1), against what is actually in the artifacts and the repository: 16 approved requirements (requirement#112, RCP-1…RCP-16) and 16 matrix rows; 5 approved quality attributes and 5 rows; 1 acceptance artifact (acceptance_spec#133) and 1 Gherkin feature. All counts equal. Spot-checked statements against the source: `Receipt` has no photo column (backend/app/models.py, the `Receipt` class — id, user_id, amount, description, created_at only); `User.role` exists (backend/app/models.py, `role = Column(String, default="user")`); `create_all` runs in `create_app()` after only the health and auth routers are included (backend/app/main.py); the 10-second `TimeoutMiddleware` and `REQUEST_TIMEOUT_SECONDS` are present in backend/app/main.py; backend/requirements.txt lists fastapi, uvicorn[standard], sqlalchemy, psycopg2-binary, pytest, httpx, bcrypt, PyJWT and email-validator — no `python-multipart`, so INV-NFR-4's threshold is a real constraint; frontend/src/pages holds only Landing and NotFound, so no expense screen exists. Every claim the baseline makes about the code checked out.

## Scope

**In scope**
- A new `receipt_photos` table holding photo bytes, keyed by its own id, with the receipt id as a foreign key cascading the way `User.receipts` already cascades, plus content type — **no column added to `receipts`** (settled_question#91).
- Attach one photo (≤ size limit, jpeg/png bytes only) to one of the signed-in person's own receipts, at or after recording time.
- Serve that photo back through the authenticated API only; the frontend fetches bytes with the bearer token and renders locally (no embeddable unauthenticated photo URL).
- A frontend receipts listing screen, with attach and reopen from each receipt's own entry.
- Startup table creation via `Base.metadata.create_all` against the existing live database, `receipts` untouched.
- Cascade deletion of photos with their receipts and users.

**Out of scope**
- Reading anything off the photo: no OCR, no amount or date extraction, no auto-filling the expense from the image.
- Bulk import of an existing camera roll.
- Sharing or exporting receipts to anyone else.
- Multiple photos per expense.
- Any storage backend beyond what this repository already runs (no object store, no second service, no cloud bucket); any schema change to the existing `receipts` table; any filesystem photo storage.
- Expense summarisation/reporting.
- Photo replacement or deletion once attached; more than one photo per receipt; thumbnails or any image processing; showing the photo anywhere other than its own receipt (explicitly deferred, settled_question#106).
- Receipt creation/editing CRUD (deliberately rejected by the earlier foundation process and not part of this set; RCP-8 demands only a listing screen).

## Definitions

Per the baseline audit (settled_question#147), these terms are used in a specific sense by the requirements:

- **expense** / **receipt** — treated as the same entity. The goal and narrative say "expense"; the requirements and code say "receipt": the existing `Receipt` model (backend/app/models.py). This identification is an assumption carried in Open questions (item 4); it was never confirmed directly by the maker.
- **valid** photo/upload (RCP-1) — a file whose bytes are `image/jpeg` or `image/png` (RCP-5) and whose size does not exceed the size limit (RCP-4, 5 MB unless the bound upload test brings it down).
- **owner** / **owning user** / "a receipt they own" — the user the receipt's `user_id` points at. An administrator role grants nothing here (settled_question#110); the admin is treated as not the owner.
- **administrator role** — the value of the `role` column on `User` (backend/app/models.py). It confers no photo-reading rights in this feature.
- **carries a photo** — a `receipt_photos` row exists whose foreign key references that receipt.
- **later session** (RCP-2, RCP-14) — a new authenticated session with a fresh bearer token, after the upload session has ended (settled_question#130).
- **unchanged** (RCP-7, RCP-10, RCP-11) — for the table (RCP-7): schema identical to the recorded pre-feature schema with existing rows readable; for a receipt row (RCP-10/11): its column values identical to before the failed operation.
- **conflict response** (RCP-15) — an HTTP 409-class refusal naming the one-photo-per-receipt rule.
- **not-found response** (RCP-3, RCP-12) — the response served for a receipt id that does not exist; all refusals covered by those requirements are **byte-identical** to it.

## Functional requirements

Copied verbatim from [[concept-1/req]] (requirement#112). Priority and verification method as recorded there.

**RCP-1 — Attach a photo to a receipt that has none** (must; test)
> When an authenticated user submits a photo upload for a receipt they own that carries no photo, the receipts service shall store the photo bytes in a new receipt_photos table linked to that receipt by foreign key.

**RCP-2 — Reopen the photo later** (must; test)
> When the owner opens a receipt that carries a photo, the receipts service shall serve the stored photo to that authenticated user.

**RCP-3 — Only the owner can read a photo** (must; test)
> If a request for a receipt photo arrives from anyone other than the owning user, including an unauthenticated request or one bearing an administrator role, then the receipts service shall refuse it with the same not-found response given for a nonexistent receipt id.

**RCP-4 — Reject oversized photos** (must; test)
> If an uploaded photo exceeds 5 MB, then the receipts service shall refuse it with a message naming both the limit and the actual size, storing nothing.

**RCP-5 — Accept jpeg and png bytes only** (must; test)
> If an uploaded file's bytes are neither image/jpeg nor image/png, then the receipts service shall refuse it before storing anything.

**RCP-6 — Photo storage table created on startup** (must; test)
> When the backend starts against a database that already contains receipts rows, the application shall create the photo storage table as a new table.

**RCP-7 — The receipts table is left unchanged** (must; test)
> While the deployed database contains receipts rows recorded before the photo feature, the application shall leave the receipts table definition unchanged.

**RCP-8 — Receipts screen on the frontend** (must; demonstration)
> The frontend shall provide a screen listing the signed-in person's receipts.

**RCP-9 — Photo dies with its receipt or user** (must; test)
> When a receipt or its owning user is deleted, the receipts service shall delete the receipt's photo row so that no photo remains without its receipt.

**RCP-10 — Failed upload rolls back whole** (must; test)
> If a photo upload fails or is aborted part way through, including by the existing 10-second request timeout, then the receipts service shall roll the write back in a single transaction, leaving no photo row and the receipt unchanged.

**RCP-11 — No orphaned state on write failure** (must; test)
> If a database write fails during a photo upload, then the receipts service shall leave the receipt unchanged with no photo row stored.

**RCP-12 — Photoless receipt is an ordinary answer** (must; test)
> When a photo is requested for a receipt that has none, the receipts service shall return the same not-found response it returns for a nonexistent receipt id.

**RCP-13 — Attach a photo from the receipt's own entry** (must; demonstration)
> When the signed-in person is viewing their receipts screen, the frontend shall offer attaching one photo to a receipt from that receipt's own entry.

**RCP-14 — Reopen the photo from the receipt's own entry** (must; demonstration)
> When the signed-in person opens a receipt entry that carries a photo in a later session, the frontend shall present that photo from the receipt's own entry without leaving the application.

**RCP-15 — A receipt that already has a photo refuses a second upload** (must; test)
> If an authenticated user submits a photo upload for a receipt they own that already carries a photo, then the receipts service shall refuse the upload with a conflict response naming the one-photo-per-receipt rule, storing nothing.

**RCP-16 — Photos are served only through the authenticated API** (must; inspection)
> When the frontend displays a receipt photo, the frontend shall fetch the photo bytes through an authenticated API request carrying the signed-in person's bearer token and render them locally.

## Quality attributes

From [[qa]] (quality_attribute#113). Thresholds 5 MB, jpeg/png-only, one photo per receipt, the 10-second upload bound and the 2000 ms p95 figure are the maker's binding choices (settled_question#107, "Chosen, and binding"); the measurement conditions below them are stage-authored assumptions (see Open questions and assumptions).

**INV-NFR-1 — Photo open latency** (must; test, category performance)
> While the backend runs under the existing 10-second TimeoutMiddleware, when the owner opens a receipt photo, the receipts service shall serve the stored photo in a response meeting the stated threshold.

- Metric: p95 response time for serving a stored receipt photo to its owner
- Threshold: 2000 ms
- Conditions: measured locally on the deployed compose stack, over at least 50 consecutive fetches of a photo at the 5 MB limit, after upload in a separate session

**INV-NFR-2 — Photo confidentiality** (must; test, category security)
> While the receipts service is running, when any request for a receipt photo arrives without the owning user's authentication, the receipts service shall return the same refusal it gives for a nonexistent receipt id.

- Metric: proportion of unauthorized photo requests (other user, admin, unauthenticated) returning byte-identical not-found responses to the nonexistent-id case
- Threshold: 100%
- Conditions: automated test suite exercising all three unauthorized cases against every photo-serving route, run on every CI pass

**INV-NFR-3 — Screen-reader access to the photo viewer** (should; inspection, category accessibility)
> Where the receipt screen displays an attached photo, the frontend shall render that photo with alt text naming the receipt it belongs to.

- Metric: receipt screens whose photo img element carries non-empty alt text naming its receipt
- Threshold: 100%
- Conditions: every rendered state of the receipt screen showing a photo, verified by inspection at code review

**INV-NFR-4 — Single-maintainer plainness** (must; inspection, category maintainability)
> While the project is maintained by one person on a 2-4 day appetite, the receipts service shall implement photo storage using only the database and dependencies the repository already runs, apart from python-multipart.

- Metric: count of new runtime dependencies in backend/requirements.txt attributable to this feature
- Threshold: 1 (python-multipart)
- Conditions: inspected at the pull request diff, and at every later change touching photo storage

**INV-NFR-5 — Compose-stack self-containment** (must; inspection, category portability)
> While the application is deployed by docker compose on the maker's laptop, the receipts service shall serve and store receipt photos using only the existing /data volume and the existing single backend container.

- Metric: count of services and volumes added to docker-compose.yml by this feature
- Threshold: 0
- Conditions: inspected at the pull request diff; a working docker compose up against an existing database with real receipts rows

Categories explicitly **not settled** (quality_attribute#113): availability (laptop, docker compose — no target proposed), scalability (one user, excluded), usability and observability (no threshold named anywhere in this run), compliance (answered "none" — settled_question#108, on the record as asked).

## Acceptance scenarios

From [[feature-1]] (acceptance_spec#133), lifted verbatim. One coverage gap is recorded honestly rather than papered over, per the baseline audit (settled_question#144): **RCP-13 has no scenario of its own** — the spec's traceability asserts it is covered through the receipts screen and attach scenarios, but no Gherkin step exercises attachment being *offered from the receipt's own entry*, which is the demonstrated behaviour RCP-13 names. It is verified by demonstration outside this Gherkin; the matrix below says so on its row. The scenarios are size-parameterised in spirit (settled_question#132): the boundary is "exactly the limit" versus "one past it", with the limit's final number the one open question carrying a decided fallback.

```gherkin
Feature: Receipt photos on expenses

  Background:
    Given Dee is signed in
    And Dee has recorded a receipt for £12.50 with the description "team lunch"

  Scenario: Attaching a photo to a receipt that has none (RCP-1)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of the receipt to it
    Then the photo is stored against that receipt

  Scenario: Opening the photo again in a later session (RCP-2, RCP-14, RCP-16)
    Given the receipt carries a photo Dee attached last week
    When Dee signs in again and opens that receipt's entry
    Then Dee sees the same photo from the receipt's own entry
    And Dee does not leave the app to see it

  Scenario: The receipts screen lists the signed-in person's receipts (RCP-8)
    When Dee opens the receipts screen
    Then Dee sees only Dee's own receipts listed

  Scenario Outline: A photo of exactly the size limit is the boundary (RCP-4)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of <size> to the receipt
    Then the upload is <outcome>

    Examples:
      | size                | outcome  |
      | exactly 5 MB        | accepted |
      | 5 MB and 1 byte     | refused  |

  Scenario: An oversized photo is refused with a message naming both sizes, storing nothing (RCP-4)
    Given the receipt has no photo
    When Dee attaches a jpeg photo of 6 MB to the receipt
    Then Dee is told the limit is 5 MB and the file was 6 MB
    And no photo is stored against the receipt

  Scenario: Non-image bytes are refused even when declared as jpeg (RCP-5)
    Given the receipt has no photo
    When Dee attaches a text file declared as a jpeg
    Then the upload is refused before anything is stored

  Scenario: A second photo to a receipt that already has one is refused as a conflict (RCP-15)
    Given the receipt already carries a photo
    When Dee attaches a second photo to it
    Then Dee is told the receipt already has its one photo
    And the photo already stored is unchanged

  Scenario Outline: Only the owner can read a photo, and every refusal looks the same (RCP-3, RCP-12)
    Given the receipt carries a photo
    When <who> tries to open that receipt's photo
    Then they receive the same not-found answer given for a receipt id that does not exist

    Examples:
      | who                                        |
      | nobody, without signing in                 |
      | another signed-in person, Pat              |
      | a signed-in administrator                  |
      | Dee, but for a receipt that has no photo   |
      | anyone, for a receipt id that does not exist |

  Scenario: Deleting a receipt takes its photo with it (RCP-9)
    Given the receipt carries a photo
    When the receipt is deleted
    Then no photo remains without its receipt

  Scenario: Deleting a user takes every photo with it (RCP-9)
    Given Dee has receipts carrying photos
    When Dee's account is deleted
    Then no photo of Dee's remains without its receipt

  Scenario: An upload aborted part way stores nothing (RCP-10)
    Given the receipt has no photo
    When Dee's photo upload is cut off part way through
    Then no photo is stored against the receipt
    And the receipt itself is unchanged

  Scenario: A database failure during upload leaves nothing behind (RCP-11)
    Given the receipt has no photo
    When the photo upload's database write fails
    Then no photo is stored against the receipt
    And the receipt itself is unchanged

  Scenario: The photo table is created on an existing database without touching receipts (RCP-6, RCP-7)
    Given the database already holds receipts recorded before the photo feature
    When the backend starts
    Then the photo storage table exists
    And the receipts table is exactly as it was before
    And the pre-existing receipts are still readable
```

## Traceability matrix

| Requirement | Traces up to | Priority | Verification | Scenarios |
|---|---|---|---|---|
| RCP-1 [[concept-1/req-1]] | [[concept-1]] → [[prob-1]] | must | test | [[feature-1]] (1 scenario) |
| RCP-2 [[concept-1/req-2]] | [[concept-1]] → [[prob-1]] | must | test | [[feature-1]] (1 scenario, shared with RCP-14/RCP-16) |
| RCP-3 [[concept-1/req-3]] | [[prob-1]] | must | test | [[feature-1]] (1 shared outline with RCP-12) |
| RCP-4 [[concept-1/req-4]] | [[prob-1]] | must | test | [[feature-1]] (2 scenarios) |
| RCP-5 [[concept-1/req-5]] | [[prob-1]] | must | test | [[feature-1]] (1 scenario) |
| RCP-6 [[concept-1/req-6]] | [[concept-1]] → [[prob-1]] | must | test | [[feature-1]] (1 shared scenario with RCP-7) |
| RCP-7 [[concept-1/req-7]] | [[concept-1]] → [[prob-1]] | must | test | [[feature-1]] (1 shared scenario with RCP-6) |
| RCP-8 [[concept-1/req-8]] | [[prob-1]] | must | demonstration | [[feature-1]] (1 scenario) |
| RCP-9 [[concept-1/req-9]] | [[prob-1]] | must | test | [[feature-1]] (2 scenarios) |
| RCP-10 [[concept-1/req-10]] | [[prob-1]] | must | test | [[feature-1]] (1 scenario) |
| RCP-11 [[concept-1/req-11]] | [[prob-1]] | must | test | [[feature-1]] (1 scenario) |
| RCP-12 [[concept-1/req-12]] | [[prob-1]] | must | test | [[feature-1]] (1 shared outline with RCP-3) |
| RCP-13 [[concept-1/req-13]] | [[prob-1]] | must | demonstration | none in the Gherkin — the audit (settled_question#144) counted 15 of 16 covered; verified by demonstration outside it |
| RCP-14 [[concept-1/req-14]] | [[prob-1]] | must | demonstration | [[feature-1]] (1 shared scenario with RCP-2/RCP-16) |
| RCP-15 [[concept-1/req-15]] | [[prob-1]] | must | test | [[feature-1]] (1 scenario) |
| RCP-16 [[concept-1/req-16]] | [[prob-1]] | must | inspection | [[feature-1]] (1 shared scenario with RCP-2/RCP-14) |
| INV-NFR-1 [[qa-nfr-1]] | [[concept-1]] → [[prob-1]] | must | test | none — verified by its own measure conditions; no Gherkin needed (audit, settled_question#144) |
| INV-NFR-2 [[qa-nfr-2]] | [[prob-1]] | must | test | none — verified by its own measure conditions; no Gherkin needed (audit, settled_question#144) |
| INV-NFR-3 [[qa-nfr-3]] | [[prob-1]] | should | inspection | none |
| INV-NFR-4 [[qa-nfr-4]] | [[concept-1]] → [[prob-1]] | must | inspection | none |
| INV-NFR-5 [[qa-nfr-5]] | [[concept-1]] → [[prob-1]] | must | inspection | none |

All 16 requirements and 5 quality attributes are accounted for above; the RCP-13 scenario gap is the one deliberate hole, named rather than hidden.

## Chain check

Walked up and down on two requirements picked at random:

- **RCP-3** up: must-have 3 of settled_question#106 ("Nobody can read anybody else's photo. This is the one I will not trade") ← the constraints answer settled_question#84 ("photos are personal financial documents … must not become reachable by anyone else") ← the problem's core claim that expense records must be usable as proof. Down: the owner-refusal outline in [[feature-1]] (nobody, another user, admin, photoless, nonexistent id) exercises exactly what the sentence promises; INV-NFR-2 carries the completeness level. Closes.
- **RCP-7** up: must-have 5 of settled_question#106 ← the maker's chosen-direction answer settled_question#91 (the photo must not be a column on `receipts`, because `create_all` alters nothing) ← the architecture answer settled_question#83 (no migration tooling; a column on the live table needs hand-written SQL against real rows). Down: the "photo table created on an existing database without touching receipts" scenario covers creation and preservation together; the schema-comparison test in RCP-7's verification makes it provable. Closes.

## Open questions and assumptions

### Open questions

1. **5 MB vs the 10-second TimeoutMiddleware** (backend/app/main.py, `REQUEST_TIMEOUT_SECONDS`): whether a real 5 MB upload reliably completes inside the timeout is deliberately untested — bohdan bound it to be tested against the deployed stack (settled_question#107). The fallback is decided: the RCP-4 / INV-NFR-1 size limit comes down, the middleware does not go up. Only the final size number waits on that test; acceptance scenarios must stay size-parameterised.
2. **Timeout-at-commit tie** (settled_question#132, point 5): whether a photo survives correctly when the 10-second timeout fires exactly at commit — RCP-10 defines the rollback, but the link between "response delivered" and "transaction committed" is unspecified; to be tested, not assumed.
3. **Refusal latency** (settled_question#130): whether a rejected or conflicted upload consumes the request's 10-second budget in a way that could mask which refusal fired — no requirement speaks to refusal latency; undecided.
4. **"Expense" = `Receipt`?** (from triage, problem_brief#72, solution_concept#87): whether the goal's "expense" means the existing `Receipt` model or a distinct Expense concept was never answered directly by the maker; carried only as an assumption. The chosen storage approach survives either answer.
5. **Receipt creation path**: RCP-8 demands only a listing screen, but the scenarios' Background presumes receipts exist and can be recorded — how receipts get created is deliberately nobody's requirement in this set (the foundation process rejected it), so the demo path depends on an undocumented capability.
6. **RCP-13's scenario gap** (settled_question#144): the acceptance spec covers 15 of 16 requirements; RCP-13 is verified by demonstration outside the Gherkin. Closing it means amending acceptance_spec#133 with a demonstration scenario, not this document.
7. **Explicitly deferred** (for the record, so they are not re-litigated silently): photo replacement/deletion, multiple photos per receipt, thumbnails. Deliberately excluded by requirements and scenarios alike.
8. **Categories not settled** (quality_attribute#113): availability, scalability, usability, observability — deliberately no thresholds. Compliance answered "none" (settled_question#108).

### Assumptions

The headline thresholds (5 MB, jpeg/png-only, one photo per receipt, 10-second upload bound, 2000 ms p95) are **confirmed** by the maker (settled_question#107, "Chosen, and binding"). What follows were proposed by the stage rather than confirmed by a person (settled_question#146) and are committed here as assumptions:

1. INV-NFR-1's measurement conditions — "at least 50 consecutive fetches", "at the 5 MB limit", "after upload in a separate session", "measured locally on the deployed compose stack" — the 50-fetch sample size and the at-limit photo are stage-authored; nobody accepted them.
2. INV-NFR-2's 100% threshold and "every CI pass" condition — a formalisation of RCP-3's rule; the completeness level was authored by the stage.
3. INV-NFR-3/4/5's binary and count thresholds (100% alt text, exactly 1 new dependency, 0 new compose services/volumes) — derived from settled_question#84/#85/#108, but the specific numbers were fixed by the stage.
4. Standing assumption until the bound upload test runs: **5 MB fits** inside the 10-second timeout (quality_attribute#113's open questions).
5. "Expense" means the existing `Receipt` model (backend/app/models.py) rather than a distinct Expense concept — see open question 4.
6. A single photo per expense, attached at or after recording time one at a time (carried from solution_concept#87; the natural shape of the `receipt_photos` table, not separately confirmed).
7. Photos are small (phone receipts, a few MB) and sqlite practical blob limits are workable — untested; covered by the bound upload test in open question 1.
8. The one active user is the whole user base for the foreseeable future; nothing here is designed to scale beyond that.
9. The maker's "roughly a third of expenses need receipts" figure is directionally right — one person's estimate, not a measurement.
