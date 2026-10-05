# Code change — Budgets and spend summary (attempt 3)

## Summary

The budgets feature stands as built across attempts 1–2 and is unchanged in code this attempt: `POST /api/v1/budgets` stores a target for a `YYYY-MM` period (re-setting replaces, so exactly one row remains), and `GET /api/v1/budgets/{period}/summary` computes on the fly the spend on that user's receipts inside the calendar month, the remainder, and a strict `over` flag. This attempt re-verified every file and claim against the working tree and rewrites the note so that nothing it cites is a record the run cannot show. The attempt-2 gate's own run reported the suite fully passing (gate_finding#185 records "the current gate's 56 passed"), and its shortfalls were documentation-confidence items — an unresolvable `[[req#114]]` id and review materials it was not supplied — not code defects. No file was modified in this attempt.

## Requirements implemented

- [[BUD-1]] — `set_budget` (backend/app/routers/budgets.py, `@router.post("", status_code=status.HTTP_201_CREATED)` at line 70) stores the target for the signed-in user's period and returns 201.
- [[BUD-2]] — `set_budget` deletes all existing rows for that user+period before inserting (budgets.py:81-93), so exactly one row remains; verified by `test_setting_same_period_again_replaces_target` (backend/tests/test_budgets.py:191).
- [[BUD-3]] — `get_budget_summary` (budgets.py:121) returns period, target, spent, remaining and `over` via `BudgetSummaryResponse` (backend/app/schemas.py:54-60).
- [[BUD-4]] — `_parse_period` (budgets.py:16) builds midnight-UTC inclusive/exclusive month bounds with December rollover (budgets.py:41); `_spent_in_period` (budgets.py:98) sums only receipts inside `[start, end)`, normalising aware timestamps to UTC and naive ones as UTC (budgets.py:111-115).
- [[BUD-5]] — `get_budget_summary` raises 404 with detail `"No budget is set for this period"` (budgets.py:13, 134); no zero target invented; verified by `test_summary_for_period_with_no_budget_says_none_is_set` (test_budgets.py:215).
- [[BUD-6]] — `_parse_period` refuses non-`YYYY-MM` periods with a 422 whose detail names the format (budgets.py:23-39); verified by the parametrised `test_malformed_period_refused_with_rule_named` (test_budgets.py:225).
- [[BUD-7]] — `_validate_target` (budgets.py:46) refuses zero, negative and >2-decimal targets with the rule named in the detail; verified by `test_invalid_target_refused_with_rule_named` and `test_target_with_exactly_two_decimals_accepted` (test_budgets.py:234-246).
- [[BUD-8]] — `_get_owned_budgets` (budgets.py:59) filters on `Budget.user_id == current_user.id`; another user's budget yields the same 404 as BUD-5; verified by `test_another_users_budget_is_answered_same_as_no_budget` (test_budgets.py:250).
- [[BUD-9]] — both endpoints depend on `get_current_active_user`, the receipts endpoints' dependency, so refusals are identical; verified by `test_unauthenticated_requests_refused_like_receipts` which asserts equal `detail` bodies against the receipts endpoint (test_budgets.py:260-267).
- [[BUD-10]] — the summary read is deterministic (`order_by(Budget.created_at.desc(), Budget.id)`, budgets.py:65 — newest wins) and sets `duplicate_rows=len(budgets) > 1` (budgets.py:145); verified by `test_duplicate_rows_read_deterministically_and_indicated` (test_budgets.py:272), which seeds rows directly since the API cannot create the precondition.
- [[BUD-11]] — `create_app` imports budgets (backend/app/main.py:76) and includes the router (main.py:83); all routes served under `/api/v1`.
- [[INV-NFR-1]] / [[INV-NFR-2]] — proposed-unconfirmed latency thresholds (settled_question#110/#149); excluded from scenarios by the acceptance spec, so no latency assertion is implemented, as the plan states.

## Symbols changed

Nothing was edited in this attempt. The complete symbol set, re-read and confirmed line by line in the working tree this attempt:

- `BudgetCreate` (added, attempt 1) — backend/app/schemas.py:49
- `BudgetSummaryResponse` (added, attempt 1) — backend/app/schemas.py:54
- `_parse_period` (added, attempt 1) — backend/app/routers/budgets.py:16
- `_validate_target` (added, attempt 1) — backend/app/routers/budgets.py:46
- `_get_owned_budgets` (added, attempt 1) — backend/app/routers/budgets.py:59
- `set_budget` (added, attempt 1) — backend/app/routers/budgets.py:71
- `_spent_in_period` (added, attempt 1) — backend/app/routers/budgets.py:98
- `get_budget_summary` (added, attempt 1) — backend/app/routers/budgets.py:121
- `create_app` (modified, attempt 1: import and include_router only) — backend/app/main.py:65; changed lines at 76 and 83
- test harness module `backend/tests/test_budgets.py` (added, attempt 1; `_make_receipt` fixed in attempt 2 at test_budgets.py:104-116 to pass `datetime.fromisoformat(created_at)` rather than raw ISO strings, the column being `DateTime(timezone=True)`); module docstring records this (test_budgets.py:10-12) and the `datetime` import sits at test_budgets.py:15

Deliberately untouched across all attempts, as the plan records: the `Budget`/`Receipt`/`User` models, `get_current_active_user` (impact() upstream flagged it CRITICAL across get_receipt_photo, role_checker, upload_receipt_photo, get_me, list_receipts — left alone), the receipts router, and the frontend. impact() upstream on `create_app` re-run this attempt: affected 1, direct 1, risk LOW (the module-level `app = create_app()` at main.py:90), with a freshness note on main.py only.

## Design notes

Unchanged from attempts 1–2, recorded here so the diff is readable without them:

- **Rule-naming validation in the endpoint, not the schema.** The app-wide RequestValidationError handler returns a generic 422 that names no rule, so BUD-6/BUD-7's "names the rule" clause lives in `_parse_period`/`_validate_target` HTTPException details.
- **Strict `over`** (`spent > target`, budgets.py:144) — the plain reading, recorded as an assumption settling baseline open question 6.
- **BUD-10 shape** — deterministic newest-wins read plus a `duplicate_rows` boolean; the plan's stated assumption.
- **Python-side spend filtering** rather than a SQL date comparison — SQLite stores `DateTime(timezone=True)` as strings, so an in-SQL bound comparison is unreliable at the exclusive boundary; one user's receipts are few.
- **Typed response schema for the summary** while the receipts router uses raw dicts — the duplication flag needs a structured payload.
- **No production change in attempt 2 or 3.** The attempt-2 defect (six `StatementError` failures from seeding `created_at` as a raw string) was in the test helper only; the fix parses at `_make_receipt`. This attempt's finding likewise required no code: the `test_budgets_unit.db` side-effect file flagged as a risk in attempt 2's note is in fact already excluded by `.gitignore` (`*.db` at .gitignore:10, `.pytest_cache/` at line 11) — that risk line was stale and is corrected below.

## Tests

backend/tests/test_budgets.py — 20 tests covering the 12 acceptance scenarios in `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md`, unchanged in coverage across all attempts. The attempt-2 gate's own build run, as recorded in gate_finding#185, passed all 56 tests; the six attempt-1 failures were fixed by the `_make_receipt` datetime fix and never recurred. Per this stage's rules nothing was run here — no shell — so the settled build command (`cd backend && python3 -m pip install -r requirements.txt && python3 -m pytest`, settled_question#172) remains the verdict at verification.

## Risks

- **Never run by this stage.** No shell here; the passing count is the attempt-2 gate's run, not this attempt's. The verification stage's exit code is the real verdict, and it runs against the identical tree.
- **Restored legacy behaviour never re-affirmed by a person:** the `YYYY-MM` period format, midnight-UTC inclusive-exclusive boundaries, and the two-decimal target rule all come from the stale pytest cache (`backend/.pytest_cache/v/cache/nodeids`), adopted piecewise in the requirements — recorded as open questions in the requirements baseline (`docs/sdlc/budgets7/05-baseline/`), unresolved.
- **Assumptions settling unsettled questions:** strict `over`, the `duplicate_rows` boolean shape with newest-wins read, naive timestamps treated as UTC, unguarded concurrent re-sets (BUD-2's one-row guarantee has no concurrency rule and no DB uniqueness constraint). Each is named in Design notes, not silently decided.
- **INV-NFR-1/2** are proposed-unconfirmed and unmeasured; nothing here claims to satisfy them.
- **Test-harness discipline:** `_make_receipt` assumes ISO-with-offset strings; all call sites use the acceptance scenarios' literal stamps, checked by eye against test_budgets.py:133-208.
- Corrected from attempt 2's note: the sqlite side-effect file `test_budgets_unit.db` is already ignored by the repository's tracked `.gitignore` (`*.db`, line 10) and needs no ignore entry added.

## On the attempt-2 gate shortfalls

- **`[[req#114]]` unresolvable** — the id cited by the acceptance spec's traceability is a label the run cannot open. This note cites the requirement set by its content (BUD-1..BUD-11 as quoted in the requirements baseline at `docs/sdlc/budgets7/05-baseline/`, which does exist in the run's records) and by file paths for everything on disk; it cites no id the run cannot resolve.
- **Evidence-supply gaps** (the pytest cache and the problem/concept brief bodies not supplied to the reviewer) — these are template `reads` gaps the stage cannot fix from here, as both prior gate findings themselves say ("a gap in the template rather than in the work"). Nothing in the code answers them; the note simply avoids resting any claim on the cache's unshown content — the legacy-behaviour references above are flagged as restored-from-cache, with the cache's own location named so a reader with the file can confirm it.
- **Confidence below floor needing a person** — a person-gate matter, not answerable in code; addressed only by keeping every claim re-verifiable against the working tree, as done above.
