"""pytest bootstrap: put the repo root and backend/ on sys.path.

The backend tests use two import styles: `from backend.app...`
(backend/tests/test_auth.py) and `from app...` (test_health.py,
test_error_handling.py). Both resolve only if the repository root AND the
backend/ directory are importable, regardless of the directory pytest is
invoked from (repo root in CI, backend/ in the local build command).
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
