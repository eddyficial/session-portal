"""Pytest bootstrap — put the repo root on sys.path so ``Codebase.v2`` imports.

Tests use absolute imports rooted at the repository root; this conftest makes
that work regardless of where pytest is invoked from.
"""
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)