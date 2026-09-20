# Requirements — Receipt photos on expenses

Review pass (attempt 5) over the attempt-4 set. The gate's shortfalls against attempt 3 (gate_finding#114) were resolved in the attempt-4 document itself and re-checked here line by line: RCP-15 now names its refusal response (a conflict refusal naming the one-photo-per-receipt rule, deliberately not the not-found of RCP-3/RCP-12 — the requester owns the receipt, so there is nothing to conceal); RCP-10 defines its response as single-transaction rollback rather than an undefined "partial"; and the photo-serving URL shape is settled in-set by RCP-16 (bytes only through the bearer-authenticated API, rendered client-side; no embeddable unauthenticated photo URL), which is what lets RCP-2 and RCP-3 be fully realized. Feasibility is settled on the record: `python-multipart` is carried as a feature cost per the chosen concept (solution_concept#87) and the constraint answer (settled_question#84) permits one ordinary dependency; backend/requirements.txt lists fastapi, uvicorn, sqlalchemy, psycopg2-binary, pytest, httpx, bcrypt, PyJWT and email-validator only, so the addition is real and small. The 5 MB-versus-10-second question keeps only its final number open, with the fallback decided (the RCP-4 limit comes down, the middleware does not go up), so the set is realizable at some size limit regardless of that test's outcome.

This review found no new shortfalls and made no requirement-level changes. Two overlaps were examined and are deliberate, not drift: RCP-10 and RCP-11 guarantee the same consistency but differ in trigger (aborted or timed-out upload versus database write failure), which is a distinction a test needs — they are kept separate on that basis; and RCP-3 with RCP-12 share the byte-identical not-found response by explicit design (refusal equivalence, settled_question#109). RCP-16 is written as behaviour the frontend can be demonstrated to perform rather than as a component design; it exists to settle, in this document, the one decision bohdan bound earlier stages to make deliberately (settled_question#91). Every requirement traces to the concept or the elicited answers, the priorities follow must-have (settled_question#106) — the refused-priority items (replace/delete a photo, multiple photos, thumbnails) are nowhere in the set — and the single open question below is the one with its fallback already decided.

## RCP-1 — Attach a photo to a receipt that has none

### Requirement

When an authenticated user submits a photo upload for a receipt they own that carries no photo, the receipts service shall store the photo bytes in a new receipt_photos table linked to that receipt by foreign key.

### Rationale

Must-have 1 of settled_question#106, scoped to the first attach so the second-attach case is RCP-15's alone. The new-table shape is the maker's chosen direction (settled_question#91): schema creation in this repository can add tables but not columns.

### Verification

Test: upload a valid image to an owned photoless receipt and assert a receipt_photos row exists with the exact bytes and receipt id.

### Traces to

- solution_concept#87 — chosen approach
- settled_question#106 — must-have 1 and 5

## RCP-2 — Reopen the photo later

### Requirement

When the owner opens a receipt that carries a photo, the receipts service shall serve the stored photo to that authenticated user.

### Rationale

Must-have 2 (settled_question#106): the photo opens again from the receipt in a later session. Deliberately functional only — the 2-second p95 threshold lives once, as INV-NFR-1 in quality_attribute#113. The endpoint serving it is the authenticated API endpoint settled under RCP-16.

### Verification

Test: upload, then in a new authenticated session fetch the photo through the authenticated endpoint and assert the bytes round-trip.

### Traces to

- solution_concept#87 — chosen approach
- settled_question#106 — must-have 2
- settled_question#91 — URL-shape binding

## RCP-3 — Only the owner can read a photo

### Requirement

If a request for a receipt photo arrives from anyone other than the owning user, including an unauthenticated request or one bearing an administrator role, then the receipts service shall refuse it with the same not-found response given for a nonexistent receipt id.

### Rationale

Must-have 3 (settled_question#106), the priority the maker will not trade. The identical-refusal rule is settled_question#109: a distinct "not yours" tells a stranger which receipt ids are real. The `role` column exists on `User` (backend/app/models.py:22), and the actors answer (settled_question#110) is explicit that it grants nothing here and the existing PyJWT auth is the only authentication. The behavioural capability lives here; the completeness measure of the refusal-equivalence rule lives as INV-NFR-2 in quality_attribute#113 — the capability/level division the gate finding endorsed.

### Verification

Test: request another user's photo as another user, unauthenticated, with an invalid token, and as an admin; assert all return byte-identical not-found responses to the nonexistent-id case.

### Traces to

- settled_question#106 — must-have 3
- settled_question#109 — refusal equivalence rule
- settled_question#110 — admin grants nothing, existing auth only

## RCP-4 — Reject oversized photos

### Requirement

If an uploaded photo exceeds 5 MB, then the receipts service shall refuse it with a message naming both the limit and the actual size, storing nothing.

### Rationale

Binding 5 MB threshold from settled_question#107; the failure answer (settled_question#109) requires rejection before anything is stored. If the bound upload test (settled_question#107) shows 5 MB cannot complete inside the 10-second timeout, this threshold is the value that comes down — the middleware does not go up.

### Verification

Test: upload a 5 MB-plus-one-byte file and assert a refusal naming 5 MB and the actual size, and that no receipt_photos row exists.

### Traces to

- settled_question#107 — 5 MB limit
- settled_question#109 — reject before storing

## RCP-5 — Accept jpeg and png bytes only

### Requirement

If an uploaded file's bytes are neither image/jpeg nor image/png, then the receipts service shall refuse it before storing anything.

### Rationale

Binding content-type rule from settled_question#107: checked against the bytes, not only the declared header.

### Verification

Test: upload a file with a jpeg content-type header and non-image bytes, and a gif; assert both are refused and nothing is stored.

### Traces to

- settled_question#107 — accepted content types checked against bytes

## RCP-6 — Photo storage table created on startup

### Requirement

When the backend starts against a database that already contains receipts rows, the application shall create the photo storage table as a new table.

### Rationale

Must-have 5, capability half (settled_question#106): with no migration tooling in the repository, the only schema change that can land on the live database is a table `Base.metadata.create_all` creates on start-up.

### Verification

Test: start the backend against a copy of a database containing existing receipts rows; assert the photo table exists with the expected columns.

### Traces to

- settled_question#106 — must-have 5
- settled_question#91 — new-table decision

## RCP-7 — The receipts table is left unchanged

### Requirement

While the deployed database contains receipts rows recorded before the photo feature, the application shall leave the receipts table definition unchanged.

### Rationale

Must-have 5, constraint half (settled_question#106): no column is added to receipts and no hand-written SQL touches the maker's existing rows. backend/app/models.py:56–64 confirms Receipt has no photo column today; this requirement holds that true after the change.

### Verification

Test: after start-up against the pre-feature database, compare the receipts table schema to the recorded pre-feature schema and assert it is identical, with existing rows readable.

### Traces to

- settled_question#106 — must-have 5
- settled_question#91 — no column on receipts

## RCP-8 — Receipts screen on the frontend

### Requirement

The frontend shall provide a screen listing the signed-in person's receipts.

### Rationale

Must-have 6, part one (settled_question#106): no expense screen exists today (only Landing and NotFound under frontend/src/pages), and without a listing screen there is nowhere for the attach and reopen capabilities of RCP-13 and RCP-14 to live.

### Verification

Demonstration: sign in and see the person's own receipts listed.

### Traces to

- settled_question#106 — must-have 6
- settled_question#35 — the outcome someone would notice

## RCP-9 — Photo dies with its receipt or user

### Requirement

When a receipt or its owning user is deleted, the receipts service shall delete the receipt's photo row so that no photo remains without its receipt.

### Rationale

Retention from settled_question#107: photos live as long as the receipt, cascading the way `User.receipts` already cascades all, delete-orphan (backend/app/models.py). Also the never-condition from settled_question#109: no photo row pointing at a receipt that is not there.

### Verification

Test: delete a receipt with a photo, then delete a user with receipts; assert no receipt_photos rows remain in either case.

### Traces to

- settled_question#107 — retention rule
- settled_question#109 — consistency on delete

## RCP-10 — Failed upload rolls back whole

### Requirement

If a photo upload fails or is aborted part way through, including by the existing 10-second request timeout, then the receipts service shall roll the write back in a single transaction, leaving no photo row and the receipt unchanged.

### Rationale

From settled_question#107 and settled_question#109: the write is all or nothing. This resolves the gap gate_finding#114 named — "partial" is now defined as anything short of the committed transaction, and the response is rollback, not cleanup of a half-written row. The 10-second middleware is confirmed present (backend/app/main.py, `REQUEST_TIMEOUT_SECONDS`).

### Verification

Test: abort an upload mid-flight at the timeout and induce a write failure during upload; assert in both cases no receipt_photos row exists and the receipt is unchanged.

### Traces to

- settled_question#107 — timeout bound to be tested, not assumed
- settled_question#109 — nothing partial stored
- gate_finding#114 — the undefined "partial" this wording replaces

## RCP-11 — No orphaned state on write failure

### Requirement

If a database write fails during a photo upload, then the receipts service shall leave the receipt unchanged with no photo row stored.

### Rationale

From settled_question#109: a database write failure leaves the receipt unchanged and nothing orphaned; every failure ends with receipt and photo consistent. Distinct from RCP-10 in trigger (a database failure rather than an aborted or timed-out upload) and identical in the consistency it guarantees; the review pass examined the pair and kept both on that trigger distinction, which a test needs.

### Verification

Test: induce a write failure during upload (forced fault or connection loss); assert the receipt is unchanged and no photo row exists.

### Traces to

- settled_question#109 — database failure behaviour

## RCP-12 — Photoless receipt is an ordinary answer

### Requirement

When a photo is requested for a receipt that has none, the receipts service shall return the same not-found response it returns for a nonexistent receipt id.

### Rationale

From settled_question#109: most receipts will have no photo, and photo-optional behaviour of existing expenses must be unchanged (must-have 4). The byte-identical wording means neither the absence of a photo nor the absence of the receipt reveals which ids are real — the same discipline RCP-3 enforces.

### Verification

Test: request the photo of a photoless receipt and of a nonexistent receipt id; assert byte-identical not-found responses.

### Traces to

- settled_question#109 — no-photo answer
- settled_question#106 — must-have 4

## RCP-13 — Attach a photo from the receipt's own entry

### Requirement

When the signed-in person is viewing their receipts screen, the frontend shall offer attaching one photo to a receipt from that receipt's own entry.

### Rationale

Must-have 6 part two (settled_question#106), first half; attach and reopen are demonstrated separately.

### Verification

Demonstration: from a receipt's entry on the receipts screen, attach a photo and see it recorded against that receipt.

### Traces to

- settled_question#106 — must-have 6
- settled_question#35 — the outcome someone would notice

## RCP-14 — Reopen the photo from the receipt's own entry

### Requirement

When the signed-in person opens a receipt entry that carries a photo in a later session, the frontend shall present that photo from the receipt's own entry without leaving the application.

### Rationale

Must-have 6 part two, second half, and the outcome someone would notice (settled_question#35): open the photo again without leaving the app and without matching by date against the camera roll.

### Verification

Demonstration: attach a photo in one session, then in a new session open that photo from the same receipt's entry.

### Traces to

- settled_question#106 — must-have 6
- settled_question#35 — outcome someone would notice

## RCP-15 — A receipt that already has a photo refuses a second upload

### Requirement

If an authenticated user submits a photo upload for a receipt they own that already carries a photo, then the receipts service shall refuse the upload with a conflict response naming the one-photo-per-receipt rule, storing nothing.

### Rationale

The binding answer "one photo per receipt" (settled_question#107) given a definite behaviour. The response is named, resolving the Complete shortfall gate_finding#114 raised: an explicit conflict refusal (HTTP 409-class) naming the rule, not the not-found of RCP-3/RCP-12 — the requester owns the receipt, so there is nothing to conceal. Replacing, if ever wanted, is a later code change to the table this feature owns; this choice forecloses nothing.

### Verification

Test: upload a photo to a receipt, then upload a second; assert the second receives the named conflict refusal and the stored photo row still holds the first upload's bytes.

### Traces to

- settled_question#107 — one photo per receipt
- gate_finding#114 — the unspecified refusal response this wording names

## RCP-16 — Photos are served only through the authenticated API

### Requirement

When the frontend displays a receipt photo, the frontend shall fetch the photo bytes through an authenticated API request carrying the signed-in person's bearer token and render them locally.

### Rationale

This settles the photo-serving URL shape that bohdan bound the design to decide deliberately (settled_question#91), resolving the Complete shortfall gate_finding#114 raised against RCP-2/RCP-3. An `<img>` tag cannot carry a bearer header, and dropping authorization is not available for financial documents (settled_question#108); therefore no photo URL exists that works without authorization — the bytes are fetched with the bearer token and rendered client-side (an object URL), so every photo-serving route is RCP-3's authenticated, refusal-equivalent endpoint. The maker's constraint answer (settled_question#84) makes the existing PyJWT auth the only authentication this work may add.

### Verification

Inspection and test: inspect that no route serves photo bytes without the auth dependency, and test that a rendered photo request in the frontend carries the bearer header while no embeddable unauthenticated photo URL exists.

### Traces to

- settled_question#91 — URL-shape binding
- settled_question#84 — existing auth is the only authentication
- settled_question#108 — personal financial documents

## Open questions (one, with its fallback decided)

- **Whether a real 5 MB upload reliably completes inside the existing 10-second TimeoutMiddleware** (backend/app/main.py, `REQUEST_TIMEOUT_SECONDS`) is untested by design: bohdan bound it to be tested against the deployed stack (settled_question#107). The fallback is decided, so feasibility does not depend on the answer: if 5 MB does not fit, the size limit in RCP-4 comes down and the middleware does not go up. Only the final number waits on that test.
