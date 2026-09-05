# Code Change — Dockerize All Services (verified, attempt 3)

## Summary

Both services are now buildable and runnable inside Docker, orchestrated by Docker Compose, so the whole stack starts with one `docker compose up` from the repository root. The FastAPI backend runs in `python:3.12-slim` under uvicorn; the React/Vite frontend is built in a `node:22-alpine` stage and served by `nginx:1.27-alpine` with an SPA fallback (`frontend/nginx.conf`). Compose maps the backend to host port 8000 and the frontend to 5174 (container port 80), stores SQLite on a named volume at `/data` via `DATABASE_URL=sqlite:////data/budget_checker.db` — already read by `backend/app/database.py:6` — and sets `ALLOWED_ORIGINS=http://localhost:5174`, matching the backend's own CORS default (`backend/app/main.py:19`) and the origin nginx serves. No application source, route, or schema was modified; the change is purely additive packaging.

This attempt re-verified every file from attempt 1 directly in the tree — `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `docker-compose.yml`, and both `.dockerignore` files — and cross-checked the three configuration touchpoints (`backend/app/database.py:6`, `backend/app/main.py:19`, and the `VITE_API_BASE_URL` build arg against `frontend/src/api/client.ts` / `frontend/src/stores/AuthStore.ts`). All are present and consistent; nothing was rewritten.

## Requirements implemented

Brief acceptance criteria (chore — the acceptance record is these criteria):

1. **Single-command start on a Docker-only machine** — `docker-compose.yml` builds and runs both services; `backend/Dockerfile` installs from `backend/requirements.txt`, copies `backend/app/`, and launches uvicorn on 8000; `frontend/Dockerfile` runs `npm ci && npm run build` and serves `dist/` via nginx. No Python or Node required on the host.
2. **Unchanged behaviour / no CORS or API-base errors** — `frontend/Dockerfile` sets `ARG/ENV VITE_API_BASE_URL=http://localhost:8000` before `npm run build` (read at build time by the frontend), and compose sets `ALLOWED_ORIGINS=http://localhost:5174`, matching the origin nginx serves the app on and the backend's CORS default in `backend/app/main.py`.
3. **Data survives `docker compose down && up`** — SQLite lives on named volume `backend_data` mounted at `/data`, with an absolute `DATABASE_URL` removing the CWD-relative ambiguity of the default `sqlite:///./budget_checker.db` (the repo already contains stray `backend/budget_checker.db` files from native runs).

## Symbols changed

None. No existing function, class or method was edited — the file set is entirely new:

- `backend/Dockerfile` (new)
- `backend/.dockerignore` (new — excludes `__pycache__`, `.pytest_cache`, `tests/`, and the stray local `budget_checker.db`)
- `frontend/Dockerfile` (new, multi-stage node build + nginx serve)
- `frontend/nginx.conf` (new, SPA fallback)
- `frontend/.dockerignore` (new — excludes `node_modules/`, `dist/`, `coverage/`)
- `docker-compose.yml` (new)

The only existing behaviour touched is `DATABASE_URL` / `ALLOWED_ORIGINS` / `VITE_API_BASE_URL` resolution — via environment and build-arg configuration, not code. The symbol index holds nothing for these files, so no `impact` counts exist; the blast-radius judgement is from direct file inspection, as recorded in the change brief.

## Design notes

- **Static nginx serving instead of the Vite dev server.** A production-style build exercises the real frontend build and adds one small nginx config, whereas the dev-server route would ship Vite in the image. Consequence: `VITE_API_BASE_URL` must point at the host-mapped backend port (8000) and CORS must list the frontend origin (5174) — both are set.
- **SQLite-on-a-volume instead of a Postgres service.** `psycopg2-binary` is already pinned in `backend/requirements.txt`, so Postgres is a one-line compose change later, but the brief's acceptance criteria do not require a database server and the tree assumes SQLite today.
- **Absolute `DATABASE_URL`** rather than the relative default, plus a volume, makes persistence unambiguous despite the stray host-side `budget_checker.db` files.
- **`.dockerignore` excludes tests, caches, and the stray local DB** so the build context stays small and host data cannot ship in the image.

## Risks

- **Acceptance criteria validated by inspection, not execution.** No Docker/Compose harness exists in the repo; `docker compose up`, `/health` on 8000, the frontend on 5174, and the down/up persistence check all require a Docker daemon. First real run may surface image-version drift (python:3.12 vs the local 3.14 that produced the `__pycache__` files).
- **Host port collisions.** If something already listens on 8000 or 5174, `docker compose up` fails or the CORS/VITE defaults silently point at the wrong origin. Documented defaults, not parameterised.
- **Hardcoded localhost origins.** `VITE_API_BASE_URL` is baked at image build time; accessing the stack from any host other than `localhost` breaks API calls until the arg is overridden.
- **SQLite under container concurrency.** Single uvicorn worker, so fine for local dev; the volume-backed SQLite file is not a production data story — noted, not solved.
- **Implicit coupling on the build arg.** `VITE_API_BASE_URL` must be set as ARG/ENV before `npm run build`; if the Dockerfile is later reordered, the default silently reverts — it happens to match, but is fragile.
