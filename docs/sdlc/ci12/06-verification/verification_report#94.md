# Verification — GitHub Actions CI for budget-checker

Verifying code_change#66: `.github/workflows/ci.yml` (new, 42 lines), two jobs — `backend-tests` ("Backend (pytest)") and `frontend-tests` ("Frontend (vitest)") — on `push` and `pull_request`.

**Headline: nothing was executed.** This stage provides no command-execution tool, so no check below was run live. Every statement is either a static reading of the repository or a correction of a prior claim. Where the gate or a person must run something, it is named under Known gaps.

## Commands run

None. No command could be run; there is no execution tool in this stage. Specifically not run:

- The gate's test command (settled_question#88): `pip3 install -r backend/requirements.txt && PYTHONPATH=.:backend python3 -m pytest backend/tests -v && cd frontend && npm ci && npm test` — exit status: not run.
- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` / `meridian sdlc verify-links` — not run; this was already reported as NOT DONE in settled_question#87 and remains undone.
- The build command (settled_question#60) — not run.
- `sdlc_check()` — not available as a tool in this stage.

## Results

What I could do was verify the change against the repository by reading it:

- `.github/workflows/ci.yml` exists as described (verified by read_file, 42 lines): `on: push` + `on: pull_request` (acceptance 1); backend job does `pip install -r backend/requirements.txt` then `python -m pytest backend/tests -v` with `PYTHONPATH` set to workspace root and `workspace/backend`; frontend job does `npm ci` then `npm test` in `frontend/` with Node 20 and lockfile-keyed npm cache (acceptance 2). Separate jobs mean a red backend does not mask a green frontend, and pytest `-v` / vitest both name failures (acceptance 3) — but acceptance 3's red-result behaviour is by construction, not observation.
- The PYTHONPATH design is consistent with the tests as they actually stand: `test_health.py` and `test_error_handling.py` and `test_models.py` import `from app...` (needs `backend/` on the path); `test_auth.py` imports `from backend.app...` (needs the root on the path). The workflow's two-entry PYTHONPATH satisfies both — statically. It has never been exercised.
- `backend/requirements.txt` declares pytest>=8.3,<9.0 and httpx, so the workflow installs only what the project declares. `frontend/package-lock.json` exists, so `npm ci` is correct. `npm test` maps to `vitest run` (frontend/package.json line 9). `vite.config.ts` configures the vitest jsdom environment and setupFiles, so no extra CI config is needed. All verified by reading.
- **Correction to the change brief and code change:** both claim `.pytest_cache` last-failed records `test_auth.py::test_login_success_and_me`. The current `backend/tests/test_auth.py` (read in full, 97 lines) contains `test_user_registration_and_login_flow` and `test_invalid_login_credentials` — no such test exists. The cache entry is stale evidence and should not be counted as a prediction of a red first run.
- Static checks: none exist in the project (no ruff/mypy config tracked; `.ruff_cache/` is untracked tool residue, and no manifest, script, or CI file names a linter) — consistent with settled_question#89's "none".
- No test was added or changed (settled_question#92): correct and appropriate; a workflow YAML is not exercisable by either in-repo suite.

Nothing was changed to make anything pass, because nothing ran.

## Acceptance coverage

Acceptance criteria from docs/sdlc/ci12/00-triage/change_brief#35.md:

| Scenario | Test |
|---|---|
| 1. Push/PR produces a visible Actions run before review | none — only observable on GitHub after pushing branch `sdlc/ci12` |
| 2. Clean-checkout install and run of both suites, no local artifacts | gate's test command (settled_question#88) approximates it locally, but not run here; the true test is the first Actions run |
| 3. Failing suite shows red and is named | none — behaviour follows from separate jobs + `-v` output, verified only by reading |

In-repo suites that exist and are what CI invokes: `backend/tests/test_auth.py`, `test_error_handling.py`, `test_health.py`, `test_models.py`; `frontend/src/App.test.tsx` ("App routing", 2 tests).

## Known gaps

- **Everything dynamic is unverified.** Neither suite was run, the workflow has never executed, and the index was not refreshed or verify-links run. The gate's own run of the test command (settled_question#88) is the only executable check that can stand in locally; the workflow itself is only proven by pushing `sdlc/ci12` to GitHub and watching the run.
- The PYTHONPATH two-path setup is the least-tested element: it satisfies both observed import styles, but a third style (e.g. bare `import models`) would fail, and pytest rootdir/conftest discovery from the repo root was not exercised.
- The stale last-failed entry (`test_login_success_and_me` no longer exists) means the "first run may be red" risk in code_change#66 is overstated; the current auth tests' clean-environment status is simply unknown.
- Node 20 pin and unpinned Python requirements ranges are assumptions taken on trust; nothing here could test them.
- Stray sqlite files at root and backend/ are local clutter; the workflow does not depend on them (verified by reading), but their cleanup is out of scope.
- Whether `sdlc/ci12` has been pushed, and whether the branch is committed, could not be checked beyond the refs listing (the branch ref exists locally; remote refs for it do not, so it has not been pushed).