"""Two-stage delete recycle bin for v2.

Deletes route through here instead of ``provider.delete`` so they are
recoverable. The trash is filesystem-only: it moves a session's source file or
directory into ``Codebase/v2/.trash/<provider>/<id>/`` and records the original
location in a manifest. Restore moves it back; purge removes it permanently.

For Claude, only the session file is moved — ``history.jsonl`` is left alone so
that a restore is a pure file move (the leftover history row is harmless).
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import (
    CLAUDE_DIR,
    CODEX_SESSIONS_DIR,
    COPILOT_SESSIONS_DIR,
    GROK_SESSIONS_DIR,
    PROJECTS_DIR,
    TRASH_DIR,
)
from .logging_setup import get_logger
from .models import Session

MANIFEST_FILE = TRASH_DIR / "manifest.json"
logger = get_logger(__name__)

ALLOWED_RESTORE_ROOTS = {
    "claude": [PROJECTS_DIR, CLAUDE_DIR],
    "codex": [CODEX_SESSIONS_DIR],
    "grok": [GROK_SESSIONS_DIR],
    "copilot": [COPILOT_SESSIONS_DIR],
}


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _is_under(path: Path, root: Path) -> bool:
    try:
        _resolved(path).relative_to(_resolved(root))
        return True
    except ValueError:
        return False


def _is_safe_trash_path(path: Path) -> bool:
    return _is_under(path, TRASH_DIR)


def _is_safe_restore_path(provider: str, path: Path) -> bool:
    roots = ALLOWED_RESTORE_ROOTS.get(provider, [])
    return any(_is_under(path, root) for root in roots)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_manifest() -> list[dict]:
    if MANIFEST_FILE.exists():
        try:
            data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            logger.exception("Failed to read trash manifest from %s", MANIFEST_FILE)
    return []


def _save_manifest(entries: list[dict]) -> None:
    TRASH_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def trash_session(session: Session) -> dict | None:
    """Move a session's file/dir into the trash. Returns the manifest entry."""
    src = Path(session.source_file) if session.source_file else None
    sdir = Path(session.session_dir) if session.session_dir else None

    if sdir and sdir.exists() and sdir.is_dir():
        kind = "dir"
        original = str(sdir)
        target_parent = TRASH_DIR / session.provider / session.id
        target = target_parent / sdir.name
    elif src and src.exists() and src.is_file():
        kind = "file"
        original = str(src)
        target_parent = TRASH_DIR / session.provider / session.id
        target = target_parent / src.name
    else:
        # Nothing on disk to trash (e.g. history-only row). Nothing to do.
        return None

    target_parent.mkdir(parents=True, exist_ok=True)
    # If a previous trash entry exists for this id, purge it first.
    if target.exists():
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            try:
                target.unlink()
            except OSError:
                pass
    try:
        shutil.move(str(original), str(target))
    except OSError:
        logger.exception("Failed to move session %s to trash", session.id)
        return None

    entry = {
        "id": session.id,
        "provider": session.provider,
        "kind": kind,
        "original_path": original,
        "trashed_path": str(target),
        "display": session.display or "",
        "project": session.project or "",
        "trashed_at": _now_iso(),
    }
    entries = _load_manifest()
    entries = [e for e in entries if e.get("id") != session.id]
    entries.append(entry)
    _save_manifest(entries)
    return entry


def list_trashed() -> list[dict]:
    return _load_manifest()


def restore_session(trash_id: str) -> bool:
    entries = _load_manifest()
    entry = next((e for e in entries if e.get("id") == trash_id), None)
    if not entry:
        return False
    provider = str(entry.get("provider", ""))
    trashed = Path(entry["trashed_path"])
    original = Path(entry["original_path"])
    if not _is_safe_trash_path(trashed) or not _is_safe_restore_path(provider, original):
        logger.warning("Rejected unsafe trash restore path for session %s", trash_id)
        return False
    if not trashed.exists():
        # Already gone; just drop the manifest entry.
        _save_manifest([e for e in entries if e.get("id") != trash_id])
        return False
    original.parent.mkdir(parents=True, exist_ok=True)
    try:
        if original.exists():
            # Conflict: something already occupies the original path. Rename
            # the restored item with a .restored suffix rather than clobbering.
            original = original.with_name(original.name + ".restored")
        shutil.move(str(trashed), str(original))
    except OSError:
        logger.exception("Failed to restore trashed session %s", trash_id)
        return False
    # Clean up the now-empty trash/<provider>/<id> folder if empty.
    try:
        trashed.parent.rmdir()
    except OSError:
        pass
    _save_manifest([e for e in entries if e.get("id") != trash_id])
    return True


def purge_session(trash_id: str) -> bool:
    entries = _load_manifest()
    entry = next((e for e in entries if e.get("id") == trash_id), None)
    if not entry:
        return False
    trashed = Path(entry["trashed_path"])
    if not _is_safe_trash_path(trashed):
        logger.warning("Rejected unsafe trash purge path for session %s", trash_id)
        return False
    if trashed.exists():
        try:
            if trashed.is_dir():
                shutil.rmtree(trashed, ignore_errors=True)
            else:
                trashed.unlink(missing_ok=True)
        except OSError:
            logger.exception("Failed to purge trashed session %s", trash_id)
    try:
        trashed.parent.rmdir()
    except OSError:
        pass
    _save_manifest([e for e in entries if e.get("id") != trash_id])
    return True


def empty_trash() -> int:
    entries = _load_manifest()
    count = len(entries)
    for entry in entries:
        trashed = Path(entry.get("trashed_path", ""))
        if not _is_safe_trash_path(trashed):
            logger.warning("Skipped unsafe trash path during empty_trash: %s", trashed)
            continue
        if trashed.exists():
            try:
                if trashed.is_dir():
                    shutil.rmtree(trashed, ignore_errors=True)
                else:
                    trashed.unlink(missing_ok=True)
            except OSError:
                logger.exception("Failed to empty trashed item %s", trashed)
    _save_manifest([])
    return count
