pull_request — NOT CREATED (attempt 3): forge still unidentified; no URL to report

## What is confirmed this frame

The diff now exists in this frame's tree: `docker-compose.yml` (25 lines, read in full), `backend/Dockerfile` (15 lines), `frontend/Dockerfile` (23 lines), and `frontend/nginx.conf` (13 lines) all read directly — resolving attempt 2's finding that the packaging files were invisible. The review gate passed (settled_question#108, Bohdan) on review_report#106 (READY), and branch strategy is "stay" (settled_question#128), so the base would be the repository default branch.

## What still blocks creation

- This frame has repository read/write and graph tools only: no shell, no git remote, no forge CLI (`gh`/`glab`/`tea`) to run, and no `pr-create-command` answer naming one. Opening through a forge API or MCP server is disallowed; a PR opened any other way cannot be confirmed by `pr-verify-command`, and an unconfirmed claim fails the gate like a missing PR.
- No `pr-base` answer exists anywhere in the chain; with strategy "stay" the default branch is the correct base.

## Ready to fire

The complete body is on disk at `docs/sdlc/budget-checker-dockerize/08-delivery/pr-body.md` (Summary / Requirements covered / Testing / Risk and blast radius, drawn from change_brief#34, verification_report#76 and review_report#106).

## Person-steps to finish

1. `git remote -v` to identify the forge; confirm an authenticated CLI and check its flags against `--help`.
2. Create the PR from the current branch to the default branch with `--body-file docs/sdlc/budget-checker-dockerize/08-delivery/pr-body.md`.
3. Re-run this stage so the pull_request artifact can be registered with the URL as its first line, parented to review_report#106.

## Prepared PR body (verbatim from pr-body.md)

## Summary

Dockerizes both services so the whole stack starts with one `docker compose up` from the repository root: the FastAPI backend runs under uvicorn on host port 8000 (python:3.12-slim), and the React/Vite frontend is built in a node:22-alpine stage and served by nginx:1.27-alpine on host port 5174 with an SPA fallback. SQLite lives on the named `backend_data` volume at `/data` via an absolute `DATABASE_URL=sqlite:////data/budget_checker.db`, and `ALLOWED_ORIGINS=http://localhost:5174` plus a `VITE_API_BASE_URL=http://localhost:8000` build arg keep CORS and the API base consistent with the existing code defaults (`backend/app/main.py:19`, `backend/app/database.py:6`, `frontend/src/api/client.ts:1`). The change is a chore and purely additive: six new files, no application source, route, or schema modified.

## Requirements covered

Chore — the change brief's three acceptance criteria are the whole acceptance record (change_brief#34):

- Single-command start on a Docker-only machine: `docker-compose.yml` + `backend/Dockerfile` + `frontend/Dockerfile`; no host Python or Node needed.
- Unchanged behaviour, no CORS or API-base errors: env/build-arg values match existing defaults at `main.py:19`, `database.py:6`, `client.ts:1`, `AuthStore.ts:25`.
- Data survives `docker compose down && up`: `backend_data` named volume + absolute `DATABASE_URL`; `.dockerignore` keeps stray host-side DB files out of the images.

## Testing

Verification (verification_report#76) and review (review_report#106) were inspection-only — no Docker daemon was available in any stage:

- All six packaging files read and cross-checked against every configuration touchpoint; all consistent.
- Compose healthcheck absent (review finding, low, non-blocking); build-arg ordering fragility in `frontend/Dockerfile:14-15` flagged (review finding, low).
- Backend pytest suite (`backend/tests/`, 4 files) and frontend vitest suite exist but were not run.
- None of the acceptance criteria has been executed. A person should run, once: `docker compose up --build`; `curl http://localhost:8000/health`; browse http://localhost:5174; create data, `docker compose down && up`, confirm persistence; `docker compose down -v` to confirm the volume is the persistence boundary.

## Risk and blast radius

- No existing file depends on the new ones; the only runtime touchpoints are the three environment/build-arg variables, all set to values matching existing defaults.
- Dominant risk: first real `docker compose up` is the first execution of the capability — image-build failures (python:3.12-slim vs local 3.14), host port collisions on 8000/5174, or volume permissions are all possible and inspection cannot catch them.
- `VITE_API_BASE_URL` is baked at build time and hardcoded to localhost:8000; non-localhost access breaks API calls until the arg is overridden.
- The frontend image's correctness rests on `ARG/ENV VITE_API_BASE_URL` preceding `npm run build` — fragile to Dockerfile reordering.
- Post-merge watch: run the five-command manual sequence above before treating the capability as delivered.