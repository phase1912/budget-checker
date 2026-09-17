# Change brief — GitHub Actions CI for budget-checker

## What I asked the code graph, and what came back

- `impact("create_app", upstream)` → found: true, `backend/app/main.py`, 1 affected (1 direct), risk LOW, no processes — the app entry point has exactly one direct dependent and nothing downstream of this change reaches it.
- `query("GitHub Actions continuous integration CI workflow")` → 0 hits — the repository has no CI concept the graph knows about.
- `search_text("actions/workflows", whole repo)` → hits only inside `.venv/` vendored package metadata (FastAPI, pytest, pydantic, etc.) — these are other projects' badges, not evidence this project has CI. No hit under the repo's own tree.
- `search_text("vitest run")` → 1 hit: `frontend/package.json:10`, the `test` script.
- `search_text("pytest", backend/)` → `backend/requirements.txt:5` pins `pytest>=8.3,<9.0`; test files exist under `backend/tests/`.
- `list_files` on the (then-absent) CI area → empty: there is no `.github/` directory.

## What changes

Every push and every pull request automatically runs the existing backend pytest suite and the existing frontend vitest suite, and the pass/fail result is visible in GitHub before anyone reviews the change. No linter is introduced and no application code is touched; if a test is already failing, the run surfaces it rather than hiding it.

## Kind of change

`chore` — as decided at triage (change_kind#31), matching the maker's recommendation.

## Why this kind

The change is purely additive: a new `.github/workflows/ci.yml` wrapping commands that already exist (`pytest` per `backend/requirements.txt`, `vitest run` per `frontend/package.json:10`). No function, class, module, public interface, or stored schema moves. `impact` on the main entry point (`create_app`, backend/app/main.py) reports 1 direct dependent and LOW risk — and that is the upstream surface of the most-connected symbol this workflow invokes; the change itself modifies no symbol at all, so the graph's blast radius is empty, which for an additive-infrastructure change is the expected result, not a gap. This is new behaviour (the repo has never had CI — `query` returned 0 hits, no `.github/` directory exists, and no prior SDLC document covers it), so it is not a bugfix. I would not have chosen `feature`: although the repository gains a new capability in a loose sense, nothing about the product's behaviour changes, and the full feature path (problem, concept, requirements, scenarios, baseline) would cost more than the risk warrants. The honest caveat: a CI workflow that everyone's pushes gate on is higher-stakes than a typical chore — provisioning Python and Node correctly is where it can fail — which is why the acceptance criteria below are behavioural, not file-existence checks.

## Expected blast radius

- `create_app` (backend/app/main.py) — 1 direct dependent, risk LOW; **invoked but not modified** by this change.
- backend test suite (`backend/tests/`: test_auth.py, test_health.py, test_models.py, test_error_handling.py) — run by the workflow, not modified; no graph dependency on the new workflow (it does not exist yet).
- frontend test suite (`frontend/src/App.test.tsx` via `vitest run`, frontend/package.json:10) — run by the workflow, not modified.
- No existing symbol is touched; the only new file is `.github/workflows/ci.yml`. Blast radius on existing code: zero.

## Acceptance criteria

1. Opening (or updating) a pull request shows a GitHub Actions run that executes both `pytest` in `backend/` and `npm test` (`vitest run`) in `frontend/`, with each suite's result visible in the PR checks.
2. A deliberately failing assertion on a branch shows a red/failing check in GitHub before review; reverting it turns the check green.
3. The workflow provisions its own Python and Node environments from the repo's manifests (`backend/requirements.txt`, `frontend/package.json`) — a fresh runner needs no manual setup steps.

## Out of scope

- No linter, formatter, type-check job, coverage reporting, or Dependabot config is added — tests only. (Dependabot may follow as a separate change if wanted.)
- No fixes to any test the new CI reveals as already failing on the default branch; the run surfaces failures, it does not repair them.
- No deployment, Docker build, or release automation.

## Open questions

- None outstanding. (Branch strategy settled as `new` — work proceeds on a fresh branch, not the default.)