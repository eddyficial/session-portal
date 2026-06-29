"""Default no-console launcher for Session Portal.

The public launcher points at the modular V2 app. The legacy V1 script is kept
under ``Codebase/legacy/session_portal_v1.py`` as a temporary rollback path.
"""
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from Codebase.v2.main import main


if __name__ == "__main__":
    main()
