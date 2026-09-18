# code_change — GitHub Actions CI for budget-checker (attempt 1 of stage_instance#233)

## Summary

`.github/workflows/ci.yml` runs the existing backend pytest suite and the existing frontend vitest suite on every push and pull request, as two independent, visible checks. This stage continues after the pull-request stage (stage_instance#211) failed, so its scope is narrow: deliver a tree the delivery stage can ship, with the PR stage's likely blocker removed and the one code-level finding from the review addressed. Two deltas from the accepted tree of code_change#153:

1. **`.github/workflows/ci.yml` — the pip cache is now live, not dead** (review_report#205, finding 1): the install step previously ran `pip install --no-cache-dir -r requirements.txt`, which never reads the wheel cache that `setup-python`'s `cache: pip` block computes and stores. `--no-cache-dir` is dropped; the install step is now `pip install -r requirements.txt` (verified on disk, line 22).
2. **`docs/sdlc/ci14/pr-body.md` is written** — the body file that the settled PR command (settled_question#223) names but which did not exist on disk. The `gh pr create --body-file docs/sdlc/ci14/pr-body.md` command fails on a missing file before it ever reaches the forge, which is the most plausible cause of the pull-request stage failing three of three tries. This document is the change note itself, filed under this process's document folder, so the delivery stage's command and the artifact on disk now agree.

Everything else — `backend/conftest.py`, the completed `backend/requirements.txt`, the `_make_user` fixture fix in `backend/tests/test_models.py` — is carried forward from the accepted code_change#153 unchanged, re-verified on disk this attempt.

## Requirements implemented

- [[AC1]] Both suites execute on push/PR as separate visible checks → jobs `backend-tests` and `frontend-tests`, both triggered on `push` and `pull_request` in `.github/workflows/ci.yml` (verified on disk, 41 lines). GitHub-side visibility is only provable on the first real Actions run of branch `sdlc/ci14` — stated, not claimed as proven.
- [[AC2]] A failing assertion fails the job → both jobs run the real suites (`python3 -m pytest`, `npm test`) with no `continue-on-error` or failure tolerance; each job's exit code is pytest/vitest's own. Gate builds have demonstrated this end to end: pytest ran to completion and failed the build on its own red tests (attempt-4 log and gate_finding#135: 17 passed / 2 failed) on the pre-fix tree.
- [[AC3]] A fresh runner needs no manual setup → `backend/requirements.txt` names the app's full runtime dependency set (bcrypt, PyJWT at lines 7–8 per `backend/app/security.py:6–7`; `email-validator>=2.0,<3.0` at line 9, backing the `EmailStr` in `backend/app/schemas.py` — the gap whose absence sank the attempt-3 gate build on three test modules); `backend/conftest.py` bootstraps `sys.path` so both test import styles (`from backend.app...` in test_auth.py, `from app...` in test_health/test_error_handling/test_models) resolve from any invocation directory; `npm ci` runs against the tracked `frontend/package-lock.json`; Python 3.12 / Node 22 match `backend/Dockerfile` and `frontend/Dockerfile`.

## Symbols changed

- **`_make_user` (backend/tests/test_models.py:23–25)** — test helper supplying `hashed_password="test-hash"`, the value the non-nullable column at `backend/app/models.py:25` requires. Carried forward from code_change#153; not modified this attempt. `impact` upstream: not indexed (test helper); searched — no file outside test_models.py references it.
- **`test_deleting_user_with_dependents_leaves_no_orphaned_records` (backend/tests/test_models.py:31)** — creates its user via `_make_user`. Carried forward, not modified. `impact` upstream: 0 affected, 0 direct, risk LOW (file flagged stale in the index; verified by reading the file on disk).
- **`test_deleting_user_with_no_dependents_succeeds_cleanly` (backend/tests/test_models.py:50)** — same. Carried forward, not modified; same impact result.
- **`create_app` (backend/app/main.py)** — invoked by the suite, not modified. `impact` upstream re-run this attempt: 1 affected, 1 direct, risk LOW, index fresh (2026-09-16).

Configuration files carried forward / changed (not symbols):

- `.github/workflows/ci.yml` — **modified this attempt** (one line: `--no-cache-dir` removed from the pip install step), answering review_report#205 finding 1. Otherwise unchanged: two independent jobs on push/PR, pip/npm caches keyed to `backend/requirements.txt` and `frontend/package-lock.json`, no failure tolerance.
- `backend/conftest.py` — carried forward unchanged, re-verified on disk (16 lines).
- `backend/requirements.txt` — carried forward unchanged (10 lines), re-verified on disk.
- `docs/sdlc/ci14/pr-body.md` — **new this attempt**; the PR body file the delivery stage's settled command requires.

## Tests written

None new this attempt — this is a continuation after review acceptance, not new behaviour. The discriminating tests for the one test-file change remain the two `test_models.py` deletion tests themselves: both provably failed on the pre-fix tree (two independent gate logs: `NOT NULL constraint failed: users.hashed_password`, 17 passed / 2 failed) and pass only with `_make_user`, so reverting the fixture fix makes them fail. The workflow file has no in-repo test that would fail if `ci.yml` were deleted — a structural limit of a workflow-only chore the verification stage's reviewer already scored as such (run_journal#19); AC1 and the visibility half of AC2 rest on the first real Actions run of branch `sdlc/ci14` (base `master`).

## Design notes

- **Two deltas only, each answering something on the record.** The `--no-cache-dir` removal answers review_report#205's only code-level finding; the pr-body.md file answers the only plausible mechanical cause of the pull-request stage's three failures, given the settled command names a file that did not exist. Everything else is carried forward because the review scored it READY (review_report#205) and the gate did not complain about it.
- **Why pr-body.md is here and not the delivery stage.** The pull-request stage's plan questions were answered (settled_question#223–225) but the body file was never written, and a body-file command cannot succeed without it. Writing it here means delivery's attempt 2 starts from a state where its own command can run, instead of re-deriving why attempt 1 failed.
- **Alternative considered and rejected: rewriting the PR body into the command.** The plan explicitly settled a body *file* (`--body-file`), for the stated reason that argument-passed text is retyped text. Writing the file, not inlining the body, is the settled decision.
- **Kept from the accepted tree:** Python 3.12 / Node 22 pinned from the Dockerfiles, two independent jobs, npm cache keyed to the lockfile, pip cache now actually used by the install step, `python3 -m pytest` spelling, conftest bootstrap, complete manifest, `_make_user`.

## Risks

- **The post-fix backend suite has not been executed in this run's record** — no shell here. Basis for expecting 19/19: the last executed gate build on the reverted tree (gate_finding#135) showed 17 passed and only the two tests `_make_user` fixes failing, with all import and dependency errors gone. The engine's gate run of the settled command (`pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm run build && npm test`) is the arbiter.
- **The frontend half (`npm ci && npm test`, and `npm run build`) has never completed in any recorded run** — every earlier failure short-circuited at backend pytest. Pre-existing frontend failures, if any, surface red on the first push; per the brief, surfaced, not repaired.
- **The workflow has never run on GitHub.** AC1, the GitHub-visibility half of AC2, the frontend job end-to-end, and the cache configuration are only provable on the first real Actions run of branch `sdlc/ci14`.
- **I cannot confirm the pull-request stage failed for the missing-body-file reason** — the run journal records the failure without its stderr. If the actual cause was elsewhere (e.g. `gh` not authenticated, or the branch not pushed), the pr-body.md file alone does not fix it, and delivery will surface the real cause on its next attempt.
- **Python version drift:** gate hosts run Python 3.14 (deprecation warnings in every gate log) while CI pins 3.12 per `backend/Dockerfile`; the 3.12 run is untested here.
- **Loose npm ranges and mutable major action tags** (`@v4`/`@v5`) — standard practice, not supply-chain-hardened; out of scope per the brief.