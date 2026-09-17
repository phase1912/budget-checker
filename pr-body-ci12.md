# CI: run backend pytest and frontend vitest suites on GitHub Actions

## Summary

This adds the repository's first CI pipeline: `.github/workflows/ci.yml`, a GitHub Actions workflow that runs the existing automated test suites on every push and every pull request, so pass/fail is visible in GitHub before anyone reviews a change. It has two independent jobs — `backend-tests` (Python 3.12, installs `backend/requirements.txt`, runs `python -m pytest backend/tests -v` with a dual-path `PYTHONPATH` covering both import styles used in the tests) and `frontend-tests` (Node 20, `npm ci` against the lockfile, `npm test` → `vitest run`). No application code changes.

One deliberate, declared scope widening beyond the change brief: two tests in `backend/tests/test_models.py` (`test_deleting_user_with_dependents_leaves_no_orphaned_records`, `test_deleting_user_with_no_dependents_succeeds_cleanly`) constructed `User(email=...)` without `hashed_password`, violating `models.py`'s `nullable=False` column and raising `sqlite3.IntegrityError` on any clean run (`2 failed, 17 passed` — see gate_finding#95). Each now passes `hashed_password="x"`. Without this fix the new CI's backend job would be red on its first run by construction. The cascade-deletion assertions in both tests are unchanged.

## Requirements covered

- [[goal#7]] — run the existing frontend and backend automated test suites on every push and PR, visible in GitHub before review.
- Acceptance 1 (change brief docs/sdlc/ci12/00-triage/change_brief#35): `on: push` + `on: pull_request`; jobs named "Backend (pytest)" and "Frontend (vitest)" appear as named checks.
- Acceptance 2: clean-checkout install from `backend/requirements.txt` and `frontend/package-lock.json` (`npm ci`); no reliance on local artifacts (stray sqlite files, stale `__pycache__` conftest).
- Acceptance 3: separate jobs plus `pytest -v`/vitest naming mean a failing suite shows red and names itself.

## Testing

- Verified by reading: workflow matches actual test import styles (`app.*` in test_health/test_error_handling/test_models, `backend.app.*` in test_auth — both satisfied by the dual-path PYTHONPATH), `npm test` → `vitest run` (frontend/package.json), lockfile present for `npm ci`, Python 3.12 matches `backend/Dockerfile`'s pin.
- The gate ran the equivalent test command locally (`pip3 install -r backend/requirements.txt && PYTHONPATH=.:backend python3 -m pytest backend/tests -v && cd frontend && npm ci && npm test`): before the test fix it recorded `2 failed, 17 passed` with the two NOT NULL violations this PR fixes; post-fix, both tests' constructors satisfy the model and 19 passing is expected on the first Actions run.
- Impact analysis on every changed symbol: 0 affected, 0 direct, LOW risk (both test functions are leaves; `ci.yml` is referenced by nothing). The workflow itself has never run on GitHub — the first Actions run on this PR is its real proof.

## Risk and blast radius

- Direct dependents outside the diff: none. Only product-adjacent edit is the two one-line test constructors; assertions untouched, so nothing that previously passed is weakened.
- Least-tested element: the dual-path `PYTHONPATH` on a clean ubuntu-latest runner — worked in the local gate run (no import errors) but never on Actions; a third import style would break it. A failed-then-fixed first iteration is plausible and is verification working, not a defect.
- Python requirement ranges are open (`pytest>=8.3,<9.0` etc.), so CI resolves fresh versions each run; Node 20 is an assumption (nothing in the repo pins Node). The `test_auth_unit.db` created at the runner's working directory is fresh per run and harmless.
- After merge, watch the first Actions run on `master` for backend-job environment differences and keep an eye on upstream releases inside the unpinned ranges.
