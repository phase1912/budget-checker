# Change brief — backend crashes in Docker on missing `bcrypt`

## What changes

`docker compose up` brings up both services and the backend stays up: the container no longer dies at import time with `ModuleNotFoundError: No module named 'bcrypt'`. The fix is expected in the Docker build inputs (backend/requirements.txt, backend/Dockerfile, possibly .dockerignore / build flags) — not in Python code. Because the dependency is already declared in the tree, an important part of the outcome is knowing *why* it was absent from the image, so the same drift cannot recur silently.

## Kind of change

bugfix

## Why this kind

The maker recommended bugfix/chore-scale and the decision recorded is **bugfix** (change_kind#37, Bohdan). I agree, and did not argue for anything smaller. This is a defect against existing intent — `bcrypt>=4.0,<5.0` is already declared (backend/requirements.txt:7), and the code that needs it is committed and correct: backend/app/security.py:6 `import bcrypt`, used at lines 17–18 (`bcrypt.gensalt`, `bcrypt.hashpw`) and line 25 (`bcrypt.checkpw`). Nothing new is being built, no public interface or stored schema moves. It is not a chore, because the outcome is *not* obvious: requirements.txt already lists the module the container says is missing, so the root cause (stale image cache, an image built before line 7 was added, a build-context or wheel-installation problem on python:3.12-slim) is unknown and needs reproduction and diagnosis — exactly the bugfix path.

Evidence from the tree (ordinary reads, not graph calls):
- backend/Dockerfile:5–6 — `COPY requirements.txt .` then `RUN pip install --no-cache-dir -r requirements.txt`, so the image *should* contain bcrypt from the committed file.
- backend/Dockerfile:1 — `python:3.12-slim`; bcrypt ≥4.1 ships binary wheels for this platform, but a source build would fail without a compiler, a candidate root cause.
- docker-compose.yml:2–11 — `build: ./backend`, nothing overriding the build or mounting over site-packages.
- Version drift noted in sizing: the local .venv has bcrypt 5.0.0 while requirements.txt pins `<5.0`, so local and container environments are not built from the same inputs.
- backend/tests/ has test_health.py and test_auth.py — existing coverage the regression test can extend.

## Expected blast radius

What I asked the code graph and what came back:
- `impact("hash_password", upstream) → found: false` — the index holds no symbol by that name.
- `query("password hashing / auth security backend") → 0 hits` — the graph holds no symbols for this repository's backend at all.

So the graph could not measure this change; the radius below is argued from the files and the traceback in the goal, not from the index.

- **backend/app/security.py** — no Python edit; it is the crash site (line 6) and the consumer of bcrypt. Its callers (app/deps.py → app/routers/auth.py → app/main.py create_app) all start working again once the import succeeds; none change.
- **backend/requirements.txt** — single entry point for backend dependencies; consumed only by backend/Dockerfile:6 in the repo.
- **backend/Dockerfile** — single owner of the image build; nothing else in the repository references it except docker-compose.yml:3.
- **docker-compose.yml** — expected to be read-only for this fix; touched only if diagnosis shows a build-context cause.
- **backend/tests/** — gains a test; nothing existing breaks.

## Acceptance criteria

(first sketch; the diagnosis stage sharpens)

1. `docker compose up --build` starts both services; the backend container stays running and `GET /health` (or the backend root) returns success from localhost:8000.
2. The traceback `ModuleNotFoundError: No module named 'bcrypt'` no longer appears in the backend container logs on a clean build (no cache).
3. A test exists that fails without the fix and passes with it — e.g. a smoke test that imports `app.main` / exercises an auth route against the installed environment, added under backend/tests/.
4. The diagnosis names the actual root cause (why an already-declared dependency was missing from the image), recorded so the drift mechanism is understood, not just patched.

## Out of scope

- Reconciling the local .venv (bcrypt 5.0.0) with the requirements.txt pin (`<5.0`) as a tooling/environment-policy change; noted, but only touched if it turns out to be the root cause.
- Switching base images, adding multi-stage builds, or other Dockerfile modernisation beyond what the fix requires.
- Any change to hashing behaviour, JWT handling, or the auth API surface.
- Frontend changes of any kind; it is only an acceptance witness that it also comes up.

## Open questions

- What is the actual root cause? requirements.txt:7 already declares bcrypt and the Dockerfile installs from it — so why was the module absent? Candidates: image built before the dependency line was added and not rebuilt; a `pip install` failure on python:3.12-slim (source build without toolchain) that did not fail the build; something in the build context or cache. The diagnosis step must settle this — the one-line fix without the cause would leave the drift mechanism in place.
- Should the bcrypt pin be re-examined (the local env is on 5.0.0, outside the declared range) once the cause is known? Decided during diagnosis, not now.