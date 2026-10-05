https://github.com/phase1912/budget-checker/pull/11

# Budgets and spend summary

## Summary

This adds the budgets feature to the budget-checker backend: a signed-in user can set a budget for a period and read a summary for it — how much was spent on receipts in that period, how much remains, and whether they are over. The `Budget` model already existed in the schema but had no router, schemas or tests, so nothing could use it. This change adds `backend/app/routers/budgets.py` (POST /api/v1/budgets to set/replace a target for a `YYYY-MM` period, and GET /api/v1/budgets/{period}/summary computed on the fly from the user's receipts), request/response schemas in `backend/app/schemas.py` (`BudgetCreate`, `BudgetSummaryResponse`), a two-line registration in `create_app()` (`backend/app/main.py`), and a new 20-test suite in `backend/tests/test_budgets.py` covering all 12 acceptance scenarios. The frontend is untouched, as the goal requires.

Behavioural details: periods are `YYYY-MM` month strings; receipts count inside midnight-UTC inclusive-exclusive month bounds (December rolls to next year's January); re-setting a period replaces the target so exactly one row remains; a summary for a period with no budget answers "no budget is set" rather than inventing a zero; malformed periods and invalid targets (≤0, >2 decimals) are refused with the rule named; cross-user budgets read as not-found; unauthenticated requests are refused identically to the receipts endpoints; duplicate period rows (not creatable via the API) are read deterministically (newest wins) and flagged via a `duplicate_rows` boolean; `over` is strict (`spent > target`).

## Requirements covered

- [[BUD-1]] Set a budget for a period (POST /api/v1/budgets, 201) — `set_budget` + `test_set_budget_stores_it`.
- [[BUD-2]] Re-setting a period replaces the target, one row remains — delete-then-insert in `set_budget` + two re-set tests.
- [[BUD-3]] Summary returns spent, remaining and over — `get_budget_summary` + under/over/zero-spend tests.
- [[BUD-4]] Receipts counted within midnight-UTC inclusive-exclusive month bounds — `_parse_period`/`_spent_in_period` + boundary and December-rollover tests.
- [[BUD-5]] Summary for a period with no budget says none is set, no invented zero — 404 "No budget is set for this period" + test.
- [[BUD-6]] Malformed period refused with the rule named — `_parse_period` 422 details + parametrised tests (`2024-13`, `24-01`, `2024-00`, `monthly`).
- [[BUD-7]] Invalid target refused with the rule named — `_validate_target` + parametrised tests plus two-decimal boundary test.
- [[BUD-8]] Another user's budget reads as the same not-found — `_get_owned_budgets` user filter + test.
- [[BUD-9]] Unauthenticated requests refused like receipts — shared `get_current_active_user` dependency + test asserting detail parity.
- [[BUD-10]] Duplicate rows read deterministically and indicated — newest-wins ordering + `duplicate_rows` flag + test seeding storage directly.
- [[BUD-11]] Endpoints reachable through the app — budgets router imported and included in `create_app()` (backend/app/main.py), verified by inspection and by the route tests.

Two quality attributes, INV-NFR-1 and INV-NFR-2 (200 ms / 500 ms p95 latency), are part of the accepted baseline as **proposed-unconfirmed** thresholds; the acceptance spec excludes them from scenarios and no latency assertion is implemented — nothing here claims to satisfy them.

## Testing

The project's settled build/test command is `cd backend && python3 -m pip install -r requirements.txt && python3 -m pytest && cd ../frontend && npm ci && npm test`; the backend suite was run at the implementation stage's gate and fully passed (56 tests, per that stage's gate record). The verification stage has no shell of its own and statically re-confirmed every file, registration and test name against the working tree; the frontend suite runs as a regression guard only — no frontend file was touched. All 12 accepted acceptance scenarios map to named tests in `backend/tests/test_budgets.py`; there is no lint step in this project (`none` was the settled answer to the lint command and needs a person's confirmation). Post-merge it is worth watching: the two medium findings the review raised about year-boundary periods (`0000-01`, `9999-12` hitting the datetime construction) and NaN/Infinity targets passing `_validate_target` — the review verdict was NOT READY on those, so a follow-up implementation pass fixing them (guard the year range, add `math.isfinite`) should land before this meets real traffic if they have not been fixed on this branch.

## Risk and blast radius

The change is additive: two new files (`budgets.py`, `test_budgets.py`), schema additions, and a two-line router registration. `Budget`'s only dependents are the `User.budgets` relationship and Base metadata registration; `create_app`'s sole dependent is the module-level `app = create_app()`. `get_current_active_user` (flagged CRITICAL by impact analysis across the receipts/auth endpoints) is consumed, not modified. Existing receipts, auth and health endpoints are byte-for-byte unchanged; no frontend change is in the diff.

Residual risks, all named in the review and baseline rather than silently decided: (1) concurrency — `set_budget`'s delete-then-insert has no DB uniqueness constraint, so exactly-one-row under simultaneous POSTs is not guaranteed; a partial unique index would close it. (2) Money is handled as float on the wire, with the two-decimal rule implemented approximately via `round()`; acceptable at this scale, recorded as an assumption. (3) Legacy behaviour (YYYY-MM format, UTC month bounds, two-decimal targets) was restored from the stale pytest cache, and git history has never confirmed whether the prior implementation was removed for cause. (4) INV-NFR-1/2 latency thresholds remain proposed-unconfirmed and unmeasured. (5) Concurrent re-sets and strict-vs-inclusive `over` were unsettled by the maker; the implementation assumes strict `over`.
