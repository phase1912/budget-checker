# Problem brief — backend container crashes on startup: missing `bcrypt`

## Problem

The project cannot be started in Docker. When the developer runs `docker compose up`, the frontend starts but the backend container exits at startup with `ModuleNotFoundError: No module named 'bcrypt'` (traceback: uvicorn → app/main.py create_app → app/routers/auth.py → app/deps.py → app/security.py line 6, `import bcrypt`) and leaves with exit code 1, so the application never comes up. This reproduces on every startup attempt (developer's answer to `repro-steps`, Bohdan; the log itself is a single recorded occurrence).

The puzzle at the centre of the problem: the dependency is *already declared*. `backend/requirements.txt` line 7 carries `bcrypt>=4.0,<5.0`, and the backend Dockerfile installs from that file — `COPY requirements.txt .` on backend/Dockerfile:5 followed by `RUN pip install --no-cache-dir -r requirements.txt` on backend/Dockerfile:6. docker-compose.yml builds the backend from `./backend` (docker-compose.yml:3) and mounts only `/data` (docker-compose.yml:10–11), so nothing in the compose file shadows site-packages. Yet the image the container runs from does not contain the module. Why an already-declared dependency is missing from the built image is unknown; that is the diagnosis this work owes. A likely-related inconsistency, reported but not re-verified here: the local `.venv` has bcrypt 5.0.0 installed, outside the declared `<5.0` pin (from the answer to `expected-symbols`), so local and container environments are evidently not built from the same inputs.

## Who is affected

The project's developer (Bohdan), who reports hitting this on every startup attempt: each `docker compose up` fails to bring the backend up. Source: the developer's own answer (`who-is-affected`). No other users are known to run this stack.

## Evidence

The evidence is first-hand and reproducible but thin in quantity, as expected for a single-developer project:

- An actual error log from `docker compose`: `ModuleNotFoundError: No module named 'bcrypt'` raised in `app/security.py` (`import bcrypt`), backend container exiting with code 1 (from the answer to `evidence`, Bohdan — one recorded occurrence; the "every time" frequency is the developer's report, not a log count).
- `backend/app/security.py:6` imports bcrypt; it is used at lines 17–18 (`bcrypt.gensalt`, `bcrypt.hashpw`) and line 25 (`bcrypt.checkpw`) — the dependency is genuinely required by committed code, not a stray import.
- `backend/requirements.txt:7` already declares `bcrypt>=4.0,<5.0`, and the Dockerfile installs from that file (backend/Dockerfile:5–6, contents read directly this attempt, addressing the prior gate's complaint that the file contents were not in evidence) — which makes the absence of the module in the image the unexplained part.
- `docs/sdlc/ci14/` recorded the *same* `No module named 'bcrypt'` symptom fixed in the CI environment (requirements gained `bcrypt>=4.0,<5.0` and `PyJWT>=2.8,<3.0`; from the answer to `prior-attempts`); the Docker-image side was never revisited, and ci14's own review flagged Python-version drift (3.14 vs the Dockerfile's 3.12) — the same drift visible in the local `.venv`'s bcrypt 5.0.0.
- The earlier `budget-checker-dockerize` SDLC run delivered `docker compose up` as working and recorded no bcrypt problem; this is a regression in, or a gap left by, that delivered work (from `prior-attempts`).

No other users, tickets or metrics exist for this; the report is a first-hand, reproducible failure.

## Cost of inaction

While nothing changes:

- The project remains unrunnable via Docker — `docker compose up` does not produce a working stack, so the Dockerised delivery produced by the earlier `budget-checker-dockerize` SDLC run does not work locally.
- Any work that depends on a running stack (manual verification, the acceptance criteria of other runs, onboarding of a second developer) is blocked or has to work around a broken compose setup.
- The drift mechanism — local environment and Docker image being built from different inputs (venv on bcrypt 5.0.0, requirements pinning `<5.0`, image missing the module entirely) — stays invisible and can keep producing failures of the same shape, in Docker or in CI, as it already has once in CI (ci14).

## Success metrics

Each of these is observable tomorrow with an explicit measurement, unless marked as requiring new work:

1. `docker compose up` brings up both backend and frontend, with no container exiting on startup. Measured by running it and reading `docker compose ps` (both services `Up`, none `Exited`) (from the answer to `success-signal`, Bohdan).
2. The backend answers a health request: `curl -sf http://localhost:8000/health` returns `{"status":"ok"}`. The endpoint exists (`backend/app/routers/health.py:6`, `@router.get("/health")` returning `{"status": "ok"}` at lines 7–8) and `backend/tests/test_health.py` covers it locally; running the request against the container needs no new tooling.
3. `ModuleNotFoundError: No module named 'bcrypt'` does not appear in the backend container logs on a clean (no-cache) build. Measured by reading `docker compose up --build` output.
4. A regression test exists that fails without the fix and passes with it. The command is already settled from the reproduction work: `python -m pytest backend/tests/test_docker_bcrypt.py -v` (from `repro-test-command`) — the file must be written as part of the fix, so this metric **requires new work (the test) before it can be measured**.
5. The diagnosis records the actual root cause — why a declared dependency was absent from the image — so the failure mode is understood, not just patched. Measured by the diagnosis document naming the mechanism.

## Out of scope

- Frontend changes of any kind; it is only a witness that it also comes up.
- Changes to hashing behaviour, JWT handling or the auth API surface.
- Reconciling the local `.venv` (bcrypt 5.0.0) with the requirements pin as an environment-policy change — noted, but only touched if it turns out to be the root cause.
- Dockerfile modernisation (base-image changes, multi-stage builds) beyond what the fix requires.
- Re-adding bcrypt to `requirements.txt` as if it were never declared — it is already there (ci14 added it for CI); re-adding it without understanding why the image misses it would mask the problem.
- CI changes: the ci14 run already fixed this same symptom for the CI environment; this work targets the Docker image, not the workflow.

## Assumptions

Everything here is believed but unconfirmed:

- The frontend currently works and will come up under compose once the backend stops dying; only the backend failure was observed.
- The image in the crash was built from the committed `requirements.txt` that already lists bcrypt (rather than from an older version of the file).
- Candidate root causes, none confirmed: a stale Docker cache or an image built before the bcrypt line was added; a `pip install` failure on `python:3.12-slim` that did not fail the build (a source build of bcrypt would need a compiler this image lacks, though this platform should get a binary wheel — the wheel claim itself is unverified); something in `.dockerignore` or the build context.
- The version drift (venv bcrypt 5.0.0 vs the `<5.0` pin) is a symptom of environment drift, not a separate bug to fix now.
- Single-developer project: no other environments or users are affected.
- The code graph holds no symbols for this repository's backend (`impact` and `query` returned nothing for this area, per `expected-symbols`), so no upstream callers were measured — the import chain is taken from the traceback and from reading the files.

## Open questions

- What is the actual root cause — why is a declared dependency missing from the built image? Candidates are listed under Assumptions; the bugfix path's diagnosis stage must settle this.
- Should the bcrypt pin (`>=4.0,<5.0`) be re-examined once the cause is known, given the local environment sits on 5.0.0? Deferred to diagnosis.
- Exact shape of the regression test `backend/tests/test_docker_bcrypt.py` (import smoke test vs exercising an auth route against the container) — to be fixed during the bugfix's acceptance work.
- Template note from the prior gate: the reviewer could not apply part of its rubric because the Dockerfile contents were cited but not supplied in evidence; this attempt reads backend/Dockerfile directly, and the stage template's `reads` should include it so this does not recur (the developer accepted that stage with this noted as a template gap).