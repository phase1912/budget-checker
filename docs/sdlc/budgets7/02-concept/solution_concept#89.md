# Solution concept — Budgets and spend summary

This follows the problem brief at `docs/sdlc/budgets7/03-problem/problem_brief#74.md` (referred to below as [[prob-74]]). The chooser has now answered `chosen-direction`; the decision is folded back in below and replaces the earlier draft's recommendation.

## Options considered

### Option A — Restore the prior design as evidenced by the pytest cache

Rebuild exactly what `backend/.pytest_cache/v/cache/nodeids` records once existed: a `POST /api/v1/budgets` that takes a `YYYY-MM` period and target, replaces the row on re-set, refuses malformed periods and invalid targets *naming the rule* (nodeids lines 11-17: `2024-13`, `24-01`, `10.999`, `-10.00`, `0.00`), and a `GET /api/v1/budgets/{period}/summary` returning spent/remaining/over, with month boundaries at midnight UTC inclusive-exclusive (nodeids lines 18-20), cross-user isolation, uniform not-found, and unauthenticated refusal like receipts. Also `test_duplicate_rows_read_deterministically_and_indicated` (line 10) implies the summary tolerates — and flags — duplicate period rows, since the column has no uniqueness constraint.

- **Cost:** fits bohdan's appetite — small, a day at most (settled_question#87). The endpoint paths and behaviours are externally evidenced, so requirements/acceptance stages get a ready-made test list of ~25 cases to re-derive.
- **Gives up:** the chance to ask whether `YYYY-MM` month-string budgets are what is wanted *now* — it restores behaviour nobody has re-affirmed (an open question in [[prob-74]]).
- **Changing mind later:** cheap. Everything is additive; deleting the router removes the feature (bohdan, settled_question#88).

### Option B — Same capability, minimally specified: set + summary without restoring every legacy rule

Build the two endpoints, but specify only what [[prob-74]]'s success metrics require: create a budget for a period, and a summary returning spent, remaining, over. Period format validated as `YYYY-MM` (it is the only shape the receipts' `created_at` can be matched against cheaply), basic auth/ownership like receipts, but no rule-naming error messages, no duplicate-row flagging, no strict two-decimal target rule — those legacy behaviours are re-decided in requirements only if wanted.

- **Cost:** less than A — roughly half a day to a day, fewer test cases to write.
- **Gives up:** the free specification the cache provides. Acceptance criteria would have to be invented rather than read off nodeids lines 4-28, and a later tightening to A's rules is a second pass through requirements.
- **Changing mind later:** cheap in the same way as A; the endpoints and contract can be the same, so tightening validation is additive.

### Option C — Do nothing (or the smallest possible thing)

Do nothing: the Budget model stays unused; the user keeps doing arithmetic by hand. The smallest possible thing short of that — e.g. only `GET` summary over an implied current-month target — is not viable because there is no way to set a target without the POST, so the smallest coherent thing is already Option B.

- **Cost:** zero now. **Gives up:** the product remains named budget-checker and cannot check a budget ([[prob-74]], cost of inaction). Bohdan judged six months of this a real cost, not a neutral one (settled_question#71).

## Chosen approach

Bohdan's answer (settled_question#93): "A budgets router with the endpoints the summary needs, reading receipts for the period and computing the summary on the fly. No stored aggregates."

The direction chosen is the build of both endpoints — the capability of A and B — with the summary **computed on the fly** by reading the user's receipts for the period at request time: no stored aggregates, no summary caching, no background rollup. Spent, remaining, and an over flag are derived fresh from `Receipt` rows each time the summary endpoint is called. That rules out the one design this choice forecloses: any precomputed-spent column on `budgets` or a companion aggregates table. Since the `budgets` table is used as it stands (bohdan, settled_question#86 — no migration, no ALTER), on-the-fly computation is in fact the only shape compatible with the stored schema anyway; the decision affirms it explicitly.

At concept level the approach is: an additive `budgets` router alongside `receipts.py` in `backend/app/routers/`, included in `create_app()` (`backend/app/main.py:76-82` pattern); a small request/response schema addition; the `period` column stays a plain String (no ALTER) with period semantics enforced in router code; the summary filters the current user's receipts over the period window and computes spent/remaining/over in the request; all reads and writes scoped to the current user with the receipts router's uniform not-found pattern (`receipts.py:35-42`) and its unauthenticated refusal. Reversibility is unchanged: removing the router removes the feature (settled_question#88).

One thing the answer leaves open, and the document says so rather than guessing: it names the *shape* of the decision, not the legacy validation details. Whether the rule-naming refusals, duplicate-row flagging and strict two-decimal target rules from the pytest cache come back is the substance of the requirements stage, which now runs against this settled direction. The rest of the legacy behaviour the cache records (endpoint paths `POST /api/v1/budgets` and `GET /api/v1/budgets/{period}/summary`, cross-user isolation, unauthenticated refusal) is consistent with the answer and is the cheapest externally evidenced shape to build.

## Why not the alternatives

**Option A (restore the cache-recorded design wholesale)** — not chosen as an all-or-nothing bet. Its endpoint shape and its on-the-fly summary are what was chosen; what was not adopted is the commitment to every legacy validation rule as a pre-made specification. The reason A stood or fell on the assumption that the cache-recorded behaviour was intended rather than removed for cause — an assumption [[prob-74]] left open — and bohdan's answer does not make that bet; it specifies the capability directly and leaves the legacy rules to requirements.

**Option B (minimal spec)** — the chosen answer is very close to B in spirit (build what the summary needs, no more) and B's scope is effectively subsumed: the difference between B and the chosen direction is only whether the legacy rules are dropped *by decision* or *left open*, and bohdan's answer leaves them open rather than dropping them. B as written is therefore not a rejected direction so much as the floor of the chosen one.

**Option C (do nothing)** — rejected on bohdan's own cost of inaction: the product is named budget-checker and cannot check a budget; receipts accumulate with nothing to compare against (settled_question#71). It stays recorded because the change is cheap enough that declining it was a live choice, and the chooser considered and declined it.

## Constraints

From bohdan (settled_question#86) and [[prob-74]] out-of-scope, all respected by the chosen approach: backend only; FastAPI/SQLAlchemy/pytest as they stand; the Budget model used as-is, no migration or ALTER on the budgets table; no frontend, no alerts, no multi-currency, no shared budgets, no recurring/rolling budgets, no changes to the receipts router or Receipt model. No stored aggregates — a constraint made explicit by the chosen direction itself. Appetite: small, a day at most (settled_question#87). Reversibility: fully reversible — removing the router removes the feature (settled_question#88).

## Assumptions

- `YYYY-MM` month-string periods remain the period format — **cheap to check now**: the pytest cache's nodeids (lines 11-20) evidence this format and the receipts model's `created_at` supports matching it; no counter-evidence found in `backend/app/models.py`. Still to be re-affirmed in requirements since bohdan's answer did not name a format.
- Per-user duplicate-period rows can occur (no DB uniqueness constraint) and the summary must read them deterministically — **cheap to check now**, checked: `period` is a plain String column with no unique constraint (`backend/app/models.py`, `__tablename__ = "budgets"` block at line 92).
- One user, one set of budgets; overlapping/multiple budgets need no special semantics — **cheap to check now**, checked: the `who-is-affected` answer (settled_question#69) confirms a single-account, single-person product.
- The prior implementation was removed for cause rather than merely lost — **only discoverable later** by inspecting git history; no longer load-bearing for the decision as it was for the old Option A recommendation, since the direction is now specified directly rather than restored wholesale. The check is still cheap and worth doing before implementation.

## Risks

- **Requirements stage inherits an underspecified contract.** The chosen answer fixes the shape but not the validation and edge-case rules (malformed periods, duplicate rows, target precision). If requirements does not settle these, the endpoints ship with invented behaviour. Mitigation: the pytest cache names the exact test cases that once covered them — requirements should re-derive its criteria from that list.
- **Numeric/float serialization drift** between target (Numeric(12,2)) and computed spent/remaining — rounding mismatches in the `over` flag. Early signal: the boundary tests the cache already names (exact-two-decimal target, exact-target case).
- **Summary cost grows with receipt count** since it is computed on the fly per request, by explicit decision. At one user's scale this is negligible (noted in settled_question#82); if it ever is not, on-the-fly is the part that is expensive to walk back.

## Out of scope

Carried from [[prob-74]]: no frontend work; no alerts or notifications; no multi-currency; no shared budgets; no recurring or rolling budgets; no changes to the receipts router or Receipt model; no migration or ALTER on the budgets table. Newly excluded by this choice: any stored aggregate of spend (no summary column, no rollup table); any change to the stored schema (no unique constraint added to `budgets.period`); no usage telemetry (listed as needing instrumentation in [[prob-74]] and explicitly not a criterion here).