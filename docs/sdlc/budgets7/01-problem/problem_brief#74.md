# Problem brief — Budgets and spend summary

## Problem

budget-checker cannot check a budget. The `Budget` data model has existed since the schema was written (`class Budget(Base)` at `backend/app/models.py:91`, with the `User.budgets` relationship at `backend/app/models.py:34-36`), and nothing reads or writes it: there is no budgets router in `backend/app/routers/`, no budget schemas in `backend/app/schemas.py`, and `create_app()` at `backend/app/main.py:65` includes only the health, auth and receipts routers (`app.include_router(...)` calls at `backend/app/main.py:80-82`). The person using the product can record receipts but has no way to set a target for a period or see where they stand against it — they do the arithmetic by hand or not at all.

## Who is affected

The person using budget-checker to track their own spending — one account, one person's receipts. There is no shared or team budget use case, and no usage count exists to quantify frequency (see Evidence). (From the answer to `who-is-affected` by bohdan.)

## Evidence

- **The feature has never been reachable.** The `Budget` model exists but, per the graph (`context("Budget")` in triage, recorded in `change_brief#50`), has zero callers and zero callees. Because no endpoint has ever exposed it, there is by construction no usage data for it — the absence of usage data is not a gap in this evidence, it is what the evidence shows.
- **A prior implementation existed and is gone.** The stale pytest cache `backend/.pytest_cache/v/cache/nodeids` (lines 4-28) records a full `tests/test_budgets.py` that once ran: `test_set_budget_stores_it`, `test_summary_shows_spent_remaining_and_not_over`, `test_over_target_month_is_shown_as_over`, `test_month_boundary_receipts`, `test_another_users_budget_is_not_found`, and `test_budgets_endpoints_refuse_unauthenticated_like_receipts` against `POST /api/v1/budgets` and `GET /api/v1/budgets/{period}/summary`. Neither the test file nor any budget router or schema exists in the working tree today. The cache also records prior design decisions: periods were `YYYY-MM` strings, re-setting a period replaced the target with one row (`test_setting_same_period_again_replaces_target_with_one_row`), and receipt matching used month boundaries at midnight UTC (`test_month_boundary_receipts` cases at nodeids lines 18-20).
- **Weakness in the evidence, stated plainly:** there is no usage data, no ticket count and no metric. Bohdan's own answer to `evidence` is that the absence of usage data is the finding — nobody has ever been able to use the feature the product is named after. The pytest cache proves the endpoints were built and tested at some point, but not why they disappeared; git history was not inspected at the step that found the cache (settled_question#63).

## Cost of inaction

If nobody touches this for six months, the product is called budget-checker and still cannot check a budget: receipts accumulate with nothing to compare them against. (From the answer to `cost-of-inaction` by bohdan; this is a consequence of the gap above, not a measured loss.)

## Success metrics

1. A user sets a target for a period via the API and a summary response returns three values — spent, remaining, and an over-budget flag — each independently checkable with curl against a running app once the endpoints exist. (From the answer to `success-signal`; measurable today, no instrumentation needed.)
2. Automated tests cover create + summary, including an over-budget case — a `backend/tests/test_budgets.py` file that the pytest cache shows once existed is restored and passing.
3. *Needs instrumentation first:* any usage signal (budgets created per week, summaries fetched) — no usage telemetry exists today, as the evidence answer confirms. Not a criterion for this change; listed so it is not mistaken for one.

## Out of scope

From the answer to `out-of-scope` (bohdan), and the goal:

- No frontend work — explicitly excluded by the goal.
- No alerts, notifications, or progress indicators.
- No multi-currency.
- No budgets shared between users.
- No recurring or rolling budgets — a period is set once, by an explicit API call.
- No changes to the receipts router or the `Receipt` model; the summary only reads from them. (A reasonable reader might assume the summary needs to touch receipts code — this excludes that.)
- No migration or ALTER on the budgets table — the table already exists in `backend/budget_checker.db` via `Base.metadata.create_all` at `backend/app/main.py:84`.

## Assumptions

- The prior design visible in the pytest cache (`YYYY-MM` periods, replacement-on-reset, month-boundary receipt matching, cross-user isolation, unauthenticated refusal) is the intended behaviour and should be restored — nobody has confirmed this; it is inferred from `backend/.pytest_cache/v/cache/nodeids`.
- The summary is per single budget; interactions between multiple overlapping budgets are undefined and assumed out of scope.
- Receipt amounts (`Numeric` columns) should serialize to JSON numbers consistently; there is no established typed-schema pattern to copy, since the receipts router returns raw dicts.
- "The user does the arithmetic by hand or not at all" is bohdan's characterisation of current behaviour, not an observation from data.

## Open questions

- Was the prior budgets implementation deliberately removed, and if so why? Restoring it without knowing the reason risks re-introducing something that was pulled for cause. Git history has not been inspected — that inspection would answer it.
- Should the prior behaviour recorded in the pytest cache be treated as the specification, or redesigned?
- Confirm exact period semantics: `YYYY-MM` strings with month boundaries as the cache's `test_month_boundary_receipts` cases imply (midnight UTC, inclusive-exclusive) — is that what is wanted now, and has anyone re-affirmed it?
- How do multiple budgets for overlapping periods behave, if the per-single-budget assumption above is wrong?
