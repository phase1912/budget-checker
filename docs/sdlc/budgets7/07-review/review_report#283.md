# Review — Budgets and spend summary (branch `budgets7`)

## Scope reviewed

Read in full, from the working tree:

- `backend/app/routers/budgets.py` (147 lines) — both endpoints and all four helpers
- `backend/app/main.py` (91 lines) — `create_app`, middleware and error handlers, budgets registration at lines 76 and 83
- `backend/app/schemas.py` (61 lines) — `BudgetCreate` (line 49), `BudgetSummaryResponse` (lines 54-60)
- `backend/app/models.py` (101 lines) — `Budget` (91-100), `Receipt` (55-72), `User.budgets` (34-36)
- `backend/app/routers/receipts.py` (131 lines) — the pattern the budgets router claims to follow (not-found behaviour, auth dependency)
- `backend/tests/test_budgets.py` (288 lines) — all 20 tests
- `docs/sdlc/budgets7/` listing — all ten documents plus `baseline.md` present as files

Impact re-run this stage: `create_app` upstream — affected 1, direct 1, risk LOW (the module-level `app = create_app()` at `main.py:90`), with a freshness note on `main.py`; `Budget` upstream — affected 3, direct 3, risk LOW, freshness note on `models.py`; `set_budget` — not in the index (`found: false`), confirming the index predates the new router and that the new symbols have zero pre-existing dependents. No shell was available to this stage; the suite verdict remains the engine's run of the settled test command.

## Findings

1. **Medium — `backend/app/routers/budgets.py:40` (code_change artifact: `docs/sdlc/budgets7/05-implementation/code_change#236.md`) — a shape-valid but impossible period raises an uncaught `ValueError` → HTTP 500, violating BUD-6.** `_parse_period` validates the `YYYY-MM` shape and `1 <= month <= 12`, then calls `datetime(year, month, 1, tzinfo=timezone.utc)` (line 40) with no guard on `year`. A period of `"0000-01"` or `"0001-01"`... wait, year 1 is fine; year 0 is not: `datetime(0, 1, 1)` raises `ValueError: year 0 is out of range`, which is not caught — the two `except ValueError` blocks at lines 27-34 wrap only the `int()` calls. The request escapes every handler in `register_error_handling` (`backend/app/main.py:47-62` handles only `RequestValidationError` and `SQLAlchemyError`) and surfaces as an unhandled server error, not the 422-with-rule-named that BUD-6 requires. Same hole at line 42 for `"9999-12"`: `datetime(10000, 1, 1)` raises `ValueError: year 10000 is out of range` — and December is exactly the month the rollover path runs in. The test suite covers month `00` and `13` but never year `0000` or `9999-12`, so this ships green. If it ships: a user (or anyone probing) sending `POST /api/v1/budgets` with `{"period": "0000-01", ...}` or `GET /api/v1/budgets/9999-12/summary` gets a 500 and a stack trace in the log for input BUD-6 says must be refused with the rule named.

2. **Medium — `backend/app/schemas.py:51` and `backend/app/routers/budgets.py:46-52` (code_change#236) — NaN and Infinity pass `_validate_target` and are stored.** `BudgetCreate.target_amount` is a plain `float`, and Python's JSON parser accepts `NaN` and `Infinity` literals. For NaN: `nan <= 0` is False and `abs(nan - nan) > 1e-9` is False (NaN comparisons), so the NaN target is stored. For `Infinity`: `inf <= 0` is False and `abs(inf - inf)` is NaN, so `> 1e-9` is False, and the Infinity target is stored. A budget with target NaN then poisons every summary for that period (spent/remaining/over all computed against it). Nothing in `math.isfinite` terms guards the value, and no test exercises a non-finite target. If it ships: a single malformed client request permanently breaks that period's summary until the row is manually removed.

3. **Low — `backend/app/routers/budgets.py:51-52` — the two-decimal check runs `round()` on a float, so acceptance depends on binary representation, not on the decimal the user sent.** `10.005` arrives as the double 10.004999...89, `round(10.005, 2)` is `10.0`, and the diff of 0.005 is refused — correct by luck; a value like `8.215` can behave the other way depending on the double. The rule BUD-7 states is about decimal places; the check is about floats. Same root as finding 2 and the long-known float-for-money choice in `BudgetSummaryResponse` (schemas.py:54-60). Acceptable at this scale and named as an assumption in the plan, but it is a rule implemented approximately.

4. **Low — `backend/app/routers/budgets.py:81-94` — delete-then-insert with no uniqueness constraint means BUD-2's "exactly one row remains" is not guaranteed under concurrent POSTs.** Named as an open question in `docs/sdlc/budgets7/baseline.md` and settled_question#282; the code adds nothing (no partial unique index, no retry). For a single-user SQLite product this is tolerable, but it is a real ordering hazard, not a closed one.

5. **Informational — test isolation: `backend/tests/test_budgets.py:29-31` writes `test_budgets_unit.db` into the CWD at import time.** Ignored by the root `.gitignore` (`*.db`), but two parallel test runs share the file and would race. Not a product defect.

## Blast radius

Every direct dependent outside the diff, from impact this stage and reading the dependents:

- **`create_app` → module-level `app = create_app()`** (`main.py:90`) — opened `main.py` directly: the budgets import (line 76) and `include_router(budgets.router)` (line 83) sit inside `create_app()` before `Base.metadata.create_all` (line 85). Inspected and sound; no signature or behavioural change reaches the dependent.
- **`Budget` → `User.budgets` relationship, `Budget.user` back-reference, `Base.metadata` registration** (`models.py:34-36, 91-100`) — the model is only read by the new router, never modified; all three dependents hold. Inspected and sound.
- **`get_current_active_user`** (`deps.py`) — flagged CRITICAL in earlier impact runs across get_receipt_photo, role_checker, upload_receipt_photo, get_me, list_receipts. Not modified by this change; the budgets router consumes it as a plain dependency. Inspected and sound — the CRITICAL flag is a leave-it-alone warning that was honoured.
- **`register_error_handling`** — consumed unchanged by the test harness (`test_budgets.py:55`). Inspected and sound, though it is also why findings 1 and 2 surface as 500s rather than named 422s (it handles only `RequestValidationError` and `SQLAlchemyError`).
- **New symbols** (`set_budget`, `get_budget_summary`, `BudgetCreate`, `BudgetSummaryResponse`, the four helpers) — zero pre-existing dependents; `set_budget` is not yet in the index at all (`found: false`), which is index staleness, not a broken dependency.
- Receipts, auth, health endpoints and the frontend: untouched; the receipts router is only read for pattern parity. No dependent there.

## Residual risk

- **The suite has not been observed passing by any stage that could see this tree's final state.** The last claimed run ("56 passed", per the implementation gate's own record) predates no code change — attempts 2-4 modified nothing — so the risk is low, but no review-stage command ran either; the engine's exit code on the settled test command is still the only executed verdict.
- **Previously working behaviour that could regress:** none in the existing endpoints — nothing outside the two new files and the two registration lines changed, and the receipts/auth/health routers read this stage are byte-for-byte in their documented shape.
- **Still unresolved after looking:** (a) whether the prior budgets implementation was deliberately removed and why — git history has never been inspected anywhere in this run, so restoring the cache-recorded behaviour (YYYY-MM, midnight-UTC inclusive-exclusive bounds, two-decimal targets) remains a bet that the removal wasn't for cause; (b) the strict-vs-inclusive `over` comparison is settled only by the implementer's assumption (`spent > target`, budgets.py:144), never by the maker; (c) concurrency on re-sets (finding 4); (d) the INV-NFR-1/2 latency thresholds remain proposed-unconfirmed and unmeasured, as the baseline itself records.

## Verdict

**NOT READY.** Findings 1 and 2 are concrete, reachable defects in new code against requirements the baseline accepted: BUD-6 says a malformed period is refused with the rule named, and `"0000-01"` or `"9999-12"` instead produces an unhandled 500 (`budgets.py:40-42`); BUD-7's rule-named refusal for an invalid target lets NaN and Infinity through and stores them (`budgets.py:52`, `schemas.py:51`), after which that period's summary is poisoned. Neither is caught by the current 20 tests, so the suite passing proves nothing about them. Both are small, localised fixes (guard the year at the boundary construction and add `math.isfinite` to `_validate_target`, with a test each), but code is frozen at this stage — this goes back to implementation with findings 1 and 2 named, and findings 3-4 are for the maker to accept or reject as recorded assumptions.
