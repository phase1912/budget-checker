Change brief — Receipt photos on expenses

## What changes
When this is done, a person recording an expense in the budget tracker can attach a photograph of the receipt to it, and open that photograph again later from the expense's own screen — without leaving the app and without matching it by date against the camera roll. Expenses recorded without a photo behave exactly as they do today.

## Kind of change
feature

## Why this kind
This is new intent, not a defect: nothing in the repository handles expense photos today, so there is nothing that "used to work". The maker's own recommendation was feature, and the evidence supports it.
- `query("expense photo attachment receipt upload")` → 0 hits — the concept does not exist in the index; there is no flow to modify, only to create.
- `context`/`impact("Receipt", upstream)` → found: false — the index does not hold even the closest existing symbol, so no callers or flows can be named from the graph. The only graph answer available is an absence, and the honest reading of it is that the graph cannot bound this change for us; the tree has to.
- Reading the tree: backend/app/models.py:54-64 has a `Receipt` SQLAlchemy model (user_id, amount, description) — no photo/image column, no router, no schemas, no frontend surface. It is scaffolding, not a flow, so the change is additive end to end: a new model/column, new schemas, a new upload/download endpoint pair, new frontend UI.
- It is not a chore: it needs a stored-schema decision (photo bytes in DB vs filesystem vs object store), new API surface, and UI. Nor is it a bugfix: there is no failing behaviour and no reproduction.
Open question worth flagging now (not enough to change the kind): the backend has no migration tooling (`Base.metadata.create_all` only), so altering the `receipts` table is not free in a deployment with existing data.

## Expected blast radius
Nothing existing carries a graph-recorded dependency on the touched area, so this list comes from the tree, not from `impact`:
- `Receipt` (backend/app/models.py:54) — graph: no symbol by that name (impact found: false). Tree: referenced only by `User.receipts` in the same file and one table assertion in backend/tests/test_models.py:29. Leaf.
- `backend/app/schemas.py` — new request/response models; additive.
- `backend/app/routers/` — a new router file (only auth.py and health.py exist); `main.py` includes it.
- `backend/app/database.py` / `main.py` — schema change relies on `create_all`; no migration tooling exists.
- `frontend/src` — App.tsx, api/client.ts, plus new expense screen/store components; there are no expense screens today, only auth/health/landing.
- Unknown, and here is why: the code graph holds no symbol for any expense/receipt concept, so no caller counts, flow touches, or risk score can be quoted. The radius as far as the tree shows is new files plus one leaf model — but the graph cannot confirm that.

## Acceptance criteria
First sketch, for later stages to sharpen:
1. From the expense screen, a person can choose a photo from their device, attach it to the expense, and see it confirmed as attached without leaving the app.
2. Reopening that same expense later shows/opens the attached photo again, matched to that expense, not found by date in a camera roll.
3. An expense recorded without a photo behaves exactly as before (no photo prompt failure, no changed record shape visible to the user).

## Out of scope
Deciding or building expense summarisation/reporting on top of receipts. (A stale `__pycache__/app.cpython-314.pyc` references an 'expense'/'summarize' module that no longer exists in source; no code or document for it remains.)

## Open questions
- Where receipt photos are stored: DB blob, server filesystem, or object store — must be settled before code, and drives size.
- Does "expense" mean the existing `Receipt` model (add a column) or a distinct Expense concept (grow)? One question, worth asking before concept stage.
- Image size/format limits and retention (what happens to the photo when the expense is deleted) are unsettled.