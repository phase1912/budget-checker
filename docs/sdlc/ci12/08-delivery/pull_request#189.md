NO PR URL ON RECORD — the preceding open-pr-v1 step did not report a pull request URL, and the body file it was to pass to the forge (docs/sdlc/ci12/pr-body.md) is not present in the tree (read_file: found:false). No pull request has been confirmed opened, so none is claimed here. This artifact must not be treated as closing the process; the forge step must be re-run before a pull_request artifact can be registered.

What is on record: the branch is sdlc/ci12, base master, repo phase1912/budget-checker; the planned open command is `gh pr create --repo phase1912/budget-checker --base master --head sdlc/ci12 --title "ci: add GitHub Actions workflow running backend pytest and frontend vitest suites on push/PR" --body-file docs/sdlc/ci12/pr-body.md`; the planned verify command is `test "$(gh pr view "$PR_URL" --repo phase1912/budget-checker --json state --jq .state)" = "OPEN"`.

The body intended for the PR, assembled from the accepted artifacts:

## Summary

Adds `.github/workflows/ci.yml`, a GitHub Actions workflow with two independent jobs on every push and pull request: `backend-tests` (Python 3.12, `pip install -r backend/requirements.txt`, `python -m pytest backend/tests -v` with PYTHONPATH covering both import styles used by backend tests) and `frontend-tests` (Node 20, `npm ci`, `npm test` / `vitest run`). Also includes one declared, gate-evidence-driven widening: two tests in `backend/tests/test_models.py` constructed `User(email=...)` without `hashed_password`, violating `models.py`'s `nullable=False` and failing any clean run (`sqlite3.IntegrityError: NOT NULL constraint failed: users.hashed_password`, gate's own run: 2 failed, 17 passed, exit 1); both now pass `hashed_password="x"`, leaving their cascade-deletion assertions untouched. Without this fix the deliverable would be a permanently red CI on its first run.

## Requirements covered

- [[change_brief#35]] acceptance 1 — run on push/PR, visible before review: `on: push` + `on: pull_request`; named checks 'Backend (pytest)' and 'Frontend (vitest)'.
- [[change_brief#35]] acceptance 2 — clean-checkout install and run of both suites, no local artifacts: `pip install -r backend/requirements.txt`, `npm ci` against frontend/package-lock.json; no reliance on stray sqlite files.
- [[change_brief#35]] acceptance 3 — failing suite shows red and is named: separate jobs plus `pytest -v` / vitest naming.
- [[code_change#112]] — declared scope widening: `hashed_password="x"` in test_deleting_user_with_dependents_leaves_no_orphaned_records and test_deleting_user_with_no_dependents_succeeds_cleanly (backend/tests/test_models.py).

## Testing

- The gate's own run of the test command (gate_finding#95) initially showed 2 failed, 17 passed — the two failures exactly the NOT NULL violations the widening removes.
- Impact analysis upstream on every changed symbol: 0 affected, 0 direct, risk LOW for both edited tests and `_make_session`; no dependents outside the diff. [[verification_report#137]] and [[review_report#162]] confirm the fix present in the tree (lines 29 and 47).
- Verification of the fixed suite post-fix is inference (expected 19 passing), not observation; the first real Actions run is the only true proof of acceptance 1 and 3.

## Risk and blast radius

No dependents outside the diff (review_report#162 blast radius: none). Residual risks, from the review: the workflow has never run on GitHub (the dual-path PYTHONPATH and runner environment are the least-tested elements; a failed-then-fixed first run is plausible); unpinned Python requirement ranges mean CI resolves fresh versions each run; Node 20 pin is an assumption; the widening needs a person's explicit acceptance since the brief said backend/tests would be 'invoked, not modified'; the stale `.pytest_cache` last-failed entry for `test_login_success_and_me` should not be carried forward (that test no longer exists). Watch after merge: the first Actions run on push/PR, and freshness of resolved dependency versions.