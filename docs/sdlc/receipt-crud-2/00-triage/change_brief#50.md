# Change brief: receipt-crud-2 — Receipt create, read, update, delete

## What changes

The receipts API gains the four operations it is missing. Today `backend/app/routers/receipts.py` can list receipts and attach or fetch a photo (only three handlers on `router`, lines 45–130), so nothing in the backend can put a receipt there in the first place — `list_receipts` lists rows the backend itself cannot produce. When this is done: create a receipt, read one back, change its amount or description, and delete it. Each new endpoint refuses a receipt that is not the caller's with the module's uniform not-found (`_get_owned_receipt`, `_NOT_FOUND_DETAIL`, backend/app/routers/receipts.py lines 23, 35–42), and deleting a receipt takes its photo (`ReceiptPhoto`) with it. Backend only; no migration — the `Receipt` table is used as it stands; the existing list endpoint answers exactly as it does today; the frontend is untouched.

## Kind of change

**feature** (confirmed by the person, settled_question#44; my recommendation agreed).

## Why this kind

I recommended feature in the kind-recommendation answer (settled_question#34) and the decision matches it. The case, from evidence:

- **New behaviour, not a defect.** Nothing ever existed to create, update or delete a receipt; there is nothing that used to work. That is the definition of feature, not bugfix.
- **The public HTTP surface grows** by four authenticated endpoints, each needing contract-level specification (status codes, request/response schemas, foreign-receipt not-found semantics) — too much specification for a chore, whose acceptance record is the whole process.
- **Contained blast radius.** The impact analysis (below) shows LOW risk on every touched symbol; the handlers are additive inside one router file that already contains the ownership idiom, the uniform not-found and the commit pattern to copy. That argues for a *small* feature, not against the kind itself.
- **It reverses a deliberate prior scoping decision** — `docs/sdlc/receipts6/…/baseline.md` line 27 explicitly rejected receipt CRUD ("deliberately rejected by the earlier foundation process"). Reversing prior settled scope is intent, which again is feature territory, and the person should confirm the reversal is deliberate (open question below).

The case against feature was that the change is small and well-bounded — arguably a chore-plus. I argued against waving it through as a chore because new public endpoints need problem/concept/requirements stages, and the person confirmed feature.

## Expected blast radius

What I asked the code graph and what came back:

- `impact("_get_owned_receipt", upstream)` → found: true; affected 2, direct 2, risk LOW, processes: get_receipt_photo, upload_receipt_photo. The new read/update/delete handlers join these callers, reusing it — its blast radius grows, its contract does not move.
- `impact("list_receipts", upstream)` → found: true; affected 0, direct 0, risk LOW, no processes (HTTP-invoked only; its response shape is frozen by the goal anyway).
- `impact("Receipt", upstream)` → found: true; affected 3, direct 3, risk LOW; no model change needed.
- `impact("ReceiptPhoto", upstream)` → found: true; affected 3, direct 3, risk LOW; relevant only to the delete cascade, which the receipts6 run already settled.

Note: the freshness record flags `backend/app/routers/receipts.py` as changed after the index was built, so these counts may be slightly behind for that one file — the file as read shows only the three known handlers, so nothing material has moved.

Per-symbol/module lines:

- `backend/app/routers/receipts.py` — all four new handlers land here; graph shows no code-level dependents on the existing handlers (`list_receipts`: 0 affected).
- `_get_owned_receipt` — 2 direct callers today (upload_receipt_photo, get_receipt_photo); gains callers, does not change.
- `Receipt` (backend/app/models.py) — 3 affected, LOW risk; unchanged, no migration.
- `ReceiptPhoto` (backend/app/models.py) — 3 affected, LOW risk; only its deletion path is exercised.
- `backend/tests/test_receipts.py` — 410 lines, dedicated app fixture (lines 51–60), already covers the router end-to-end and anticipates the delete cascade (test_deleting_receipt_takes_its_photo_with_it); new CRUD tests extend it. `backend/tests/test_receipts_aborted_upload.py` touches the same router.
- Frontend (`ReceiptsStore`, `api/client.ts`) — named in the goal as untouched; deliberately not in the radius.

## Acceptance criteria

First sketch, to be sharpened by later stages:

1. A signed-in caller can create a receipt (amount, description) and then see it in the list endpoint's answer, which otherwise answers exactly as it does today.
2. A signed-in caller can read one of their receipts, update its amount or description, and delete it — and a request against a receipt that exists but belongs to someone else gets the same uniform 404 the photo endpoints already return (`_NOT_FOUND_DETAIL`).
3. Deleting a receipt that carries a photo removes the `ReceiptPhoto` row too (the behaviour the existing cascade test anticipates); no migration is added and the frontend is unchanged.

## Out of scope

- Any frontend change — the goal forbids it, and `ReceiptsStore`/`api/client.ts` are not touched even though they appear in graph queries.
- Any schema change or migration — the `Receipt` table is used exactly as it stands.
- Changing the list endpoint's response, the photo endpoints, or `_get_owned_receipt`'s semantics.

## Open questions

- **Reversal of intent:** receipts6 deliberately excluded receipt CRUD (its baseline line 27). Is reversing that settled decision the deliberate intent? The goal asserts the operations, so I have treated it as yes, but it deserves one explicit confirmation from the person.
- **Create request shape:** what fields create accepts (amount, description, anything else?) and their validation rules — the goal does not say; the concept/requirements stages should settle it.
- **Photo-on-create:** does create accept a photo inline, or does the existing one-photo-per-receipt upload endpoint remain the only way to attach one? The receipts6 run settled RCP-15 for uploads; create's relationship to it is unstated.