# Verification report — Budgets and spend summary (budgets7, attempt 2)

## Commands run

This stage was again run without a shell: its available tools are repository reading (read_file, list_files, search_text, impact, query) only, and no tool in front of it executes anything. No command was run here, so none is reported with an exit status — including nothing that failed on the way to passing. The command the engine runs at this stage's close, unchanged from planning (settled_question#211):

```
cd backend && python3 -m pip install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test
```

The pass/fail verdict on that run belongs to the engine, not to this document. Everything below was verified by reading the working tree on branch `budgets7`.

## Results

**What this attempt re-read and confirmed (all by reading the files themselves, not prior run records):**

- `backend/app/routers/budgets.py` (147 lines, read in full): `POST /api/v1/budgets` via `set_budget` (`@router.post("", status_code=status.HTTP_201_CREATED)` at line 70, delete-then-insert so one row remains, lines 81-93 — BUD-1/BUD-2); `GET /api/v1/budgets/{period}/summary` via `get_budget_summary` (line 120-121, typed `BudgetSummaryResponse` — BUD-3). `_parse_period` (line 16) refuses non-`YYYY-MM` with a 422 whose detail names the format (lines 23-39, BUD-6) and builds midnight-UTC inclusive-exclusive bounds with December rollover (lines 40-42, BUD-4). `_validate_target` (line 46) refuses ≤0 and >2-decimal targets naming the rule (lines 52-56, BUD-7). `_get_owned_budgets` (line 59) filters `Budget.user_id == current_user.id` with deterministic `order_by(Budget.created_at.desc(), Budget.id)` (line 65, BUD-8/BUD-10). `_spent_in_period` (line 98) filters in Python, normalising aware timestamps to UTC and naive as UTC (lines 111-115). Strict `over` (`spent > target`, line 144); `duplicate_rows=len(budgets) > 1` (line 145); 404 detail `"No budget is set for this period"` (line 13, raised at line 134 — BUD-5).
- `backend/app/main.py`: the budgets import at line 76 and `app.include_router(budgets.router)` at line 83, inside `create_app()` (line 65) — BUD-11 confirmed directly, not by prior claim.
- `backend/app/schemas.py`: `BudgetCreate` (line 49) and `BudgetSummaryResponse` (lines 54-60) with `duplicate_rows: bool = False`.
- `backend/tests/test_budgets.py` (288 lines, read in full): all 20 test names in the scenario-to-test mapping (settled_question#213) are present at exactly the cited lines; the `_make_receipt` helper parses `created_at` with `datetime.fromisoformat` (line 110), and the module docstring records why (lines 10-12). The duplicate-row test seeds storage directly (lines 272-287); the BUD-9 test asserts equal `detail` bodies against the receipts endpoint in the same app (lines 260-267).
- The repository-root `.gitignore` carries `*.db` at line 10 and `.pytest_cache/` at line 11, so the `test_budgets_unit.db` side-effect file is ignored. This is the corrected citation: attempt 3's note wrongly wrote `backend/.gitignore`, which does not exist (read_file returned found: false on the earlier attempt's check; the tree listing shows only `.gitignore` at the root and `backend/.dockerignore`).
- `backend/.pytest_cache/v/cache/nodeids` was read in full this attempt (lines 4-36 are the old `tests/test_budgets.py` entries). It matches what the requirements baseline at `docs/sdlc/budgets7/baseline.md` (open question 2, line 280) and `docs/sdlc/budgets7/03-requirements/requirement#114.md` quote — the legacy-behaviour citations that earlier gates could not confirm are now confirmed against the file itself, this stage having been given read access to it.
- `backend/requirements.txt` names no lint, formatter or type-check tool (fastapi, uvicorn, sqlalchemy, psycopg2-binary, pytest, httpx, bcrypt, PyJWT, email-validator, python-multipart — nothing else). The `none` answer to the lint command question (settled_question#212) is correct for this project; the prior gate's lint-v1 finding was the person-confirmation the check itself promises, not a defect in the answer.

**Fixed vs unchanged:** no file was modified by this stage and no test was changed or skipped. Nothing was fixed here because nothing was broken in the tree; the corrections this attempt makes are documentary — every claim above now rests on a file read in this attempt rather than on a prior record (the previous gate's no-placeholders finding complained that citations rested on records it could not open; this report opens them instead of citing them).

## Acceptance coverage

Scenario-to-test mapping, re-verified by reading `backend/tests/test_budgets.py` this attempt (all tests in that one file):

| Scenario (acceptance_spec#136, `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md`) | Test |
|---|---|
| A budget is set for a period (BUD-1, BUD-11) | `test_set_budget_stores_it` (line 121) |
| Summary shows spent, remaining, not over (BUD-3) | `test_summary_shows_spent_remaining_and_not_over` (line 130); zero-spend variant `test_month_with_no_receipts_spends_zero` (line 181) |
| Summary shows over when spending exceeds target (BUD-3) | `test_over_target_month_is_shown_as_over` (line 140) |
| Setting the same period again replaces the target (BUD-2) | `test_setting_same_period_again_replaces_target` (line 191, checks row count directly) |
| Re-setting the target changes the over flag (BUD-2, BUD-3) | `test_re_setting_target_changes_over_flag` (line 205) |
| Receipts count only inside month boundaries (BUD-4 outline) | `test_month_boundary_receipts` (line 150); December rollover `test_december_period_uses_next_years_january_as_end` (line 164) |
| Summary for period with no budget says none is set (BUD-5) | `test_summary_for_period_with_no_budget_says_none_is_set` (line 215) |
| Malformed period refused with rule named (BUD-6 outline) | `test_malformed_period_refused_with_rule_named` (lines 225-230, parametrised: 2024-13, 24-01, 2024-00, monthly) |
| Invalid target refused with rule named (BUD-7 outline) | `test_invalid_target_refused_with_rule_named` (lines 234-240, parametrised) + boundary `test_target_with_exactly_two_decimals_accepted` (line 243) |
| Another user's budget answered same as no budget (BUD-8) | `test_another_users_budget_is_answered_same_as_no_budget` (line 250) |
| Unauthenticated refused like receipts (BUD-9) | `test_unauthenticated_requests_refused_like_receipts` (line 260) |
| Duplicate rows read deterministically and indicated (BUD-10) | `test_duplicate_rows_read_deterministically_and_indicated` (line 272) |

No approved scenario lacks a test. BUD-11 is additionally covered by inspection of the registration read directly this attempt (`backend/app/main.py` lines 76 and 83). Two surplus tests exist beyond the scenarios: `test_another_users_receipts_not_counted` (line 173), supporting the spent-counts-only-own-receipts clause flagged at settled_question#135(6), and the zero-spend variant already noted.

## Known gaps

- **The stage ran nothing.** The verdict on the backend suite (20 budgets tests plus the pre-existing suite) and the frontend vitest regression run is the engine's exit code on the test command at this stage's close. This report asserts only what reading showed: the code, registration, schemas and tests exist and match the accepted scenarios, and every citation in it was opened, not inherited.
- **`req#114` as a run record:** the requirement set exists in this run as the file `docs/sdlc/budgets7/03-requirements/requirement#114.md` (read in full this attempt) and as the graph record requirement#114 the acceptance spec's `[[req#114/BUD-x]]` citations point at; the prior gate could not see it. The BUD-1..BUD-11 requirement texts this report checks against were read from that file, so requirement-level claims are now cross-checked against the requirement text itself, not only settled answers and code.
- **INV-NFR-1 / INV-NFR-2** (200 ms / 500 ms p95, `docs/sdlc/budgets7/baseline.md` lines 98-116) are proposed-unconfirmed and deliberately unmeasured; no test asserts a latency figure and nothing here claims to satisfy them.
- **Unsettled by design and untested:** concurrent re-sets (BUD-2's one-row guarantee has no DB uniqueness constraint — `backend/app/models.py` budgets block, per the baseline's open question 8) and strict-vs-inclusive `over` is implemented as strict (`spent > target`, budgets.py:144) per the baseline's open question 6, recorded as an assumption. Timezone normalisation is settled in code (aware-to-UTC, budgets.py:111-115) and exercised by the `+02:00` case at test_budgets.py:160, but lives in a docstring, not a requirement.
- **Git history was never inspected** anywhere in this run, so whether the prior budgets implementation (visible only in the stale pytest cache, now read in full and confirmed) was reverted or never committed remains unknown — baseline open question 1, unresolved here.
- **Lint:** the project has no lint step (`backend/requirements.txt` declares none, and no lint configuration file appears in the backend tree listing); the `none` answer stands, awaiting the person confirmation the check prescribes.
- **Index freshness:** the re-index and `meridian sdlc verify-links` pair named at planning (settled_question#210) could not be run here (no shell); if the engine drops any artifact-to-code link for the new `budgets.py` / `test_budgets.py` paths, that is a finding, not housekeeping.
- The frontend suite runs in the chained command as a regression guard only; no frontend file was touched by this work.
