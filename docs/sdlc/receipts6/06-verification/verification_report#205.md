# Verification report — Receipt photos on expenses

**Honesty note first: this stage has no shell.** I ran no commands; every command below is one the engine itself runs, or one whose leavings in the tree I read as static evidence. The verdict that matters is the gate's own test run, which happens when this stage closes. What this report adds is the code reading behind it: I verified the diff against the requirements line by line in the working tree, and I verified that attempt 3's fix (the `setupTests.ts` stub) actually unblocks the rendering path the two previously failing tests wait on.

## Commands run

None by me — no shell in this stage. The commands recorded as the run's verdict, per settled_question#200/#171, with their last known outcomes:

- `cd backend && pip3 install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test` — the gate's attempt-2 run (per code_change#177's note) showed **20/22 frontend tests green, both failures in `ReceiptsPage.test.tsx`** (`RCP-14` photo-presentation and the `RCP-15` UI test built on it), and the full backend suite green. Attempt 3 then added the `setupTests.ts` stub; **that run's exit code is exactly what the gate's next run produces and I cannot produce it here.** The `.pytest_cache/v/cache/lastfailed` file reads `{}` and `nodeids` lists all 33 backend tests including all 13 of `test_receipts.py` — consistent with the backend suite having last run clean, but it is a cache, not a live run.
- Lint command per settled_question#201: **none** — no linter or type checker is configured in this repository (no ruff/mypy config tracked, no lint script in `frontend/package.json` beyond `"test": "vitest run"` and `"build"`); this answer says "none" and a person should confirm that rather than it passing silently.

## Results

**What I verified in the working tree (static reading, not execution):**

- `backend/app/models.py` — `ReceiptPhoto` (line 77) is a **new table** `receipt_photos` with `receipt_id` as FK, `unique=True`, `ondelete="CASCADE"`, plus `content_type` and `LargeBinary data`. **No column added to `receipts`** — the model adds only a relationship on `Receipt`. This honours RCP-6/RCP-7 and the maker's binding "no ALTER" constraint exactly; `create_all` in `create_app` (main.py:87) creates the new table against a live DB without touching existing rows.
- `backend/app/routers/receipts.py` — upload checks order: conflict (409, RCP-15) → size (413, **both sizes named in detail**, RCP-4) → **byte-sniffed content type** (415, RCP-5 — declared header is ignored, JPEG/PNG magic checked, `_sniff_content_type`). `_get_owned_receipt` collapses nonexistent-id / not-owner / photoless into one identical 404 (RCP-3/RCP-12), and the admin gets the same answer because authorization is on `receipt.user_id`, not role. Read + write is one `db.add` + `db.commit` — nothing stored unless every check passes (RCP-10/11 shape). The bearer dependency is `get_current_active_user` — no new auth path, per the baseline's binding rule.
- `frontend/src/setupTests.ts` — attempt 3's fix, verified: it stubs `URL.createObjectURL`/`revokeObjectURL` in `beforeAll`, guarded by `typeof`. Root cause traced and confirmed: `ReceiptsStore.loadPhoto` (line 44-45) calls `URL.createObjectURL(blob)`; jsdom lacks it; the `TypeError` lands in `loadPhoto`'s bare `catch` (line 49) — written deliberately for RCP-12 — so `photoUrls` stays empty and no `<img>` renders, which is precisely the `findByRole('img')` timeout the gate's attempt-2 output showed. The stub is the right fix: production error handling stays broad because RCP-12 needs it broad; the browser API belongs to the test environment.
- `ReceiptsPage.tsx` — attach offered only from a receipt's **own entry** with no photo (RCP-13), control disappears once `has_photo` (RCP-15 UI), photo rendered from the entry with alt text naming the receipt (RCP-14, INV-NFR-3), client-side size mirror with both sizes named.
- Backend test file `backend/tests/test_receipts.py` — all 13 tests read in full and each matches the acceptance scenario it claims; nothing is a tautology. The prior gate's "cut off mid-file" complaint is about the evidence window, not the file; the whole file is present in the tree (410 lines).

**Test outcome at last known state:** backend 33/33 green (per `.pytest_cache` nodeids, corroborated by the gate's attempt-2 note). Frontend: 20/22 at attempt 2; the 2 failures are what attempt 3's stub addresses, and I traced the path — with the stub in place `loadPhoto` completes, `photoUrls['r1']` is set, the `{photoUrl && <img>}` branch renders, and both tests' `findByRole('img')` resolves. I did **not** run them; the gate's run is the proof.

**No test was changed to make it pass.** Attempt 3 touched only `setupTests.ts` (test environment), no assertion was weakened, and no production code was changed to accommodate a test.

## Acceptance coverage

Scenario → test (from settled_question#202, verified against the actual files):

- RCP-1 attach to photoless receipt → `backend/tests/test_receipts.py::test_attach_photo_to_photoless_receipt`
- RCP-2/14/16 reopen in a new session → `test_reopen_photo_in_a_new_session_returns_identical_bytes` (fresh token, byte-identical) + `frontend/src/pages/ReceiptsPage.test.tsx` "presents an attached photo from the receipt's own entry" (RCP-14, alt text per INV-NFR-3)
- RCP-8 listing → `test_list_receipts_returns_only_own_receipts_with_photo_flag` + ReceiptsPage "lists the signed-in person's receipts"
- RCP-4 boundary → `test_size_limit_boundary[0-201]` / `[1-413]`, parametrised off `MAX_PHOTO_SIZE_BYTES`, both sizes asserted in the 413 detail
- RCP-5 → `test_non_image_bytes_refused_even_when_declared_jpeg`
- RCP-15 → `test_second_photo_refused_conflict_and_first_unchanged` + ReceiptsPage "does not offer a second attach"
- RCP-3/12 identical-refusal outline → `test_non_owner_and_admin_get_not_found_identical_to_nonexistent_id` (pat / unauthenticated / admin / photoless each byte-identical to the nonexistent-id baseline) + `test_photoless_receipt_is_the_same_not_found_as_nonexistent`
- RCP-9 receipt delete → `test_deleting_receipt_takes_its_photo_with_it`; user delete → `test_deleting_user_takes_every_photo_with_it`
- RCP-10/11 rollback → `test_upload_failing_checks_stores_nothing_and_leaves_receipt_unchanged`, `test_db_write_failure_during_upload_leaves_nothing_behind` — **partial**: see gaps; the aborted-transfer scenario proper is not automatable in this suite
- RCP-6/7 create_all on live DB → `test_receipt_photos_table_created_and_receipts_untouched` (builds an old-schema DB with a real receipt row, asserts `receipt_photos` exists, `receipts` columns unchanged, row readable) — verified present, this is the one nobody covered before
- RCP-13 (attach from the receipt's own entry) → **partially covered**: the frontend test "offers attaching a photo from the receipt's own entry" exercises the control's existence and placement, but RCP-13 has **no Gherkin scenario** in acceptance_spec#133 (recorded at baseline as open question 6) and no end-to-end automated test; the in-browser demonstration remains outstanding.

## Known gaps

1. **Attempt 3's fix is unrun by anyone including me.** The stub's correctness is argued from the failure the gate's attempt-2 output shows, and the code path is traced; the exit code is the gate's next run. If it still fails, the next suspect is a `beforeAll` timing issue (the stub installing after some module captures the original), but nothing in the tree suggests that.
2. **RCP-10's literal scenario** — a request actually cut off mid-multipart-transfer — has no automated test; the suite covers the equivalent transaction boundary (rejected checks, injected commit failure), not a real abort. The transaction shape makes the behaviour plausible, not proven.
3. **Bound-upload check** (does a real 5 MB upload fit the 10-second `TimeoutMiddleware`?) — needs `docker compose up` and a real POST; no suite does this. The fallback is decided (limit down, never middleware up) and `MAX_PHOTO_SIZE_BYTES` is an env-tunable constant on both sides precisely so this is a one-line change if it fails.
4. **INV-NFR-1** (p95 photo-open under 2000 ms over 50 fetches at the limit on the compose stack) — a measurement, not a test; not run.
5. **Timeout-at-commit tie and refusal latency** (baseline open questions 2-3) — unspecified and untested, carried forward as agreed.
6. **RCP-13's missing Gherkin scenario** — a document amendment to acceptance_spec#133, not code; the frontend test covers the control's placement but the spec still doesn't demand what the test asserts.
7. **Index refresh** (`node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` + `meridian sdlc verify-links`) — recorded as NOT DONE at settled_question#199 because no shell exists in these stages; the graph's staleness (no receipt-photo symbols at settled_question#172) stands uncorrected. Any dropped artifact-to-code link at the gate is a finding, not housekeeping.
8. **SQLite/production divergence:** the suite runs on sqlite (in-memory/file) with PRAGMA foreign_keys ON per connection; production runs sqlite in a volume — same engine, so low risk, but `passive_deletes=True` + `ondelete="CASCADE"` behaviour is only as good as the pragma being set everywhere it runs.