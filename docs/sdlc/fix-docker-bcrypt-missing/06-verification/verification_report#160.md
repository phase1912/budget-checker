# Verification report — fix-docker-bcrypt-missing (stage_instance#143)

## Commands run

None. This stage has no shell access — only repository reads. No command was run by me, so none has an exit status to report. The commands the process itself records for this run, and their ownership:

- `python3 -m pip install -r backend/requirements.txt && python3 -m pytest backend/tests && cd frontend && npm ci && npm test` (settled_question#156, test-command) — run by the engine at this gate, not by me. Its exit code is the gate's verdict, not mine.
- `python3 -m pytest backend/tests/test_docker_bcrypt.py -v` (settled_question#72, repro-test-command) — the narrow regression command; first real execution is at this gate, since prior stages established no Docker daemon exists in this environment.
- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` and `meridian sdlc verify-links` (settled_question#155) — not run; the graph has held no backend symbols at triage, planning and implementation (impact on `security.py` / `hash_password` returned `found: false`), and I could not confirm re-indexing happened.

## Results

What I verified by reading the repository (the change is exactly what code_change#136 declares):

- `docker-compose.yml:9` — `pull_policy: build` on the `backend` service, with the root-cause comment at lines 4–8 referencing root_cause#114. This is the fix: a bare `docker compose up` can no longer reuse the stale pre-bcrypt image. No other line of the compose file changed from its prior shape (frontend service and `backend_data` volume untouched).
- `backend/tests/test_docker_bcrypt.py` — new file (60 lines). `test_backend_image_built_from_current_tree_imports_app_and_bcrypt` (line 30) runs `docker compose build backend` (lines 31–36), asserts `returncode == 0` (line 37), then `docker compose run --rm --no-deps backend python -c "import bcrypt; import app.main"` (lines 40–55) and asserts `returncode == 0` (line 56). `pytest.mark.skipif` on `shutil.which("docker") is None` (lines 24–27) — on a host with no docker CLI the test skips rather than fails, so it cannot have caught anything there. This matches the repro command from reproduction#97.
- `backend/requirements.txt:7` — `bcrypt>=4.0,<5.0` present (added by ci14, per settled_question#56); deliberately untouched, correctly.
- `backend/Dockerfile:5-6` — copies and installs requirements.txt; untouched, correctly.
- `backend/app/security.py:6` — `import bcrypt` present; untouched, correctly.
- `backend/.dockerignore` — excludes only `__pycache__/`, `*.pyc`, `.pytest_cache/`, `budget_checker.db`, `tests/`; does not exclude `requirements.txt` or `app/`, so the build context is sound.

**What passed and what failed: I cannot say, and this report does not claim it.** The decisive assertions — `docker compose build backend` succeeding and `import bcrypt; import app.main` succeeding inside the built image — require a Docker daemon this environment does not have. Their first execution is the gate's own run of the test command. If the build itself fails there (pip/toolchain on `python:3.12-slim` — candidate 4 in root_cause#114's candidate list, judged unlikely), that is a build-input defect and the fix moves to the Dockerfile; the diagnosis says so explicitly.

No test was changed to make anything pass. Nothing was changed at all in this stage; the tree contains the two files code_change#136 declares and nothing else, as far as `list_files` shows.

## Acceptance coverage

The change records AC-1..AC-4 in code_change#136; the bugfix path produced no separately approved scenario ids, so the table uses the ACs:

| Scenario / AC | Test |
|---|---|
| AC-1 `docker compose up` starts backend from an image built from the current tree | `backend/tests/test_docker_bcrypt.py::test_backend_image_built_from_current_tree_imports_app_and_bcrypt` (compose-level half: covered by the `pull_policy: build` declaration, docker-compose.yml:9 — not directly asserted by any test) |
| AC-2 fresh build cannot be missing bcrypt | `backend/tests/test_docker_bcrypt.py::test_backend_image_built_from_current_tree_imports_app_and_bcrypt` |
| AC-3 a test exists that fails without the fix | same test — not demonstrated in this environment (no daemon); the argument is that the in-image import is the exact chain that crashed |
| AC-4 recurrence lever (compose image reuse) removed | none — no test asserts `pull_policy: build` is present or that a second `up` rebuilds; this is configuration read as evidence only |

## Known gaps

- **The fix has never been executed anywhere.** No Docker daemon exists in this environment; the build + in-image import assertions run for the first time at this gate. Until then, the stale-image root cause (candidate 5) vs. a build-time install failure (candidate 4) is separated by git history and file reads, not by a captured run.
- **The end-to-end outcome (both services up) is untested.** No test runs `docker compose up`, hits `GET /health` on :8000, or loads the frontend on :5174. AC-1's full behaviour rests on the manual checks in settled_question#159, which nobody here could perform.
- **`pull_policy: build` requires Compose v2** (or a recent v1); the code change records this as an unverified compatibility assumption. On an old compose it fails loudly at `up` rather than silently, but that failure mode itself was not observed.
- **The skipif weakens the gate-coverage claim.** On a host with the docker CLI absent (which includes this environment), the new test skips — so the gate's test-suite run can report green without the regression test having executed anything. The verification that matters is the gate's docker-attached run, if it has one, or the manual command in settled_question#159.
- **No test pins the fix itself.** Nothing asserts `pull_policy: build` remains in docker-compose.yml; a future edit removing it reopens the defect with no failing test.
- **Code graph blind spot persists.** Re-index / verify-links were not run (no shell); the graph holds no backend symbols, so no artifact-to-code link status can be reported here. The stale-index risk named in settled_question#155 is passed to the gate.
- **Local venv drift, recorded not resolved:** the host `.venv` runs bcrypt 5.0.0 against the `>=4.0,<5.0` pin (visible in the `cpython-314` pycache under `backend/`). Judged out of scope — the container resolves from PyPI — but it is why the local suite passed while Docker failed.
