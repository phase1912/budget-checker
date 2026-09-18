# Add GitHub Actions CI running backend pytest and frontend vitest on push/PR

## Summary

The repository had no CI at all — no `.github/` directory, no workflow, nothing. This change adds `.github/workflows/ci.yml`, which on every push and pull request runs the two existing test suites as two independent, visible checks: `backend-tests` (Python 3.12, matching `backend/Dockerfile`, `pip install -r requirements.txt` then `python3 -m pytest` in `backend/`) and `frontend-tests` (Node 22, matching `frontend/Dockerfile`, `npm ci` against the tracked lockfile then `npm test` = `vitest run`). Neither job tolerates failure — each exits with pytest/vitest's own exit code, so a red test is a red check in GitHub before anyone reviews.

Getting to a suite that a fresh runner can actually run required three supporting fixes, each proven necessary by a build run of this exact tree, not assumed:

- `backend/requirements.txt` was incomplete — the app imports `bcrypt` and `PyJWT` (`backend/app/security.py:6–7`) and needs `email-validator` for `EmailStr` (`backend/app/schemas.py`), none of which were declared. All three are appended.
- `backend/conftest.py` (new) bootstraps `sys.path` so both test import styles resolve (`from backend.app...` in `test_auth.py`, `from app...` in `test_health.py`/`test_error_handling.py`/`test_models.py`).
- `backend/tests/test_models.py` — the two user-deletion tests constructed `User(email=...)` without `hashed_password`, which `backend/app/models.py` declares `nullable=False`; both provably failed with `NOT NULL constraint failed: users.hashed_password` in two independent build runs (17 passed / 2 failed each time). A small `_make_user` helper now supplies the required field. The model is right; the fixtures were constructing an invalid row.

No application code changes.

## Requirements covered

- [[AC1]] Both suites execute on every push and pull request as separate visible GitHub checks — jobs `backend-tests` and `frontend-tests`, triggered on `push` and `pull_request` in `.github/workflows/ci.yml`. GitHub-side visibility lands on the first real Actions run of this branch.
- [[AC2]] A failing assertion shows a failing check — both jobs run the real suites with no `continue-on-error`; demonstrated end-to-end by the gate's own builds failing on pytest's own exit code (17 passed / 2 failed on the pre-fixture-fix tree).
- [[AC3]] A fresh runner needs no manual setup — the completed `backend/requirements.txt`, the `conftest.py` path bootstrap, `npm ci` against the tracked lockfile, and Python 3.12 / Node 22 pinned from the Dockerfiles.

## Testing

The gate's build of this tree ran `pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm run build && npm test`. Earlier attempts' logs isolated every failure this change fixes: `ModuleNotFoundError: email_validator` (three test modules, pre-manifest-fix), `No module named 'backend'` (pre-conftest), and the two `NOT NULL constraint failed: users.hashed_password` fixture failures. All dependencies and imports now resolve; the two previously-failing tests create valid rows via `_make_user`. Verification and review confirmed every changed file on disk against this evidence trail; the review verdict was READY.

## Risk and blast radius

- No existing symbol is modified; `impact` on `create_app` (the most-connected symbol the suite exercises) shows 1 direct dependent, risk LOW — invoked, not changed. Nothing that previously worked stops working; the conftest only adds paths.
- The first real GitHub Actions run is the first execution of the workflow itself and of the frontend suite (`npm ci && npm test` has never completed in any recorded run). Pre-existing frontend failures, if any, will land red on an otherwise-green backend job — by design: CI surfaces failures, it does not repair them.
- Python drift: gate evidence ran on 3.14; CI pins 3.12 per the backend Dockerfile. The broad dependency pins make this unlikely to bite, but the 3.12 run is untested until the first push.
- Low: the pip cache key (`cache: pip`) is never read because the install step uses `--no-cache-dir` — dead configuration, cosmetic only.
- Watch after merge: the first Actions run's two checks, and that subsequent PRs show them.
