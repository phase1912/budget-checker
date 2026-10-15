# Problem brief — backend container crashes on startup: missing `bcrypt`

## Problem

The project cannot be started in Docker. When the developer runs `docker compose up`, the backend container exits at startup with `ModuleNotFoundError: No module named 'bcrypt'` (traceback: uvicorn → app/main.py create_app → app/routers/auth.py → app/deps.py → app/security.py line 6, `import bcrypt`) and leaves with exit code 1, so the application never comes up.

The puzzle at the centre of the problem: the dependency is *already declared*. `backend/requirements.txt` line 7 carries `bcrypt>=4.0,<5.0`, and the backend Dockerfile installs from that file (`COPY requirements.txt .` then `RUN pip install --no-cache-dir -r requirements.txt`, backend/Dockerfile:5–6) — yet the image the container runs from does not contain the module. Why an already-declared dependency is missing from the built image is unknown; that is the diagnosis this work owes. A likely-related inconsistency: the local `.venv` has bcrypt 5.0.0 installed, outside the declared `<5.0` pin, so local and container environments are evidently not built from the same inputs.

## Who is affected

The project's developer (Bohdan), who reports hitting this on every startup attempt: each `docker compose up` fails to bring the backend up. Source: the developer's own answer (`who-is-affected`). No other users are known to run this stack.

## Evidence

The evidence is first-hand and reproducible but thin in quantity, as expected for a single-developer project:

- An actual error log from `docker compose`: `ModuleNotFoundError: No module named 'bcrypt'` raised in `app/security.py` (`import bcrypt`), backend container exiting with code 1 (from the answer to `evidence`, Bohdan — one recorded occurrence; the "every time" frequency is the developer's report, not a log count).
- `backend/app/security.py:6` imports bcrypt; it is used at lines 17–18 (`bcrypt.gensalt`, `bcrypt.hashpw`) and line 25 (`bcrypt.checkpw`) — the dependency is genuinely required by committed code, not a stray import.
- `backend/requirements.txt:7` already declares `bcrypt>=4.0,<5.0`, and `backend/Dockerfile:5–6` installs from that file — which makes the absence of the module in the image the unexplained part.
- `docs/sdlc/ci14/` recorded the *same* `No module named 'bcrypt'` symptom fixed in the CI environment (requirements gained `bcrypt>=4.0,<5.0` and `PyJWT>=2.8,<3.0`); the Docker-image side was never revisited, and ci14's own review flagged Python-version drift (3.14 vs the Dockerfile's 3.12) — the same drift visible in the local `.venv`'s bcrypt 5.0.0.

No other users, tickets or metrics exist for this; the report is a first-hand, reproducible failure.

## Cost of inaction

While nothing changes:

- The project remains unrunnable via Docker — `docker compose up` does not produce a working stack, so the Dockerised delivery produced by the earlier `budget-checker-dockerize` SDLC run is effectively dead for local use.
- Any work that depends on a running stack (manual verification, the acceptance criteria of other runs, future onboarding of a second developer) is blocked or has to work around a broken compose setup.
- The drift mechanism — local environment and Docker image being built from different inputs (venv on bcrypt 5.0.0, requirements pinning `<5.0`, image missing the module entirely) — stays invisible and can keep producing failures of the same shape, in Docker or in CI.

## Success metrics

Each of these is observable today, without new instrumentation, unless marked:

1. `docker compose up` brings up both backend and frontend, with no container exiting on startup. Measured by running it and reading container states (from the answer to `success-signal`, Bohdan).
2. The backend answers a health request: `GET /health` on the backend port returns success. The endpoint exists (`backend/app/routers/health.py:6`) and `backend/tests/test_health.py` covers it locally; running the equivalent request against the container needs no new tooling.
3. `ModuleNotFoundError: No module named 'bcrypt'` does not appear in the backend container logs on a clean (no-cache) build. Measured by reading `docker compose up --build` output.
4. A regression test exists that fails without the fix and passes with it — **requires work that does not exist yet**: a smoke test under `backend/tests/` that imports `app.main` against the installed environment must be written as part of the fix; this is the only metric needing new instrumentation first.
5. The diagnosis records the actual root cause — why a declared dependency was absent from the image — so the failure mode is understood, not just patched. Measured by the diagnosis document naming the mechanism.

## Out of scope

- Frontend changes of any kind; it is only a witness that it also comes up.
- Changes to hashing behaviour, JWT handling or the auth API surface.
- Reconciling the local `.venv` (bcrypt 5.0.0) with the requirements pin as an environment-policy change — noted, but only touched if it turns out to be the root cause.
- Dockerfile modernisation (base-image changes, multi-stage builds) beyond what the fix requires.
- Re-adding bcrypt to `requirements.txt` as if it were never declared — it is already there (ci14 added it for CI); re-adding it without understanding why the image misses it would mask the problem.
- Adding CI changes: the ci14 run already fixed this same symptom for the CI environment; this work targets the Docker image, not the workflow.

## Assumptions

Everything here is believed but unconfirmed:

- The frontend currently works and will come up under compose once the backend stops dying; only the backend failure was observed.
- The image in the crash was built from the committed `requirements.txt` that already lists bcrypt (rather than from an older version of the file).
- A stale Docker cache or an image built before the bcrypt line was added is a plausible root cause; alternatively a `pip install` failure on `python:3.12-slim` (a source build of bcrypt would need a compiler this image lacks, though this platform should get a binary wheel) that did not fail the build. Neither is confirmed.
- The version drift (venv bcrypt 5.0.0 vs the `<5.0` pin) is a symptom of environment drift, not a separate bug to fix now.
- Single-developer project: no other environments or users are affected.
- The code graph holds no symbols for this repository's backend (`impact` and `query` returned nothing for this area), so no upstream callers were measured — the import chain is taken from the traceback and from reading the files.

## Open questions

- What is the actual root cause — why is a declared dependency missing from the built image? Candidates: stale cache / image built before the dependency line was added; a build-time pip failure that did not fail the image build; something in `.dockerignore` or the build context. The bugfix path's diagnosis stage must settle this.
- Should the bcrypt pin (`>=4.0,<5.0`) be re-examined once the cause is known, given the local environment sits on 5.0.0? Deferred to diagnosis.
- Exact shape of the regression test (import smoke test vs exercising an auth route against the container) — to be fixed during the bugfix's acceptance work.