# Requirements: receipt-crud-2 — Receipt create, read, update, delete

Derived from the approved solution concept (docs/sdlc/receipt-crud-2/02-concept/solution_concept#90.md): four additive endpoints inside the existing `backend/app/routers/receipts.py` router, reusing `_get_owned_receipt` and `_NOT_FOUND_DETAIL` (backend/app/routers/receipts.py lines 23, 35–42), leaning on the declarative Receipt–ReceiptPhoto cascade, with no migration and the list endpoint frozen.

Review notes on this revision (all against ISO/IEC/IEEE 29148):

- **RCR-1** no longer names the model-default mechanism (implementation leak); it states the observable capability.
- **RCR-2** previously left the response body undecided — two engineers could have built different bodies and both been right. It now names the fields, chosen to match a list entry (backend/app/routers/receipts.py lines 57–64). This choice was not made by the person; it is recorded as an open question below.
- **RCR-3** was ambiguous between PATCH and PUT semantics (does an omitted field stay or clear?). It now states partial-update semantics; whether a cleared description is distinguishable from an unchanged one via the API is an open question for bohdan.
- **RCR-4** said "return a success answer", which 200-with-body and 204-no-body both satisfy. The assumption (the module's `MessageResponse` idiom, as `upload_receipt_photo` uses at line 111) is stated in the requirement and recorded as open.
- **RCR-6**'s "the module's uniform not-found answer" was a dangling reference; the term is now defined in the requirement itself.
- **RCR-7** is retained: it is demanded verbatim by the failure-behaviour answer (settled_question#113) and makes the chosen approach's known validation gap explicit rather than silently accepted.
- **RCR-8** was checked against the code: the pinned shape is exactly what `list_receipts` returns (backend/app/routers/receipts.py lines 51–66), including `amount` as a number and ordering by `created_at` descending.
- Priorities: all requirements are `must`, matching the must-have answer (settled_question#110), which named exactly this set and nothing more — nothing is misprioritised.

## RCR-1 — Create a receipt

### Requirement

When an authenticated caller submits a new receipt with an amount and an optional description, the receipts router shall create a receipt owned by that caller with a unique identifier and a creation timestamp it did not take from the request.

### Rationale

Nothing in the backend can put a row in the receipts table today, so `list_receipts` (backend/app/routers/receipts.py lines 45–66) lists rows nothing can produce — the core loop the goal asks for first.

### Verification

Test: POST a valid body, assert a success status, then read the created receipt back through the list endpoint with the caller's user id, a server-generated id and timestamp, and the submitted amount and description.

### Traces to

- [[prob-1/concept-1]] — chosen approach: create stamps user_id from the authenticated caller and takes amount and optional description and nothing else.

## RCR-2 — Read one receipt

### Requirement

When an authenticated caller requests a receipt by identifier, the receipts router shall return that receipt's id, amount, description and creation timestamp if the receipt exists and belongs to the caller, and not return any other receipt.

### Rationale

The goal names read-one as one of the four missing operations; the list endpoint alone cannot fetch a single receipt. The returned fields were chosen to match a list entry (backend/app/routers/receipts.py lines 57–64) minus `has_photo`, which the read-one body is assumed not to carry — an assumption, not a decision (see open questions).

### Verification

Test: create a receipt, GET it by id, assert the returned fields match; test a second user's id returns 404 per RCR-6.

### Traces to

- [[prob-1/concept-1]] — chosen approach: read-one resolves through `_get_owned_receipt` like the photo endpoints.

## RCR-3 — Update a receipt's amount or description

### Requirement

When an authenticated caller submits a new value for an existing receipt's amount or description, the receipts router shall apply exactly the submitted changes to the caller's receipt, leave every field not submitted unchanged, and change no other field.

### Rationale

The success signal (settled_question#73) includes correcting a typo in the amount; update is scoped to amount and description by the chosen approach, which rules out touching id, user_id or created_at. Partial-update semantics are now stated explicitly so that omitting the description cannot be read as clearing it.

### Verification

Test: create, submit only a new amount, assert the amount moved and the description, id, user_id and created_at are unchanged; then submit both and assert both moved.

### Traces to

- [[prob-1/concept-1]] — chosen approach: update touches only amount and/or description.

## RCR-4 — Delete a receipt

### Requirement

When an authenticated caller requests deletion of a receipt that belongs to the caller, the receipts router shall delete that receipt and answer with a success status and a body in the module's existing simple-message form, as the photo-upload endpoint answers.

### Rationale

Fourth missing operation in the goal; deletion is irreversible for the user (settled_question#89), which is why it must resolve through the ownership check before anything is removed. The success body shape was never decided; the stated form follows the module's existing `MessageResponse` idiom (backend/app/routers/receipts.py line 111) and is recorded as an open question.

### Verification

Test: create, DELETE, assert the success status and body form, then assert GET by that id returns 404.

### Traces to

- [[prob-1/concept-1]] — chosen approach: delete is `db.delete(receipt)` in the existing router.

## RCR-5 — Deleting a receipt takes its photo with it

### Requirement

When a receipt is deleted through the API, the receipts router shall remove that receipt's attached photo in the same operation.

### Rationale

The goal states it explicitly, and the declarative cascade (`cascade="all, delete-orphan"`, `ondelete="CASCADE"`) already provides the mechanism — the requirement pins that it holds through the HTTP path, not only at the model layer where `test_deleting_receipt_takes_its_photo_with_it` (backend/tests/test_receipts.py line 310) already pins it.

### Verification

Test: create a receipt, upload a photo, delete the receipt, assert no photo remains retrievable for that receipt id.

### Traces to

- [[prob-1/concept-1]] — chosen approach: the declarative cascade removes the ReceiptPhoto.

## RCR-6 — Uniform not-found for foreign or missing receipts

### Requirement

If a receipt identifier names a receipt that does not exist or does not belong to the authenticated caller, then the receipts router shall answer with HTTP 404 and the detail "Receipt not found", identically in status code and body for both cases.

### Rationale

The goal demands it of each new operation. "Uniform not-found" is defined here rather than referenced, so the requirement is complete on its own: this is the answer `_NOT_FOUND_DETAIL` (backend/app/routers/receipts.py line 23) and `_get_owned_receipt` (lines 35–42) already produce for the photo endpoints; nothing may leak whether a foreign receipt exists.

### Verification

Test: for read, update and delete, assert a nonexistent id and another user's receipt id both yield 404 with detail "Receipt not found" and indistinguishable bodies.

### Traces to

- [[prob-1/concept-1]] — chosen approach: nonexistent id and someone else's receipt both get the same not-found.
- [[prob-1/concept-2]] — failure behaviour: a receipt that is not the caller's is the same uniform not-found as one that does not exist.

## RCR-7 — Amount validation refuses negative or over-precise values

### Requirement

If a create or update submits an amount that is negative or carries more than two decimal places, then the receipts router shall refuse it with an answer that names the rule broken, without creating or changing any receipt.

### Rationale

The failure-behaviour answer (settled_question#113) demands it: the chosen raw-dict approach gives no typed validation, so without an explicit check a bad amount reaches the database layer — the same failure class the budgets7 review documented for `BudgetCreate.target_amount`. "Without creating or changing any receipt" was added so the refusal is falsifiable on the data, not only on the status code.

### Verification

Test: create and update with a negative amount and with three decimal places, assert refusal with a rule-naming detail and that no row was created or changed.

### Traces to

- [[prob-1/concept-2]] — failure behaviour: a negative or over-precise amount is refused with the rule named.
- [[prob-1/concept-3]] — risks: untyped create/update letting bad input reach the database.

## RCR-8 — The existing list endpoint answers as it does today

### Requirement

The receipts router shall return from GET /api/v1/receipts the authenticated caller's receipts as objects with id, amount as a number, description, created_at and has_photo, ordered by creation time descending.

### Rationale

The goal freezes the existing list endpoint's answer exactly; pinning the shape here is what makes any drift in service of the new endpoints visible. Verified against the code: this is exactly what `list_receipts` returns (backend/app/routers/receipts.py lines 51–66), including the float conversion of `amount` and the `has_photo` flag.

### Verification

Inspection and test: the existing list tests in backend/tests/test_receipts.py pass unmodified, and the diff never touches `list_receipts`.

### Traces to

- [[prob-1/concept-4]] — constraints: the existing list endpoint's response must not change.
