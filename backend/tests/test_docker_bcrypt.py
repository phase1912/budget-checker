"""Container-level regression tests for the `No module named 'bcrypt'` startup crash.

The local (host) pytest run installs bcrypt 5.0.0 in .venv, so backend/tests
passing here proves nothing about the Docker image — which is exactly how this
regression slipped through (root_cause#114: the backend image was built at the
budget-checker-dockerize commit, before the ci14 run appended
`bcrypt>=4.0,<5.0` to backend/requirements.txt, and nothing forced a rebuild).

Two layers are covered:

1. test_backend_image_built_from_current_tree_imports_app_and_bcrypt — builds
   the backend image from the current tree and asserts that the app imports
   *inside that image* — the same import chain uvicorn walks at startup
   (app.main -> routers.auth -> deps -> security, security.py:6 `import
   bcrypt`). Skipped when no Docker daemon is available.

2. test_compose_backend_service_pins_pull_policy_build — a host-level guard on
   the fix itself: root_cause#114's fix strategy removes the recurrence lever
   (compose silently reusing a stale image) via `pull_policy: build` on the
   backend service in docker-compose.yml. Nothing else in the suite would fail
   if that line were deleted, so this test pins it. It runs anywhere pytest
   runs — the skip-if-no-docker marker is deliberately scoped to test 1 only,
   so this guard cannot be silently skipped on a daemonless host.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_COMPOSE_FILE = _REPO_ROOT / "docker-compose.yml"

_requires_docker = pytest.mark.skipif(
    shutil.which("docker") is None,
    reason="docker CLI not available on PATH",
)


@_requires_docker
def test_backend_image_built_from_current_tree_imports_app_and_bcrypt():
    build = subprocess.run(
        ["docker", "compose", "build", "backend"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"docker compose build backend failed:\n{build.stdout}\n{build.stderr}"
    )
    run = subprocess.run(
        [
            "docker",
            "compose",
            "run",
            "--rm",
            "--no-deps",
            "backend",
            "python",
            "-c",
            "import bcrypt; import app.main",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        "backend image cannot import bcrypt / app.main; the stale-image "
        f"regression is back:\n{run.stdout}\n{run.stderr}"
    )


def test_compose_backend_service_pins_pull_policy_build():
    # This guard does not need the daemon — it runs anywhere pytest runs,
    # including hosts (and gates) with no Docker installed.
    assert _COMPOSE_FILE.is_file(), f"{_COMPOSE_FILE} missing"
    text = _COMPOSE_FILE.read_text(encoding="utf-8")
    lines = text.splitlines()
    backend_block = "\n".join(lines[lines.index("  backend:") :])
    assert "pull_policy: build" in backend_block, (
        "docker-compose.yml no longer sets `pull_policy: build` on the backend "
        "service. That line is the fix for the stale-image regression "
        "(root_cause#114): without it, a bare `docker compose up` can reuse a "
        "cached image built before a dependency was added to "
        "backend/requirements.txt, and the container crashes at startup with "
        "ModuleNotFoundError (e.g. `No module named 'bcrypt'`)."
    )
