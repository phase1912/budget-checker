# Verification report — fix-docker-bcrypt-missing (stage_instance#187, attempt 2)

## Commands run

None, with exit statuses to match. This stage has no shell access — only repository reads — so no command was run by me and none has an exit code to report. The commands that belong to this stage and who owns them:

- `python3 -m pip install -r backend/requirements.txt && python3 -m pytest backend/tests && cd frontend && npm ci && npm test` (test-command, settled at the previous verification planning) — run by the engine at this gate; its exit code is the gate's verdict, not mine.
- `python3 -m pytest backend/tests/test_docker_bcrypt.py -v` — the repro-test-command. **Warning carried forward unchanged:** the reproduction stage recorded it with the bare spelling `python -m pytest backend/tests/test_docker_bcrypt.py -v`, and the gate of stage_instance#143 ran exactly that and got exit 127 (`/bin/sh: python: command not found`) before pytest started. code_change#177 (Design notes, last bullet) records that this is a property of the recorded answer, not of the tree, and cannot be fixed in code. Unless the recorded answer has been re-recorded as `python3`, `reproduction-fixed-v1` will fail again on the same exit 127, and that failure says nothing about the fix.
- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` and `meridian sdlc verify-links` — not run by me (no shell). The graph held no backend symbols at triage, planning and implementation (`impact` returned `found: false` throughout); whether the index was refreshed is not verifiable from here.

## Results

What I verified by reading the repository this pass — the tree contains exactly what code_change#177 declares, re-confirmed line by line:

- `docker-compose.yml:9` — `pull_policy: build` on the `backend` service, with the root-cause comment at lines 4–8 citing root_cause#114. This is the fix: a bare `docker compose up` rebuilds the backend image from the current tree instead of reusing the stale pre-bcrypt image. The frontend service (lines 19–27) and `backend_data` volume (lines 29–31) are untouched; the file is 31 lines, matching code_change#177's citation.
- `backend/tests/test_docker_bcrypt.py` — 89 lines as declared. `test_backend_image_built_from_current_tree_imports_app_and_bcrypt` (line 42) runs `docker compose build backend` (lines 43–48, asserted at 49), then `docker compose run --rm --no-deps backend python -c "import bcrypt; import app.main"` (lines 52–67, asserted at 68) — the exact import chain uvicorn walks (`app.main -> routers.auth -> deps -> security`, `backend/app/security.py:6 import bcrypt`). The `_requires_docker` skipif on `shutil.which("docker") is None` (lines 35–38) is applied only to this test via decorator (line 41). `test_compose_backend_service_pins_pull_policy_build` (line 74) is daemon-free: it slices the compose file from the `  backend:` service line (line 80) and fails with the root cause spelled out if `pull_policy: build` disappears (lines 81–88). This guard runs everywhere, including daemonless gate hosts — it is verification actually exercised in this environment, unlike the container-level test.
- `backend/requirements.txt:7` — `bcrypt>=4.0,<5.0` present (added by ci14; deliberately not re-added). `backend/Dockerfile:5-6` — copies and pip-installs requirements.txt. `backend/app/security.py:6` — `import bcrypt`. All three untouched, correctly; the diagnosis established their contents were never wrong.
- No lint tooling is configured by this project. The answer to the lint question was "none", and I re-checked: the only ruff traces on disk are `.ruff_cache/` (a tool's leavings, not adoption) and hits inside `.venv/site-packages`; no manifest, config file or CI step of the project names ruff, mypy or any other linter. That "none" stands, and per the check's own wording a person is being asked here to confirm it: **this project has no static-check step to run.**

**What passed and what failed: I cannot say, and this report does not claim it.** No Docker daemon exists in this environment (established at every prior stage), so the container-level test's build + in-image import assertions have never executed anywhere; their first run is the gate's own. The two failure modes that would falsify the diagnosis there are: the build itself failing (pip/toolchain on python:3.12-slim — candidate 4 in root_cause#114, judged unlikely since bcrypt 4.x ships manylinux wheels for 3.12), which would move the fix to the Dockerfile; and the import failing inside a freshly built image, which would falsify the stale-image root cause outright.

No test was changed to make anything pass, and no file was changed in this stage. The only delta between attempt 1's accepted tree and this one is documentation: code_change#177 corrects attempt 1's change note, which had cited the container-level test at "docker-compose.yml lines 42–71" — a location that does not exist (the test lives at backend/tests/test_docker_bcrypt.py:41–71; the compose file has 31 lines).

## Acceptance coverage

The bugfix path produced no separately approved scenario ids; the change records AC-1..AC-4 in code_change#177, so the table uses those:

| Scenario / AC | Test |
|---|---|
| AC-1 `docker compose up` starts backend from an image built from the current tree | `backend/tests/test_docker_bcrypt.py::test_compose_backend_service_pins_pull_policy_build` (pins the `pull_policy: build` declaration, docker-compose.yml:9); the full up-both-services behaviour itself: none — manual only |
| AC-2 a fresh build cannot be missing bcrypt | `backend/tests/test_docker_bcrypt.py::test_backend_image_built_from_current_tree_imports_app_and_bcrypt` — never executed; requires a Docker daemon |
| AC-3 a test that fails without the fix | the container-level test (in-image import is the exact crashing chain) and the guard test (fails on the pre-fix compose file); the guard's pre-fix failure is demonstrable by reading it, the container-level one is not demonstrable here |
| AC-4 recurrence lever (compose image reuse) removed and pinned | `backend/tests/test_docker_bcrypt.py::test_compose_backend_service_pins_pull_policy_build` — the gap named in the attempt-1 report is now closed: deleting the fix line fails the suite on any host |

## Known gaps

- **The behavioural half of the fix has never run.** No Docker daemon exists here at any stage; `docker compose build backend` plus the in-image import execute for the first time at a gate or host with Docker. Until then, stale-image reuse vs. a build-time install failure is separated by git history and file reads, not a captured run.
- **The recorded repro-test-command is still wrong.** It reads bare `python` (reproduction#97.md line 51, settled_question#72); the previous gate ran it and got exit 127. If it was not re-recorded to the `python3` spelling, `reproduction-fixed-v1` fails again for a reason outside the tree — this report predicts that failure and asks that it be read as a template/record defect, not a code defect.
- **The end-to-end outcome is untested.** Nothing runs `docker compose up`, `curl http://localhost:8000/health` (expect 200 `{"status": "ok"}`), or loads the frontend on :5174; those remain manual checks (previous stage's commands-to-run answer).
- **`pull_policy: build` needs Compose v2.** An older compose errors loudly at `up`; that failure mode was not observed and could not be.
- **The guard is textual and indentation-sensitive.** `lines.index("  backend:")` (test file line 80) raises ValueError if the compose file's indentation changes — a confusing failure, though not a silent one.
- **A present-but-daemonless docker CLI fails the container-level test rather than skipping it** — the marker tests the CLI's presence, not the daemon. Loud, but the failure message would point at docker, not at bcrypt.
- **Code-graph blind spot persists.** Re-index / verify-links were not run (no shell); the index holds no backend symbols, so no artifact-to-code link status can be reported.
- **Host venv drift, recorded not resolved:** the local `.venv` runs Python 3.14 with bcrypt 5.0.0 against the `>=4.0,<5.0` pin (visible in the cpython-314 pycache). Judged out of scope — the container resolves from PyPI — but it is why the local suite passed while Docker failed, and why only the container-level test catches this regression.
