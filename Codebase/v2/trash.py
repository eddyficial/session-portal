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
from pathlib import Path
from datetime import datetime, timezone

from .config import TRASH_DIR
from .models import Session

MANIFEST_FILE = TRASH_DIR / "manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_manifest() -> list[dict]:
    if MANIFEST_FILE.exists():
        try:
            data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:
            pass
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
    trashed = Path(entry["trashed_path"])
    original = Path(entry["original_path"])
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
    if trashed.exists():
        try:
            if trashed.is_dir():
                shutil.rmtree(trashed, ignore_errors=True)
            else:
                trashed.unlink(missing_ok=True)
        except OSError:
            pass
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
        if trashed.exists():
            try:
                if trashed.is_dir():
                    shutil.rmtree(trashed, ignore_errors=True)
                else:
                    trashed.unlink(missing_ok=True)
            except OSError:
                pass
    _save_manifest([])
    return count