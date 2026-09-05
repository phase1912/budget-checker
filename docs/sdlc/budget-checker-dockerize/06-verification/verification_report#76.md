# Verification — Dockerize All Services (verification-direct, run-verification-v1, attempt 1)

## Commands run

No command could be executed in this frame: the tools available to this stage are repository read/graph tools only — there is no shell, no Docker daemon, and no test runner access. Everything below was verified by direct file inspection; every executable check is reported under Known gaps as unverified.

- Read `docker-compose.yml` (25 lines) — inspected, not run. `docker compose config` not executed.
- Read `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `backend/.dockerignore`, `frontend/.dockerignore` — inspected, not built. `docker compose build` not executed.
- Read `backend/app/database.py`, `backend/app/main.py`, `backend/app/routers/health.py`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/api/client.ts` — cross-checked configuration touchpoints (see Results).
- Read `backend/tests/test_health.py` and listed both test trees.
- Index/verify-links: `node .meridian/run.cjs analyze --index-only` could not be run from this frame; index state remains unverified.

## Results

**Verified by inspection (all green):**

1. **Single-command start** — `docker-compose.yml` defines both services with correct build contexts (`./backend`, `./frontend`); `backend/Dockerfile` installs from `requirements.txt` (pins fastapi, uvicorn, sqlalchemy), copies `backend/app/`, runs uvicorn on 8000; `frontend/Dockerfile` is a multi-stage node:22-alpine build (`npm ci` + `npm run build`) served by nginx:1.27-alpine. Consistent end to end.
2. **CORS / API base** — compose sets `ALLOWED_ORIGINS: http://localhost:5174`, matching the backend default at `backend/app/main.py:19` and the origin nginx serves on host port 5174; frontend `VITE_API_BASE_URL=http://localhost:8000` is passed as a compose build arg and set as ARG/ENV before `npm run build` in `frontend/Dockerfile:14-15`, matching the fallback in `frontend/src/api/client.ts:1`. No mismatch found.
3. **Persistence** — `DATABASE_URL: sqlite:////data/budget_checker.db` (absolute) on named volume `backend_data:/data`; `backend/app/database.py:6` reads `DATABASE_URL` and `backend/Dockerfile` pre-creates `/data`. The `.dockerignore` files exclude caches, tests, and the stray host-side `budget_checker.db`, so host data cannot ship in the image.
4. **SPA fallback** — `frontend/nginx.conf` `try_files $uri $uri/ /index.html` present.
5. **No application source modified** — confirmed by inspection: `backend/app/*` and `frontend/src/*` are untouched relative to what the change brief describes; the change is purely additive packaging.

**New findings against earlier stage answers (which had no repository access):**

- A **backend pytest suite exists**: `backend/tests/test_auth.py`, `test_error_handling.py`, `test_health.py`, `test_models.py`, with `pytest`/`httpx` pinned in `requirements.txt`. `test_health.py::test_health_check_returns_available` covers the `/health` route the compose readiness story relies on. Earlier answers claiming no tests touch this area were correct only in that no test exercises Docker packaging; the application code does have coverage. Test command is therefore knowable: `cd backend && pytest`.
- A **frontend suite exists**: `vitest run` via `frontend/package.json` (`test` script), with tests for App, Layout, ThemeToggle, Landing, AuthStore, HealthStore, ThemeStore.
- Neither suite covers the Docker packaging itself — that part of the earlier answers stands.

**Nothing was changed** to make verification pass; no tests were modified. Nothing failed — nothing ran.

## Acceptance coverage

The change is a chore whose acceptance criteria are the compose behaviours; there are no approved scenario IDs with mapped automated tests, so:

| Criterion | Automated test |
|---|---|
| Single-command `docker compose up` builds/starts both services | none |
| `/health` reachable on host port 8000 | `backend/tests/test_health.py::test_health_check_returns_available` covers the route logic in-process only, not the container/port mapping |
| Frontend served on 5174, SPA fallback, correct API base/CORS | none (route-level vitest suites exercise components, not the served image) |
| Data survives `docker compose down && up` | none |

## Known gaps

- **No Docker execution.** Every acceptance criterion requires a Docker daemon: `docker compose up --build`, `curl http://localhost:8000/health`, browsing http://localhost:5174, and the down/up persistence check. None were executed. This is the principal gap; the verification engine must run them or they must be done manually.
- **Existing suites not executed.** `pytest` (backend, 4 test files) and `vitest run` (frontend, 7 test files) could not be run from this frame. They exercise unmodified code, so a pass is expected but unobserved — if they fail, the failure predates this change but should be recorded.
- **Index/verify-links unverified.** The symbol re-index could not be run; since no indexed symbol was touched, zero link repairs/drops is predicted, not observed.
- **Image-version drift, host port collisions (8000/5174), and non-localhost access breakage** are design risks from the change brief (hardcoded `VITE_API_BASE_URL` baked at build time); only a real run can confirm or refute them.
- **No new tests added** — packaging behaviour has no automated coverage; a compose smoke script or testcontainers harness would close that and was not built in this attempt.
