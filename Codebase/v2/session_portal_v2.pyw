"""No-console launcher for Session Portal v2.

Adds the repo root to ``sys.path`` so the ``Codebase.v2`` package imports
resolve when this file is launched directly with ``pyw -3``.
"""
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Codebase.v2.main import main  # noqa: E402

if __name__ == "__main__":
    main()