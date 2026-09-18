# Review — GitHub Actions CI for budget-checker (code_change#247, second review, attempt 2)

## Scope reviewed

This attempt re-reviews the tree after attempt 1's gate finding (gate_finding#292), which said a READY verdict carrying an open delivery-blocking item "is close to the contradiction this metric exists for". That finding is answered below by re-verifying the open item and changing the verdict to follow from it. Nothing else was complained about and is kept.

Read in full, on disk, this attempt:

- `.github/workflows/ci.yml` (all 41 lines) — re-verified: `on: push` + `pull_request`, two independent jobs (`backend-tests`: Python 3.12, `cache: pip` keyed to `backend/requirements.txt`, `pip install -r requirements.txt` at line 22, `python3 -m pytest`; `frontend-tests`: Node 22, `cache: npm` keyed to `frontend/package-lock.json`, `npm ci`, `npm test`). No `--no-cache-dir` anywhere; no `continue-on-error` anywhere.
- `pr-body-ci14.md` (repo root, all 32 lines) — the delivery artifact; content re-read this attempt (see finding 2 — it is not fully accurate).
- `docs/sdlc/ci14/pr-body.md` — `read_file` returns **not-found**, twice this attempt. This is the path the settled PR command names (settled_question#223).
- `backend/tests/test_models.py` (all 61 lines) — `_make_user` (lines 22–24) supplying `hashed_password="test-hash"`; both deletion tests (lines 30, 50) use it.
- `backend/conftest.py` (16 lines) — sys.path bootstrap covering both import styles.
- `backend/requirements.txt` (10 lines) — bcrypt, PyJWT, email-validator present.
- `backend/app/models.py:15–30` — `hashed_password = Column(String, nullable=False)` confirmed as the fixture defect's root cause.
- `backend/app/security.py` — `import bcrypt` confirmed at line 6 (runtime import the manifest must name).

Tools run this attempt: `impact(create_app, upstream)` → **found: false** — consistent with the previous attempt; the 2026-09-16 index does not hold the symbol earlier stages ran impact against, so all blast-radius claims below rest on direct file reads, not the graph. `search_text` for the delivery path's references. Cross-read: verification_report#270, settled_question#201/#202/#204, gate_finding#251/#273/#292, prior review_report#205 and #289.

## Findings

1. **Medium — delivery-blocking, unresolved, now re-verified twice: the settled PR command names a body file that does not exist.** `docs/sdlc/ci14/pr-body.md` returns not-found from `read_file` this attempt, exactly as it did in verification_report#270 and review_report#289; the body lives at `pr-body-ci14.md` in the repository root. The settled command (settled_question#223) is `gh pr create --base master --head sdlc/ci14 ... --body-file docs/sdlc/ci14/pr-body.md`, which fails on the missing file before reaching the forge. This is a mismatch between the tree and the delivery stage's settled command, not a defect in code_change#247's code — the body file's content itself is correct. It is the most plausible cause of the pull-request stage failing 3 of 3 (run_journal#19 records no stderr, so the cause is inferred; the mismatch is fact). Two one-step resolutions, either of which a person may pick: move the file to the settled path, or re-settle the command to `--body-file pr-body-ci14.md`. This stage fixes neither; it is named so the person need not rediscover it at delivery.

2. **Low — `pr-body-ci14.md:29` contains a now-false statement.** The body's last risk bullet says: "the pip cache key (`cache: pip`) is never read because the install step uses `--no-cache-dir` — dead configuration, cosmetic only." The workflow this PR delivers no longer has that defect: `.github/workflows/ci.yml:22` is `pip install -r requirements.txt`, `--no-cache-dir` was removed (the fix review_report#205 finding 1 asked for, confirmed on disk this attempt). The PR body therefore describes a defect the diff does not contain. Cosmetic — it would not block the PR — but the body is the one artifact a reviewer reads first, and it contradicts the diff it ships with. Fixable by delivery in the same stroke as finding 1 (the body file must be touched anyway if it is moved).

3. **Low — the code graph index does not hold `create_app`** (`impact` found:false this attempt and at settled_question#202, against earlier stages' 1 direct dependent / risk LOW). No consequence for this diff — the symbol is invoked, not modified — but blast radius in this review is certified by direct reads, not the graph, and later stages are judging against a degraded index. Recorded, not actionable here.

No medium or high findings against the code itself. The four code files are unchanged from the tree the previous review re-verified, and the one code-level finding that review carried (dead pip cache) is confirmed fixed on disk. Nothing unexplained is in the diff beyond the delivery artifacts named above; no application code changed.

## Blast radius

Direct dependents outside the diff — impact unavailable (finding 3); every entry below is from direct reads:

- **`create_app` / `backend/app/main.py`** — invoked by the workflow's pytest step, not modified. `backend/tests/test_auth.py` imports `from backend.app.main import app`; `backend/conftest.py` inserts both the repo root and `backend/` on `sys.path`, so the import resolves from either invocation directory (CI runs pytest with `working-directory: backend`). Inspected: sound.
- **`_make_user` and the two deletion tests (`backend/tests/test_models.py`)** — read in full on disk; nothing outside the file references them (searched); the non-nullable constraint is real at `backend/app/models.py`. Inspected: sound.
- **`backend/requirements.txt` consumers** — the gate's build/test command and `ci.yml:22`; each added entry traces to a real import (`bcrypt`/`jwt` at `security.py:6–7`, `email-validator` via `EmailStr` in `backend/app/schemas.py`). Inspected: sound.
- **Every future contributor's push/PR** — gated by the workflow once merged; both jobs propagate pytest/vitest's own exit codes with no tolerance. Sound by construction; execution unproven (residual risk below).
- **The delivery stage itself** — findings 1 and 2; not sound until the body-file path is reconciled.

## Residual risk

- **The post-fix backend suite has not been executed by anyone in this record.** The last executed gate builds (attempt-4 log; gate_finding#135) ran the *pre-fixture-fix* tree: 17 passed / 2 failed, the two failures exactly the two tests `_make_user` fixes, with all import and dependency errors gone. 19/19 is the reasoned expectation, not a claim as seen; the engine's own gate run of the settled command is the arbiter and precedes this document.
- **The workflow has never run on GitHub, and the frontend suite has never completed in any recorded run** — every prior failure short-circuited at backend pytest. AC1 (triggers firing, checks visible), the GitHub-visibility half of AC2, the frontend job end-to-end, and the `cache-dependency-path` behaviour all land on the first real Actions run of branch `sdlc/ci14` (base `master`). Pre-existing frontend failures, if any, surface red — per the brief, surfaced, not repaired.
- **Python version drift:** all gate evidence ran on 3.14; CI pins 3.12 per `backend/Dockerfile`. Broad pins make this unlikely to bite; untested on exactly the version CI uses.
- **What previously worked that might not now:** nothing in application code. No existing symbol is modified; `conftest.py` only adds paths; the manifest only gains entries the code already imported. The prior reviews' reasoning on this point carries forward unchanged and was re-checked this attempt against the files themselves.

## Verdict

**NEEDS DISCUSSION.** The code change itself is, in my judgement, ready: it is the same four-file tree the previous two reviews verified, its only code-level finding is confirmed fixed on disk, and no new code defect was found this attempt. What changed this attempt's verdict from the previous READY is the gate's own point, which re-verification confirmed rather than resolved: a medium, delivery-blocking finding is still open — the settled `gh pr create --body-file docs/sdlc/ci14/pr-body.md` names a file that does not exist (finding 1), and the body file that does exist misdescribes the diff it ships (finding 2). A READY headline over an open delivery blocker is the contradiction this stage exists to catch, so the blocker is now the headline. The decision it needs from a person is small and explicit — move `pr-body-ci14.md` to the settled path or re-settle the command to point at it, and correct its stale pip-cache bullet — after which this change needs no further implementation work and delivery can proceed.