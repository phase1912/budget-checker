# Code change — Budgets and spend summary (attempt 4)

## Summary

The budgets feature is complete and unchanged in code: `POST /api/v1/budgets` stores a target for a `YYYY-MM` period (re-setting replaces, so exactly one row remains), and `GET /api/v1/budgets/{period}/summary` computes on the fly the spend on that user's receipts inside the calendar month, the remainder, and a strict `over` flag. This attempt re-verified every file against the working tree — the router (147 lines), the schemas, the `create_app()` registration, the root `.gitignore`, and the full 288-line test file were all re-read this attempt — and writes the note with only path-and-symbol citations that a reviewer can open. No file was modified in this attempt; the tree is the one the verification stage examined (verification_report#216, which confirmed the same files and corrected the one wrong path citation in attempt 3's note).

## Requirements implemented

- [[BUD-1]] — `set_budget` (backend/app/routers/budgets.py:70, `@router.post("", status_code=status.HTTP_201_CREATED)`) stores the target for the signed-in user's period and returns 201.
- [[BUD-2]] — `set_budget` deletes all existing rows for that user+period before inserting (budgets.py:81-93), so exactly one row remains; verified by `test_setting_same_period_again_replaces_target` (backend/tests/test_budgets.py:191), which checks the row count directly.
- [[BUD-3]] — `get_budget_summary` (budgets.py:121) returns period, target, spent, remaining and `over` via `BudgetSummaryResponse` (backend/app/schemas.py:54-60).
- [[BUD-4]] — `_parse_period` (budgets.py:16) builds midnight-UTC inclusive/exclusive month bounds with December rollover (budgets.py:41); `_spent_in_period` (budgets.py:98) sums only receipts inside `[start, end)`, converting aware timestamps to UTC and treating naive ones as UTC (budgets.py:111-115); exercised by `test_month_boundary_receipts` (test_budgets.py:150) and `test_december_period_uses_next_years_january_as_end` (test_budgets.py:164).
- [[BUD-5]] — `get_budget_summary` raises 404 with detail `"No budget is set for this period"` (`_NOT_FOUND_DETAIL`, budgets.py:13; raised at budgets.py:134); no zero target invented; verified by `test_summary_for_period_with_no_budget_says_none_is_set` (test_budgets.py:215).
- [[BUD-6]] — `_parse_period` refuses non-`YYYY-MM` periods with a 422 whose detail names the format (budgets.py:23-39); verified by the parametrised `test_malformed_period_refused_with_rule_named` (test_budgets.py:226, cases `2024-13`, `24-01`, `2024-00`, `monthly`).
- [[BUD-7]] — `_validate_target` (budgets.py:46) refuses zero, negative and >2-decimal targets with the rule named in the detail; verified by `test_invalid_target_refused_with_rule_named` (test_budgets.py:235) and the boundary case `test_target_with_exactly_two_decimals_accepted` (test_budgets.py:243).
- [[BUD-8]] — `_get_owned_budgets` (budgets.py:59) filters on `Budget.user_id == current_user.id`; another user's budget yields the same 404 as BUD-5; verified by `test_another_users_budget_is_answered_same_as_no_budget` (test_budgets.py:250).
- [[BUD-9]] — both endpoints depend on `get_current_active_user`, the receipts endpoints' dependency, so refusals are identical; verified by `test_unauthenticated_requests_refused_like_receipts`, which asserts equal `detail` bodies against the receipts endpoint in the same app (test_budgets.py:260-267).
- [[BUD-10]] — the summary read is deterministic (`order_by(Budget.created_at.desc(), Budget.id)`, budgets.py:65 — newest wins) and sets `duplicate_rows=len(budgets) > 1` (budgets.py:145); verified by `test_duplicate_rows_read_deterministically_and_indicated` (test_budgets.py:272), which seeds rows directly since the API cannot create the precondition.
- [[BUD-11]] — `create_app` imports budgets (`from .routers import auth, budgets, health, receipts`, backend/app/main.py:76) and includes the router (`app.include_router(budgets.router)`, main.py:83); all routes served under `/api/v1`.
- [[INV-NFR-1]] / [[INV-NFR-2]] — proposed-unconfirmed latency thresholds (baseline; settled_question#149). Excluded from scenarios by the acceptance spec, so no latency assertion is implemented, as the plan states.

## Symbols changed

Nothing was edited in this attempt. The complete symbol set, re-read and confirmed against the working tree this attempt:

- `BudgetCreate` (added, attempt 1) — backend/app/schemas.py:49
- `BudgetSummaryResponse` (added, attempt 1) — backend/app/schemas.py:54
- `_parse_period` (added, attempt 1) — backend/app/routers/budgets.py:16
- `_validate_target` (added, attempt 1) — backend/app/routers/budgets.py:46
- `_get_owned_budgets` (added, attempt 1) — backend/app/routers/budgets.py:59
- `set_budget` (added, attempt 1) — backend/app/routers/budgets.py:71
- `_spent_in_period` (added, attempt 1) — backend/app/routers/budgets.py:98
- `get_budget_summary` (added, attempt 1) — backend/app/routers/budgets.py:121
- `create_app` (modified, attempt 1: import and include_router only) — backend/app/main.py:65; changed lines at 76 and 83
- test module `backend/tests/test_budgets.py` (added, attempt 1; `_make_receipt` fixed in attempt 2 at test_budgets.py:104-116 to pass `datetime.fromisoformat(created_at)` rather than raw ISO strings, the column being `DateTime(timezone=True)`; the module docstring records this at test_budgets.py:10-12)

Deliberately untouched, per the plan (settled_question#173): the `Budget`/`Receipt`/`User` models, `get_current_active_user` (impact() upstream flagged it CRITICAL across get_receipt_photo, role_checker, upload_receipt_photo, get_me, list_receipts — left alone), the receipts router, and the frontend. impact() re-run this attempt: `create_app` — affected 1, direct 1, risk LOW (the module-level `app = create_app()`, main.py:90), freshness note on main.py; `Budget` — affected 3, direct 3, risk LOW, freshness note on models.py. Both notes say only that those files changed after the index was built; neither contradicts the picture, and the files were read directly.

## Design notes

Unchanged from attempts 1–3, recorded here so the diff is readable without them:

- **Rule-naming validation in the endpoint, not the schema.** The app-wide RequestValidationError handler returns a generic 422 that names no rule, so BUD-6/BUD-7's "names the rule" clause lives in the `_parse_period`/`_validate_target` HTTPException details.
- **Strict `over`** (`spent > target`, budgets.py:144) — the plain reading, recorded as an assumption settling the baseline's open question 6.
- **BUD-10 shape** — deterministic newest-wins read plus a `duplicate_rows` boolean in `BudgetSummaryResponse`; the plan's stated assumption (settled_question#176).
- **Python-side spend filtering** rather than a SQL date comparison — SQLite stores `DateTime(timezone=True)` as strings, so an in-SQL bound comparison is unreliable at the exclusive boundary; one user's receipts are few (concept stage).
- **Typed response schema for the summary** while the receipts router returns raw dicts — the duplication flag needs a structured payload.
- **No production change in attempts 2–4.** Attempt 2's defect was in the test helper only (the `_make_receipt` datetime fix); attempt 3 found the `test_budgets_unit.db` side-effect file already excluded by the repository-root `.gitignore` (re-read this attempt: `*.db` at .gitignore:10, `.pytest_cache/` at .gitignore:11 — the tracked file is at the repository root, not `backend/.gitignore`, which does not exist; attempt 3's Risks section wrongly wrote that path and verification_report#216 corrected it, and this note cites the right one).

## Tests

backend/tests/test_budgets.py — 20 tests covering the 12 acceptance scenarios in `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md`, all re-read this attempt at the exact lines cited above. The scenario-to-test mapping is recorded in full in settled_question#213 and confirmed by the verification stage (verification_report#216); every mapped name was found present. Per this stage's rules nothing was run here — no shell — so the settled build command (`cd backend && python3 -m pip install -r requirements.txt && python3 -m pytest`, settled_question#172) remains the verdict at verification, which is the stage that follows this one.

## Risks

- **Never run by this stage.** No shell here; passing counts quoted in earlier documents came from earlier gates' build runs, and this note claims none as its own result. The verification stage's exit code on the test command is the real verdict, and it runs against the identical tree.
- **Restored legacy behaviour never re-affirmed by a person:** the `YYYY-MM` period format, midnight-UTC inclusive-exclusive boundaries, and the two-decimal target rule all come from the stale pytest cache (`backend/.pytest_cache/v/cache/nodeids`), adopted piecewise in the requirements; recorded as open questions in the requirements baseline at `docs/sdlc/budgets7/05-baseline/`, unresolved.
- **Assumptions settling unsettled questions:** strict `over`, the `duplicate_rows` boolean shape with newest-wins read, naive timestamps treated as UTC, and unguarded concurrent re-sets (BUD-2's one-row guarantee has no concurrency rule and no DB uniqueness constraint). Each is named in Design notes, not silently decided.
- **INV-NFR-1/2** are proposed-unconfirmed and unmeasured; nothing here claims to satisfy them.
- **Index freshness:** both impact() calls this attempt carried freshness notes on main.py and models.py. Mitigated by reading both files directly this attempt; nothing in them differs from what the note describes.

## On the prior attempts' gate shortfalls

- **`[[req#114]]` unresolvable** (verification finding): the id cited by the acceptance spec's traceability is a label the run cannot open. This note cites the requirement set by content (BUD-1..BUD-11 as quoted in the requirements baseline at `docs/sdlc/budgets7/05-baseline/`) and by file paths and line numbers for everything on disk — every citation above is a file a reviewer can open.
- **`backend/.gitignore` cited but nonexistent** (verification finding, corrected by verification_report#216): this note cites the repository-root `.gitignore`, read this attempt, with the `*.db` and `.pytest_cache/` lines quoted above.
- **`gate_finding#185` cited as a record but not openable**: this note no longer rests any claim on it; where a passing count matters, the note says the verdict belongs to the verification stage's own run.
- **Evidence-supply gaps** (pytest cache, problem/concept brief bodies): template `reads` gaps the stage cannot fix from here — every prior finding itself calls them "a gap in the template rather than in the work". The note keeps all legacy-behaviour references flagged as restored-from-cache with the cache's location named, so a reader with the file can confirm them.
- **Confidence below floor needing a person** — a person-gate matter, not answerable in code; addressed only by keeping every claim re-verifiable against the working tree, as done above.
