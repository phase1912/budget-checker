# Requirements baseline — Budgets and spend summary

## Purpose

This document is the baseline for the feature "Budgets and spend summary" (branch `budgets7`, based on `master`). It assembles, in one place, everything accepted by the stages that produced the problem brief at `docs/sdlc/budgets7/01-problem/problem_brief#74.md` ([[prob-74]]), the solution concept at `docs/sdlc/budgets7/02-concept/solution_concept#89.md` ([[concept-89]]), the requirements and quality attributes (requirement#114 at `docs/sdlc/budgets7/03-requirements/requirement#114.md`, quality_attribute#115 at `docs/sdlc/budgets7/03-requirements/quality_attribute#115.md`), and the acceptance scenarios at `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md` ([[spec-136]]). Design and implementation are committed against this document: a requirement that is not in it is not in the feature.

The change: add budgets to the budget-checker backend API. A signed-in user sets a budget for a period (period, target_amount) and reads a summary for it — spent, remaining, over — computed on the fly from that user's receipts. Backend only; the frontend is explicitly out of scope. The `Budget` model already exists at `backend/app/models.py:91` (`backend/app/models.py:91-100`: plain `String` `period` at line 96, `Numeric(12, 2)` `target_amount` at line 97) and is unused; no budgets router exists and `create_app()` (`backend/app/main.py:65`) includes none — its only routers today are health, auth and receipts (`backend/app/main.py:80-82`).

## Scope

**In scope**

- A budgets router in `backend/app/routers/`, modelled on the receipts router (`APIRouter` with the `/api/v1` prefix, the `get_current_active_user` dependency at `backend/app/deps.py:52`, the receipts router's per-user filtering with uniform not-found at `backend/app/routers/receipts.py:35-42`).
- Two endpoints: `POST /api/v1/budgets` (set/replace a target) and `GET /api/v1/budgets/{period}/summary` (spent, remaining, over).
- Request/response schemas added to `backend/app/schemas.py` (or raw-dict style, as receipts does at `backend/app/routers/receipts.py:45-66` — an implementation choice not fixed by this baseline).
- One-line router registration in `create_app()` (`backend/app/main.py:76-82` pattern).
- The `period` column stays a plain `String` (`backend/app/models.py:96` — no ALTER, no added uniqueness constraint); `YYYY-MM` semantics and duplicate-row tolerance are enforced in router code.
- Automated tests in `backend/tests/test_budgets.py` (the file does not exist in the working tree today — `backend/tests/` contains only auth, error_handling, health, models and receipts tests).

**Out of scope** (from [[prob-74]] out-of-scope and [[concept-89]])

- No frontend work — excluded by the goal.
- No alerts, notifications, or progress indicators.
- No multi-currency.
- No budgets shared between users.
- No recurring or rolling budgets — a period is set once, by an explicit API call.
- No changes to the receipts router or the `Receipt` model; the summary only reads from them.
- No migration or ALTER on the budgets table — it is already created by `Base.metadata.create_all` at `backend/app/main.py:84`.
- No stored aggregates: no summary column, no rollup table; the summary is computed fresh from `Receipt` rows at request time.
- No usage telemetry.

## Definitions

Terms the requirements use in a specific sense (gathered at settled_question#150):

- **Signed-in user** — a requester who passes the `get_current_active_user` dependency (`backend/app/deps.py:52`), the same authentication the receipts endpoints use. The authenticated owner of the receipts.
- **Valid authenticated user** — same as signed-in user: the request carries credentials the receipts endpoints would accept. (Whether an expired-but-decodable token counts is defined by that dependency's behaviour, not restated here.)
- **Period** — a `YYYY-MM` month string, e.g. `2025-03`. The period's month runs from the first day of the month at midnight UTC inclusive to the first day of the next month at midnight UTC exclusive (BUD-4, BUD-6). The "next month" of December is January of the following year — the stale pytest cache records `test_december_period_uses_next_years_january_as_end` (`backend/.pytest_cache/v/cache/nodeids:9`), though no acceptance scenario covers the December case (see Open questions).
- **Valid target amount** — a target that is greater than zero and has no more than two decimal places. `10.99` is valid; `-10.00`, `0.00` and `10.999` are not (BUD-7).
- **Spent** — the sum of that user's `Receipt.amount` for receipts whose timestamp falls within the period's month boundary as defined above, and only that user's receipts (BUD-3, BUD-4; the cache's `test_another_users_receipts_not_counted` at nodeids line 5 evidences this was prior behaviour).
- **Remaining** — target minus spent.
- **Over** — whether spending exceeds the target. **The strict vs inclusive comparison (spent > target vs spent ≥ target) is NOT defined anywhere in the accepted set** — see Open questions; an exact-target receipt total is an unsettled case.
- **The same refusal / the same not-found outcome** — the response the receipts endpoints currently give for unauthenticated requests (BUD-9) and for a resource not belonging to the requesting user (BUD-5/BUD-8) respectively. The responses are pinned by the receipts router's behaviour at implementation time, not by a stated status code or shape here.
- **Budgets API** — the new budgets router served by the FastAPI backend under the versioned prefix; the system named in every requirement.

## Functional requirements

Verbatim from requirement#114 (accepted at stage_instance#94). System name in each: the budgets API.

**BUD-1 — Set a budget for a period** — must — test

When a signed-in user submits a period and target amount to the budgets API, the budgets API shall store that target amount for that user and period.

**BUD-2 — Re-setting a period replaces the target** — must — test

When a signed-in user sets a budget for a period they have already set, the budgets API shall replace the previous target so that exactly one budget row remains for that user and period.

**BUD-3 — Summary returns spent, remaining and over** — must — test

When a signed-in user requests the summary for a period with a budget set, the budgets API shall return, computed on the fly from that user's receipts in the period, the amount spent, the amount remaining, and whether spending is over the target.

**BUD-4 — Receipts counted within month boundaries** — must — test

When the budgets API computes spent for a period, the budgets API shall include only receipts whose timestamp falls in the period's month, from the first day of the month at midnight UTC inclusive to the first day of the next month at midnight UTC exclusive.

**BUD-5 — Summary for a period with no budget** — must — test

If a summary is requested for a period for which the user has set no budget, then the budgets API shall respond that no budget is set for that period rather than reporting a zero target.

**BUD-6 — Refuse a malformed period, naming the rule** — must — test

If a budget request carries a period that is not a `YYYY-MM` month string (for example `2024-13` or `24-01`), then the budgets API shall refuse the request with an error naming the required `YYYY-MM` format.

**BUD-7 — Refuse an invalid target, naming the rule** — must — test

If a budget request carries a target amount that is zero, negative, or has more than two decimal places (for example `-10.00`, `0.00` or `10.999`), then the budgets API shall refuse the request with an error naming the accepted target rule.

**BUD-8 — Another user's budget is not readable** — must — test

If a signed-in user requests a budget summary for a period that only a different user has set, then the budgets API shall respond with the same not-found outcome it gives for a period with no budget — without any part of the other user's budget in the response.

**BUD-9 — Unauthenticated requests refused like receipts** — must — test

If a request to a budgets endpoint carries no valid authenticated user, then the budgets API shall refuse it with the same refusal the receipts endpoints give unauthenticated requests.

**BUD-10 — Duplicate period rows read deterministically and indicated** — must — test

If more than one budget row exists for the same user and period, then the budgets API shall return the same summary for every read of that period, indicating the duplication in the response.

**BUD-11 — Endpoints reachable through the application** — must — inspection

The backend application shall expose the budgets endpoints under the versioned API prefix alongside the existing routers.

## Quality attributes

Verbatim measures from quality_attribute#115. **Both thresholds are proposed, not confirmed** — settled_question#110 explicitly declined to settle a latency number; bohdan and the implementer must confirm or delete them (see Open questions).

**INV-NFR-1 — Summary and set latency** — should — test

While the backend is under normal single-user load, the budgets API shall respond to a summary or set-budget request within 200 ms at the 95th percentile.

| | |
|---|---|
| metric | p95 response time for `POST /api/v1/budgets` and `GET /api/v1/budgets/{period}/summary` |
| threshold | 200 ms |
| conditions | 5 requests/second sustained over 5 minutes, local SQLite backend, production-sized data for one user (a few thousand receipts), single authenticated user |

**INV-NFR-2 — On-the-fly summary scales with receipt volume** — should — test

While the summary is computed on the fly from receipt rows at request time, the budgets API shall return the summary within 500 ms at the 95th percentile with 10,000 receipts for the user.

| | |
|---|---|
| metric | p95 response time for `GET /api/v1/budgets/{period}/summary` |
| threshold | 500 ms |
| conditions | 10,000 receipts for the user spread across periods, local SQLite backend, measured over 100 requests |

## Acceptance scenarios

Lifted verbatim from `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md` ([[spec-136]], 12 scenarios: 9 scenarios plus 3 Scenario Outlines). Note on BUD-11: it is verified by inspection (of `create_app()` plus a routing demonstration) per requirement#114, and is tagged on the first scenario; it has no dedicated behavioural scenario of its own, which the acceptance spec's traceability note records by design.

### BUD-1 (with BUD-11) — A budget is set for a period

```gherkin
Feature: Budgets and spend summary

  Background:
    Given Alex is signed in
    And the period is "2025-03"

  Scenario: A budget is set for a period (BUD-1, BUD-11)
    When Alex sets a target of "150.00" for the period
    Then the summary for the period shows a target of 150.00
```

### BUD-3 — Summary under and over target

```gherkin
  Scenario: The summary shows spent, remaining and over for a period under target (BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 90.00 inside the period's month
    When Alex reads the summary for the period
    Then the summary shows 90.00 spent
    And the summary shows 60.00 remaining
    And the summary shows Alex is not over

  Scenario: The summary shows over when spending exceeds the target (BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 175.50 inside the period's month
    When Alex reads the summary for the period
    Then the summary shows 175.50 spent
    And the summary shows Alex is over
```

### BUD-2 — Re-setting the target

```gherkin
  Scenario: Setting the same period again replaces the target (BUD-2)
    Given a target of "150.00" is set for the period
    When Alex sets a target of "200.00" for the period again
    Then the summary for the period shows a target of 200.00

  Scenario: Re-setting the target changes the over flag (BUD-2, BUD-3)
    Given a target of "150.00" is set for the period
    And Alex has receipts totalling 175.50 inside the period's month
    When Alex sets a target of "200.00" for the period again
    Then the summary shows Alex is not over
```

### BUD-4 — Month boundaries

```gherkin
  Scenario Outline: Receipts count only inside the month boundaries (BUD-4)
    Given a target of "150.00" is set for the period
    And Alex has a receipt for 10.00 timestamped <when> UTC
    When Alex reads the summary for the period
    Then the summary shows <spent> spent

    Examples:
      | when                                | spent |
      | 1 March 2025 at midnight            | 10.00 |
      | 15 March 2025 at noon               | 10.00 |
      | 1 April 2025 at midnight            | 0.00  |
```

### BUD-5 — No budget set

```gherkin
  Scenario: A summary for a period with no budget says none is set (BUD-5)
    When Alex reads the summary for a period they never set
    Then Alex is told no budget is set for that period
    And the summary does not report a target of zero
```

### BUD-6 — Malformed period

```gherkin
  Scenario Outline: A malformed period is refused with the rule named (BUD-6)
    When Alex sets a target of "150.00" for the period "<period>"
    Then the request is refused
    And the refusal names the required "YYYY-MM" format

    Examples:
      | period   |
      | 2024-13  |
      | 24-01    |
```

### BUD-7 — Invalid target

```gherkin
  Scenario Outline: An invalid target is refused with the rule named (BUD-7)
    When Alex sets a target of "<amount>" for the period
    Then the request is refused
    And the refusal names the accepted target rule

    Examples:
      | amount  |
      | -10.00  |
      | 0.00    |
      | 10.999  |
```

### BUD-8 — Cross-user isolation

```gherkin
  Scenario: Another user's budget is answered the same as no budget (BUD-8)
    Given a target of "150.00" is set for the period by Priya
    When Alex reads the summary for the period
    Then Alex is told no budget is set for that period
    And the response carries none of Priya's target
```

### BUD-9 — Unauthenticated refusal

```gherkin
  Scenario: A request with no valid authenticated user is refused like receipts (BUD-9)
    Given a request is made without a valid authenticated user
    When the budgets summary for the period is read
    Then the request is refused the same way an unauthenticated receipts request is
```

### BUD-10 — Duplicate rows

```gherkin
  Scenario: Duplicate budget rows are read deterministically and indicated (BUD-10)
    Given two budget rows exist in storage for Alex and the period
    When Alex reads the summary for the period twice
    Then both reads show the same target of 150.00
    And the response indicates the duplication
```

## Traceability matrix

Every accepted requirement and quality attribute, traced up through the chain. Upstream artifacts: [[prob-74]] = `docs/sdlc/budgets7/01-problem/problem_brief#74.md`, [[concept-89]] = `docs/sdlc/budgets7/02-concept/solution_concept#89.md`, [[req-114]] = `docs/sdlc/budgets7/03-requirements/requirement#114.md`, [[qa-115]] = `docs/sdlc/budgets7/03-requirements/quality_attribute#115.md`, [[spec-136]] = `docs/sdlc/budgets7/04-acceptance/acceptance_spec#136.md`. Counts, checked against the accepted artifacts and not estimated: **11 requirement artifacts (BUD-1..BUD-11) == 11 matrix rows**; **2 quality-attribute artifacts (INV-NFR-1, INV-NFR-2) == 2 matrix rows**; **11 requirements with a scenario reference == 11** (BUD-11's reference is its tag on the BUD-1 scenario plus its inspection verification, per the audit answer at settled_question#147 — uncovered count 0); **1 acceptance artifact ([[spec-136]], Gherkin embedded) == 1 feature block in the scenarios above** (there are no separate `.feature` files in the repo).

| Requirement | Traces up to | Priority | Verification | Scenarios |
|---|---|---|---|---|
| BUD-1 | [[prob-74/success-metrics]] → [[prob-74]], [[concept-89/chosen-approach]] → [[concept-89]] | must | test | [[spec-136]] (1 scenario: A budget is set for a period) |
| BUD-2 | [[concept-89/chosen-approach]] → [[concept-89]] | must | test | [[spec-136]] (2 scenarios: replace target; over flag changes) |
| BUD-3 | [[prob-74/success-metrics]] → [[prob-74]], [[concept-89/chosen-approach]] → [[concept-89]], [[qa-115/INV-NFR-1]] | must | test | [[spec-136]] (4 scenarios tagged BUD-3: under, over, re-set over flag, plus first scenario) |
| BUD-4 | [[concept-89/assumptions]] → [[concept-89]] | must | test | [[spec-136]] (1 Scenario Outline, 3 examples) |
| BUD-5 | [[prob-74/problem]] → [[prob-74]] | must | test | [[spec-136]] (1 scenario) |
| BUD-6 | [[prob-74/evidence]] → [[prob-74]] | must | test | [[spec-136]] (1 Scenario Outline, 2 examples) |
| BUD-7 | [[concept-89/risks]] → [[concept-89]] | must | test | [[spec-136]] (1 Scenario Outline, 3 examples) |
| BUD-8 | [[concept-89/chosen-approach]] → [[concept-89]] | must | test | [[spec-136]] (1 scenario) |
| BUD-9 | [[concept-89/chosen-approach]] → [[concept-89]] | must | test | [[spec-136]] (1 scenario) |
| BUD-10 | [[concept-89/assumptions]] → [[concept-89]] | must | test | [[spec-136]] (1 scenario) |
| BUD-11 | [[prob-74/problem]] → [[prob-74]], [[concept-89/chosen-approach]] → [[concept-89]] | must | inspection | [[spec-136]] (tagged on the BUD-1 scenario; inspection by design, per settled_question#147) |
| INV-NFR-1 | [[concept-89/chosen-approach]] → [[concept-89]], BUD-3 → [[req-114]] | should | test | No acceptance scenario — [[spec-136]] explicitly excludes latency; the measure table above is the checkable form |
| INV-NFR-2 | [[concept-89/risks]] → [[concept-89]], [[concept-89/chosen-approach]] → [[concept-89]] | should | test | No acceptance scenario — same exclusion; the measure table above is the checkable form |

## Open questions and assumptions

Gathered from every stage (settled_question#148, #149, #135; requirement#114 and quality_attribute#115 open questions; [[prob-74]]; [[concept-89]]). These are the ones most likely to be quietly dropped; none blocks the baseline, but each unsettles something in it.

**Open questions**

1. Was the prior budgets implementation deliberately removed, and if so why? Git history has never been inspected (flagged in the requirements gate finding, gate_finding#119). Restoring cache-recorded behaviour without knowing the removal reason risks re-introducing something pulled for cause.
2. Should the prior behaviour recorded in `backend/.pytest_cache/v/cache/nodeids` be treated as the specification, or redesigned? Requirements adopted it piecewise (BUD-4, BUD-6, BUD-7, BUD-10) without a re-affirmation by anyone. Relatedly, this baseline does not restore every legacy test the cache records: `test_malformed_period_refused_with_rule_named[2024-00]` and `[monthly]` (nodeids lines 14, 17) are additional period-refusal examples beyond BUD-6's two, `test_target_with_exactly_two_decimals_accepted` (line 28) is the acceptance half of BUD-7, `test_month_with_no_receipts_spends_zero` (line 21) and `test_receipts_outside_period_not_counted` (line 23) are covered by BUD-4's rule but not by dedicated scenarios, and `test_december_period_uses_next_years_january_as_end` (line 9) is a December boundary case with no scenario. Implementing BUD-4 and BUD-6 as written satisfies all of these implicitly; restoring the named tests themselves is an implementation choice.
3. Are `YYYY-MM` month-string periods with midnight-UTC inclusive-exclusive boundaries re-affirmed as wanted now? Adopted from the cache; bohdan's chosen-direction answer never named a format. If the format changes, BUD-4 and BUD-6 change.
4. The strict two-decimal target rule in BUD-7 comes from the pytest cache and the concept's rounding note, not from an explicit bohdan decision. Relaxing it changes only BUD-7.
5. How do multiple/overlapping budgets behave? Closed only by an assumption in [[concept-89]] (single-account product needs no special semantics), never by a person.
6. **Strict vs inclusive "over":** whether `over` means spent > target or spent ≥ target is nowhere stated, and the exact-target case appears in no scenario. Two implementations could legitimately differ. Must be settled before or during implementation.
7. Timezone normalisation of boundary receipts (settled_question#135): BUD-4 says midnight UTC but not whether a receipt stored with a timezone offset is compared after conversion to UTC or on its naive reading.
8. Concurrent re-sets (settled_question#135): BUD-2's "exactly one row" has no concurrency rule, and no DB uniqueness constraint enforces it. Whether the API guarantees one row under simultaneous POSTs is not stated.
9. Whether any security attribute beyond BUD-8/BUD-9 is wanted (deferred from quality_attribute#115 to acceptance-scenario time; the acceptance stage ran without it being decided).
10. No pagination/list of set budgets exists; a reader might assume the API offers it. Confirmed absent, not planned.

**Assumptions**

1. **INV-NFR-1's 200 ms p95 threshold is proposed, not confirmed** (settled_question#149). Bohdan declined to settle a latency number (settled_question#110). Bohdan and the implementer must confirm or delete it before it is treated as an agreed target.
2. **INV-NFR-2's 500 ms / 10,000-receipt threshold is proposed, not confirmed** (settled_question#149). It turns the concept's judgement that per-request computation is negligible at one user's scale (settled_question#82) into a checkable bound; confirm or delete before treating as agreed.
3. The prior design visible in the pytest cache is the intended behaviour and is being restored deliberately — inferred from the cache, never confirmed (see open question 2).
4. The summary is per single budget; overlapping budgets need no special semantics (see open question 5).
5. The receipts endpoints meet INV-NFR-1's threshold informally at today's scale, so satisfying it costs nothing extra — assumed, not measured.
6. "The user does the arithmetic by hand or not at all" is bohdan's characterisation of current behaviour, not an observation from data ([[prob-74]] assumptions).
7. No latency threshold beyond the two proposed attributes applies; no acceptance scenario asserts one ([[spec-136]] explicitly excludes latency).
