# Review — GitHub Actions CI for budget-checker

## Scope reviewed

Read in full, on disk:

- `.github/workflows/ci.yml` (all 41 lines) — the deliverable.
- `backend/tests/test_models.py` (all 61 lines) — the reinstated `_make_user` helper and both deletion tests that use it.
- `backend/conftest.py` (all 16 lines) — the sys.path bootstrap.
- `backend/requirements.txt` (all 10 lines) — including bcrypt, PyJWT, email-validator.
- `backend/app/models.py` (lines 1–30) — confirms `hashed_password = Column(String, nullable=False)` is the root cause the fixture fix answers.
- `backend/app/security.py` (lines 1–15) — confirms `bcrypt` and `jwt` are real runtime imports the manifest must name.
- `backend/app/schemas.py` (lines 1–20) — confirms `EmailStr` (which requires `email-validator`) is used by `UserRegister`, `UserLogin`, `UserResponse`.
- `backend/tests/test_auth.py` (lines 1–10) — confirms the `from backend.app...` import style the conftest must support.
- `frontend/package.json` (all 35 lines) — confirms `npm test` = `vitest run` and that no `lint` script exists.
- `.gitignore` (all 21 lines) — line 10 `*.db` covers the stale sqlite artifacts a fresh Actions checkout would otherwise inherit.
- `frontend/src/` listing — `App.test.tsx` present at src root; `AuthStore.test.ts` confirmed under `frontend/src/stores/` by search.

Tools run: `impact(create_app, upstream)` → found, `backend/app/main.py`, 1 affected (1 direct), risk LOW, index fresh (2026-09-16, no stale files for this answer). `search_text` for lint configuration and for prior frontend test inventory. Cross-read the run record: gate build logs from attempts 2–5 (gate_finding#62, #77, #135, #156), verification_report#182, and the accepted code_change#153.

Lenses: diff-vs-brief, dependency traceability of every manifest line, blast radius, acceptance coverage, adversarial (what fails on the first real run).

## Findings

1. **Low — `.github/workflows/ci.yml:22` — the pip cache and the install step disagree.** `cache: pip` (setup-python) caches the pip wheel cache keyed to `backend/requirements.txt`, but the install step is `pip install --no-cache-dir -r requirements.txt`, which never reads that cache. The cache key will be computed and stored every run and never used — harmless (a wasted cache upload, a few seconds), but it is dead configuration. Either drop `--no-cache-dir` or drop the `cache:` block. Cosmetic; does not gate.

2. **Low — `.github/workflows/ci.yml:40` — the frontend job has never executed anywhere.** Not a defect in the file: `npm ci` then `npm test` are both real, failure-tolerant nowhere, and `vitest run` is the repo's own script (`frontend/package.json:10`). But every recorded failure in this run short-circuited at backend pytest, so no human or machine has ever seen the frontend suite complete. The first Actions run is its first execution. This is a residual-risk statement, not a code defect — there is no in-repo way to execute a workflow, and the brief explicitly scopes this work to surfacing, not repairing, whatever that run finds.

3. **Low — Python version drift between gate evidence and CI target.** Every gate build log in the record ran on Python 3.14 (`pip 25.2 -> 26.2.1 ... python3.14` notices throughout), while `ci.yml:19` pins 3.12 per `backend/Dockerfile`. The 19/19-backend expectation therefore rests on 3.14 evidence for a 3.12 run. The pins in `backend/requirements.txt` (fastapi ≥0.115, sqlalchemy ≥2.0, bcrypt ≥4.0, etc.) are broad enough that this is very unlikely to bite, but it is untested on exactly the version CI will use.

No medium or high findings. Notably, nothing in the diff is unexplained: all four files trace to gate-build evidence (workflow → AC1/AC2; conftest.py → attempt-2's `No module named 'backend'`; requirements.txt lines 8–10 → attempt-3's `ModuleNotFoundError: email_validator` on three test modules; `_make_user` → the `NOT NULL constraint failed: users.hashed_password` failures in two independent gate logs, with the root constraint confirmed at `backend/app/models.py:25`). No drive-by reformatting, no dependency bumps beyond the three proven-missing entries, no application code touched.

## Blast radius

Direct dependents outside the diff:

- **`create_app` (backend/app/main.py)** — the most-connected symbol the suite exercises. `impact` upstream: 1 affected, 1 direct, risk LOW, index fresh. It is *invoked* by the workflow's pytest step, not modified. Inspected: `backend/tests/test_auth.py:8` imports `from backend.app.main import app`; the conftest bootstrap makes that resolve from the repo root, which is where the CI job runs (`working-directory: backend` for the shell, but pytest's rootdir is `backend/`, and the conftest inserts both the repo root and `backend/` onto sys.path — both import styles covered, verified by reading `conftest.py` against the actual imports in `test_auth.py:7–8`). Sound.
- **`test_deleting_user_with_dependents_leaves_no_orphaned_records` / `test_deleting_user_with_no_dependents_succeeds_cleanly` (backend/tests/test_models.py)** — impact upstream: 0 affected, 0 direct, risk LOW; nothing outside the file references them or `_make_user` (searched). Read in full on disk: both construct users via `_make_user`, which supplies the non-nullable `hashed_password` the model requires. Sound.
- **Configuration consumers** — the backend manifest is now consumed by both the gate's build command and `ci.yml:22`; every entry cross-checked against a real import (`bcrypt`/`jwt` at `security.py:6–7`, `email-validator` via `EmailStr` at `schemas.py:3–16`, plus the pre-existing fastapi/uvicorn/sqlalchemy/psycopg2/pytest/httpx). Sound.
- **Every future contributor's push/PR** — once merged, the workflow gates them. Its steps run the suites' own exit codes with no `continue-on-error`; a red suite surfaces rather than passes silently, which is the brief's stated intent. Sound by construction; execution unproven (finding 2).

## Residual risk

- **The post-fix backend suite has not been executed in this run's record.** The last executed gate build (gate_finding#135) was on the *reverted* tree and showed exactly 17 passed / 2 failed, the two failures being the two tests `_make_user` fixes, with all import/dependency errors gone. I expect 19/19 but cannot claim it as run; the engine's own gate run of the settled command is the arbiter, and it precedes this document's acceptance.
- **The first real GitHub Actions run** (branch `sdlc/ci14`, base `master`) is the only proof of AC1 (push/PR triggers firing, checks visible in GitHub), the GitHub-visibility half of AC2, the frontend job end-to-end, and the `cache-dependency-path` configuration. This is structural to a workflow-only chore, not an unexamined corner — but until that run happens, AC1 is satisfied structurally, not behaviourally.
- **The frontend suite has never completed in any recorded run** (finding 2). Pre-existing vitest failures, if any, will land red on an otherwise-green backend job on the first push — per the brief, surfaced, not repaired.
- **What previously worked that might not now:** nothing. No application symbol changed (the diff's only non-new file is a test file whose two changed tests previously could not run at all). Local developers running pytest from `backend/` gain from conftest.py; nothing that resolved before stops resolving, since the bootstrap only adds paths.

## Verdict

**READY.** The diff is exactly the four files the record says it is, every line of every file traces to a requirement or to a gate-build-proven necessity, the manifest is now verifiably complete against the code's real imports, and the fixture fix repairs tests that two independent gate logs prove could not run — against a non-nullable column (`models.py:25`) the model is right to enforce. The three findings are low and forward-looking (dead pip-cache config, unexecuted frontend half, 3.12-vs-3.14 evidence drift); none is a defect in what shipped. The one thing inspection cannot deliver — AC1's behaviour on GitHub itself — lands on the first Actions run of `sdlc/ci14`, and a red result there is the brief working as specified, not this review being wrong. A person should watch that first run; that is delivery's job, not a reason to hold this back.