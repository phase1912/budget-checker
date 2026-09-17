# Verification — GitHub Actions CI for budget-checker

## Commands run

This environment exposes repository reads only — no shell — so I could not execute the test command myself. The executable evidence in hand is the gate's own run of the same command (from gate_finding#77 / run_journal#19): the attempt-4 gate build ran `pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm run build && npm test` and the backend pytest step reached **17 passed / 2 failed**, the only failures being the two `test_models.py` fixture defects this change fixes. That run predates the `_make_user` fix, so **the post-fix suite has not been executed by anyone in this run — the engine's own gate run is the proof that is pending.**

What I ran here was a full static verification of the change against the tree:

| Check | Result |
|---|---|
| `.github/workflows/ci.yml` exists, matches code_change#76's description | ✅ verified on disk (two jobs, `push`+`pull_request`, Python 3.12 / Node 22, `npm ci`, no failure-tolerant steps) |
| `backend/requirements.txt` lines 8–10 = bcrypt, PyJWT, email-validator | ✅ verified on disk |
| `backend/conftest.py` sys.path bootstrap present | ✅ verified on disk |
| `_make_user` helper in `backend/tests/test_models.py`, supplies `hashed_password="test-hash"` to both previously-failing tests | ✅ verified at backend/tests/test_models.py:23–28, used at :41 and :54 |
| `hashed_password` really is `nullable=False` (the fixture defect's root cause) | ✅ backend/app/models.py:20 |
| Stale sqlite artifacts gitignored | ✅ `.gitignore:10` = `*.db`, which covers `backend/budget_checker.db` and `test_auth*.db` at any depth |
| No lint command exists in the project | ✅ none declared (no ruff/flake8/mypy config tracked; consistent with settled_question#103 "none") |

## Results

- **Backend suite:** not re-run post-fix. Pre-fix state per the attempt-4 gate log: 17 passed, 2 failed on `NOT NULL constraint failed: users.hashed_password` — exactly the two tests the `_make_user` fix targets, and both now supply the non-nullable column. I expect 19/19 but **cannot claim it as run**; the engine's gate run of `pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm test` is the arbiter.
- **Frontend suite:** never executed in any gate run (every previous failure short-circuited at backend pytest). `npm test` = `vitest run` (frontend/package.json:10); test files exist (App.test.tsx, Layout.test.tsx, ThemeToggle.test.tsx, Landing.test.tsx, AuthStore.test.ts, HealthStore.test.ts). Unverified — could surface pre-existing failures, which the brief says to surface, not repair.
- **No test was changed to make anything pass in this stage.** The only test change in the whole work (already accepted at the implementation gate) was the two `test_models.py` fixtures moved onto `_make_user`, because the old fixtures inserted a row the schema forbids (backend/app/models.py:20) — the model was right, the fixtures were wrong.

## Acceptance coverage

| Scenario | Test |
|---|---|
| AC1 — both suites run on every push and PR as visible checks | none in-repo — provable only by the first real GitHub Actions run of `.github/workflows/ci.yml` |
| AC2 — a failing assertion shows a failing check | partially: the attempt-4 gate run demonstrated pytest failing the build end-to-end; GitHub-side visibility still needs the first Actions run |
| AC3 — a fresh runner needs no manual setup | backend half proven by the attempt-4 gate run collecting and running all 19 tests from the manifest alone; frontend half unproven |
| Backend pytest suite passes | backend/tests/ — `python3 -m pytest`, pending the engine's run |
| Frontend vitest suite passes | frontend/src/*.test.* — `npm test`, never yet run |

## Known gaps

- **The post-fix tree has never been executed.** I have no shell; the engine's own run of the test command is the only executable verdict, and this report is written before it.
- **The workflow has never run on GitHub.** AC1, the visibility half of AC2, the frontend job, and the `cache-dependency-path` configuration all land on the first real push (branch `sdlc/ci14`, base `master`).
- **`npm run build` (tsc + vite) has never completed** in any recorded run — earlier attempts short-circuited before reaching it.
- **Python version drift:** the gate host runs Python 3.14; CI pins 3.12 per backend/Dockerfile. Package behaviour may differ between them; 3.14 deprecation warnings were visible in the gate log.
- **No new tests were written for the workflow or conftest** — by design (settled_question#58/#106); nothing in this repo can execute a GitHub Actions workflow.
