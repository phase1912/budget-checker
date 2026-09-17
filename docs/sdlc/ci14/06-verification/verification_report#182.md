# Verification — GitHub Actions CI for budget-checker (stage_instance#166, code_change#153)

## Commands run

This environment exposes repository reads only — no shell — so no command was executed by me. Every claim below is verified by reading the tree; the executable verdict is the engine's own gate run of the settled commands (`pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm run build && npm test` per settled_question#55, and the same chain ending in `npm test` per settled_question#102).

On the prior finding: the lint question was answered "none" and a person was asked to confirm. Confirming from the tree: there is no configured linter anywhere — frontend/package.json has no `lint` script (only dev/build/preview/test), backend/requirements.txt declares no lint tool, and no ruff/flake8/mypy/pyproject configuration file exists. The only ruff traces on disk are `.ruff_cache/` and third-party files inside the untracked `.venv/` — leftovers of a one-off run, not project adoption; a tracked file naming the tool exists nowhere. "None" stands.

## Results

Static verification of the accepted tree (code_change#153):

- `.github/workflows/ci.yml` — verified on disk, 41 lines: `push` + `pull_request` triggers, two independent jobs (`backend-tests` pytest, `frontend-tests` vitest), Python 3.12 / Node 22 matching the Dockerfiles, pip/npm caches keyed to `backend/requirements.txt` and `frontend/package-lock.json`, real `python3 -m pytest` and `npm test` steps with no `continue-on-error` or failure tolerance anywhere.
- `backend/tests/test_models.py` — verified on disk: `_make_user` helper (lines 23–25) supplying `hashed_password="test-hash"`; both previously-failing deletion tests (`test_deleting_user_with_dependents_leaves_no_orphaned_records` line 32, `test_deleting_user_with_no_dependents_succeeds_cleanly` line 51) create users through it. Root cause confirmed in the tree: `hashed_password = Column(String, nullable=False)` at backend/app/models.py:25.
- `backend/requirements.txt` — verified, 9 entries including `bcrypt`, `PyJWT`, `email-validator` (line 9) — the dependency whose absence sank the attempt-3 gate build on three test modules.
- `backend/conftest.py` — verified: sys.path bootstrap covering both import styles (`from backend.app...` and `from app...`) from any invocation directory.
- `.gitignore` line 10 is `*.db`, so the stale sqlite artifacts (`backend/budget_checker.db`, `test_auth*.db`) will not appear in a fresh Actions checkout.

Executable evidence, prior attempts: the attempt-4 gate log and gate_finding#135's run both show the backend suite reaching **17 passed / 2 failed**, the only failures being exactly the two tests the `_make_user` fix targets, with all import and dependency errors gone. **The post-fix tree has not been executed by anyone in this run** — the engine's gate run is the pending arbiter; 19/19 is expected, not claimed as seen.

No test was changed to make anything pass in this stage. The only test change in the whole work (accepted at gate_finding#43 and re-argued successfully at gate_finding#156's stage) was the two `test_models.py` fixtures moved onto `_make_user`, because the old fixtures inserted a row the schema forbids — the model was right, the fixtures were wrong.

## Acceptance coverage

| Scenario | Test |
|---|---|
| AC1 — both suites run on every push and PR as visible GitHub checks | none in-repo — provable only by the first real Actions run of branch `sdlc/ci14` (base `master`) |
| AC2 — a failing assertion shows a failing check | demonstrated end to end twice by the gates' own builds (pytest failing the build on its own red tests, gate_finding#135); GitHub-side visibility needs the first Actions run |
| AC3 — a fresh runner needs no manual setup | backend half proven by the gate runs collecting and running all 19 tests from the manifest alone; frontend half unproven |
| Backend pytest suite passes | backend/tests/ — `python3 -m pytest`, pending the engine's run of the post-fix tree |
| Frontend vitest suite passes | frontend/src/*.test.* via `npm test` — never yet executed in any recorded run |

## Known gaps

- **Post-fix execution:** no shell here; the engine's gate run of the test command is the only executable verdict, and this report precedes it.
- **The workflow has never run on GitHub** — AC1, the visibility half of AC2, the frontend job, and `cache-dependency-path` behaviour all land on the first real push.
- **The frontend suite and `npm run build` (tsc + vite) have never completed** in any recorded run; every earlier failure short-circuited at backend pytest. Pre-existing frontend failures, if any, will surface red — per the brief, surfaced, not repaired.
- **Python version drift:** gate hosts run 3.14 (deprecation warnings visible in every log); CI pins 3.12 per backend/Dockerfile. The workflow's own 3.12 run is untested here.
- **No in-repo test covers the workflow or conftest** — structural to a workflow-only chore, as the previous verification reviewer scored it; nothing in this repo can execute a GitHub Actions workflow.
- **Lint:** none exists to run — confirmed above from the manifest and configuration files, not from the absence of cache directories.
