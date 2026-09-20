# Verification report — Receipt photos on expenses (attempt 2)

This stage still has no shell: I ran no commands. What changed since the failed attempt is that the prior gate finding's substance is addressed and now verifiable by reading, and I have read the files the last gate said it could not see. The verdict that still matters is the engine's own run of the test command when this stage closes; what I add is the file-by-file reading behind it.

## Commands run

None by me — no shell exists in this stage. The commands the engine runs as the verdict, per settled_question#200:

- `cd backend && pip3 install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test` — run by the engine; I cannot produce its exit code here. Last known state (gate's attempt-2 run, per code_change#177): backend suite green (33 tests), frontend 20/22, the 2 failures being the photo-rendering tests that attempt 3's `setupTests.ts` stub addresses.
- Lint command: **none** (settled_question#201), confirmed again by reading the tree: `frontend/package.json` has no lint script (dev/build/preview/test only, build running `tsc --noEmit`), `backend/requirements.txt` declares no lint tool, and the only ruff traces (`.ruff_cache/`, `.venv/`) are untracked leavings, not adoption. The lint-v1 finding asks a person to confirm this rather than it passing quietly — that confirmation is still outstanding, and this report does not pretend otherwise.
- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex && meridian sdlc verify-links` — still NOT RUN, recorded at settled_question#199; this stage has no shell. The graph holds no receipt-photo symbols (impact returned found:false on every touched symbol across attempts 3–5). Any dropped artifact-to-code link at the gate is a finding, not housekeeping.

## Results

**Changed since the failed verification (stage_instance#185):** attempt 5 (code_change#223) added `backend/tests/test_receipts_aborted_upload.py` and hardened its two tests — the literal RCP-10 scenario the last gate failed the coverage count on. I read that file in full (192 lines) and verified what it does: it drives the ASGI app directly through `httpx.ASGITransport` with a multipart body whose generator yields half the bytes then raises, catching both `ConnectionResetError` and `httpx.RemoteProtocolError` so the test holds whichever way Starlette surfaces the dying body (propagated exception or a 4xx `MultiPartException` response). Both tests then assert RCP-10's actual demand through the shared `_assert_nothing_stored` helper: zero `receipt_photos` rows for the receipt, and the receipt row's amount and description exactly as before. The second test further proves no debris: after the abort, a normal upload to the same receipt returns 201 and leaves exactly one photo row — so RCP-15's one-photo rule is not tripped by a failed request. **This closes prior finding item 2: RCP-10's literal scenario now has an automated test.** No test was weakened to make anything pass; the change removed a version-sensitive `pytest.raises` wrapper, it did not loosen an assertion (the 4xx branch requires `400 <= status < 500` and still fails loudly on a 2xx).

**Verified by reading the working tree (this answers the prior gate's evidence-window complaints directly):**

- `backend/tests/test_receipts.py` — **read in full, all 410 lines**; the prior gate could see only the first half. Every named test exists and matches its mapped scenario: create_all on a live DB (RCP-6/7, asserting `receipt_photos` exists, `receipts` columns are exactly the pre-feature five, and the pre-existing row readable), attach (RCP-1), reopen with a fresh login token and byte-identical body (RCP-2), the byte-identical refusal set including an admin token (RCP-3/INV-NFR-2), photoless ≡ nonexistent (RCP-12), the size boundary parametrised off `MAX_PHOTO_SIZE_BYTES` with both sizes asserted in the 413 detail (RCP-4), byte-sniffed content type (RCP-5), 409 conflict with first bytes intact (RCP-15), both cascades (RCP-9), rejected-check and injected-commit-failure transaction boundaries (RCP-10/11), and owner-only listing (RCP-8).
- `frontend/src/setupTests.ts` — read in full (26 lines); attempt 3's guarded `createObjectURL`/`revokeObjectURL` stub is present as described, and the reasoning comment names the exact failure it fixes.
- `frontend/src/pages/ReceiptsPage.test.tsx` — read in full (94 lines); five tests covering sign-out, listing (RCP-8), photo presentation with receipt-naming alt text (RCP-14/INV-NFR-3), attach offered from the receipt's own entry (RCP-13), and no second attach (RCP-15 UI). The last two wait on `findByRole('img')` — exactly what the stub unblocks: `ReceiptsStore.loadPhoto` calls `URL.createObjectURL`, whose jsdom `TypeError` was being swallowed by the RCP-12 catch, so no `<img>` rendered.
- `backend/app/routers/receipts.py` — read in full; check order is conflict (409) → size (413, both sizes named) → byte-sniffed type (415), `_get_owned_receipt` collapses nonexistent/not-owner into one 404, and read+write is one `db.add` + `db.commit` after all checks — the all-or-nothing shape RCP-10/11 demand.
- `backend/app/models.py` — `ReceiptPhoto` is a new `receipt_photos` table (FK to receipts.id, `ondelete="CASCADE"`, unique, `LargeBinary data`, `content_type`); **no column added to `receipts`**, only the `photo` relationship — RCP-6/7 honoured exactly.

**No test was changed to make it pass in the weakening sense.** The only test edits in this run's diff are the attempt-5 hardening of the aborted-upload tests (removing a version-dependent exception pin) and, in earlier attempts, tests written new against untested ground.

## Acceptance coverage

Scenario → test (all files read in full this attempt; settled_question#202's mapping verified against them):

| Scenario | Test |
|---|---|
| Attach to photoless receipt (RCP-1) | backend/tests/test_receipts.py::test_attach_photo_to_photoless_receipt |
| Reopen in a later session (RCP-2/14/16) | test_reopen_photo_in_a_new_session_returns_identical_bytes + ReceiptsPage.test.tsx "presents an attached photo from the receipt's own entry…" |
| Receipts screen lists own receipts (RCP-8) | test_list_receipts_returns_only_own_receipts_with_photo_flag + ReceiptsPage "lists the signed-in person's receipts" |
| Size-limit boundary (RCP-4) | test_size_limit_boundary[0-201] / [1-413] |
| Oversized refused, both sizes named, nothing stored (RCP-4) | test_size_limit_boundary[1-413] |
| Non-image bytes declared jpeg refused (RCP-5) | test_non_image_bytes_refused_even_when_declared_jpeg |
| Second photo refused as conflict, first unchanged (RCP-15) | test_second_photo_refused_conflict_and_first_unchanged + ReceiptsPage "does not offer a second attach…" |
| Identical-refusal outline (RCP-3/12) | test_non_owner_and_admin_get_not_found_identical_to_nonexistent_id (pat / unauthenticated / admin) + test_photoless_receipt_is_the_same_not_found_as_nonexistent |
| Deleting a receipt takes its photo (RCP-9) | test_deleting_receipt_takes_its_photo_with_it |
| Deleting a user takes every photo (RCP-9) | test_deleting_user_takes_every_photo_with_it |
| Upload cut off part way stores nothing (RCP-10) | backend/tests/test_receipts_aborted_upload.py::test_upload_aborted_part_way_stores_nothing_and_leaves_receipt_unchanged + test_cut_off_upload_then_normal_upload_succeeds + test_upload_failing_checks_stores_nothing_and_leaves_receipt_unchanged |
| DB failure leaves nothing behind (RCP-11) | test_db_write_failure_during_upload_leaves_nothing_behind |
| Photo table created on live DB, receipts untouched (RCP-6/7) | test_receipt_photos_table_created_and_receipts_untouched |
| Attach from the receipt's own entry (RCP-13) | ReceiptsPage.test.tsx "offers attaching a photo from the receipt's own entry…" — but no Gherkin scenario of its own (see gaps) |

## Known gaps

1. **Everything is unrun by me.** No shell in this stage; the exit code that proves all of the above is the engine's run of the test command. What I verified is that every named test exists, reads as its scenario claims, and that the attempt-3 stub addresses the exact failure mode the gate's attempt-2 output showed.
2. **RCP-13 has no Gherkin scenario** in acceptance_spec#133 — a document amendment, not code; only the frontend control-placement test plus a manual browser demonstration stand for it. Still open from the baseline's open questions.
3. **Lint "none"** awaits the person-confirmation the lint-v1 check asks for; it was re-verified from the tree this attempt (no lint script, no declared lint tool).
4. **Index refresh** never ran (no shell); the code graph is stale relative to the working tree, and impact evidence for the touched symbols does not exist — dependents were judged from the diff against the declared radius.
5. **Bound-upload check** (real 5 MB jpeg vs the 10-second TimeoutMiddleware), **INV-NFR-1** (p95 open under 2000 ms over 50 fetches on the compose stack), and the manual RCP-13 demonstration all need `docker compose up` — outside any suite, per settled_question#204.
6. **Timeout-at-commit tie and refusal latency** (baseline open questions 2–3) remain unspecified and untested, carried by decision; the aborted-upload test's 4xx branch is asserted loosely, so a 400 from some cause other than the abort is possible in principle — covered indirectly because the same hand-rolled multipart format returns 201 on the success path of the second test.
7. **SQLite cascade semantics** depend on `PRAGMA foreign_keys=ON`, set per connection only in the test engines; production sessions rely on the ORM-level cascade and `passive_deletes=True`, which is the same shape the pre-existing `User.receipts` chain has always used.