# Review — Dockerize All Services (review-direct, write-review-v1, attempt 1)

Parent: code_change#52, per change_brief#34 (chore). Verified against the tree directly, not only the prior stage documents.

## Scope reviewed

Read in full: `docker-compose.yml` (25 lines), `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `backend/.dockerignore`, `frontend/.dockerignore`, `backend/app/main.py` (89 lines), `backend/app/database.py`, `backend/requirements.txt`, `frontend/src/api/client.ts`, `frontend/src/stores/AuthStore.ts` (lines 1–30), `frontend/vite.config.ts`. Listed `backend/` to confirm the file set. Ran `impact` on `create_app` (backend/app/main.py) — index found it, 1 affected dependent, LOW risk, index fresh (2026-09-01), which contradicts every earlier stage's claim that "the symbol index holds nothing for this project". Ran `search_text` for `5173` to chase a port mismatch. Lenses: correctness of configuration touchpoints, blast radius, acceptance coverage, adversarial.

## Findings

1. **Medium — `frontend/src/stores/AuthStore.ts:25`** — `const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''` — the fallback here is the empty string, unlike `client.ts:1` which falls back to `http://localhost:8000`. If `VITE_API_BASE_URL` is ever unset at build time (e.g. the fragile ARG/ENV ordering in `frontend/Dockerfile:14-15` is reordered, as code_change#52 itself flags), auth requests would go to the nginx origin and fail, while health checks would still work — a half-broken, hard-to-diagnose stack. Today the compose build arg covers it. This is about the pre-existing code, not this document; the change wraps it correctly but inherits the fragility. Send to implementation only if hardening is wanted now; not a blocker for the packaging as built.

2. **Medium (process, on code_change#52) — nothing was executed.** All three acceptance criteria require a Docker daemon; verification_report#76 and settled_question#104 confirm none ran. The change is configuration-consistent end to end by inspection (values match: `DATABASE_URL=sqlite:////data/budget_checker.db` ↔ `backend/app/database.py:6`; `ALLOWED_ORIGINS=http://localhost:5174` ↔ `backend/app/main.py:19`; `VITE_API_BASE_URL=http://localhost:8000` ↔ `client.ts:1`), but "consistent on paper" is not "works". The known failure classes — host port collision on 8000/5174, python:3.12-slim vs local 3.14 drift, non-localhost access — are exactly what inspection cannot refute.

3. **Low — `docker-compose.yml` has no healthcheck.** The compose story leans on `/health` (settled_question#75), but the backend service defines no healthcheck, so `depends_on` in the frontend service is start-order only. Harmless for nginx static serving (the browser calls the backend directly), so noting rather than blocking.

4. **Low — image-version drift risk.** `backend/Dockerfile:1` pins `python:3.12-slim` while the local `__pycache__`/`.pytest_cache` artifacts indicate local dev runs a newer Python. Requirements use range pins (`>=,<`), so a rebuild under 3.12 is plausible but unproven.

Not findings, checked and clean: nginx SPA fallback present (`frontend/nginx.conf:11`); `.dockerignore` files correctly exclude tests, caches, the stray `backend/budget_checker.db`, `node_modules/`, `dist/`; no application source modified — `backend/app/*` and `frontend/src/*` match the pre-change descriptions; the `5173` search confirms the Vite dev-server default port is 5173, distinct from the served 5174 — consistent within Docker, and the pre-existing dev-server/CORS mismatch is out of scope here.

## Blast radius

The change adds six files; nothing existing depends on them. Direct dependents outside the diff, each inspected:

- `backend/app/database.py:6` (`DATABASE_URL`) — compose value is an absolute SQLite path the existing code already reads; sound.
- `backend/app/main.py:19,70` (`ALLOWED_ORIGINS` → `CORSMiddleware`) — compose value equals the code's own default; sound.
- `frontend/src/api/client.ts:1` and `frontend/src/stores/AuthStore.ts:25` (`VITE_API_BASE_URL` at build time) — covered by the build arg placed before `npm run build` (`frontend/Dockerfile:14-16`); sound but fragile (finding 1).
- `backend/tests/test_health.py` (`/health` route) — route untouched; covers in-process logic only, not the container; sound.
- `impact(create_app)`: 1 direct dependent, LOW risk, index fresh — and note the symbol index is **not** empty, contrary to the record in settled_question#89/#99; the diff-based conclusion (purely additive, no broken dependents) still holds.

## Residual risk

Previously working and possibly not now: nothing — no native-run path is altered; `backend/app/database.py` default and CORS default are unchanged, so a developer running uvicorn/vite natively sees exactly today's behaviour. What I am still unsure of, concretely: (1) that `docker compose up --build` succeeds at all — never run; (2) that `pip install -r requirements.txt` builds clean under python:3.12-slim — never run; (3) that data actually survives `docker compose down && up` on the `backend_data` volume — configuration implies it, execution never confirmed it; (4) the existing backend pytest and frontend vitest suites were never executed, so a pre-existing red could be misattributed later. Index re-index/verify-links also unverified (settled_question#69).

## Verdict

**NEEDS DISCUSSION.** The packaging is internally consistent under every lens I ran: all three environment touchpoints resolve to values the existing code already defaults to, the file set is purely additive, no dependent outside the diff breaks, and the adversarial pass found no secrets or outside input parsed. But every acceptance criterion this chore has is unproven — no `docker compose up`, no `/health` on 8000, no down/up persistence check ever executed, and even the pre-existing test suites were not run. A READY here would certify what inspection alone cannot: that the stack starts. The decision needed is small — a person with a Docker daemon runs the five-command sequence already written out in settled_question#75 (plus `cd backend && pytest` and `cd frontend && npm run build`) and this moves to READY, or the first real failure comes back here as findings. Finding 1 (AuthStore empty-string fallback) is worth a look at the same time but should not gate this chore.
