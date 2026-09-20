# Problem brief — Receipt photos on expenses

## Problem
When a person records an expense in this budget tracker and later needs the receipt behind it — for a reimbursement or a tax return — the tracker stores the amount and description but no image, so the record itself carries no evidence. The only way to find the proof is to leave the app, search the device's camera roll, and match a photo to the expense by date — a search that gets less likely to succeed the older the expense is, because camera rolls get culled. The tracker's expense records are therefore not usable as proof, and the person recording the expense has no way to fix that from within the app.

## Who is affected
The maker (bohdan) and anyone else who uses this tracker to claim money back. It is a personal project with one active user, so there is no headcount to give. By the maker's own estimate roughly a third of recorded expenses are ones where the receipt matters, and each of those currently means a search through the camera roll. That share is one person's estimate, not a measurement. (from the answer to `who-is-affected`)

## Evidence
The evidence is thin and the maker says so plainly: no tickets, no metrics, no recordings — there is nobody but the maker to report anything. What exists is one person's own experience of going looking for a receipt behind an expense and not finding it. (from the answer to `evidence`)

The repository confirms the gap structurally rather than empirically:
- The `Receipt` model (backend/app/models.py:56) carries id, user_id, amount, description and created_at — no photo or image field of any kind. Its sqlite `receipts` table likewise has no photo column. (from the answer to `prior-attempts`, confirmed at triage)
- `create_app()` in backend/app/main.py registers only the health and auth routers (main.py:80-81), so no endpoint serves expense data at all; there are no expense screens on the frontend either. (from the answer to `evidence` and `expected-symbols`, confirmed by reading main.py)
- The code graph holds no symbol for any expense/receipt-photo concept: `query` returned 0 hits and `context`/`impact` on `Receipt` came back `found: false`, so no callers or flows can bound the change from the graph — the tree is the only evidence there. (from the answer to `expected-symbols`)

## Cost of inaction
Not much breaks, and the maker says so honestly: the tracker keeps working exactly as it does now. What happens is that the records stay unusable for anything needing proof — a reimbursement, a tax return — so the tool stays a notebook rather than a record. The one thing that decays is recoverability: camera rolls get culled and paper receipts fade, so the older an unlinked expense gets, the less likely its evidence still exists to be linked at all. (from the answer to `cost-of-inaction`)

## Success metrics
In the maker's own order of how soon each can be checked (from the answer to `success-signal`):
1. For an expense recorded earlier, its receipt photo opens from that expense's own screen, without leaving the app and without a manual date-matching search in the device's camera roll. Checkable by hand the moment the feature exists: record an expense, reopen it, open the photo.
2. Expenses recorded without a photo behave exactly as they do today — checkable by running the existing test suite unchanged: backend/tests/test_models.py exercises `Receipt` (including `test_schema_defines_core_entities` and the user-deletion cascade test) and must pass without modification.
3. The share of receipt-bearing expenses that carry a photo — **not measurable yet**: no counter for that exists today and this work deliberately does not add one. Requires instrumentation that does not exist; stated here so it is not mistaken for a shipped metric.

## Out of scope
(from the answer to `out-of-scope`)
- Reading anything off the photo: no OCR, no amount or date extraction, no auto-filling the expense from the image. The photo is evidence a person looks at, not a data source. (docs/sdlc/srs-1/baseline.md:15 already listed receipt-photo recognition and duplicate-photo detection out of scope.)
- Bulk import of an existing camera roll.
- Sharing or exporting receipts to anyone else.
- Multiple photos per expense.
- Any storage backend beyond what this repository already runs (i.e. no object store integration in this piece of work).

Also out, from the change brief: deciding or building expense summarisation/reporting on top of receipts (a stale `__pycache__/app.cpython-314.pyc` references a removed 'expense'/'summarize' module; no code or document for it survives).

## Assumptions
- That "expense" means the existing `Receipt` model (add a photo column) rather than a distinct Expense concept — unsettled at triage and still not confirmed (carried as an open question below).
- That the photo can be stored within what the repository already runs (sqlite + the existing deployment), rather than needing new infrastructure — but the storage decision itself is open.
- That the one active user is the whole user base for the foreseeable future; nothing here is designed to scale beyond that.
- That the maker's "roughly a third of expenses need receipts" figure, being one person's estimate, is directionally right even though it is not a measurement.
- That a photo is attached at or near recording time. Single retro-attachment after the fact has not been confirmed either way — see open questions.

## Open questions
- Where receipt photos are stored: DB blob, server filesystem, or object store — flagged at triage as a decision that must be settled before code, and one that drives size. Still open.
- Does "expense" mean the existing `Receipt` model or a new distinct concept? Flagged at triage as worth one question; not yet answered.
- Image size/format limits, and retention: what happens to the photo when the expense is deleted — unsettled (carried from the change brief).
- Whether a photo can be attached to an expense after the fact (one at a time), or only at recording time — assumed in the assumptions above, never asked.