# Verification report: receipt-crud-2 — Receipt create, read, update, delete (verification, attempt 1)

Branch: `receipt-crud-2`. Code under verification: `backend/app/routers/receipts.py` (four new endpoints `create_receipt`, `get_receipt`, `update_receipt`, `delete_receipt`, plus helpers `ReceiptCreate`, `ReceiptUpdate`, `_check_amount`, `_owned_receipt_or_404`, `_receipt_body`, and the photo endpoints refactored onto `_owned_receipt_or_404`) and `backend/tests/test_receipts_crud.py` (439 lines, 17 test functions / 21 collected items). Registering document: `docs/sdlc/receipt-crud-2/05-implementation/code_change#170.md`.

## Commands run

**None.** This stage's toolset reads and searches the repository (read_file, list_files, search_text, context, impact, query) and executes no shell — so `cd backend && pip3 install -r requirements.txt && python3 -m pytest` (settled_question#187) could not be run from here, and neither could `git diff --stat`. This is the same gap the implementation stage recorded (settled_question#186: the re-index could not be executed either). The gate runs the test command itself and its exit code is the verdict; what this report adds is the file-level evidence below. I did not fabricate any exit status.

What I did run, as repository reads, all succeeding:

- `read_file backend/app/routers/receipts.py` (253 lines) — confirms every handler and helper the code_change names, with the implementations matching the described contract.
- `read_file backend/tests/test_receipts_crud.py` (439 lines, two windows) — confirms all 17 test functions, `_naive_utc_now` at lines 97–101, `before = _naive_utc_now()` at line 109, `datetime.fromisoformat(body["created_at"]).replace(tzinfo=None)` at line 120 — exactly the attempt-2 fix the code_change describes.
- `list_files backend/tests` — confirms the new module and that no other test file was added or renamed.
- `search_text` for `test_deleting_receipt_takes_its_photo_with_it` — found at backend/tests/test_receipts.py line 310, as the code_change claims; the existing module also still carries its 13 tests (lines 109–393 hits), so the pre-existing guard suite is intact.
- `read_file docs/sdlc/receipt-crud-2/05-implementation/code_change#170.md` (64 lines) — registered document and materialized file agree; the attempt-3 materialization-integrity finding is closed as far as reads can close it.

## Results

Not run, so no pass/fail verdict is mine to give. What the file evidence establishes:

- **The attempt-2 fix is present in the working tree.** The one test the previous gate failed (`test_create_receipt_returns_body_and_row_exists`, TypeError on naive-vs-aware datetime subtraction per code_change#170) now compares against `_naive_utc_now()` (line 109) and normalizes the parsed timestamp (line 120). The code_change itself flagged that this fix "has still not been run" — the gate's run of the suite is the first execution of it. The fix is confined to that test's arithmetic; the router's answer was already correct.
- **The implementation matches the registered document symbol-for-symbol.** All four endpoints exist with the documented status codes (POST 201 at receipts.py line 103, PATCH line 177, DELETE 200 with `MessageResponse` at line 197, GET line 147); `_check_amount` raises 422 with the exact rule-naming details (lines 56–71); `_owned_receipt_or_404` raises 404 with detail exactly `_NOT_FOUND_DETAIL` = "Receipt not found" (lines 25, 84–89); `list_receipts` is untouched in shape (lines 123–144); `models.py` is not in the diff surface; no frontend file is in the test list or the router's imports.
- **Test count:** 17 test functions in `test_receipts_crud.py`; the two parametrized sets (uniform-404 ×3 methods, bad-amount ×2 amounts on each of create and update) make 21 collected items, consistent with the "1 failed, 76 passed" figure the previous gate reported for the whole suite.
- **Existing suites untouched:** `test_receipts.py` (13 test functions, unchanged, including the model-level cascade pin at line 310) and `test_receipts_aborted_upload.py` remain, which guard the photo-endpoint refactor.

## Acceptance coverage

Scenario → test (all in `backend/tests/test_receipts_crud.py` unless stated):

| Scenario | Test |
|---|---|
| RCR-1 A receipt is created | `test_create_receipt_returns_body_and_row_exists` |
| RCR-1 Created without a description | `test_create_receipt_without_description_reads_back_null` |
| RCR-1 New receipt first in list | `test_created_receipt_appears_first_in_list_newest_first` |
| RCR-2 Read back by identifier | `test_read_back_own_receipt` |
| RCR-3 Amount corrected, nothing else moves | `test_update_amount_leaves_everything_else` |
| RCR-3 Field not submitted left alone | `test_update_only_description_leaves_amount`, `test_empty_update_changes_nothing_and_returns_receipt` |
| RCR-4 Deleted, then not found | `test_delete_receipt_then_read_is_not_found` |
| RCR-5 Delete takes photo | `test_delete_receipt_takes_its_photo_with_it` (HTTP); model pin `test_deleting_receipt_takes_its_photo_with_it`, `backend/tests/test_receipts.py:310` |
| RCR-6 Uniform not-found (read/update/delete × missing/foreign/deleted) | `test_missing_foreign_and_deleted_are_the_same_not_found` (parametrized ×3, asserting status, byte-identical body and content-length — RCR-NFR-2's quantified form) |
| RCR-7 Bad amount refused on create | `test_bad_amount_refused_on_create_and_nothing_created` (×2) |
| RCR-7 Bad amount refused on update | `test_bad_amount_refused_on_update_and_nothing_changed` (×2) |
| RCR-7 accepted boundaries | `test_amount_boundaries_accepted` (0, 0.01, 99999999999.99 → 201) |
| RCR-8 List answers as always | `test_list_endpoint_shape_and_ordering_frozen` |

Beyond the spec: `test_client_supplied_id_and_created_at_are_ignored` (baseline open question 6), `test_unauthenticated_requests_refused` (open question 7), `test_foreign_admin_gets_not_found_not_server_error`. Every functional scenario RCR-1..RCR-8 has a row; none is uncovered.

## Known gaps

- **Nothing was executed.** The entire verdict — including whether the attempt-2 timezone fix actually passes — rests on the gate's own run of `cd backend && pip3 install -r requirements.txt && python3 -m pytest`. If it exits non-zero, the first suspect is `test_create_receipt_returns_body_and_row_exists`, the only test whose content changed after the last failing run.
- **RCR-NFR-1 (200 ms p95 under proposed load) has no test of any shape** — settled at plan time, unchanged here. Needs a manual/out-of-suite measurement or an explicit wave-through by bohdan.
- **RCR-NFR-3 (0 files changed outside the router and tests) is verified only by inspection**, not by a command — and this stage could not run `git diff --stat`. The read evidence (router + one new test file; no other backend file appears changed) supports it but is not the diff itself.
- **sqlite-only execution.** `test_amount_boundaries_accepted` posts the Numeric(12,2) maximum and passes, if it passes, by sqlite laxity; the deployed database never sees it. Datetime handling is normalized in-test for both backends but only the sqlite path runs.
- **Baseline assumptions still stand unconfirmed** (read-one without `has_photo`, delete 200 not 204, explicit null ≡ omitted, no amount upper bound, 422 refusals) — implemented as documented in the router's own docstrings; each is one handler away from changing if bohdan decides differently.
- **Graph staleness:** the re-index (settled_question#186) never ran from a stage; the graph counts quoted in earlier documents describe pre-change code.
- **Leftover `test_receipts_crud.db` files** are pytest artifacts, not tracked work.
