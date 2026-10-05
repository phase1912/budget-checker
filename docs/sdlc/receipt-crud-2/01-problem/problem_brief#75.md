# Problem brief: receipt-crud-2 — Receipt create, read, update, delete

## Problem

The receipts tracker's own API cannot put a receipt into its own table. `backend/app/routers/receipts.py` has only three endpoints — list receipts, attach a photo, fetch a photo (settled_question#71) — so there is no way to create a receipt, read one back, change its amount or description, or delete it. The result is that `list_receipts` lists rows the backend itself cannot produce, and every downstream feature that reads receipts, budgets included, reads a table nothing can fill (settled_question#72).

## Who is affected

The signed-in owner of the receipts, through the API — one account, one person's receipts, as every other endpoint in this backend already assumes (settled_question#70). Frequency: any time a receipt needs to be entered, corrected or removed, which is the core loop of a receipts tracker; no count was given.

## Evidence

The evidence is thin — it is the shape of the code, not a ticket count or a metric:

- `backend/app/routers/receipts.py` exposes exactly three endpoints: GET the list, POST a photo, GET a photo. There is no POST to create a receipt and no way to read, change or remove one, so `list_receipts` lists rows the backend cannot produce (settled_question#71).
- Prior work confirms this gap is deliberate, not accidental: `docs/sdlc/receipts6/` — the complete earlier run that built this router — explicitly scoped receipt CRUD out; its baseline line 27 reads "Receipt creation/editing CRUD (deliberately rejected by the earlier foundation process and not part of this set; RCP-8 demands only a listing screen)" (settled_question#64).
- No support tickets, user complaints, or usage metrics were offered; none were found.

## Cost of inaction

Six months on, the product is still a receipts tracker in which receipts cannot be entered through its own API. Every other feature, budgets included, reads a table nothing can fill (settled_question#72).

## Success metrics

- A signed-in caller creates a receipt and sees it appear in the list endpoint's answer, which otherwise answers exactly as it does today. Observable today once the endpoint exists; today the attempt fails outright (from settled_question#73).
- The same caller reads one of their receipts back, corrects a typo in its amount, and deletes it — each step through the API (settled_question#73).
- Each of those requests against a receipt belonging to someone else returns the same uniform 404 the photo endpoints already return (`_NOT_FOUND_DETAIL`), not a leak of another user's data. Measurable today against the existing photo endpoints' behaviour; verifiable for the new endpoints once they exist.
- Deleting a receipt that carries a photo removes the `ReceiptPhoto` row too — the existing test `test_deleting_receipt_takes_its_photo_with_it` in `backend/tests/test_receipts.py` already anticipates this behaviour and can serve as the measuring stick.

## Out of scope

All from settled_question#74:

- No frontend work (the goal forbids it; `ReceiptsStore` / `api/client.ts` untouched).
- No bulk import.
- No currency handling beyond the `Numeric(12,2)` the column already has.
- No change to the photo endpoints beyond what deleting a receipt requires of them.

## Assumptions

- That the receipts table stays exactly as it stands — no migration is needed — is taken from the goal, not verified against a schema inspection in this stage.
- That the goal's reversal of the receipts6 scoping decision (its baseline line 27 deliberately rejected receipt CRUD) is intentional. The goal asserts the operations, so this brief treats it as deliberate, but the person has not confirmed it.
- That the uniform not-found semantics (`_get_owned_receipt`, `_NOT_FOUND_DETAIL`) should extend unchanged to the four new operations, by analogy with the photo endpoints — the goal says so in words; the exact contract is unstated.
- That exactly one account, acting only through the API, exercises this — no import paths, scripts, or other clients were examined.
- That no evidence-gathering (usage metrics, ticket counts) exists beyond what is recorded here; none was searched for in external systems.

## Open questions

- **Reversal of prior scope:** is deliberately undoing the receipts6 run's exclusion of receipt CRUD (baseline line 27) the intended intent? Carried unanswered from the change brief (change_brief#50).
- **Create request shape:** what fields create accepts (amount, description, anything else) and their validation rules — the goal does not say (from the change brief, still unsettled here).
- **Photo-on-create:** does create accept a photo inline, or does the existing one-photo-per-receipt upload endpoint (RCP-15, settled by receipts6) remain the only way to attach one? Unstated.
- **Volume:** how often receipts would be created if the operation existed — no estimate was given, so "how often" in Who is affected is qualitative only.
