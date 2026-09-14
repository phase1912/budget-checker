pull_request — NOT CREATED (attempt 2): forge now identified as GitHub, command fully resolved, but no shell in this frame to run it

## What is confirmed this frame

- **Forge identified** (resolving attempt 1's blocker): `.git/config` names origin as `https://github.com/phase1912/budget-checker.git` — the forge is **GitHub**, and prior PRs in this repo were opened at `https://github.com/phase1912/budget-checker/pull/3` and `/pull/5`, confirming the URL shape.
- **Branch and base**: current branch is `dockerize-budget-checker` (`.git/HEAD`; pushed to origin at commit `22e921096ac9f12849ad470244bf9159b866f998` per `.git/refs/remotes/origin/dockerize-budget-checker`). No `pr-base` answer exists in the chain; branch strategy is "stay" (settled_question#128), so the base is the repository default branch, **`master`** (`.git/config` tracks `master` from origin).
- **PR body finalised on disk**: `docs/sdlc/budget-checker-dockerize/08-delivery/pr-body.md` (29 lines), read back verbatim this frame — Summary / Requirements covered / Testing / Risk and blast radius, drawn from change_brief#34, verification_report#76 and review_report#106.
- **Review gate passed** (settled_question#108, Bohdan) on review_report#106 (READY).

## What still blocks creation

This frame has repository read/write and graph tools only — no shell, no `gh` CLI execution. The PR cannot be opened through a forge API or MCP server, and a PR opened any other way cannot be confirmed by a `pr-verify-command`, so an unconfirmed claim fails the gate as surely as a missing one. No URL is reported because none exists.

## Person-steps to finish (mechanical, nothing left to decide)

1. `gh pr create --repo phase1912/budget-checker --base master --head dockerize-budget-checker --title "Dockerize all services" --body-file docs/sdlc/budget-checker-dockerize/08-delivery/pr-body.md`
2. Verify: `gh pr view <url>` (or a `$PR_URL`-reading check) exits non-zero unless GitHub confirms the PR.
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
- **None of the acceptance criteria has been executed.** A person should run, once: `docker compose up --build`; `curl http://localhost:8000/health`; browse http://localhost:5174; create data, `docker compose down && up`, confirm persistence; `docker compose down -v` to confirm the volume is the persistence boundary.

## Risk and blast radius

- No existing file depends on the new ones; the only runtime touchpoints are the three environment/build-arg variables, all set to values matching existing defaults.
- Dominant risk: first real `docker compose up` is the first execution of the capability — image-build failures (python:3.12-slim vs local 3.14), host port collisions on 8000/5174, or volume permissions are all possible and inspection cannot catch them.
- `VITE_API_BASE_URL` is baked at build time and hardcoded to localhost:8000; non-localhost access breaks API calls until the arg is overridden.
- The frontend image's correctness rests on `ARG/ENV VITE_API_BASE_URL` preceding `npm run build` — fragile to Dockerfile reordering.
- Post-merge watch: run the five-command manual sequence above before treating the capability as delivered.
