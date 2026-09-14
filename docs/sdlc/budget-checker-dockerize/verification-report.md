# Verification Report — Dockerize All Services (verification-direct, attempt 1)

Parent: code_change#52 (change_brief#34, kind: chore)

## Commands run

**None could be executed.** This verification frame has no command-execution
capability — the available tooling is repository inspection only (read/list/
search/impact). The `sdlc_check()` advisory gate is also not callable from this
frame. Every command below is therefore *prescribed for the engine/gate*, not
run by me. Exit statuses: none observed.

Intended verification commands (from the plan-verification answers, confirmed
against the tree):

1. `cd backend && pytest` — backend has a real suite: `backend/tests/test_auth.py`, `test_error_handling.py`, `test_health.py`, `test_models.py` (pytest and httpx pinned in `backend/requirements.txt:5-6`).
2. `cd frontend && npm run test` — vitest is configured (`frontend/package.json`: `"test": "vitest run"`); test files exist: `App.test.tsx`, `Layout.test.tsx`, `ThemeToggle.test.tsx`, `Landing.test.tsx`, `AuthStore.test.ts`, `HealthStore.test.ts`, `ThemeStore.test.ts`.
3. `docker compose up --build` → `curl http://localhost:8000/health` → exercise http://localhost:5174 → create data → `docker compose down && up` → confirm persistence — the Docker acceptance criteria; require a Docker daemon this frame does not have.
4. `cd frontend && npm run build` (`tsc --noEmit && vite build`) — the build the frontend Dockerfile runs.

## Results

Verified by direct file inspection (all findings are observations of the tree):

- `docker-compose.yml` (25 lines, read in full): backend on host 8000, `DATABASE_URL: sqlite:////data/budget_checker.db` on named volume `backend_data` at `/data`, `ALLOWED_ORIGINS: http://localhost:5174`; frontend build arg `VITE_API_BASE_URL: http://localhost:8000`, ports `5174:80`, `depends_on: backend`.
- `backend/app/database.py:5` reads `DATABASE_URL` with a relative default — the compose env var overrides it with an absolute path; no code change needed. Confirmed.
- `backend/app/main.py:19` CORS default is `http://localhost:5174` — matches the compose `ALLOWED_ORIGINS` and the nginx-served origin. Confirmed.
- `frontend/src/api/client.ts:1` falls back to `http://localhost:8000`, matching the Dockerfile build arg. Confirmed.
- `frontend/Dockerfile`: `ARG/ENV VITE_API_BASE_URL` correctly placed **before** `npm run build` (lines 16–18), so Vite bakes it in. Confirmed.
- `frontend/nginx.conf`: SPA fallback `try_files $uri $uri/ /index.html`. Confirmed.
- `backend/Dockerfile`: installs from requirements, copies `app/`, uvicorn on 8000. Confirmed. Note: it copies only `app/` and `.dockerignore` excludes `tests/` — the backend suite will **not** run inside the image; tests must run on host/CI.
- **Correction to prior planning answers** (settled_question#56, #59): tests **do** exist in the repository, contrary to "no tests touching this area". Four backend test modules (`backend/tests/`) and seven frontend test files are present. They exercise unchanged application code, so no covered code moves — but the engine's gate should run both suites.

Nothing failed and nothing was changed in between — no tests were run and no code was modified by this stage.

## Acceptance coverage

| Scenario | Test |
|---|---|
| Single-command start, Docker-only machine (`docker compose up`) | none — requires Docker daemon; manual |
| `/health` reachable on localhost:8000 | `backend/tests/test_health.py::test_health_check_returns_available` covers the route in-process, not through the container/port mapping |
| Frontend served on 5174 without CORS/API-base errors | none — requires running stack |
| Data survives `docker compose down && up` | none — requires running stack |
| Frontend builds with VITE_API_BASE_URL baked correctly | none as a test; `frontend/Dockerfile` `npm run build` (`tsc --noEmit && vite build`) is the mechanical check |

## Known gaps

- **No command was executed in this verification.** The pytest/vitest suites, the Docker build, and all four acceptance scenarios are unverified by execution here; the engine's gate must run commands 1, 2 and 4 above, and a Docker-capable environment must run 3.
- No automated coverage for compose orchestration itself (port mappings, volume persistence, cross-container CORS) — manual execution only.
- Image-tag drift risk stands: `python:3.12-slim` vs host `__pycache__` artifacts built by CPython 3.14.
- Index refresh / verify-links not run; the change added only new files and touched no indexed symbols, so zero link repairs are predicted but unobserved.
- Host port collisions on 8000/5174 and non-localhost access remain documented-but-unparameterised risks from the change brief.
