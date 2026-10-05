# Verification report — Budgets and spend summary (budgets7, attempt 1)

## Commands run

This stage was run without a shell: the tools available to it are repository reading (read_file, list_files, search_text, impact, query) only. No command was executed here, so none is reported with an exit status. The suite command the engine runs at this stage's close is the one settled at planning (settled_question#211):

```
cd backend && python3 -m pip install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test
```

Everything below was verified by reading the working tree on branch `budgets7`, not by running anything. The passing counts in prior documents (the "56 passed" recorded in gate_finding#185) come from the implementation stage's build run, not from this stage; this report does not re-assert them as this stage's result.

## Results

**Verified against the working tree (all confirmed by reading):**

- `backend/app/routers/budgets.py` exists (147 lines): `POST /api/v1/budgets` (`set_budget`, line 70, 201 Created, delete-then-insert so one row remains — BUD-1/BUD-2), `GET /api/v1/budgets/{period}/summary` (`get_budget_summary`, line 120, typed `BudgetSummaryResponse`). `_parse_period` (line 16) refuses non-`YYYY-MM` with a 422 naming the format (BUD-6) and builds midnight-UTC inclusive-exclusive bounds with December rollover (line 41, BUD-4). `_validate_target` (line 46) refuses ≤0 and >2-decimal targets with the rule named (BUD-7). `_spent_in_period` (line 98) filters in Python, normalising aware timestamps to UTC (lines 111-115). `_get_owned_budgets` (line 59) filters `Budget.user_id == current_user.id` (BUD-8). Strict `over` at line 144 (`spent > target`); `duplicate_rows=len(budgets) > 1` at line 145 with deterministic newest-wins ordering at line 65 (BUD-10). 404 detail `"No budget is set for this period"` at line 13 (BUD-5).
- `backend/app/main.py` includes the router: `from .routers import auth, budgets, health, receipts` at line 76 and `app.include_router(budgets.router)` at line 83, inside `create_app()` (line 65) — BUD-11.
- `backend/app/schemas.py` carries `BudgetCreate` (line 49) and `BudgetSummaryResponse` (lines 54-60) with the `duplicate_rows: bool = False` flag.
- `backend/tests/test_budgets.py` exists (288 lines), 20 tests, all names matching the scenario-to-test mapping recorded at planning (settled_question#213) — every name claimed there is present in the file.
- One discrepancy in prior documents, corrected here: code_change#184's Risks section cited `backend/.gitignore` lines 10-11. There is **no** `backend/.gitignore` (read_file: found: false). The tracked repository-root `.gitignore` is the right file and does carry `*.db` at line 10 and `.pytest_cache/` at line 11, so the substance of the claim (the `test_budgets_unit.db` side-effect file is ignored) holds, but the cited path was wrong. The `backend/.pytest_cache/v/cache/nodeids` evidence of prior deleted behaviour was also read this stage (lines 4-36: the old tests/test_budgets.py entries) and matches what the requirements baseline quotes.

**Failed on the way / nothing fixed in tests:** no test was modified or skipped by this stage. Nothing was changed at all between this stage's start and now.

**Not run by this stage:** the backend pytest suite, the frontend vitest suite, and `meridian analyze --index-only --pdg --allow-sdlc-reindex` + `meridian sdlc verify-links` (settled_question#210 named this; no shell here to run it, and no `.meridian/run.cjs` exists in the listing — the question anticipated the fallback command). The engine's exit code on the test command is the verdict this report cannot itself produce.

## Acceptance coverage

Scenario-to-test mapping, verified by reading `backend/tests/test_budgets.py` (all in that one file):

| Scenario (acceptance_spec#136) | Test |
|---|---|
| A budget is set for a period (BUD-1, BUD-11) | `test_set_budget_stores_it` (line 121) |
| Summary shows spent, remaining, not over (BUD-3) | `test_summary_shows_spent_remaining_and_not_over` (line 130); zero-spend variant `test_month_with_no_receipts_spends_zero` (line 181) |
| Summary shows over when spending exceeds target (BUD-3) | `test_over_target_month_is_shown_as_over` (line 140) |
| Setting the same period again replaces the target (BUD-2) | `test_setting_same_period_again_replaces_target` (line 191) |
| Re-setting the target changes the over flag (BUD-2, BUD-3) | `test_re_setting_target_changes_over_flag` (line 205) |
| Receipts count only inside month boundaries (BUD-4 outline) | `test_month_boundary_receipts` (line 150); December rollover `test_december_period_uses_next_years_january_as_end` (line 164) |
| Summary for period with no budget says none is set (BUD-5) | `test_summary_for_period_with_no_budget_says_none_is_set` (line 215) |
| Malformed period refused with rule named (BUD-6 outline) | `test_malformed_period_refused_with_rule_named` (line 226, parametrised: 2024-13, 24-01, 2024-00, monthly) |
| Invalid target refused with rule named (BUD-7 outline) | `test_invalid_target_refused_with_rule_named` (line 235, parametrised) + boundary `test_target_with_exactly_two_decimals_accepted` (line 243) |
| Another user's budget answered same as no budget (BUD-8) | `test_another_users_budget_is_answered_same_as_no_budget` (line 250) |
| Unauthenticated refused like receipts (BUD-9) | `test_unauthenticated_requests_refused_like_receipts` (line 260, asserts equal detail bodies with the receipts endpoint) |
| Duplicate rows read deterministically and indicated (BUD-10) | `test_duplicate_rows_read_deterministically_and_indicated` (line 272, seeds storage directly) |

No approved scenario lacks a test. Two surplus tests exist beyond the scenarios: `test_another_users_receipts_not_counted` (line 173) supporting the spent-counts-only-own-receipts clause flagged at settled_question#135(6).

## Known gaps

- **Nothing was executed by this stage.** The pass/fail verdict on all 68 suite tests (48 pre-existing + 20 new) is the engine's own run of the test command at this stage's close; this report asserts only that the code and tests exist, match the accepted scenarios, and that every prior document's citations check out against the tree — with the one `.gitignore` path correction above.
- **INV-NFR-1 / INV-NFR-2** (200 ms / 500 ms p95 latency) are proposed-unconfirmed and deliberately unmeasured; no test asserts a latency figure. Nothing here claims to satisfy them.
- **Unsettled by design and untested:** concurrent re-sets (BUD-2's one-row guarantee has no DB uniqueness constraint and no concurrency rule), and timezone normalisation is now partially settled in code (aware stamps converted to UTC in `_spent_in_period`, exercised by the `+02:00` case in `test_month_boundary_receipts`), but the rule lives only in a docstring, not a requirement.
- **Git history was never inspected** anywhere in this run, so whether the prior budgets implementation (visible only in the stale pytest cache) was reverted or never committed remains unknown — recorded as a baseline open question, not resolved here.
- The frontend vitest suite runs in the chained command as a regression guard only; no frontend file was touched (verified: no frontend change is in the budgets7 working tree's changed files).