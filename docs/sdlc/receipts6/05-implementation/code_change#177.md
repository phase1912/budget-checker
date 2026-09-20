# Code change — Receipt photos on expenses (attempt 3)

## Summary

The previous attempt (code_change#177) left exactly two failing tests, both in `frontend/src/pages/ReceiptsPage.test.tsx`: the RCP-14 photo-presentation test and the RCP-15 UI-side test built on it. The gate's own build run showed both dying at `findByRole('img')` — Testing Library could not find any `role="img"`. This attempt fixes that root cause in one file, `frontend/src/setupTests.ts`, and touches no production code.

Root cause, found by reading the path the tests exercise: `ReceiptEntry` (frontend/src/pages/ReceiptsPage.tsx) loads the photo through `receiptsStore.loadPhoto(receipt.id)`, and `loadPhoto` (frontend/src/stores/ReceiptsStore.ts:45) calls `URL.createObjectURL(blob)`. The jsdom/happy-dom environment this suite runs in does not implement `URL.createObjectURL`, so the call throws a `TypeError`. That throw lands in `loadPhoto`'s bare `catch` (ReceiptsStore.ts:49), which is written deliberately for RCP-12 — "a missing photo is an ordinary state, not a fault" — and so swallows this environment failure exactly as it should swallow a real 404. Result: `photoUrls` never gets an entry, the `{photoUrl && <img ...>}` branch never renders, and both tests time out looking for an image. The production code is correct; the test environment lacks a browser API the feature legitimately uses.

The fix: `setupTests.ts` now installs a stub for `URL.createObjectURL` (returning a stable fake URL) and `URL.revokeObjectURL` (no-op) in a `beforeAll`, guarded by `typeof ... !== 'function'` so a future environment that implements them for real is left alone. The tests assert on rendering and alt text, not on the URL's contents, so a stable fake is sufficient. Stubbing in the shared setup rather than the test file means any future test that renders a receipt with a photo gets the same working environment for free.

Everything else is unchanged from attempt 2: the backend suite passed the gate's run (20 backend tests green), and the other 20 frontend tests passed. This attempt's whole job is turning those last 2 red tests green by giving them the API their component needs.

## Requirements implemented

All requirements below were implemented in earlier attempts of this same diff and are declared here so the note remains the complete record; the new work in this attempt serves [[RCP-14]] and [[INV-NFR-3]]'s testability.

- [[RCP-14]] / [[RCP-16]] the photo presents from the receipt's own entry, bytes fetched with the bearer token and rendered locally — now actually testable: the `URL.createObjectURL` stub in `frontend/src/setupTests.ts` lets `ReceiptsStore.loadPhoto` complete, so `ReceiptEntry` renders the `<img>` the two previously failing tests assert on.
- [[RCP-15]] UI side — the "no second attach once the photo exists" assertion is built on the same now-rendering `<img>` as its wait condition.
- [[INV-NFR-3]] alt text naming the receipt — asserted by the RCP-14 test, which can now run to its assertions instead of dying at the query.
- [[RCP-1]] … [[RCP-13]], [[INV-NFR-1]], [[INV-NFR-2]], [[INV-NFR-4]], [[INV-NFR-5]] — unchanged from attempt 2; see the symbol list below. The gate's attempt-2 build run shows the backend suite (test_models, test_auth, test_health, test_error_handling, test_receipts) passing and 20 of 22 frontend tests passing; the 2 failures are what this attempt fixes.

## Symbols changed

Edited in this attempt:

- `frontend/src/setupTests.ts` (changed) — added a `beforeAll` installing `URL.createObjectURL` / `URL.revokeObjectURL` stubs when the DOM environment lacks them, with the reasoning in a comment; `import { vi } from 'vitest'` added.

Unchanged from attempt 2, declared for the blast-radius check (the full feature diff, all written in this run):

- `ReceiptPhoto` (added) and `Receipt.photo` relationship (added) — backend/app/models.py
- `list_receipts`, `upload_receipt_photo`, `get_receipt_photo`, `_get_owned_receipt`, `_sniff_content_type` (added) — backend/app/routers/receipts.py
- `create_app` (changed: includes `receipts.router`) — backend/app/main.py
- `python-multipart` (added to requirements) — backend/requirements.txt
- `fetchReceipts`, `uploadReceiptPhoto`, `fetchReceiptPhotoBytes`, `ReceiptListItem` (added) — frontend/src/api/client.ts
- `ReceiptsStore` (added; `loadPhoto` at ReceiptsStore.ts:38-52 is the method the stub unblocks) — frontend/src/stores/ReceiptsStore.ts
- `ReceiptsPage`, `ReceiptEntry`, `photoAltText`, `formatAmount` (added) — frontend/src/pages/ReceiptsPage.tsx
- receipts route (added) — frontend/src/App.tsx
- `ReceiptsPage.test.tsx` (added) — frontend/src/pages/
- `backend/tests/test_receipts.py` (added; dedicated FastAPI instance, `expire_on_commit=False`, 13 tests) — backend/tests/

## Design notes

- **Stub in setup, not a change to `loadPhoto`'s catch.** The obvious alternative was making `loadPhoto`'s catch narrower — e.g. only swallowing fetch failures, not TypeErrors — so the missing environment API would surface. Rejected: it couples a browser-API quirk of the test environment into production error handling that RCP-12 genuinely needs broad (a missing photo IS an ordinary state), and the right place to provide a browser API the component relies on is the test environment, which is what `setupTests.ts` exists for.
- **Guarded `typeof` checks rather than unconditional assignment.** If jsdom gains `createObjectURL` later, the stub steps aside rather than clobbering a real implementation with a fake — the tests keep passing either way because they never inspect the URL value.
- **Stable fake URL rather than a real blob.** Happy-path correctness of `createObjectURL` is the browser's concern, not this suite's; the assertions under test are rendering, alt text (INV-NFR-3), and the control's disappearance (RCP-15 UI).
- **No production code changed** — the gate's run attributed all 2 failures to the rendering path, and reading that path confirmed the defect was the environment, not the component or the store.

## Risks

- **Unrun by me — no shell in this stage.** The stub addresses the exact failure the gate's attempt-2 output shows (both tests dying at `findByRole('img')` because `createObjectURL` throws inside `loadPhoto`'s catch), but the exit code that proves it is the gate's next run. The one assumption in the stub: the fake URL string is enough for the component — it is only passed to `<img src>`, never parsed.
- **If the environment DOES implement `createObjectURL`, the guard skips the stub** — then the tests should pass for the real reason. Either branch of the guard should turn the tests green; the failure mode left is an environment where the function exists but throws, which no known version of jsdom or happy-dom exhibits.
- **`vi` imported into setupTests.ts is only used inside the guarded branch** — if the guard skips, the import is unused at runtime; harmless, kept for the branch that needs it.
- **Carried from attempt 2, still open by decision:** the 5 MB-vs-10-second-timeout bound-upload test belongs to the compose stack, not this suite (baseline open question 1); timeout-at-commit and refusal latency (open questions 2-3) remain untested; RCP-13's scenario gap in the acceptance spec is a document amendment, not code.
- **Import-order safety is structural, not enforced** — each test module owns its app instance (backend) and the frontend tests mock at the client boundary; nothing prevents a future module from reintroducing shared mutable state.
