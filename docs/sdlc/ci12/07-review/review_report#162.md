# Review — GitHub Actions CI for budget-checker

Reviewing code_change#112 (attempt 3) against change_brief#35 and the repository as it stands.

## Scope reviewed

- Read in full: `.github/workflows/ci.yml` (42 lines), `backend/tests/test_models.py`, `backend/tests/test_auth.py`, `backend/requirements.txt`, `frontend/package.json`.
- Ran `search_text` on backend test imports to confirm the two import styles (`app.main` in test_health.py:3, test_error_handling.py:10, test_models.py:4-5; `backend.app.main` in test_auth.py:6-7) that justify the workflow's dual-path PYTHONPATH.
- Ran `impact` upstream on both changed test symbols; the graph returned 0 affected, 0 direct, risk LOW, but self-reported `backend/tests/test_models.py` as stale (indexed 2026-09-16, before the edit). I therefore read the post-change file directly (see above) — the two `hashed_password="x"` arguments are present at lines 29 and 47.
- Lenses: requirement coverage against the brief's three acceptance criteria; declared-vs-actual diff; clean-environment assumptions (no stray sqlite dependency, no conftest dependency).
- Not run (no execution tool in this stage): the gate's test command, index refresh, `meridian sdlc verify-links`. All dynamic evidence on record is the gate's own run at gate_finding#95 (`2 failed, 17 passed` — the two failures being exactly the NOT NULL violations this change's test edit removes).

## Findings

1. **Medium — `backend/tests/test_models.py` (whole diff, second file): undeclared-in-brief scope widening, declared in code_change#112.** The brief said `backend/tests/*` would be "invoked, not modified", yet two tests now construct `User(email=..., hashed_password="x")`. This is a finding about the change relative to the brief, not about the code: gate_finding#95 proved both tests fail on any clean run (`sqlite3.IntegrityError: NOT NULL constraint failed: users.hashed_password`, exit 1), so without the edit the deliverable is a permanently red CI. The fix is correct (the model forbids NULL hashed_password), minimal, and leaves the cascade-deletion assertions untouched. A person should explicitly accept this widening; reverting just these two lines re-delivers the red CI that attempts 1–2 cycled through. Attribute to `code_change#112`.
2. **Low — `.github/workflows/ci.yml:23` (`pip install -r backend/requirements.txt`): unpinned dependency ranges.** `backend/requirements.txt` uses open ranges (`pytest>=8.3,<9.0`, `fastapi>=0.115,<0.116`), so each CI run resolves fresh versions; an upstream release inside a range can turn the job red with no repo change. Acceptable for this change; a lockfile/pin is follow-up work.
3. **Low — `.github/workflows/ci.yml:29` (`python -m pytest backend/tests -v`) with test_auth.py writing `./test_auth_unit.db`** (test_auth.py:9, `sqlite:///./test_auth_unit.db`): the backend job will create that file at the repo root on the runner and not clean it. Harmless (the file is created fresh each run; `create_all`/`drop_all` in the autouse fixture manage its contents), but it is the same root-relative-db smell the repo already carries locally.
4. **Low — `.github/workflows/ci.yml:11-13`: the dual-path `PYTHONPATH` is the least-tested element.** It satisfies both observed import styles, and the gate's local run exercised this resolution without import errors — but pytest rootdir/conftest discovery from the repo root on a clean ubuntu-latest runner has never happened. A third import style would break it. Expect a plausible failed-then-fixed first Actions run.
5. **Informational — the `.pytest_cache` `test_login_success_and_me` last-failed entry is stale**: that test does not exist in the current `backend/tests/test_auth.py` (read in full; only `test_user_registration_and_login_flow` and `test_invalid_login_credentials`), and the gate's clean run had it among the 17 passing. The change brief's "first run may be red from that test" risk should not be carried forward.
6. **Informational — index staleness.** `impact` reports `test_models.py` changed after indexing; the refresh and verify-links commands have gone unrun across attempts for lack of an execution tool. The staleness is confined to the file the diff itself touched, and the post-change file was read directly.

## Blast radius

Direct dependents outside the diff: **none.**
- `test_deleting_user_with_dependents_leaves_no_orphaned_records` — impact upstream: 0 affected, 0 direct, LOW (stale-index caveat above; file read directly). Its only collaborator, `_make_session`, is unmodified and called only by the two tests in the diff.
- `test_deleting_user_with_no_dependents_succeeds_cleanly` — same: 0 affected, 0 direct, LOW, verified by reading.
- `.github/workflows/ci.yml` — new file; no symbol references it (graph holds nothing for it); nothing to inspect.
- The frontend job invokes only existing machinery (`npm test` → `vitest run`, frontend/package.json:9); no frontend symbol is touched.

## Residual risk

Previously working and now at risk: nothing in product code — no application symbol, schema, or interface moved. The two test edits change only how the tests set up their own fixtures; the assertions they exist to make are unchanged, so nothing that previously passed is weakened.

What I am still unsure of, after looking:
- The workflow has **never run on GitHub**. Acceptance 1 (run appears on push/PR, visible before review) and acceptance 3 (red is shown and named) are satisfied by construction and verified only by reading; the first Actions run on the pushed branch is the only real proof. Nothing local can substitute.
- The fixed backend suite has not been re-run anywhere post-fix; "19 passing" is inference from gate_finding#95's failure list plus the two-line fix. The gate's next test-command run settles it.
- Python 3.12 (matching backend/Dockerfile, the only pin in the repo) and Node 20 (no repo pin exists) are assumptions on trust.
- Stray local sqlite files at root and `backend/` are clutter the workflow correctly does not depend on (verified by reading); cleanup remains out of scope.

## Verdict

**READY** — with finding 1 (the scope widening) needing a person's explicit nod rather than rework. The workflow file is correct as written against the repository's actual test imports, dependency manifests, and scripts; both changed test symbols are leaf nodes with zero dependents, verified by impact analysis and direct reading; and the one gate-proven failure the tree carried (two NOT NULL test violations) is fixed minimally and declared. The unverified remainder — the first Actions run, the fresh re-run of the fixed suite, the runner-environment pins — is exactly the set of things no stage without a shell can settle, and each is named above with the observation that will confirm or refute it.