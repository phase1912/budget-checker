# Diagnosis — backend container crashes: `ModuleNotFoundError: No module named 'bcrypt'`

## Root cause

The failure is **not in any code file** — every build input on disk is already correct. The cause is a **stale Docker image**: the local backend image still in use was built at the `budget-checker-dockerize` commit (8a7ce34, ts 1788608687), **before** `bcrypt>=4.0,<5.0` was appended to `backend/requirements.txt` by the ci14 run (commit f8a6141, ts 1789668774, which fixed the identical symptom in *CI*, not Docker — see `docs/sdlc/ci14/05-implementation/code_change#61.md`). Nothing in the repo forces a rebuild: `docker-compose.yml:3` is a bare `build: ./backend` with no `pull_policy` or freshness mechanism, so a plain `docker compose up` reuses the cached pre-bcrypt image, and uvicorn dies at `backend/app/security.py:6` (`import bcrypt`) — reached via `create_app()` → `from .routers import auth` (backend/app/main.py:76) → `deps.py` → `security.py`.

If a fresh `docker compose build backend` is run, the build inputs are provably sufficient to install bcrypt: `backend/requirements.txt:7` declares it and `backend/Dockerfile:5-6` copies and pip-installs that file. That is why the defect presents as an environment/staleness problem rather than a source defect.

## Evidence

- **Verified by direct read:** `backend/app/security.py:6` is `import bcrypt`; used at lines 17-18 (`bcrypt.gensalt`, `bcrypt.hashpw`) and 25 (`bcrypt.checkpw`). Import chain matches the recorded traceback: `app/main.py:76` imports `auth` inside `create_app()` (main.py:65, 89).
- **Verified by direct read:** `backend/requirements.txt:7` declares `bcrypt>=4.0,<5.0`; `backend/Dockerfile:5-6`: `COPY requirements.txt .` / `RUN pip install --no-cache-dir -r requirements.txt`. So the image *should* contain bcrypt when built from current inputs.
- **Verified by direct read:** `docker-compose.yml` — backend mounts only `backend_data:/data` (lines 10-11), no command/entrypoint override, no bind mount over site-packages; `backend/.dockerignore` (lines 1-6) and root `.dockerignore` (lines 1-9) exclude only caches/tests/data files — nothing excludes `requirements.txt` or `app/`.
- **Verified by git history (settled_question#112, read from .git/logs/HEAD):** the dockerize commit 8a7ce34 created the Dockerfile when requirements.txt had no bcrypt; ci14 commit f8a6141 (≈12 days later) added it; **no commit has touched `backend/Dockerfile` since dockerize**. The code moved exactly as the stale-image hypothesis predicts.
- **Inferred, not executed:** the runtime traceback itself rests on the developer's recorded container log (settled_question#54); I could not run Docker in this environment. The separation between "stale image" and "build fails silently on python:3.12-slim" (bcrypt 4.x ships manylinux wheels for 3.12, so this is unlikely) is settled by the repro test's build step — `docker compose build backend && docker compose run --rm --no-deps backend python -c "import app.main; import bcrypt"` (reproduction#97) — which the gate must run.
- **Recorded environmental drift (verified in prior stages):** the local `.venv` is Python 3.14 with bcrypt 5.0.0 — outside the `<5.0` pin — which is exactly why local tests pass while the container fails, and why the acceptance test must run in-container.

## Blast radius

No Python symbols change. The code graph holds no backend symbols (prior stage attempts returned `found: false` for `security.py`), so upstream impact could not be measured mechanically — the callers above are established from the traceback and direct reads. The edit surface is build/run configuration only: `backend/Dockerfile`, `backend/requirements.txt` (possibly the pin, possibly not), and `docker-compose.yml`. These are single-owner entry points for the image build; consumers are: (1) `docker compose up` developers, (2) the CI workflow, which installs the same `requirements.txt` (`.github/workflows/ci.yml:22` — must not regress), and (3) existing tests `backend/tests/test_health.py` and `backend/tests/test_auth.py`, which cover the affected module and should keep passing unchanged. The new test `backend/tests/test_docker_bcrypt.py` (reproduction#97) is the only test added.

## Ruled out

1. **Dependency never declared / wrong import site** — eliminated: requirements.txt:7 and security.py:6 read directly.
2. **`.dockerignore` excluding requirements.txt or app/** — eliminated by reading both ignore files; neither does.
3. **Compose shadowing site-packages or overriding the command** — eliminated by reading docker-compose.yml (only `backend_data:/data` mounted, lines 10-11; CMD comes from Dockerfile:14).
4. **Build-time pip failure on python:3.12-slim (Rust/wheel)** — unlikely and testable: bcrypt 4.x ships prebuilt manylinux wheels for 3.12, and a genuine build failure would fail `docker compose build` rather than yield a running-but-incomplete container. The repro test's build step settles this empirically.
5. **Version-pin conflict (`<5.0` vs venv's 5.0.0)** — real drift but not the cause: the container resolves from PyPI, not the venv. It only explains why local pytest passes while Docker fails.
6. **conftest.py / sys.path issues** — eliminated for the container: CMD runs uvicorn from WORKDIR /app on `app.main:app`.

## Fix strategy

Ensure the image actually running is built from the current tree: rebuild the backend image (`docker compose build backend` / `docker compose up --build`) and, so this cannot silently recur, add the container-level smoke test `backend/tests/test_docker_bcrypt.py` (build + `import app.main; import bcrypt`) and update `docker-compose.yml`/docs if a persistence mechanism is warranted. Do **not** re-add bcrypt to requirements.txt (already there, added by ci14), do **not** change `app/security.py` or any application code, and treat revisiting the `>=4.0,<5.0` pin (venv sits on 5.0.0) as out of scope for this fix unless it blocks the build. Alternative considered — pinning an exact bcrypt version to guarantee wheel availability — rejected: the wheel-availability candidate is empirically settled by the repro test, and pinning would couple this bugfix to an unrelated version policy.

## Open questions

- The stale-image vs. build-failure distinction is supported by git history and wheel availability but not yet separated by a captured run; the gate execution of the repro test does that. If `docker compose build backend` followed by the in-container import **succeeds**, the honest conclusion is "pure cache/staleness, rebuild resolves it" and the fix reduces to rebuild hygiene plus the regression test.
- Whether compose should gain an explicit freshness mechanism (e.g. documented `--build`, or a CI/dev-script guard) versus relying on the new test alone is a fix-stage decision.
- The 3.14-vs-3.12 Python drift between local venv and Docker target was flagged by the earlier ci14 review; unresolved here and out of scope.