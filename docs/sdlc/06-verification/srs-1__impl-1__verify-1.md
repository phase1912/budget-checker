## Commands run

- `node .meridian/run.cjs analyze --index-only --pdg --allow-sdlc-reindex` — re-indexed after the implementation stage changed the code (first attempt failed transiently with "Analyzer build changed while its identity was being computed", caused by a concurrent rebuild of the Meridian tool itself in a sibling working tree; retried 3s later and succeeded: 524 nodes, 659 edges, 5 clusters, 1 flow).
- `meridian sdlc verify-links --repo <path>` — 37 checked, 37 ok, 0 repaired, 0 unresolved.
- `backend/.venv/bin/python -m pytest backend/tests -q` — run twice: first at 14 passed (before this step's additions), again at 17 passed (after adding 3 tests to close named gaps).
- `npm --prefix frontend run test` (`vitest run`) — 4 passed, 2 test files (new in this step).
- `npm --prefix frontend run build` (`tsc --noEmit && vite build`) — re-run after adding the frontend test files, to confirm they did not break the typecheck/build: passed, 54 modules transformed.
- Manual smoke test (not run by any gate command): started `uvicorn app.main:app --port 8000` and confirmed `curl http://127.0.0.1:8000/health` → `HTTP 200 {"status":"ok"}` over a real socket. Started `npx vite --port 5174` (default 5173 was occupied by an unrelated process) with `ALLOWED_ORIGINS=http://localhost:5174` set on the backend, loaded it in a real browser: the landing page rendered with the product description and "Backend: available" (confirming a genuine cross-origin fetch succeeded), no console errors.
- `test-v1` and `lint-v1` gate checks previewed via `sdlc_check` before submitting: `test-v1` passed. Two prior attempts at both `test-command` and `lint-command` failed the gate because the answer text included explanatory prose after the command — the engine runs the entire answer string as the shell command, and the prose caused a shell syntax error (`syntax error near unexpected token '('`). Both answers were corrected to contain only the bare command, after which `test-v1` passed. `lint-v1` reports `NEEDS_HUMAN` because the answer is honestly `none` — this repository has no linter/formatter/type-checker configured beyond the `tsc --noEmit` already inside `build-command`.

## Results

All automated checks pass. Two mistakes were made and corrected during this stage, both worth recording:

1. **`test-command` and `lint-command` answers accidentally included reasoning text**, which the gate executed verbatim as shell code and failed on. Fixed by re-answering both with only the bare command. This is a process lesson for this template, not a code defect.
2. **Nothing in `app/` or `frontend/src/` (excluding test files) was changed in this stage** — all changes were additive: 3 new backend test functions and a new frontend test setup (2 files, 4 tests). No existing test was altered to make it pass.

Full test counts: backend 17/17 passed, frontend 4/4 passed.

## Acceptance coverage

| Scenario | Test |
|---|---|
| LAND-1 — "An anonymous visitor sees the landing page" ([[prob-1/concept-1/req-1/feature-1]]) | `frontend/src/pages/Landing.test.tsx::shows the product description to an anonymous visitor` |
| LAND-1 — "The landing page is never gated behind a login" | `frontend/src/pages/Landing.test.tsx::is never gated behind a login, regardless of backend status` |
| SKEL-1 — "The frontend confirms the backend is available" ([[prob-1/concept-1/req-2/feature-1]]) | `frontend/src/stores/HealthStore.test.ts::requests the backend health-check endpoint and reports it as available` |
| DATA-1 — "The schema defines all three required entities" / "A schema missing one... fails inspection" ([[prob-1/concept-1/req-3/feature-1]]) | `backend/tests/test_models.py::test_schema_defines_core_entities` (one assertion covers both the positive case and the implied negative — it fails identically if any entity is missing) |
| DATA-2 — "Deleting a user with receipts and budgets leaves no orphaned records" ([[prob-1/concept-1/req-4/feature-1]]) | `backend/tests/test_models.py::test_deleting_user_with_dependents_leaves_no_orphaned_records` |
| DATA-2 — "Deleting a user with no dependent records succeeds cleanly" | `backend/tests/test_models.py::test_deleting_user_with_no_dependents_succeeds_cleanly` |
| ERR-1 — "Invalid input is rejected with a generic error" (3 examples) ([[prob-1/concept-1/req-5/feature-1]]) | `backend/tests/test_error_handling.py::test_invalid_input_produces_generic_error_response` (parametrized, 3 cases) |
| ERR-2 — "A request fails gracefully when the database is unavailable" ([[prob-1/concept-1/req-6/feature-1]]) | `backend/tests/test_error_handling.py::test_database_unavailable_produces_generic_error_response` |
| ERR-2 — "The database becoming unavailable mid-request still fails gracefully" | none — see Known gaps |
| ERR-3 — "A request exceeding the timeout receives a generic error" ([[prob-1/concept-1/req-7/feature-1]]) | `backend/tests/test_error_handling.py::test_timeout_produces_generic_error_response` |
| ERR-3 — "A request finishing exactly at the timeout is not treated as a failure" | `backend/tests/test_error_handling.py::test_request_completing_at_exactly_the_timeout_is_not_treated_as_a_failure` |
| ERR-4 — "Invalid input is recorded server-side" ([[prob-1/concept-1/req-8/feature-1]]) | `backend/tests/test_error_handling.py::test_invalid_input_is_logged_server_side` |
| ERR-4 — "Multiple invalid requests are each logged individually" | `backend/tests/test_error_handling.py::test_multiple_invalid_requests_are_each_logged_individually` |
| ERR-5 — "A database-unavailable failure is recorded server-side" ([[prob-1/concept-1/req-9/feature-1]]) | `backend/tests/test_error_handling.py::test_database_unavailable_is_logged_server_side` |
| ERR-5 — "Multiple failures from the same outage are each logged individually" | `backend/tests/test_error_handling.py::test_multiple_database_unavailable_failures_are_each_logged_individually` (added this step) |
| ERR-6 — "A timed-out request is logged" ([[prob-1/concept-1/req-10/feature-1]]) | `backend/tests/test_error_handling.py::test_timeout_is_logged_server_side` |
| ERR-6 — "A request finishing exactly at the timeout is not logged as a failure" | `backend/tests/test_error_handling.py::test_request_completing_at_exactly_the_timeout_is_not_logged_as_a_failure` (added this step) |
| ERR-6 — "Multiple timeouts are each logged individually" | `backend/tests/test_error_handling.py::test_multiple_timeouts_are_each_logged_individually` (added this step) |
| PERF-NFR-1 / AVAIL-NFR-1 | none — see Known gaps |

## Known gaps

- **ERR-2's "becomes unavailable mid-request" scenario has no distinct test.** The exception handler (`handle_db_error`) is identical regardless of when in request processing an `SQLAlchemyError` is raised — `test_database_unavailable_produces_generic_error_response` raises it immediately, and a mid-handler raise would traverse the exact same handler code. Judged low-value to duplicate; the shared code path is the reason, not an oversight, but the scenario is still formally untested as its own case.
- **PERF-NFR-1 (300ms warm) and AVAIL-NFR-1 (60s cold-start) are entirely untested.** They describe the behavior of a deployed instance on a specific free-tier host that does not exist yet — no provider is chosen, nothing is deployed. There is no meaningful way to measure "cold-start recovery" against a local process. This was flagged in the concept's Risks, the baseline's Open Questions, and the implementation's Risks; it remains open here for the same reason and needs to be picked up once a real deployment exists.
- **No linter, formatter, or type-checker is configured for this project** beyond `tsc --noEmit` (already part of `build-command`). `lint-command` was honestly answered `none`, which the gate itself flags for human confirmation rather than passing silently.
- **The `implements_files`/`implements_symbols` links on the code_change artifact ([[srs-1/impl-1]]) do not resolve in the code graph**, confirmed via `sdlc_impact` in both directions after two re-indexes (with and without `--pdg`) and a `verify-links` pass. This looks like an engine defect in how inline-content artifact types handle those fields, not something fixable from this session. `sdlc_impact`-based evidence for this artifact will read as empty until that is fixed upstream.
- **Cascade-delete (DATA-2) is verified against SQLite, not PostgreSQL** — the eventual hosting provider is still undecided per the baseline's Open Questions, so the same `cascade="all, delete-orphan"` + `ondelete="CASCADE"` configuration has not been exercised against a real Postgres instance.
- **The manual browser/curl smoke test was run once, by hand, on this machine** — it is not repeatable by the gate and was not re-run after the test-suite additions in this step (only the automated suites were re-run after those changes). Included here for completeness, not as evidence with the same weight as the automated results above.
