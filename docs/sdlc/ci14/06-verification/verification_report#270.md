# Verification — GitHub Actions CI for budget-checker (code_change#247, stage_instance#254)

## Commands run

This environment exposes repository reads only — no shell — so I executed no command. The executable verdict remains the engine's own gate run of the settled build/test command (`pip3 install -r backend/requirements.txt && (cd backend && python3 -m pytest) && cd frontend && npm ci && npm run build && npm test`) and, later, the first real GitHub Actions run. What I ran here was static verification of the current tree against code_change#247's claims:

| Check | Result |
|---|---|
| `.github/workflows/ci.yml` exists and matches #247's description | ✅ verified on disk, 41 lines: `push`+`pull_request`, two independent jobs, Python 3.12 / Node 22 per the Dockerfiles, `cache: pip` keyed to `backend/requirements.txt`, `cache: npm` keyed to `frontend/package-lock.json`, real `python3 -m pytest` and `npm test`, no failure tolerance |
| **review_report#205 finding 1 fixed: pip install reads the cache** | ✅ confirmed — the install step at `.github/workflows/ci.yml:22` is `pip install -r requirements.txt`; `--no-cache-dir` is gone from the workflow (it survives only in `backend/Dockerfile:6`, which is correct there — no cache block exists in the Docker build) |
| `backend/conftest.py` sys.path bootstrap | ✅ verified on disk, 16 lines, covers both import styles |
| `backend/requirements.txt` complete manifest | ✅ verified on disk, 10 lines incl. `bcrypt`, `PyJWT`, `email-validator` (line 9) |
| `_make_user` fixture fix in `backend/tests/test_models.py` | ✅ verified on disk: helper at lines 22–24 supplying `hashed_password="test-hash"`; used by both previously-failing deletion tests (lines 31, 50) |
| Root cause in tree | ✅ `hashed_password` non-nullable in `backend/app/models.py` (consistent with the two gate logs: `NOT NULL constraint failed: users.hashed_password`) |
| Stale sqlite artifacts gitignored | ✅ `.gitignore` line 10 = `*.db` |
| Lint tooling | ✅ none exists: `frontend/package.json` has no `lint` script (only dev/build/preview/test), no ruff/flake8/mypy config tracked anywhere. The only ruff traces are `.ruff_cache/` and `.venv/` leftovers — untracked, not adoption. "None" stands |
| `docs/sdlc/ci14/pr-body.md` — **claimed written by #247** | ⚠️ **NOT at that path.** `read_file` returns not-found for `docs/sdlc/ci14/pr-body.md`. A body file **does** exist at `pr-body-ci14.md` (repo root, 32 lines, content matches the settled PR title and the review findings). The settled command (settled_question#223) names `--body-file docs/sdlc/ci14/pr-body.md`, which will fail on the missing file until the path is reconciled |

## Results

- **Code findings: all clean.** The one code-level finding from review (dead pip cache) is fixed exactly as claimed; the workflow, conftest, manifest and fixture fix all match the change note on disk.
- **One delivery-blocking discrepancy found: the PR body file is in the wrong place.** code_change#247 says "`docs/sdlc/ci14/pr-body.md` is written", but the file is actually `pr-body-ci14.md` at the repository root. The settled `gh pr create --body-file docs/sdlc/ci14/pr-body.md` command cannot succeed against the current tree — plausibly the actual cause of the pull-request stage's three failures (run_journal#19 records no stderr, so this is inference, but it is now a verified mismatch, not a hypothesis). The delivery stage must either move the file to the settled path or re-settle the command to point at `pr-body-ci14.md`. I changed nothing: the file's content itself is correct and consistent with the record.
- **No test was changed to make anything pass in this stage.** The only test change in the whole work remains the two `test_models.py` fixtures moved onto `_make_user` (accepted at the implementation gate), because the old fixtures inserted a row the schema forbids — the model was right, the fixtures were wrong.
- **Execution status unchanged:** the post-fix backend suite has never been executed by anyone in this run's record (the last executed gate build was on the pre-fix tree: 17 passed / 2 failed, the two failures being exactly the tests `_make_user` fixes). The frontend suite (`npm ci && npm test`) and `npm run build` have never completed in any recorded run.

## Acceptance coverage

| Scenario | Test |
|---|---|
| AC1 — both suites run on every push and PR as visible GitHub checks | none in-repo — provable only by the first real Actions run of branch `sdlc/ci14` (base `master`); structure verified on disk (`ci.yml` triggers + two jobs) |
| AC2 — a failing assertion shows a failing check | demonstrated end-to-end by gate builds failing on pytest's own exit code (17 passed / 2 failed, two independent logs); GitHub-side visibility needs the first Actions run |
| AC3 — a fresh runner needs no manual setup | backend half proven by gate runs collecting all 19 tests from the manifest alone; frontend half (`npm ci` against the tracked lockfile) verified on disk, never executed |
| Backend pytest suite passes post-fix | backend/tests/ — pending the engine's gate run; 19/19 expected, not claimed as seen |
| Frontend vitest suite passes | frontend/src/*.test.* via `npm test` — never yet executed in any recorded run |

## Known gaps

- **PR body path mismatch (new finding this attempt):** `docs/sdlc/ci14/pr-body.md` does not exist; the body lives at `pr-body-ci14.md` in the repo root. The delivery stage's settled command will fail until reconciled.
- **Post-fix execution:** no shell here; the engine's gate run of the test command is the only executable verdict and precedes the gate.
- **The workflow has never run on GitHub** — AC1, the visibility half of AC2, the frontend job end-to-end, and the `cache-dependency-path` behaviour all land on the first real push.
- **Python version drift:** gate hosts ran 3.14 (deprecation warnings in every gate log); CI pins 3.12 per `backend/Dockerfile`. The 3.12 run is untested until the first Actions run.
- **No in-repo test covers the workflow or conftest** — structural to a workflow-only chore; nothing in this repository can execute a GitHub Actions workflow.
