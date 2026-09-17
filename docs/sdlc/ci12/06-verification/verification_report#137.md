# Verification — GitHub Actions CI for budget-checker (attempt 2, verifying code_change#112)

Verifying the attempt-3 deliverable: `.github/workflows/ci.yml` (new, 42 lines, re-read in full this attempt) plus the declared scope widening — two `User(...)` constructors in `backend/tests/test_models.py` now passing `hashed_password="x"`.

**Headline: the widening demanded by the gate's run is confirmed present and correct in the tree; nothing else was executed because this stage provides no command-execution tool.** Static reading and the code graph are the evidence here; the gate's own run of the test command (gate_finding#95) is the executable evidence on record.

## Commands run

None executable — no shell tool exists in this stage. Specifically:

- Gate test command `pip3 install -r backend/requirements.txt && PYTHONPATH=.:backend python3 -m pytest backend/tests -v && cd frontend && npm ci && npm test` (settled_question#88) — **not run here**; last executed by the gate itself at gate_finding#95, exit 1, `2 failed, 17 passed`, with the two failures being exactly the `test_models.py` NOT NULL violations.
- `sdlc_check()` — not available in this stage.
- Index refresh (`meridian analyze --index-only --pdg --allow-sdlc-reindex`) and `meridian sdlc verify-links` — **still not run**; third consecutive attempt reporting this (see settled_question#87). The index holds a stale timestamp for `backend/tests/test_models.py` (indexed 2026-09-16, before the two-line edit), so a person or gate must refresh before link coverage is counted.

What I did run, via the code graph: `impact("test_deleting_user_with_dependents_leaves_no_orphaned_records", upstream)` and `impact("test_deleting_user_with_no_dependents_succeeds_cleanly", upstream)` → 0 affected, 0 direct, risk LOW for both, with the index flagging only `test_models.py` itself as stale.

## Results

Verified by reading the current tree:

- **The test fix is in place, exactly as declared.** `backend/tests/test_models.py` line 29 (`test_deleting_user_with_dependents_leaves_no_orphaned_records`) and line 47 (`test_deleting_user_with_no_dependents_succeeds_cleanly`) both read `User(email=..., hashed_password="x")`. These are the two failures gate_finding#95 recorded (`sqlite3.IntegrityError: NOT NULL constraint failed: users.hashed_password`, exit 1). With the fix, the same command should produce 19 passing — predicted, not observed; the gate's next run is the check.
- **The workflow file is unchanged from what code_change#112 describes** (42 lines, re-read): `on: push` + `on: pull_request` (acceptance 1); backend job on Python 3.12, `pip install -r backend/requirements.txt`, `python -m pytest backend/tests -v` with dual-path `PYTHONPATH` (acceptance 2); frontend job on Node 20, `npm ci` against `frontend/package-lock.json`, `npm test` → `vitest run` (acceptance 2). Separate jobs keep a red backend from masking a green frontend (acceptance 3, by construction).
- **The frontend suite is larger than the change brief knew**: besides `frontend/src/App.test.tsx`, six more test files exist (`App.test.tsx`, `components/Layout.test.tsx`, `components/ThemeToggle.test.tsx`, `pages/Landing.test.tsx`, `stores/AuthStore.test.ts`, `stores/HealthStore.test.ts`, `stores/ThemeStore.test.ts`). `vitest run` picks them all up with no workflow change needed — verified from `frontend/package.json`'s `"test": "vitest run"`.
- **Nothing was changed to make a check pass in this stage** — no edits at all. The only edits on record remain the two `hashed_password` arguments from attempt 3, and those are the finding-driven fix, not a test weakened to pass: the cascade-deletion assertions in both tests are untouched and still exercised.
- No lint/static-check step exists in the project (consistent with settled_question#89 "none"); the `chore-acceptance` and `chore-tests-are-real` exit-125/0-score observations from the prior finding are expected for a workflow-YAML change: reverting `ci.yml` fails nothing in-repo, and its proof is the first GitHub Actions run.

## Acceptance coverage

From the change brief (docs/sdlc/ci12/00-triage/change_brief#35.md):

| Scenario | Test |
|---|---|
| 1. Push/PR produces a visible Actions run before review | none — observable only on GitHub after pushing `sdlc/ci12` |
| 2. Clean-checkout install and run of both suites, no local artifacts | gate's test command (settled_question#88); gate run on record shows the backend suite red before the fix, expected green after; true proof is the first Actions run |
| 3. Failing suite shows red and is named | none — follows from separate jobs + `pytest -v` / vitest naming, verified only by reading |

Impact re-checks this attempt: both widened test functions → 0 affected, 0 direct, risk LOW; no product symbol touched.

## Known gaps

- **Everything dynamic remains unverified in this stage.** The fixed suite has not been re-run anywhere yet — the "19 passing" prediction is inference from gate_finding#95's failure list plus the two-line fix, and the gate's next test-command run is what settles it.
- **Index refresh and verify-links remain undone** across three attempts; the index self-reports staleness for `test_models.py`.
- The workflow has **never run on GitHub**. PYTHONPATH dual-path resolution passed the gate's local run (no import errors), but the Actions runner is a different environment; expect a plausible failed-then-fixed first iteration.
- Node 20 and unpinned Python requirement ranges are assumptions on trust, as before.
- Stray sqlite files at root and `backend/` are untracked clutter the workflow does not depend on (verified by reading); cleanup stays out of scope.
