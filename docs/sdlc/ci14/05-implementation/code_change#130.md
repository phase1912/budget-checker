# code_change — GitHub Actions CI for budget-checker (attempt 3 of stage_instance#113)

## Summary

`.github/workflows/ci.yml` runs the two existing test suites on every push and pull request as two independent, visible checks (backend pytest, frontend vitest). This attempt's only delta versus the tree the previous gate reviewed is a revert: `backend/tests/test_models.py` is returned to its pre-#76 state. The `_make_user` fixture helper is removed and both deletion tests (`test_deleting_user_with_dependents_leaves_no_orphaned_records`, `test_deleting_user_with_no_dependents_succeeds_cleanly`) again construct `User(email=...)` without `hashed_password`. The reason is the reviewer's finding at the last two gates, stated twice in the reviewer's own words: the fixture repair "does not trace to any requirement", traces to the brief's explicit out-of-scope line ("No fixes to any test the new CI reveals as already failing... the run surfaces failures, it does not repair them"), and "is exactly the decision the brief reserved for someone else". My previous note offered that revert to the person at the gate; this attempt follows through on it rather than re-arguing the point. Every other file — the workflow, `backend/conftest.py`, the completed `backend/requirements.txt` — is carried forward unchanged and re-verified on disk this attempt.

## Requirements implemented

- [[AC1]] Both suites execute on push/PR as separate visible checks → jobs `backend-tests` and `frontend-tests`, both triggered on `push` and `pull_request` in `.github/workflows/ci.yml` (verified on disk, 41 lines). The GitHub-visibility half is only provable on the first real Actions run of branch `sdlc/ci14` — stated, not claimed as proven.
- [[AC2]] A failing assertion fails the job → both jobs run the real suites (`python3 -m pytest`, `npm test`) with no `continue-on-error` or tolerated steps; each job's exit code is pytest/vitest's own. With the fixture fix reverted, this AC is now exercised *in the tree itself*: the two `test_models.py` deletion tests fail with `NOT NULL constraint failed: users.hashed_password` (proven by the attempt-4 gate log, 17 passed / 2 failed), so the workflow's first run will demonstrate a red check end to end — which is what this brief says CI is for.
- [[AC3]] A fresh runner needs no manual setup → `backend/requirements.txt` declares the app's full runtime dependency set including `email-validator>=2.0,<3.0` (the dependency whose absence sank the attempt-3 gate build on three test modules; it is required by `backend/app/schemas.py`'s `EmailStr`), `bcrypt` and `PyJWT` (imported at `backend/app/security.py`), plus pytest and httpx for the suite; `backend/conftest.py` bootstraps `sys.path` for both test import styles (`from backend.app...` in test_auth.py, `from app...` in test_health.py/test_error_handling.py/test_models.py) from any invocation directory; `npm ci` runs against the tracked `frontend/package-lock.json`; Python 3.12 / Node 22 match `backend/Dockerfile` and `frontend/Dockerfile`.

## Symbols changed

- `test_deleting_user_with_dependents_leaves_no_orphaned_records` (backend/tests/test_models.py:31) — reverted to pre-#76 form: constructs `User(email="alex@example.com")` inline. `impact` upstream: 0 affected, 0 direct, risk LOW.
- `test_deleting_user_with_no_dependents_succeeds_cleanly` (backend/tests/test_models.py:50) — reverted the same way. `impact` upstream: 0 affected, 0 direct, risk LOW.
- `_make_user` (was backend/tests/test_models.py:23–28) — **removed** in this attempt.
- `create_app` (backend/app/main.py) — invoked by the suite, not modified; 1 direct dependent, risk LOW.

Carried forward unchanged, configuration and manifest rather than symbols (re-verified on disk this attempt):

- `.github/workflows/ci.yml` — two independent jobs on push/PR; pip/npm caches keyed to `backend/requirements.txt` and `frontend/package-lock.json`.
- `backend/conftest.py` — sys.path bootstrap for both import styles.
- `backend/requirements.txt` — complete manifest, `email-validator` at line 9.

## Tests written

None new in this attempt. Deliberately: the two `test_models.py` deletion tests now fail against the tree as delivered, and that failure is the point — the brief's AC2 and its out-of-scope line both say the new CI surfaces pre-existing failures rather than repairing them. The discriminating-fixture tests that existed under code_change#76 are gone by the same stroke; anyone who wants them green must make the call the brief reserved for a person, which is now an explicit, one-file decision rather than something bundled silently into a CI chore. The workflow file itself has no in-repo test that would fail if `ci.yml` were deleted — the verification-stage reviewer scored that as the structural limit of a workflow-only chore, not a hollow test; AC1 and the visibility half of AC2 rest on the first real Actions run.

## Design notes

- **The revert is the shortfalls answer.** Two consecutive gates (gate_finding#77, gate_finding#135) scored "nothing unrelated came along" below threshold on exactly one hunk: the `_make_user` fixture fix. The reviewer's text said the fix's own note had already offered a revert path and named it "a finding for the person at this gate, not silently the maker's call". This attempt makes that call available rather than pre-empting it: the hunk is reverted, the change now traces cleanly to AC1/AC2/AC3, and the two failures the workflow will surface on its first run are visible in the branch's own diff against `master`'s pre-fix state.
- **AC2 is now testable in-tree, which it was not before.** Under the accepted #76 tree, all backend tests passed and AC2's "failing assertion shows a failing check" could only be demonstrated by deliberately breaking something on a branch. With the revert, the first Actions run demonstrates it with the failures the brief itself predicted CI would surface on `master`. This is the reading of the brief I am taking, and it is checkable against the brief's own words.
- **What I considered and rejected: keeping the fixture fix and re-arguing.** Its virtue was a green first run; its cost was a third consecutive out-of-scope finding, and the gate's build command (settled_question#55) counts exit codes, so a red backend suite fails the *gate's* build regardless — which means keeping the fix did not even buy a green gate run, only a green first Actions run at the price of scope discipline. Rejected.
- **Fix-the-tree-not-the-workflow, retained.** The import-path and dependency problems live in `conftest.py` and `requirements.txt`, so the workflow stays the plain version — no `PYTHONPATH` override, no ad-hoc installs — and the same commands work locally and on the runner.
- **Scope, now honest.** Triage expected one new file; the tree carries three (workflow, conftest, manifest). Both extra files trace to AC3 — a fresh runner cannot provision a manifest that does not name `email-validator`, and pytest cannot import the app without the path bootstrap — and both were proven necessary by gate build logs (attempt 3's `ModuleNotFoundError: email_validator` on three test modules; attempt 2's `No module named 'backend'`), not assumed. No application code changes in any attempt.

## Risks

- **The gate's build command will fail at the backend pytest step**, by design: 17 pass, the two reverted deletion tests fail on `NOT NULL constraint failed: users.hashed_password` (the attempt-4 gate log is the direct evidence for that exact outcome on this exact tree state). I am asserting the failure rather than hiding it because it is the behaviour the brief specifies; if the gate needs a green build to pass this stage, the person must either accept the red as correct-per-brief or instruct the fixture fix — and the note above says which trade each choice buys.
- **The frontend half (`npm ci && npm test`) has never completed in any recorded run** — every earlier failure short-circuited at backend pytest. It may surface pre-existing frontend failures; per the brief, surface, not repair.
- **The workflow has never run on GitHub.** AC1, the visibility half of AC2, and the `cache-dependency-path` configuration are only provable on the first real Actions run of branch `sdlc/ci14` (base `master`).
- **Python drift:** gate hosts may run Python 3.14 (3.14 deprecation warnings were visible in earlier gate logs) while CI pins 3.12 per `backend/Dockerfile`; behaviour may differ between them.
- **Loose npm ranges and mutable major action tags** (`@v4`/`@v5`) — standard practice, not supply-chain-hardened; out of scope per the brief.
