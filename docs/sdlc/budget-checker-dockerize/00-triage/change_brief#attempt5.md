# Change Brief — Dockerize All Services (attempt 5)

## What changes

The two services in this repository — the FastAPI backend and the React/Vite
frontend — become buildable and runnable inside Docker containers, orchestrated
by Docker Compose, so the whole stack starts with a single `docker compose up`
instead of manual per-service setup (`pip install` + `uvicorn`, `npm install` +
`vite`). What the application *does* does not change.

## Kind of change

`chore` — the person's answer (settled_question#29, Bohdan), recorded as
change_kind#30. Unchanged across all five attempts of this step.

## Why this kind

The answer is right, and it rests on direct inspection of the tree (re-verified
this attempt):

- **The change is purely additive packaging.** New files: `backend/Dockerfile`,
  `frontend/Dockerfile`, `docker-compose.yml`, `.dockerignore` files, and a
  reverse-proxy/static-serve config if the frontend image serves the built
  bundle. `search_text` for `Dockerfile` and `docker-compose` across the repo
  returns nothing under those names; `list_files` of `backend/` and `frontend/`
  confirms none exist. Nothing existing is rewritten.
- **No application behaviour moves.** `backend/app/main.py:19` reads
  `ALLOWED_ORIGINS` (default `http://localhost:5174`) and
  `REQUEST_TIMEOUT_SECONDS` from the environment;
  `backend/app/database.py:6` reads `DATABASE_URL` from the environment with a
  SQLite default. Containerisation supplies these variables; it does not alter
  the code that reads them. No route, API contract, or stored schema changes.
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
- `backend/app/database.py` — the one existing module containerisation touches
  at runtime: the compose file sets `DATABASE_URL` (e.g.
  `sqlite:////data/budget_checker.db`) that line 6 already reads. Note the
  requirements file already carries `psycopg2-binary`, so a Postgres URL would
  also work without a new dependency — but SQLite-on-a-volume is the default
  story here.
- `backend/app/main.py` `ALLOWED_ORIGINS` — must include the origin the
  containerised frontend is served from, otherwise CORS breaks. Config only; no
  code change.
- `frontend/src/api/client.ts:1` and `frontend/src/stores/AuthStore.ts:25` —
  both read `VITE_API_BASE_URL` at build time (client.ts defaults to
  `http://localhost:8000`, AuthStore.ts to `''`). The Docker build argument must
  make these resolve to the backend as reachable from the browser. Build-time
  configuration; no source change.
- `frontend/vite.config.ts:9-16` — the dev-server proxy on `/api` is a dev-time
  convenience only; in a container build the static bundle talks to the backend
  directly via `API_BASE_URL`, so the proxy does not carry over and must not be
  relied on.
- `backend/budget_checker.db` — SQLite data file; in the container it must live
  on a volume so data survives container recreation. (A known side-issue, out of
  scope here: the current default path is CWD-relative, so a stray
  repo-root-level `budget_checker.db` already exists.)
- Purely additive overall: nothing existing depends on the new files.

## Acceptance criteria

For a `chore`, these are the whole acceptance record:

1. On a clean machine with Docker installed but **no** Python or Node, running
   `docker compose up` from the repository root starts both services: the
   backend answers on port 8000 (`/health` returns 200) and the frontend is
   reachable in a browser.
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
- Fixing the CWD-relative SQLite default path in `database.py` (flagged in a
  prior review; separate work).

## Open questions

- Do the services need environment variables or secrets beyond
  `DATABASE_URL`, `ALLOWED_ORIGINS` and `VITE_API_BASE_URL` in
  `docker-compose.yml`?
- Should Compose also run a Postgres service (the backend already depends on
  `psycopg2-binary`), or is SQLite-on-a-volume the agreed data story for local
  development? Everything in the tree today assumes SQLite.
- Which origin will the containerised frontend be served from, and does the
  frontend call the backend directly or through a proxy? This decides the
  `VITE_API_BASE_URL` build argument and the CORS list.
