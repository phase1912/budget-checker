# Change Brief — Dockerize All Services (attempt 5)

## What changes

The two services in this repository — the FastAPI backend and the React/Vite
frontend — become buildable and runnable inside Docker containers, orchestrated
by Docker Compose, so the whole stack starts with a single `docker compose up`
instead of manual per-service setup (pip install + uvicorn, npm install + vite).
What the application *does* does not change.

## Kind of change

`chore` — the person's answer (settled_question#29, Bohdan), recorded as
change_kind#30. Unchanged across all five attempts of this step.

## Why this kind

The answer is right, and it rests on direct inspection of the tree (this frame's
`list_files` covers every non-test file in both services):

- **The change is purely additive packaging.** New files: `backend/Dockerfile`,
  `frontend/Dockerfile`, `docker-compose.yml`, `.dockerignore` files, and a
  reverse-proxy/static-serving config if the frontend image serves the built
  bundle. `search_text` for Docker-related filenames returns only prior
  change-brief documents under `docs/sdlc/budget-checker-dockerize/` — none of
  these files exist in the source tree yet, so nothing existing is rewritten.
- **No application behaviour moves.** The code reads only environment variables,
  and containerisation supplies them: `backend/app/database.py:6` reads
  `DATABASE_URL` (default `sqlite:///./budget_checker.db`);
  `backend/app/main.py:19` reads `ALLOWED_ORIGINS` (default
  `http://localhost:5174`) and line 70 passes it to `CORSMiddleware`; line 18
  reads `REQUEST_TIMEOUT_SECONDS`. `frontend/src/api/client.ts:1` and
  `frontend/src/stores/AuthStore.ts:25` read `VITE_API_BASE_URL` at build time.
  No route, API contract, or stored schema changes.
- **Not a defect.** Nothing is broken; the intent is a new developer capability.

I considered `feature` — a capability that does not exist is literally new
intent — and withdrew it, as in all four earlier attempts. The capability
belongs to developers building and running the app, not to its users, and the
runtime behaviour delta is zero. Consequence, accepted: for a chore this brief's
acceptance criteria are the whole acceptance record — no requirements,
scenarios or baseline are written downstream.

## Expected blast radius

- `backend/app/**` (`main.py`, `database.py`, `deps.py`, `models.py`,
  `schemas.py`, `security.py`, routers) — copied into the backend image
  unmodified. The graph's symbol index holds nothing for these files, so no
  `impact` counts exist; the judgement is from direct file inspection, stated as
  such.
- `backend/app/database.py` — the one existing symbol containerisation touches:
  the Dockerfile/compose file sets `DATABASE_URL` (e.g.
  `sqlite:////data/budget_checker.db`) that line 6 already reads. Worth noting
  from the prior SDLC review record: the SQLite default path is relative to the
  process's CWD, and two stray `budget_checker.db` files exist in the repo today;
  inside a container with an absolute `DATABASE_URL` this ambiguity disappears,
  but the data file should live on a volume so data survives container
  recreation.
- `backend/requirements.txt` — installed into the image. It already pins
  `psycopg2-binary`, so switching the container's `DATABASE_URL` to Postgres
  would need no new dependency; but this change need not exercise that.
- `backend/app/main.py` `ALLOWED_ORIGINS` — must include the origin the
  containerised frontend is served from, otherwise CORS breaks. Config only; no
  code change.
- `frontend/src/api/client.ts:1`, `frontend/src/stores/AuthStore.ts:25` and
  `frontend/vite.config.ts:12` — all read `VITE_API_BASE_URL` (defaults:
  `http://localhost:8000`, `''`, and `http://localhost:8000` for the dev proxy
  respectively). The build argument must make these resolve to the backend as
  reachable from the browser. Build-time configuration; no source change.
- `frontend/package.json` / `backend/requirements.txt` — inputs to the image
  builds; not modified.
- Purely additive overall: nothing existing depends on the new files.

## Acceptance criteria

For a `chore`, these are the whole acceptance record:

1. On a clean machine with Docker installed but **no** Python or Node, running
   `docker compose up` from the repository root starts both services: the backend
   answers on port 8000 (`/health` returns 200) and the frontend is reachable in
   a browser.
2. Existing behaviour is unchanged: from the served frontend, the auth and
   health flows against the containerised backend work the same as they do when
   the services run natively (no CORS or API-base errors).
3. Backend data survives `docker compose down && up`: registered users and
   records are still present afterwards.

## Out of scope

- Production deployment — no Kubernetes, image registries, TLS or CI/CD; local
  Docker Compose only.
- Any change to application code, routes, or the database schema — the services
  are wrapped as they are.
- Multi-architecture image builds and image-size optimisation.

## Open questions

- Do the services need environment variables or secrets beyond
  `DATABASE_URL`, `ALLOWED_ORIGINS` and `VITE_API_BASE_URL` in
  `docker-compose.yml`? (The code reads only these three; nothing else surfaced
  in inspection.)
- Should Compose also run a Postgres service, or is SQLite-on-a-volume the
  agreed data story for local development? (Everything in the tree today assumes
  SQLite; `psycopg2-binary` is already installed but unused.)
- Which origin will the containerised frontend be served from — the Vite dev
  server (so `vite.config.ts`'s `/api` proxy could be reused) or a static
  server serving the built bundle (so `VITE_API_BASE_URL` must point at the
  backend directly and CORS must list that origin)?
