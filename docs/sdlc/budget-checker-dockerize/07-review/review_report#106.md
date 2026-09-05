# Review — Dockerize All Services (review-direct, write-review-v1, attempt 1)

## Scope reviewed

Change under review: `code_change#52` (attempt 3), against the acceptance criteria in `change_brief#34` and the inspection record in `verification_report#76`.

Read in the tree, in full:

- `docker-compose.yml` (25 lines) — every service, port map, env var, build arg and volume
- `backend/Dockerfile` (15 lines), `frontend/Dockerfile` (23 lines)
- `frontend/nginx.conf` (13 lines), `backend/.dockerignore`, `frontend/.dockerignore`
- Existing touchpoints the diff configures: `backend/app/database.py` (1–31), `backend/app/main.py` (1–89, including `create_app` and the `CORSMiddleware` wiring), `backend/requirements.txt`, `frontend/src/api/client.ts` (1–10), `frontend/src/stores/AuthStore.ts` (1–30), `frontend/vite.config.ts` (1–22)
- `backend/tests/test_health.py` (1–11) — the readiness-route coverage claim
- `list_files` over `backend/` and `frontend/src/` to confirm the file set and that no application source was rewritten
- `search_text` across the tree for Docker filenames and healthcheck directives
- `impact` on `create_app` (the app assembly the container launches): 1 direct dependent, risk LOW, index fresh — the container executes this symbol unmodified

## Findings

1. **Low — `docker-compose.yml` (backend service): no healthcheck defined.** The verification plan (settled_question#75) leans on `/health` as the readiness signal, but the compose file only has `depends_on: - backend` on the frontend, which is start-order, not readiness. Today this is harmless — nginx serves static files and the browser calls the backend directly — but the moment anything waits on backend readiness (future CI smoke test, an nginx `/api` proxy), it silently doesn't. Recommend a `healthcheck` curling `/health`. Non-blocking for this change.
2. **Low — `frontend/src/stores/AuthStore.ts:25` default `' '` is a trap only escaped by build-arg ordering.** `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''` — a relative base only works behind the Vite dev proxy (`vite.config.ts:12`); nginx serves no `/api` location (`frontend/nginx.conf` has none). Today `frontend/Dockerfile:14-15` sets `ARG/ENV VITE_API_BASE_URL=http://localhost:8000` before `npm run build`, so the value is always present — but the correctness of the served image rests on Dockerfile statement order plus compose passing the arg. Already flagged as fragile in `code_change#52`; confirmed as real from inspection. Code is frozen for this stage; if the reorder risk is unacceptable, send `code_change#52` back with this finding.
3. **Info — host-port coupling.** Backend 8000 / frontend 5174 are hardcoded in compose and match `main.py:19` CORS default and the baked `VITE_API_BASE_URL`. Correct today; breaks on port collision or non-localhost access. Known, documented in `code_change#52`, accepted as out of scope for local-dev chore.

No defect was found that misrepresents itself: the diff is exactly the six packaging files, and no application source, route, or schema was modified (confirmed by listing both trees against `code_change#52`'s file set).

## Blast radius

Every direct dependent outside the diff, with how it was inspected:

- `backend/app/database.py:6` (`DATABASE_URL`) — inspected; compose supplies `sqlite:////data/budget_checker.db`, a value the existing line reads unchanged; `check_same_thread` branch and FK pragma both still apply since the URL still starts with `sqlite`. Sound.
- `backend/app/main.py:19,70` (`ALLOWED_ORIGINS` → `CORSMiddleware`) — inspected; compose value matches the existing default and the origin nginx serves (host 5174 → container 80). Sound.
- `frontend/src/api/client.ts:1` and `frontend/src/stores/AuthStore.ts:25` (`VITE_API_BASE_URL`, build time) — inspected; the compose build arg equals the Dockerfile default equals the compose port map. Sound, with finding #2 on the fragility of the mechanism.
- `backend/tests/test_health.py::test_health_check_returns_available` — depends on the `/health` route; route untouched, imports `app.main.app` which the container launches via the same `create_app` (impact: 1 direct dependent, LOW risk, fresh index). Sound, though it covers in-process logic only, not the container/port mapping.
- No existing file depends on any of the six new files; `search_text` found no prior references. Nothing to repair.

## Residual risk

- **None of the acceptance criteria has ever been executed.** `docker compose up`, `/health` on host 8000, the frontend on 5174 with CORS intact, and the `down && up` persistence check on `backend_data` all require a Docker daemon no stage has had. This is the dominant risk: the configuration is internally consistent by inspection across four files, and inspection cannot catch an image build failure (e.g. `pip install` under python:3.12-slim vs the local 3.14 that produced the `.pytest_cache` in the tree), a port collision, or a volume permission problem. Prior behaviour that previously worked — running pytest natively — is untouched and should still pass, but was itself never run in this chain (`verification_report#76`, Known gaps).
- Index/verify-links unverified (settled_question#69); predicted zero link changes since no indexed symbol was edited — `impact create_app` returning fresh and LOW supports the prediction but is not the re-index itself.
- I could not see `backend/app/routers/` directly in the depth-limited listing; `main.py` and `test_health.py` both import it and the tests exist, so I take the routers package as present, but I did not read `health.py` itself.

## Verdict

**READY** — with the standing caveat that this is a chore whose three acceptance criteria are configuration-consistent everywhere I could check and unexecuted everywhere I could not. The diff is exactly what the brief promised: six new files, zero application changes, every env-var touchpoint (`database.py:6`, `main.py:19/70`, `client.ts:1`, `AuthStore.ts:25`) satisfied by values matching existing defaults. The two findings are low-severity and forward-looking (missing compose healthcheck; build-arg ordering fragility), neither of which breaks the local-dev story the brief scopes. A person should run the five-command sequence from settled_question#75 once before treating the capability as delivered; a failure there is an execution-environment defect, not a diff defect, but it would be the first real evidence either way.