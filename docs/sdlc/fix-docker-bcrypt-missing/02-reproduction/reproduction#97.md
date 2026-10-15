# Reproduction — backend container crashes at startup: `ModuleNotFoundError: No module named 'bcrypt'`

## Symptom

Running `docker compose up` from the repository root brings up the frontend, but the backend container exits during startup with exit code 1. The backend log contains:

```
Traceback (most recent call last):
  ...
  File "app/main.py", in create_app
  File "app/routers/auth.py", ...
  File "app/deps.py", ...
  File "app/security.py", line 6, in <module>
    import bcrypt
ModuleNotFoundError: No module named 'bcrypt'
```

(The chain `uvicorn → app/main.py → app/routers/auth.py → app/deps.py → app/security.py:6` is from the developer's recorded log, settled_question#54; I could not execute Docker in this environment, so I did not capture the traceback myself — see Open questions.)

The import site is real and verified by direct read: `backend/app/security.py` line 6 is `import bcrypt`, with bcrypt actually used at lines 17–18 (`bcrypt.gensalt`, `bcrypt.hashpw`) and line 25 (`bcrypt.checkpw`).

## Expected behaviour

`docker compose up` should start both services and keep the backend running; the backend should answer a health request. Concretely, `GET /health` returns `{"status": "ok"}` — the endpoint is implemented in `backend/app/routers/health.py` and asserted by `backend/tests/test_health.py`.

What the repository says about the dependency: `backend/requirements.txt` line 7 already declares `bcrypt>=4.0,<5.0`, and `backend/Dockerfile` installs from that file — `COPY requirements.txt .` (line 5) followed by `RUN pip install --no-cache-dir -r requirements.txt` (line 6). So the *specified* behaviour — an image built with every declared dependency — and the *observed* behaviour — an image without the module — contradict each other. `docker-compose.yml` builds the backend from `./backend` (line 3) and mounts only `backend_data:/data` (lines 10–11), so nothing in compose shadows site-packages or overrides the command. Why the built image lacks a declared dependency is the open diagnosis question, not a settled fact.

## Steps to reproduce

1. From the repository root (branch `sdlc/budget1`), run `docker compose up --build`.
2. Watch the frontend service come up on port 5174.
3. Observe the backend container exit with code 1 and the traceback above, rooted at `app/security.py:6` (`import bcrypt`).

Expected instead: both containers stay up and `curl http://localhost:8000/health` returns `200 {"status": "ok"}`.

Frequency: every attempt, per the developer (settled_question#74: "Відтворюється щоразу"). Nothing conditional is known to change the outcome.

A narrower, deterministic form of the same defect:

`docker compose build backend && docker compose run --rm --no-deps backend python -c "import app.main; import bcrypt"`

The second half dies with the same `ModuleNotFoundError: No module named 'bcrypt'`. A plain `docker compose up` alone is not sufficient evidence, since compose may serve a stale image — the build is included so the inputs are current.

## Failing test

Path: `backend/tests/test_docker_bcrypt.py` (new file; written as part of the fix, not yet present on disk — a read returned `found: false`).

The single shell command that runs only this test:

```
python -m pytest backend/tests/test_docker_bcrypt.py -v
```

(One command, one line: pytest given the single new file path runs it and nothing else from the suite. This is the command recorded in `repro-test-command`; it must FAIL now and pass at the verification gate.)

What the test does internally: `subprocess.run(["docker", "compose", "build", "backend"], cwd=<repo root>, check=True)` followed by `subprocess.run(["docker", "compose", "run", "--rm", "--no-deps", "backend", "python", "-c", "import app.main; import bcrypt"], cwd=<repo root>, check=True)`. The build step is included because a plain `docker compose up` can reuse a stale image and mask the defect.

Expected failure output right now (shape — the CalledProcessError carries the container's stderr):

```
backend/tests/test_docker_bcrypt.py::test_backend_image_can_import_app_and_bcrypt FAILED
E   subprocess.CalledProcessError: Command '['docker', 'compose', 'run', '--rm', '--no-deps', 'backend', 'python', '-c', 'import app.main; import bcrypt']' returned non-zero exit status 1.
E   stderr: ... ModuleNotFoundError: No module named 'bcrypt'
```

I have not executed this test: this environment has no shell access, so the output above is the expected failure derived from the developer's recorded container log and the file evidence, not a captured run. The gate must run the command above and confirm it fails as described.

Why container-level and not a local smoke test: the local `.venv` *has* bcrypt (5.0.0 — itself outside the `>=4.0,<5.0` pin at `backend/requirements.txt:7`), so any test run against the local interpreter passes and proves nothing. The defect lives in the built image, so the only honest failing test builds and imports inside it.

## Environment

- Branch `sdlc/budget1`, working tree otherwise clean except untracked `docs/sdlc/` artifacts.
- Backend image: `python:3.12-slim` (`backend/Dockerfile:1`), `pip install --no-cache-dir -r requirements.txt` (`backend/Dockerfile:6`).
- `backend/requirements.txt:7` declares `bcrypt>=4.0,<5.0` — added by the earlier `docs/sdlc/ci14/` run to fix the same symptom in CI, not in Docker.
- Local development venv: Python 3.14 with bcrypt 5.0.0 — outside the declared pin, so local and container environments are demonstrably built from different inputs.
- `docker-compose.yml` builds backend from `./backend`; no bind mounts over the install, no overridden command.
- Reproduces everywhere by report: the developer says every `docker compose up` fails. Not verified on a second machine or a clean checkout.

## Open questions

- I could not run Docker or the test in this environment; the symptom rests on the developer's recorded log (settled_question#54) plus the file evidence. The gate run must execute the failing-test command and confirm it fails as described.
- Root cause is unknown: why does an image built from a requirements file that lists bcrypt not contain it? Leading candidates: the deployed image predates the bcrypt line in requirements.txt and was never rebuilt (the Dockerfile was last touched by the `budget-checker-dockerize` run, before ci14 added the dependency); or a build-time install problem on `python:3.12-slim`. If the build-then-import command succeeds on the gate machine, that is a genuine "not reproduced" finding and the fix reduces to rebuild/cache hygiene — the diagnosis stage must record that rather than bending the test.
- Whether the `>=4.0,<5.0` pin itself should be revisited (given the venv sits on 5.0.0) is deferred to diagnosis, per the change brief.
- Note for the process: the prior three attempts of this gate failed on formatting only — the repro-test-command answer read as multi-line prose. The substance carried over unchanged from reproduction#75; this draft states the command as a single one-line shell command.
