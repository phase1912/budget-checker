# Change brief: GitHub Actions CI for budget-checker

## What I asked the code graph and what came back

- `query("GitHub Actions continuous integration CI workflow")` → 0 hits: the repository has never had CI, in code or in documents.
- `impact("App", upstream)` → found: 2 symbols named `App` (frontend/src/App.tsx among them), 0 affected, 0 direct, risk LOW — the frontend entry component has no dependents recorded.
- `impact("conftest", upstream)` → found: false — the pytest fixture setup is not held as a graph symbol.
- `impact("test_health", upstream)` → found: false — the backend test modules are not held as graph symbols.
- `query("backend automated tests pytest")` → 12 hits, all backend test files (`backend/tests/test_error_handling.py` and its symbols) plus unrelated SDLC documents; no CI-related symbols.
- `impact("_build_test_app", upstream)` → found: backend/tests/test_error_handling.py, 0 affected, 0 direct, risk LOW.
- `impact("test_database_unavailable_produces_generic_error_response", upstream)` → found: backend/tests/test_error_handling.py, 0 affected, 0 direct, risk LOW.

## What changes

Every push and every pull request automatically runs the existing backend pytest suite and the existing frontend vitest suite, and the pass/fail result is visible in GitHub before anyone reviews the change. No application code changes.

## Kind of change

chore

## Why this kind

The kind decision is recorded in the triage answers: the maker recommended chore (settled_question#25) and the decision on the change-kind question was chore (settled_question#30, change_kind#31), matching that recommendation. The case: this is a first-time infrastructure addition — there is no `.github/` directory at all (root listing confirms), and the graph's `query` for CI returned zero hits, so no public interface, stored schema, or serialized format moves. The suites the workflow will invoke already exist and already have entry points: `pytest` against `backend/tests/` (test_auth.py, test_error_handling.py, test_health.py, test_models.py) and `"test": "vitest run"` in frontend/package.json (line 9). Impact analysis on the symbols the graph does hold (`App`, `_build_test_app`, and the error-handling test) all returned 0 affected, 0 direct, LOW risk — the test modules are leaf nodes. The one argument against chore: CI must correctly stand up both a Python environment and a Node environment from scratch, and there is evidence a backend test previously failed (`.pytest_cache` records a last-failed entry for `test_auth.py::test_login_success_and_me`), so the first CI run may be red. That risk is flagged, but diagnosing an already-existing failing test is separate work from adding the workflow; the shape of the work remains a bounded infrastructure change.

## Expected blast radius

- `.github/workflows/ci.yml` (new file) — touches no existing symbol; a `list_files` of the repository root confirms no `.github/` directory exists today.
- `backend/tests/*` (invoked, not modified) — graph: 0 affected, 0 direct, LOW risk for every held symbol; `impact` returned found: false for the test modules themselves, i.e. nothing depends on them.
- `frontend/src/App.tsx` (`App`) — 0 affected, 0 direct, LOW risk.
- Root `conftest.py` (invoked via pytest) — not held as a graph symbol, so its dependents are unknown to the graph; by inspection it only sets backend paths for the test run.
- Practical CI-configuration risks the graph cannot see: the stray local sqlite files (`backend/budget_checker.db`, `backend/test_auth_unit.db`, `budget_checker.db`, `test_auth.db`, `test_auth_unit.db`) at the repo root — CI setup must not depend on them existing.

## Acceptance criteria

1. Pushing a commit (or opening a pull request) produces a GitHub Actions run visible on the commit/PR before review.
2. The run installs Python dependencies from backend/requirements.txt and Node dependencies from frontend/package-lock.json and executes `pytest` and `vitest run` without needing any local artifact (no pre-existing sqlite db, no local venv).
3. If either suite fails, the Actions run shows red and names the failing suite, rather than passing silently.

## Out of scope

No linting, formatting, type-check steps, docker builds, deployment, caching optimisation, or fixing the previously failing `test_auth.py::test_login_success_and_me` test — CI surfaces failures; it does not fix them.

## Open questions

- Whether the first CI run is red because of the previously failed auth test is unknown until the workflow runs; if so, that becomes a follow-up bugfix with its own triage.
- Python version pin for the CI runner is not recorded anywhere in the repository (no `.python-version` found in the root listing); the run will use a pinned version chosen at implementation time.