# Code change — Receipt photos on expenses (attempt 5)

## Summary

The implementation gate of the previous attempt (gate_finding#225) accepted the substance of the RCP-10 work — the literal mid-transfer abort test was found and verified — and named exactly one softness in the code: the test wrapped its ASGI call in `pytest.raises(ConnectionResetError)`, which is version-sensitive because Starlette's multipart parser may convert a dying request body into an `http.multiPartIncomplete` `MultiPartException` (a 400 response) rather than letting the original exception propagate. The gate's own assessment was that "the database-state assertions would survive either way, but the test has never been run."

This attempt hardens exactly that, in one file, touching no production code. `_send_cut_off_request` no longer raises on either behaviour: it catches `ConnectionResetError` and `httpx.RemoteProtocolError` and returns a `(raised, response)` tuple. The test asserts on the outcome whichever branch the installed Starlette takes — a propagated exception, or a 4xx-class error response — and both branches feed the same `_assert_nothing_stored` helper, which is RCP-10's actual demand: no `receipt_photos` row for the receipt, and the receipt's columns exactly as before. The second test (`test_cut_off_upload_then_normal_upload_succeeds`) similarly no longer wraps the abort in `raises`; it asserts nothing stored first, then that a normal upload to the same receipt returns 201 (the RCP-15-adjacent claim that the abort left no debris to trip the one-photo rule).

Nothing else changes from the previous attempts: the backend suite (33 tests) and 20 of 22 frontend tests were green at the gate's attempt-2 run, and attempt 3's `setupTests.ts` stub addressed the 2 frontend failures.

## Requirements implemented

- [[RCP-10]] — the literal 'upload cut off part way' scenario, now made robust to both server-side behaviours a dying multipart body can produce. The mechanism is unchanged from the previous attempt (`backend/tests/test_receipts_aborted_upload.py` streams a multipart body via `httpx.ASGITransport` whose generator yields half the bytes then raises); what changed is that the assertion no longer depends on *how* the abort surfaces — exception or 4xx response — only that the endpoint body never reached `db.commit()`, which both the empty `receipt_photos` table and the untouched receipt row prove.
- [[RCP-15]] (indirect) — `test_cut_off_upload_then_normal_upload_succeeds`, unchanged in substance: an aborted upload leaves the receipt attachable.
- All other requirements ([[RCP-1]]…[[RCP-9]], [[RCP-11]]…[[RCP-16]], [[INV-NFR-1]]…[[INV-NFR-5]]) — implemented and tested in attempts 1–4 of this diff; unchanged by this attempt.

## Symbols changed

Edited in this attempt:

- `_send_cut_off_request` (changed: returns `(raised, response)` instead of propagating; catches `ConnectionResetError` and `httpx.RemoteProtocolError`) — backend/tests/test_receipts_aborted_upload.py
- `_assert_nothing_stored` (added: shared database-state assertions used by both tests) — backend/tests/test_receipts_aborted_upload.py
- `test_upload_aborted_part_way_stores_nothing_and_leaves_receipt_unchanged` (changed: no `pytest.raises` wrapper; asserts exception-or-4xx, then the database state) — backend/tests/test_receipts_aborted_upload.py
- `test_cut_off_upload_then_normal_upload_succeeds` (changed: abort no longer wrapped in `raises`; asserts nothing stored, then the normal upload succeeds) — backend/tests/test_receipts_aborted_upload.py

Unchanged from previous attempts, declared for the blast-radius check (the full feature diff):

- `ReceiptPhoto` (added) and `Receipt.photo` relationship (added) — backend/app/models.py
- `list_receipts`, `upload_receipt_photo`, `get_receipt_photo`, `_get_owned_receipt`, `_sniff_content_type` (added) — backend/app/routers/receipts.py
- `create_app` (changed: includes `receipts.router`) — backend/app/main.py
- `python-multipart` (added to requirements) — backend/requirements.txt
- `fetchReceipts`, `uploadReceiptPhoto`, `fetchReceiptPhotoBytes`, `ReceiptListItem` (added) — frontend/src/api/client.ts
- `ReceiptsStore` (added) — frontend/src/stores/ReceiptsStore.ts
- `ReceiptsPage`, `ReceiptEntry`, `photoAltText`, `formatAmount` (added) — frontend/src/pages/ReceiptsPage.tsx
- receipts route (added) — frontend/src/App.tsx
- `ReceiptsPage.test.tsx` (added) — frontend/src/pages/
- `setupTests.ts` (changed in attempt 3: `URL.createObjectURL`/`revokeObjectURL` stubs) — frontend/src/
- `backend/tests/test_receipts.py` (added, 13 tests) — backend/tests/
- `backend/tests/test_receipts_aborted_upload.py` (added in attempt 4; its remaining symbols — module-level `engine`, `TestingSessionLocal`, `override_get_db`, `app`, plus `_multipart_body`, `_dying_body`, `_register_login_and_make_receipt` — are unchanged this attempt)

Impact tooling: `impact` on `upload_receipt_photo` and `get_db` returned `found: false` — the index holds no symbol for anything this attempt touches (the index is stale relative to the working tree, a standing gap recorded since settled_question#199). The touched file is a leaf test module: nothing imports it, and the production code it exercises is unchanged.

## Design notes

- **Accept both Starlette behaviours rather than pinning one.** The alternative was to keep `pytest.raises(ConnectionResetError)` and treat a 400 as a test failure. Rejected because it is exactly the version-sensitivity the gate named: with `raise_app_exceptions=True` the transport propagates app-level exceptions, but Starlette's multipart parser has, across versions, both re-raised the body error and converted it to `MultiPartException` → 400. What RCP-10 requires is invariant across those versions — nothing stored, receipt unchanged — so the test now asserts the invariant and merely *checks* which surface the abort took. If neither happens (a 201, say, meaning the endpoint ran to commit on a half-body), the test fails loudly, as it should.
- **`httpx.RemoteProtocolError` caught alongside `ConnectionResetError`.** httpx wraps transport-level body failures in `RemoteProtocolError`; if the generator's exception surfaces through the client rather than the ASGI callable, this is how it arrives. Catching both makes the tuple's `raised` arm cover the propagation path whichever layer raises.
- **Shared `_assert_nothing_stored` helper.** Both tests asserted the identical database state inline; extracting it makes the RCP-10 demand readable in one place and guarantees the second test checks the *same* post-abort state before the follow-up upload, not a weaker version of it.
- **No production code changed.** The router's single `db.add` + `db.commit` after all checks is the all-or-nothing shape RCP-10 requires; this attempt only makes the proof of that shape independent of Starlette's error plumbing.

## Risks

- **Still unrun by me — no shell in this stage.** The exit code that proves these tests pass is the gate's run of `cd backend && pip3 install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test`. The change removes a failure mode (version-dependent exception propagation) rather than adding one, and the file was re-read in full after writing; but reading is not running.
- **The 4xx branch is asserted loosely** (`400 <= status < 500`): if Starlette ever surfaced a dying body as a 5xx, the test would fail on that assertion — correctly, since a 500 on a client disconnect would itself be a defect — but the branch exists so the test fails with a clear status in the message rather than a confusing pass-through.
- **One edge the loose branch admits:** a 400 could in principle come from something other than the abort (malformed boundary, say). The tiny hand-rolled multipart body is exercised by the *success* path of the second test (a normal upload through the same boundary format returns 201), so a systematically malformed body would fail there first — the ambiguity is covered.
- **Carried forward, unchanged:** the bound-upload check (5 MB vs the 10-second `TimeoutMiddleware`) is a compose-stack measurement (baseline open question 1); timeout-at-commit and refusal latency (open questions 2–3) remain untested; RCP-13's missing Gherkin scenario is a document amendment to acceptance_spec#133, out of this stage's scope; the graph index remains stale (no receipt-photo symbols), recorded since settled_question#199.
