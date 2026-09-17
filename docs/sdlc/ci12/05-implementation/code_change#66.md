# Code change: GitHub Actions CI for budget-checker

## Summary

Added `.github/workflows/ci.yml`, a GitHub Actions workflow with two independent jobs that run the repository's existing automated test suites on every push and every pull request: `backend-tests` installs `backend/requirements.txt` and runs `python -m pytest backend/tests -v`, and `frontend-tests` runs `npm ci` and `npm test` (`vitest run`, per frontend/package.json line 9) in `frontend/`. No application code, test file, or existing configuration was modified. Failures surface as red checks on the commit/PR, naming the failing suite; CI deliberately does not fix or mask the previously failing `test_auth.py::test_login_success_and_me` recorded in `.pytest_cache`.

## Requirements implemented

- Acceptance 1 (run on every push and PR, visible before review): workflow `on: push` and `on: pull_request` triggers in `.github/workflows/ci.yml`; job names "Backend (pytest)" and "Frontend (vitest)" appear as checks.
- Acceptance 2 (installs dependencies and runs both suites from a clean checkout, no local artifacts): `pip install -r backend/requirements.txt` (pins pytest>=8.3, httpx, declared in backend/requirements.txt lines 5–6) and `npm ci` against `frontend/package-lock.json`; the workflow never touches the stray sqlite files (`budget_checker.db`, `test_auth.db`, `test_auth_unit.db`, `backend/budget_checker.db`, `backend/test_auth_unit.db`) — pytest's sqlite tests create their own (in-memory or `./test_auth_unit.db` at the working directory).
- Acceptance 3 (failing suite shows red and is named): separate jobs, so a red backend run does not hide a green frontend one; pytest `-v` and vitest both name failing tests in the log.

## Symbols changed

None — no function, class, or module was edited, added, or removed. The change is one new file:

- `.github/workflows/ci.yml` (new) — the CI workflow.

This matches the triage answer (settled_question#24): expected to touch only new files; impact analysis already on record showed every held symbol the suites exercise (`App`, `_build_test_app`, `test_database_unavailable_produces_generic_error_response`) with 0 affected, 0 direct, LOW risk, and `found: false` for the test modules and conftest themselves — leaf nodes.

## Design notes

- **Import paths — the one real design decision.** The backend tests are split: `test_health.py` and `test_error_handling.py` import `from app.main import ...` (backend/ on the path), while `test_auth.py` imports `from backend.app.main import ...` (repo root on the path). Neither style is fully satisfiable from one working directory. The root `conftest.py` that the local machine used is not in the working tree (read_file: found: false; only its stale `__pycache__` bytecode remains), so it cannot be relied on. Rejected: rewriting test imports to one style (widens the change into application/test code beyond what the plan declared) and running pytest twice from two directories (duplicates setup and still risks double collection). Chosen: run pytest once from the repo root with `PYTHONPATH` set to both the workspace root and `workspace/backend`, satisfying both import styles in a single job.
- **Python version.** No `.python-version` exists anywhere in the repo; pinned `setup-python` to 3.12 to match `backend/Dockerfile`'s `FROM python:3.12-slim`, which is the only version pin in the repository.
- **npm ci, not npm install.** `frontend/package-lock.json` exists, so the lockfile-exact install is the reproducible choice; npm cache is keyed on that lockfile path.
- **Node version.** Node 20, the current ubuntu-latest default LTS; the repo records no Node pin to match, so this is an assumption noted under Risks.
- **Out of scope, per the change brief:** no lint/format/type-check steps, no docker builds, no caching beyond setup-node's built-in npm cache, and no attempt to fix `test_auth.py::test_login_success_and_me`. If that test is genuinely red, CI shows it red — which is the point of the workflow, and becomes a follow-up bugfix.

## Risks

- **The first CI run may be red.** `.pytest_cache/v/cache/lastfailed` records `backend/tests/test_auth.py::test_login_success_and_me` as previously failed. If it fails in a clean environment, the workflow is working as intended but the check is red; that is a separate diagnosis, not a defect in this change.
- **Unverifiable here.** No command execution is available in this stage, so the workflow has never run. The `PYTHONPATH` double-path trick is the least-tested part: it satisfies both observed import styles, but a third import style (e.g. a bare `import models`) would fail. Pytest rootdir/conftest discovery from the repo root was also not exercised locally.
- **Stray sqlite files.** `test_auth.py` writes `./test_auth_unit.db` relative to the working directory (the repo root in this setup). This works — the file is created fresh — but CI will not clean it up, and a future change adding working-directory-dependent paths would break. The existing stray dbs at root and backend/ are ignored by the workflow but are untracked-local clutter the repository carries.
- **Node 20 pin is an assumption**; nothing in the repo pins Node, and a future lockfile requiring a newer Node would need this bumped.
- **pip, not a locked environment:** `backend/requirements.txt` uses ranges (`pytest>=8.3,<9.0` etc.), so CI resolves fresh versions on each run; a future upstream release inside those ranges could turn the suite red without any repo change.