# Requirements — Budgets and spend summary

Derived from the solution concept at `docs/sdlc/budgets7/02-concept/solution_concept#89.md` and the problem brief at `docs/sdlc/budgets7/01-problem/problem_brief#74.md`. Every budgets requirement below is new behaviour — verified at `existing-behaviour` (settled_question#103) that nothing budget-related is reachable today. Where a requirement restores behaviour recorded in the stale pytest cache (`backend/.pytest_cache/v/cache/nodeids`, lines 4-28), it says so. The system name in every requirement is the budgets API (the new budgets router served by the FastAPI backend).

## BUD-1 — Set a budget for a period

### Requirement

When a signed-in user submits a period and target amount to the budgets API, the budgets API shall store that target amount for that user and period.

### Rationale

The core capability the product is named for: without a stored target there is nothing to summarise. This restores the cache-recorded `test_set_budget_stores_it` against `POST /api/v1/budgets` (nodeids line 24).

### Verification

Test: POST a budget, then read the summary for the same period and confirm the target is reflected.

### Traces to

- [[prob-74/success-metrics]] — success metric 1: a user sets a target via the API
- [[concept-89/chosen-approach]] — a budgets router with the endpoints the summary needs

## BUD-2 — Re-setting a period replaces the target

### Requirement

When a signed-in user sets a budget for a period they have already set, the budgets API shall replace the previous target so that exactly one budget row remains for that user and period.

### Rationale

Prior behaviour, evidenced by the cache's `test_setting_same_period_again_replaces_target_with_one_row` (nodeids line 25); adopting it now is a deliberate decision, since the `period` column has no uniqueness constraint (`backend/app/models.py`, `budgets` block at line 92) and the rule must be enforced in router code.

### Verification

Test: set the same period twice with different targets, confirm the summary reports the second target and only one row exists.

### Traces to

- [[concept-89/chosen-approach]] — period semantics enforced in router code, no ALTER

## BUD-3 — Summary returns spent, remaining and over

### Requirement

When a signed-in user requests the summary for a period with a budget set, the budgets API shall return, computed on the fly from that user's receipts in the period, the amount spent, the amount remaining, and whether spending is over the target.

### Rationale

Bohdan's success signal (settled_question#72): seeing spent, left and over without doing arithmetic. On-the-fly computation is the chosen direction (settled_question#93) — no stored aggregates.

### Verification

Test: seed receipts totalling a known amount against a known target, call `GET /api/v1/budgets/{period}/summary`, and check the three values, including an over-target case.

### Traces to

- [[prob-74/success-metrics]] — metric 1: a summary response returning spent, remaining and an over flag
- [[concept-89/chosen-approach]] — summary computed fresh from Receipt rows at request time

## BUD-4 — Receipts counted within month boundaries

### Requirement

When the budgets API computes spent for a period, the budgets API shall include only receipts whose timestamp falls in the period's month, from the first day of the month at midnight UTC inclusive to the first day of the next month at midnight UTC exclusive.

### Rationale

Restores the cache's `test_month_boundary_receipts` semantics (nodeids lines 18-20): midnight UTC, inclusive-exclusive. Without a stated boundary, a receipt on the 1st or at month's end is counted by nobody's rule.

### Verification

Test: seed receipts exactly on both boundaries and one inside, confirm only the inside one is counted.

### Traces to

- [[concept-89/assumptions]] — YYYY-MM periods with month-boundary receipt matching

## BUD-5 — Summary for a period with no budget

### Requirement

If a summary is requested for a period for which the user has set no budget, then the budgets API shall respond that no budget is set for that period rather than reporting a zero target.

### Rationale

Bohdan's must-have answer (settled_question#109): a period with no budget says so — an invented zero would read as "budget of 0, everything over".

### Verification

Test: request a summary for a period never set, confirm the response states none is set and does not report target 0.

### Traces to

- [[prob-74/problem]] — the user cannot currently compare receipts to anything; the empty case must not lie

## BUD-6 — Refuse a malformed period, naming the rule

### Requirement

If a budget request carries a period that is not a `YYYY-MM` month string (for example `2024-13` or `24-01`), then the budgets API shall refuse the request with an error naming the required `YYYY-MM` format.

### Rationale

Restores the cache's rule-naming refusals (nodeids lines 11-14: `2024-13`, `24-01`). Bohdan's failure-behaviour answer (settled_question#112) requires the rule to be named, since the period is a free String column and semantics live only in router code.

### Verification

Test: POST with `2024-13` and `24-01`, confirm refusal and that the message names `YYYY-MM`.

### Traces to

- [[prob-74/evidence]] — the cache-recorded prior design being deliberately restored

## BUD-7 — Refuse an invalid target, naming the rule

### Requirement

If a budget request carries a target amount that is zero, negative, or has more than two decimal places (for example `-10.00`, `0.00` or `10.999`), then the budgets API shall refuse the request with an error naming the accepted target rule.

### Rationale

Restores the cache's invalid-target refusals (nodeids lines 11-17: `10.999`, `-10.00`, `0.00`), per settled_question#112. It also bounds the Numeric-to-float rounding risk the concept names: a two-decimal target makes the `over` comparison well-defined.

### Verification

Test: POST targets `-10.00`, `0.00` and `10.999`, confirm each is refused with the rule named; POST `10.99` and confirm acceptance.

### Traces to

- [[concept-89/risks]] — Numeric/float serialization drift in the over flag

## BUD-8 — Another user's budget is not readable

### Requirement

If a signed-in user requests a budget summary for a period that only a different user has set, then the budgets API shall respond with the same not-found outcome it gives for a period with no budget — without any part of the other user's budget in the response.

### Rationale

Restores the cache's `test_another_users_budget_is_not_found`; the receipts router's per-user filtering with uniform not-found (`backend/app/routers/receipts.py:35-42`) is the established pattern the concept commits to following. The non-disclosure is folded into the single response clause to keep one `shall` and one testable outcome.

### Verification

Test: user A sets a budget; user B requests that period's summary; confirm B gets the not-found outcome, not A's numbers.

### Traces to

- [[concept-89/chosen-approach]] — all reads and writes scoped to the current user with the receipts router's uniform not-found pattern

## BUD-9 — Unauthenticated requests refused like receipts

### Requirement

If a request to a budgets endpoint carries no valid authenticated user, then the budgets API shall refuse it with the same refusal the receipts endpoints give unauthenticated requests.

### Rationale

Restores the cache's `test_budgets_endpoints_refuse_unauthenticated_like_receipts`; the budgets router uses the same `get_current_active_user` dependency (`backend/app/deps.py:52`) as receipts.

### Verification

Test: call both budgets endpoints with no token and with an invalid token, confirm the same refusal the receipts endpoints return.

### Traces to

- [[concept-89/chosen-approach]] — the receipts router's unauthenticated refusal carried over

## BUD-10 — Duplicate period rows read deterministically and indicated

### Requirement

If more than one budget row exists for the same user and period, then the budgets API shall return the same summary for every read of that period, indicating the duplication in the response.

### Rationale

Restores the cache's `test_duplicate_rows_read_deterministically_and_indicated` (nodeids line 10). The `period` column has no uniqueness constraint (checked at `backend/app/models.py`, `budgets` block, line 92) and the concept excludes adding one, so the summary must tolerate what the storage permits; the deterministic-read and the indication are one observable outcome in a single clause.

### Verification

Test: insert two budget rows for one user and period directly, request the summary repeatedly, confirm a stable response that flags the duplication.

### Traces to

- [[concept-89/assumptions]] — duplicate-period rows can occur and the summary must read them deterministically

## BUD-11 — Endpoints reachable through the application

### Requirement

The backend application shall expose the budgets endpoints under the versioned API prefix alongside the existing routers.

### Rationale

The Budget model exists but nothing exposes it (`create_app()` at `backend/app/main.py:65` includes no budgets router); registration is the one-line change that makes BUD-1 through BUD-10 reachable at all.

### Verification

Inspection of `create_app()` plus a demonstration that `GET /api/v1/budgets/{period}/summary` routes rather than 404s on an unknown path.

### Traces to

- [[prob-74/problem]] — no budgets router exists and no budget endpoint is reachable
- [[concept-89/chosen-approach]] — an additive budgets router included in `create_app()`
