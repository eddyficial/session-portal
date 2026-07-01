"""Default console launcher for Session Portal.

This wrapper launches the modular V2 app. The legacy V1 implementation is kept
at ``Codebase/legacy/session_portal_v1.py`` for temporary rollback.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Codebase.v2.main import main  # noqa: E402

if __name__ == "__main__":
    main()
