## Summary

Implements the "foundation" feature end to end from nothing: a FastAPI backend (`backend/`) exposing a health-check endpoint with global error handling (invalid input, database unavailability, request timeout — each producing a generic response and a server-side log entry), a draft SQLAlchemy schema (`users`, `receipts`, `budgets`) with cascade delete on both the ORM and database level, and a React+MobX frontend (`frontend/`) with a public landing page that checks backend connectivity without gating its own content on the result. The repository had zero application code before this change (confirmed via a fresh Meridian index showing no code symbols) — everything here is new work, not a modification. pytest tests were written alongside the code, one per acceptance scenario in the baseline's `.feature` files, and all 14 pass locally. After registering this artifact, the repository was re-indexed (`meridian analyze --allow-sdlc-reindex`, 315 nodes / 359 edges / 1 execution flow) so `implements_files`/`implements_symbols` resolve against the real code instead of the pre-implementation empty graph.

## Requirements implemented

- [[prob-1/concept-1/req-1]] (LAND-1) — `frontend/src/pages/Landing.tsx` (`Landing`): renders the product description unconditionally; backend status is an additive, non-blocking hint, never a gate.
- [[prob-1/concept-1/req-2]] (SKEL-1) — `backend/app/routers/health.py` (`health_check`) + `frontend/src/api/client.ts` (`fetchHealth`) + `frontend/src/stores/HealthStore.ts` (`HealthStore.check`): the frontend actually calls the backend's health endpoint on mount.
- [[prob-1/concept-1/req-3]] (DATA-1) — `backend/app/models.py` (`User`, `Receipt`, `Budget`): the three required entities.
- [[prob-1/concept-1/req-4]] (DATA-2) — `backend/app/models.py`: `cascade="all, delete-orphan"` on `User.receipts`/`User.budgets` plus `ondelete="CASCADE"` on the `user_id` foreign keys, so deleting a user leaves no orphaned rows regardless of deletion path.
- [[prob-1/concept-1/req-5]] (ERR-1) and [[prob-1/concept-1/req-8]] (ERR-4) — `backend/app/main.py` (`register_error_handling`'s `handle_validation_error`): generic 422 response, plus a `logger.warning` call.
- [[prob-1/concept-1/req-6]] (ERR-2) and [[prob-1/concept-1/req-9]] (ERR-5) — `backend/app/main.py` (`handle_db_error`): generic 503 response, plus a `logger.error` call.
- [[prob-1/concept-1/req-7]] (ERR-3) and [[prob-1/concept-1/req-10]] (ERR-6) — `backend/app/main.py` (`TimeoutMiddleware`): generic 504 response after `REQUEST_TIMEOUT_SECONDS`, plus a `logger.error` call.

PERF-NFR-1 and AVAIL-NFR-1 are not implemented as code in this change — see Risks.

## Symbols changed

All new (repository had zero code before this change):

- `backend/app/database.py`: `DATABASE_URL`, `engine`, `SessionLocal`, `Base`, `get_db`, `_enable_sqlite_foreign_keys`
- `backend/app/models.py`: `User`, `Receipt`, `Budget`, `_new_id`, `_now`
- `backend/app/routers/health.py`: `health_check`
- `backend/app/main.py`: `TimeoutMiddleware`, `register_error_handling`, `create_app`, `app`, `GENERIC_ERROR_MESSAGE`, `REQUEST_TIMEOUT_SECONDS`, `ALLOWED_ORIGINS`
- `backend/tests/test_health.py`: `test_health_check_returns_available`
- `backend/tests/test_models.py`: `_make_session`, `test_schema_defines_core_entities`, `test_deleting_user_with_dependents_leaves_no_orphaned_records`, `test_deleting_user_with_no_dependents_succeeds_cleanly`
- `backend/tests/test_error_handling.py`: `_Payload`, `_build_test_app`, and 9 test functions covering ERR-1 through ERR-6 (response + log, both sides, for each of invalid input / DB unavailable / timeout, plus the exact-timeout boundary)
- `frontend/src/api/client.ts`: `fetchHealth`, `API_BASE_URL`
- `frontend/src/stores/HealthStore.ts`: `HealthStore`, `healthStore`, `BackendStatus`
- `frontend/src/pages/Landing.tsx`: `Landing`
- `frontend/src/App.tsx`: `App`
- `frontend/src/main.tsx`: entry point (renders `App`)

## Design notes

- **DATABASE_URL defaults to local SQLite**, overridable via env var. The baseline's own Open Questions leave the Postgres hosting provider undecided (Supabase/Render/Neon/AWS RDS) — defaulting to SQLite lets the schema and cascade-delete behavior be built and tested now without waiting on that decision. SQLite's `PRAGMA foreign_keys=ON` is enabled explicitly so `ondelete="CASCADE"` actually takes effect.
- **DATA-2 uses both ORM cascade and DB-level `ondelete="CASCADE"`**, not just one, so deletion is correct whether a user is removed via `session.delete()` (ORM path, handled by `cascade="all, delete-orphan"`) or via a raw SQL delete against a real database (DB path, handled by `ondelete="CASCADE"`).
- **Timeout handled by one middleware (`TimeoutMiddleware`) wrapping every request**, using `anyio.fail_after`, rather than a per-route mechanism — matches ERR-3/ERR-6 being about "a request to the backend" in general, not a specific endpoint, and generalizes cleanly as more routes are added later.
- **Error-handling tests use a throwaway FastAPI app** (`_build_test_app` in `test_error_handling.py`) that imports and wires the real `register_error_handling`/`TimeoutMiddleware` from `app.main`, rather than adding debug-only routes (`/boom-db`, `/slow`) to the production app. This tests the actual production exception-handling code without widening the shipped API surface beyond what the requirements call for.
- **`HealthStore` is not wired to gate `Landing`'s render.** `App` calls `healthStore.check()` on mount and passes the (initially `unknown`) status down, but `Landing` always renders its product description synchronously regardless — matching LAND-1's acceptance scenario ("never gated behind a login" generalizes to "never gated on anything").
- **Rejected** adding a router/multi-page setup (e.g. react-router) — only one page exists in this feature (the landing page); deferred until a second page is actually needed.
- **Rejected** adding a `/users`, `/receipts`, or `/budgets` API route to exercise the models over HTTP — DATA-1/DATA-2 are schema-level requirements verified directly against the SQLAlchemy models (see `test_models.py`), and adding CRUD routes now would be scope beyond what any requirement in this baseline calls for.

## Risks

- **PERF-NFR-1 (300ms warm) and AVAIL-NFR-1 (60s cold-start) are not measured by anything in this change.** They describe behavior of a deployed instance on a specific free-tier host, which does not exist yet (no provider chosen, nothing deployed) — there is no meaningful way to test "cold-start recovery" locally. This was already flagged as a gap in the baseline's Open Questions; it remains open here and needs to be picked up once the app is actually deployed.
- **Cascade-delete behavior was verified against SQLite, not the eventual PostgreSQL deployment.** The same SQLAlchemy relationship configuration (`cascade="all, delete-orphan"` + `ondelete="CASCADE"`) is standard and expected to behave identically on Postgres, but this has not been verified against a real Postgres instance since the provider is still undecided.
- **The timeout middleware cannot forcibly stop a blocked synchronous handler.** `anyio.fail_after` cancels the *awaiting* coroutine and lets the caller get a timely 504, but a synchronous route running in FastAPI's threadpool keeps running in the background until it finishes (Python cannot preempt threads). Acceptable at this "basic" failure-handling stage per the baseline (no resilience patterns expected yet), but worth knowing before adding a slow synchronous handler later.
- **CORS (`ALLOWED_ORIGINS`) defaults to `http://localhost:5173`** (Vite's default dev port) — will need to be set via env var once the frontend is deployed to a real hostname, or cross-origin requests from the deployed frontend to the deployed backend will fail (this exact failure mode was already flagged as a risk in the concept document).
- **What the frontend shows when it cannot reach the backend at all is minimal** (`HealthStore.status` becomes `'unreachable'`, and `Landing` currently renders nothing extra for that case) — this was already flagged as a non-blocking gap in the baseline's Open Questions (no owning requirement), and stays minimal here rather than being expanded beyond what was asked for.
