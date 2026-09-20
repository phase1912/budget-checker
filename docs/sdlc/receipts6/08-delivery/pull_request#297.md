No pull-request URL was reported by the opening step (`open-pr-v1`): the body file it was supposed to write (docs/sdlc/receipts6/pull-request-body.md) is absent from the tree, and no URL was handed to this step. Recorded here rather than invented — if no pull request was actually opened on branch sdlc/receipts6, this artifact must fail rather than name one that does not exist.

## Summary

This adds receipt photos to the budget tracker (branch `sdlc/receipts6`, targeted at `master`, per the maker's branch answers settled_question#289/#290). A person recording an expense can attach a photograph of the receipt to it and open that photograph again later from the expense's own screen. The photo lives in a new `receipt_photos` table (backend/app/models.py, `ReceiptPhoto`) — deliberately no column is added to the existing `receipts` table, because this repository has no migration tooling (`Base.metadata.create_all` only, backend/app/main.py `create_app`), so a new table is created for free against the maker's live database while an ALTER would need hand-written SQL against real rows. A new receipts router (backend/app/routers/receipts.py) provides list, upload and authenticated photo download; the frontend gains a receipts screen (frontend/src/pages/ReceiptsPage.tsx, frontend/src/stores/ReceiptsStore.ts) that attaches and presents photos per receipt entry, fetching bytes with the bearer token so no unauthenticated photo URL exists anywhere. Expenses without photos behave exactly as before.

## Requirements covered

All requirements are from the requirements baseline (requirements_baseline#148), which carries them verbatim from requirement#112:

- [[RCP-1]] Attach a photo to a receipt that has none
- [[RCP-2]] Reopen the photo later
- [[RCP-3]] Only the owner can read a photo (byte-identical refusals)
- [[RCP-4]] Reject oversized photos (5 MB limit, both sizes named)
- [[RCP-5]] Accept jpeg and png bytes only (sniffed from bytes, not headers)
- [[RCP-6]] Photo storage table created on startup
- [[RCP-7]] The receipts table is left unchanged
- [[RCP-8]] Receipts screen on the frontend
- [[RCP-9]] Photo dies with its receipt or user (cascades)
- [[RCP-10]] Failed upload rolls back whole
- [[RCP-11]] No orphaned state on write failure
- [[RCP-12]] Photoless receipt is an ordinary answer
- [[RCP-13]] Attach a photo from the receipt's own entry (verified by demonstration; see risk section)
- [[RCP-14]] Reopen the photo from the receipt's own entry
- [[RCP-15]] A second upload to a photographed receipt is refused as a conflict
- [[RCP-16]] Photos are served only through the authenticated API
- [[INV-NFR-1]] Photo open latency (p95 under 2000 ms) — measurement outstanding
- [[INV-NFR-2]] Photo confidentiality (byte-identical refusals, 100%)
- [[INV-NFR-3]] Alt text on the photo viewer
- [[INV-NFR-4]] One new dependency only (python-multipart)
- [[INV-NFR-5]] No new compose services or volumes

## Testing

From verification_report#246 and the engine's runs of the settled test command (`cd backend && pip3 install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test`):

- Backend: 33 tests green (13 in backend/tests/test_receipts.py covering RCP-1..RCP-12 and RCP-15, plus the aborted-upload file backend/tests/test_receipts_aborted_upload.py with the literal RCP-10 mid-transfer abort test and its no-debris companion).
- Frontend: 22 tests, initially 20/22 (both failures in ReceiptsPage.test.tsx dying at `findByRole('img')` because jsdom lacks `URL.createObjectURL`, whose throw was swallowed by `loadPhoto`'s RCP-12 catch); attempt 3 stubbed `createObjectURL`/`revokeObjectURL` in frontend/src/setupTests.ts, and the review traced the fix to that exact failure mode. The exit code that proves 22/22 is the engine's own run.
- Lint: none — no linter or type checker is configured in this repository (no lint script in frontend/package.json, no lint tool declared in backend/requirements.txt; the ruff traces are untracked cache leavings, not adoption).
- Not runnable in a suite (recorded in verification_report#246's known gaps and settled_question#204): the bound-upload check (a real 5 MB upload inside the 10-second TimeoutMiddleware, via `docker compose up`; the decided fallback is that the size limit comes down, never the middleware up), INV-NFR-1's p95 measurement, and the manual RCP-13 in-browser demonstration.

## Risk and blast radius

From review_report#267 (verdict READY, four low findings) and its blast-radius walk:

- The graph index holds no symbols for this area (impact returned found:false throughout), so every dependent was read from the tree: `create_app` gains one router include (a broken import fails loudly for all backend test suites, which build dedicated app instances anyway); `Receipt` adds only a relationship, columns unchanged, so the test_models.py:29 table assertion holds; `get_current_active_user` gains one caller; frontend routes are additive.
- Low finding 1: the frontend hard-codes the 5 MB limit while the backend's is environment-tunable — if the bound-upload test brings the backend limit down, the frontend will accept files the server refuses. Worth a ticket so the fallback cannot land in the backend alone.
- Low finding 2: `loadPhoto`'s bare catch conflates "no photo" with "cannot read your photo" (a 401 renders as photoless). Harmless with one user and fresh tokens.
- Low finding 3: the router reads the whole upload into memory before the size check; the 10-second TimeoutMiddleware is the only guard on large bodies until the bound-upload question settles.
- Low finding 4 (document artifact): RCP-13 has no Gherkin scenario in acceptance_spec#133 — closing it is a spec amendment, not code.
- After merge, watch: `docker compose up` against the existing live database (the new table must be created by `create_all` with `receipts` untouched — covered by test_receipt_photos_table_created_and_receipts_untouched), the 5 MB-vs-10-second bound-upload check, and INV-NFR-1's p95 measurement. Production cascade for `receipt_photos` rests on the ORM-level cascade plus `ondelete="CASCADE"` without a `PRAGMA foreign_keys=ON` listener on the production engine — the same shape the pre-existing `User.receipts` chain has always used.