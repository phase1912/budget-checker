# Receipt photos on expenses

## Summary

This adds the ability to attach a photograph of a receipt to an expense in the budget tracker, and to open that photograph again later from the expense's own entry on a new receipts screen — without leaving the app and without hunting the camera roll by date. Expenses recorded without a photo behave exactly as before.

Design points worth knowing before reading the diff:

- **The photo lives in a new `receipt_photos` table, not a column on `receipts`.** The project has no migration tooling (`Base.metadata.create_all` only, no Alembic), so altering the existing `receipts` table would require hand-written SQL against the user's real data. `create_all` creates a new table for free on the live database; `receipts` is untouched except for one additive relationship.
- **Photo bytes are stored in the database** (SQLite `LargeBinary`), one photo per receipt (unique FK, `ondelete="CASCADE"`), cascading away with the receipt and the user — one storage system, one transaction, no orphan files.
- **Photos are only ever served through the authenticated API.** There is no embeddable unauthenticated photo URL; the frontend fetches the bytes with the bearer token and renders them locally, so an `<img>` tag never needs an open endpoint. Non-owners, admins and unauthenticated requests all get a byte-identical not-found response, deliberately identical to a nonexistent receipt id.
- **Uploads are validated before anything is stored:** ≤ 5 MB (message names both limit and actual size), JPEG/PNG checked against the magic bytes rather than the declared content-type, and a second photo to a receipt that already has one is refused with a 409 conflict. Read + write is a single transaction, so a failed or aborted upload stores nothing and leaves the receipt unchanged.

## Requirements covered

- [[RCP-1]] Attach a photo to a receipt that has none — upload stores bytes in `receipt_photos`, linked by FK.
- [[RCP-2]] Reopen the photo later — the service serves the stored photo to its owner; byte-identical in a new session.
- [[RCP-3]] Only the owner can read a photo — non-owner, unauthenticated and admin all get the same not-found as a nonexistent id.
- [[RCP-4]] Reject oversized photos — over 5 MB refused with both sizes named, nothing stored; boundary tested at exactly the limit.
- [[RCP-5]] JPEG/PNG bytes only — content type sniffed from bytes, not the declared header.
- [[RCP-6]] Photo table created on startup via `create_all`, even against an existing database with real receipts.
- [[RCP-7]] The `receipts` table is left unchanged — schema identical to the pre-feature definition.
- [[RCP-8]] Frontend screen listing the signed-in person's receipts only.
- [[RCP-9]] Deleting a receipt or its user deletes the photo row.
- [[RCP-10]] A failed or aborted upload rolls back whole — including a literal mid-multipart-transfer abort test.
- [[RCP-11]] A database write failure leaves the receipt unchanged with nothing stored.
- [[RCP-12]] A photoless receipt answers the same not-found as a nonexistent one.
- [[RCP-13]] Attach is offered from the receipt's own entry (verified by demonstration plus a frontend control-placement test; no Gherkin scenario — recorded as an open document amendment).
- [[RCP-14]] The photo is presented from the receipt's own entry, in a later session, without leaving the app.
- [[RCP-15]] A second photo to a photographed receipt is refused with a conflict naming the one-photo rule; the first photo is unchanged.
- [[RCP-16]] Photo bytes are fetched through the authenticated API with the bearer token and rendered locally.
- [[INV-NFR-3]] The photo `<img>` carries alt text naming its receipt. [[INV-NFR-4]] One new runtime dependency: `python-multipart`. [[INV-NFR-5]] No new compose services or volumes. [[INV-NFR-1]]/[[INV-NFR-2]] are measure-backed attributes (p95 open latency; byte-identical refusals, covered by test).

## Testing

- Backend: `backend/tests/test_receipts.py` — 13 tests covering create_all on a live pre-feature database, attach, reopen with a fresh token and byte-identical body, the byte-identical refusal set (other user / unauthenticated / admin / photoless ≡ nonexistent), the parametrised size boundary, byte-sniffed content type, 409 conflict with first bytes intact, both deletion cascades, transaction boundaries, and owner-only listing. `backend/tests/test_receipts_aborted_upload.py` — 2 tests streaming a multipart body cut mid-transfer over ASGI, asserting nothing is stored and the receipt is unchanged whichever way Starlette surfaces the abort, and that a normal upload still succeeds afterwards.
- Frontend: `frontend/src/pages/ReceiptsPage.test.tsx` — listing, photo presentation with receipt-naming alt text, attach offered from the receipt's own entry, no second attach. `frontend/src/setupTests.ts` stubs `URL.createObjectURL`/`revokeObjectURL` for the DOM environment.
- Full suite command: `cd backend && pip3 install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test`.
- Not covered here, by recorded decision: the real 5 MB upload against the 10-second `TimeoutMiddleware` and the p95 open-latency measurement both need `docker compose up` (the decided fallback if 5 MB does not fit is that the limit comes down, never the middleware up); RCP-13's in-browser demonstration; the code-graph index refresh.

## Risk and blast radius

- The diff is additive end to end: a new model + relationship on the leaf `Receipt` model, a new router included in `create_app`, `python-multipart` in requirements, and new frontend page/store/client functions plus one route. No existing route, schema column, store or middleware was modified.
- Dependents were checked from the tree (the code graph index holds no symbols for this area — a recorded staleness): every backend test suite reaches the app through `create_app`, and the receipt tests build dedicated FastAPI instances with their own `get_db` overrides, so no shared state leaks into `test_auth`/`test_models`, whose table-set assertion still holds since `receipts` is unchanged.
- Known low-severity findings from review, none blocking: the frontend hard-codes the 5 MB limit where the backend reads it from the environment (they can drift if the decided fallback fires); `loadPhoto`'s bare catch also swallows auth failures, showing a photoless entry instead of an error; the whole upload body is buffered before the size check, so the timeout middleware is the only guard until the bound-upload check runs.
- After merge, watch: the docker compose stack starting against the existing database (the new table must appear, `receipts` untouched), and the bound-upload check that decides the final size limit.
