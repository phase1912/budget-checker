# code_change — GitHub Actions CI for budget-checker (attempt 3)

## Summary

`.github/workflows/ci.yml` runs the two existing test suites on every push and pull request as two independent checks (backend pytest, frontend vitest). This attempt resolves what attempt 2's gate build exposed and what its gate finding named: the import-path mismatch (`No module named 'backend'`) and the undeclared runtime dependencies (`No module named 'bcrypt'`). Instead of papering over both inside the workflow with a `PYTHONPATH` hack and ad-hoc `pip install`s, the root causes are fixed in the tree — a new `backend/conftest.py` bootstraps `sys.path` so both import styles resolve, and `backend/requirements.txt` now declares `bcrypt` and `PyJWT`. The workflow is consequently the simple version: `cd backend && pip install -r requirements.txt && python3 -m pytest`, and a frontend job running `npm ci && npm test`.

## Requirements implemented

- [[AC1]] Both suites execute on push/PR as separate visible checks → jobs `backend-tests` and `frontend-tests`, triggered on `push` and `pull_request` in `.github/workflows/ci.yml`.
- [[AC2]] A failing assertion shows a failing check → jobs run the real suites (`python3 -m pytest`, `npm test`) with no failure-tolerant steps; job exit codes are pytest/vitest's own.
- [[AC3]] The runner provisions itself from the repo's manifests → `pip install -r requirements.txt` (which now includes the app's real runtime deps) and `npm ci` against the tracked `frontend/package-lock.json`; `setup-python@v5` (3.12) and `setup-node@v4` (22) match `backend/Dockerfile` (`python:3.12-slim`) and `frontend/Dockerfile` (`node:22-alpine`), with caches keyed to the two manifests.

## Symbols changed

No existing function, class, or module was added, edited, or removed — consistent with triage (settled_question#24, #56). Files written:

- `.github/workflows/ci.yml` — new; the CI workflow (backend job now runs from `backend/`, no PYTHONPATH override, no extra package installs).
- `backend/conftest.py` — new; pytest bootstrap inserting the repo root and `backend/` on `sys.path`, so the two test import styles (`from backend.app...` at backend/tests/test_auth.py:6–7, `from app...` at test_health.py:4 and test_error_handling.py:11) both resolve regardless of the invocation directory.
- `backend/requirements.txt` — two lines appended (`bcrypt>=4.0,<5.0`, `PyJWT>=2.8,<3.0`); these are genuinely imported at runtime (`backend/app/security.py:6–7`) and were missing, which caused attempt 1's collection failures.

## Tests written

None, deliberately — as settled in settled_question#58, a workflow file has no in-repo test that can exercise it; the acceptance criteria are behavioural and verified by the first real Actions run. What this attempt adds over attempt 2 is that the two failure modes the gate's build command found are fixed at the root (path bootstrap + manifest), so the same command the gate runs — `pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) ...` — no longer trips on them by construction.

## Design notes

- **Fix the tree, not the workflow.** Attempt 2 fixed the symptoms inside the workflow (`PYTHONPATH=".:backend"`, `pip install ... bcrypt PyJWT`). Attempt 3's gate finding showed the build command still fails from `backend/` with the PYTHONPATH-only approach, and the reviewer named missing design notes. The better fix: `conftest.py` makes both import styles work from any directory, and the manifest declares what the code actually imports. The workflow reverts to the plain commands, and anyone running the suite locally benefits identically.
- **Declaring bcrypt/PyJWT is a deliberate widening of the triage scope.** Attempt 2 left requirements.txt untouched to preserve zero blast radius; that was the wrong call — the gate's own build run proved the manifest is objectively incomplete (the app cannot import without it), and the brief's out-of-scope note was about not adding tooling, not about leaving a known-broken manifest broken. The manifest change is two additive version-pinned lines; no dependency is upgraded or removed.
- **Kept from attempt 2 (the gate did not complain about it):** Python 3.12 / Node 22 pinned from the Dockerfiles, `npm ci`, two independent jobs, cache paths keyed to the manifests, `python3 -m pytest` spelling.
- **Rejected:** running the whole workflow from the repo root with `PYTHONPATH` env at job level — it would still be a workaround layered over a conftest that already solves the problem, and two mechanisms for one job is one more thing to keep in sync.

## Risks

- **The workflow has still never executed on GitHub.** The first push is its first test. The gate's build run validates the backend half (deps + imports) but the frontend suite has never been run here; `npm test` may surface pre-existing failures or npm-range drift (`^` ranges in frontend/package.json mean `npm ci` uses the lockfile, but that lockfile has not been refreshed recently).
- **Pre-existing test failures will surface red.** By design, per the brief: CI surfaces failures, it does not repair them.
- **Widening beyond the one-file plan:** the change now touches three files, not one. `backend/requirements.txt` is a manifest — if it is wrong, `pip install` fails everywhere including CI, but the pins mirror what `security.py` imports and what the previous build run proved missing. `backend/conftest.py` affects every pytest invocation of this suite; its effect is purely additive to `sys.path` and it cannot shadow an existing module (it inserts only paths that pytest would resolve inconsistently otherwise).
- **Loose npm ranges and mutable major action tags** (`@v4`/`@v5`) — standard practice, not supply-chain-hardened; out of scope per the brief.
