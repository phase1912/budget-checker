# Change brief — Budgets and spend summary (branch `budgets7`)

## What changes

A user can set a budget for a period and get a summary for it: how much was spent on receipts in that period, how much is left, and whether they are over. Backend API only — new endpoints backed by the existing, currently unused `Budget` table. The frontend is untouched.

## Kind of change

`feature`

## Why this kind

This was settled in triage: the maker recommended `feature` (settled_question#34), the maker's answer to the change-kind question was `feature` (settled_question#44), and `change_kind#45` records `feature`.

The case, from evidence:

- **New intent, not a defect.** Nothing is broken; the capability has never existed. There is no budgets router, no budget schemas, no budget tests anywhere in `backend/`.
- **Additive, small blast radius.** `context("Budget")` → found at `backend/app/models.py`, Class, **zero callers and zero callees** — the model is pure scaffolding today. `impact("Budget", upstream)` → found, affected 3, direct 3, risk LOW (its dependents are the `User.budgets` relationship and Base metadata registration). `impact("create_app", upstream)` → found at `backend/app/main.py`, affected 1, direct 1, risk LOW (the module-level `app = create_app()`). Both calls carried a freshness note: `backend/app/main.py` and `backend/app/models.py` changed after the index was built, so these counts may be slightly behind — nothing in them contradicts the picture.
- **No public interface moves, no stored-schema migration.** The budgets table is created by `Base.metadata.create_all` at startup, the same new-table-no-ALTER pattern the receipt-photos run documented (`docs/sdlc/receipts6/`). Existing endpoints are untouched; the receipts router is only read for the summary aggregation.
- **Why not a smaller kind:** the summary semantics are real design work, not boilerplate — how a Receipt's timestamp maps to a budget period, how multiple budgets interact, Numeric-to-float serialization. And this introduces a new public HTTP surface, which warrants requirements and acceptance scenarios rather than a straight-to-code pass.

The graph findings above are corroborated by the repository walk recorded in the sizing answer (settled_question#33): `create_app` includes routers at `backend/app/main.py` (the include_router pattern), `backend/app/schemas.py` has no budget models, and the receipts router returns raw dicts, so the new schemas will set the typed pattern rather than copy one.

## Expected blast radius

What I asked the graph and what came back:

- `impact("create_app", upstream)` → found: true, affected 1, direct 1, risk LOW
- `impact("Budget", upstream)` → found: true, affected 3, direct 3, risk LOW
- `context("Budget")` → found: true, Class at backend/app/models.py, 0 callers, 0 callees

Radius, symbol by symbol:

- `Budget` (backend/app/models.py) — 3 upstream dependents (relationship and metadata wiring), all additive-safe; the change adds no columns to it.
- `create_app` (backend/app/main.py) — 1 direct dependent, the module-level `app = create_app()`; the change adds one include_router line.
- `backend/app/routers/budgets.py` (new) — touches no existing symbol; new endpoint surface.
- `backend/app/schemas.py` — additions only (BudgetCreate/BudgetResponse); existing schemas untouched.
- Existing receipts/auth endpoints and the frontend — untouched. The frontend is explicitly out of scope by the goal.
- Untested by the graph: the summary aggregation logic (new symbol) has no dependents yet, so its radius is unknowable until it exists — that is expected and is where requirements and scenarios will concentrate.

## Acceptance criteria

First sketch; later stages sharpen these.

1. A user can create a budget via an API endpoint with a period and a target amount, and read it back.
2. A summary endpoint for a budget returns: total spent on receipts in that period, remaining amount, and an over-budget flag — each observable in a response.
3. `create_app()` includes the budgets router, so a fresh app instance exposes the new routes.
4. Automated tests cover create + summary, including an over-budget case.

## Out of scope

- The frontend — explicitly excluded by the goal.
- Alerts, notifications or progress bars for budgets — UI concerns beyond the summary endpoint.
- Any change to the receipts router or the Receipt model; the summary only reads from it.
- Migration/ALTER work on the budgets table — none is needed under the new-table pattern.

## Open questions

- What does a "period" mean exactly — a fixed named month/week/year, or arbitrary start/end dates? This drives both the request schema and how receipts are matched to the budget.
- How do multiple budgets for overlapping periods interact — are summaries always per single budget?
- How are receipt amounts matched to a period — by `created_at` (Receipt at backend/app/models.py:60 area) or some other timestamp, and inclusive bounds?
- Serialization: Receipt amounts are Numeric — confirm the summary returns JSON numbers (float/Decimal-to-float) consistently.
