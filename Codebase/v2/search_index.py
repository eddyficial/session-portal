"""Persistent full-text search cache for local sessions.

Providers remain the source of truth. This module only stores the normalized
lowercase search blob that ``sessions.ensure_search_index`` already builds, so
subsequent app launches do not need to reread unchanged session transcripts.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from .config import SEARCH_INDEX_FILE
from .logging_setup import get_logger
from .models import Session

logger = get_logger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS session_search_index (
    provider TEXT NOT NULL,
    session_id TEXT NOT NULL,
    source_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    search_blob TEXT NOT NULL,
    indexed_at INTEGER NOT NULL,
    PRIMARY KEY (provider, session_id)
);
CREATE INDEX IF NOT EXISTS idx_session_search_source
ON session_search_index(source_key);
"""


def _connect() -> sqlite3.Connection:
    SEARCH_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SEARCH_INDEX_FILE)
    conn.executescript(SCHEMA)
    return conn


def session_source_key(session: Session) -> str:
    """Stable source key used to compare rows across app launches."""
    if session.source_file:
        return str(Path(session.source_file).expanduser())
    if session.session_dir:
        return str(Path(session.session_dir).expanduser())
    return f"{session.provider}:{session.id}"


def session_fingerprint(session: Session) -> str:
    """Return a cheap invalidation marker for a session.

    File-backed providers use file size and nanosecond mtime. CLI-backed
    providers such as AMP do not expose a local transcript file, so their
    metadata becomes the invalidation marker.
    """
    for value in (session.source_file, session.session_dir):
        if not value:
            continue
        try:
            stat = Path(value).stat()
            return f"fs:{stat.st_mtime_ns}:{stat.st_size}"
        except OSError:
            continue
    return "meta:{timestamp}:{message_count}:{display}:{project}:{model}".format(
        timestamp=int(session.timestamp or 0),
        message_count=session.message_count if session.message_count is not None else "",
        display=session.display or "",
        project=session.project or "",
        model=session.model or "",
    )


def hydrate_sessions(sessions: list[Session]) -> int:
    """Fill ``search_blob`` from SQLite for unchanged sessions.

    Returns the number of sessions hydrated from the persistent index.
    """
    if not sessions:
        return 0
    try:
        with _connect() as conn:
            rows = {
                (provider, sid): (fingerprint, blob)
                for provider, sid, fingerprint, blob in conn.execute(
                    "SELECT provider, session_id, fingerprint, search_blob FROM session_search_index"
                )
            }
    except sqlite3.Error:
        logger.exception("Failed to read persistent search index")
        return 0

    hydrated = 0
    for session in sessions:
        row = rows.get((session.provider, session.id))
        if not row:
            continue
        fingerprint, blob = row
        if fingerprint == session_fingerprint(session):
            session.search_blob = blob
            hydrated += 1
    return hydrated


def save_session(session: Session) -> None:
    """Persist one built search blob."""
    if not session.search_blob:
        return
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO session_search_index (
                    provider, session_id, source_key, fingerprint, search_blob, indexed_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, session_id) DO UPDATE SET
                    source_key = excluded.source_key,
                    fingerprint = excluded.fingerprint,
                    search_blob = excluded.search_blob,
                    indexed_at = excluded.indexed_at
                """,
                (
                    session.provider,
                    session.id,
                    session_source_key(session),
                    session_fingerprint(session),
                    session.search_blob,
                    int(time.time()),
                ),
            )
    except sqlite3.Error:
        logger.exception("Failed to persist search index for %s/%s", session.provider, session.id)


def prune_to_sessions(sessions: list[Session]) -> int:
    """Remove index rows for sessions no longer visible to Session Portal."""
    keep = {(s.provider, s.id) for s in sessions}
    try:
        with _connect() as conn:
            rows = list(conn.execute("SELECT provider, session_id FROM session_search_index"))
            stale = [(provider, sid) for provider, sid in rows if (provider, sid) not in keep]
            conn.executemany(
                "DELETE FROM session_search_index WHERE provider = ? AND session_id = ?",
                stale,
            )
            return len(stale)
    except sqlite3.Error:
        logger.exception("Failed to prune persistent search index")
        return 0


def clear_session(provider: str, session_id: str) -> None:
    """Forget one session's index row after delete/hide operations."""
    try:
        with _connect() as conn:
            conn.execute(
                "DELETE FROM session_search_index WHERE provider = ? AND session_id = ?",
                (provider, session_id),
            )
    except sqlite3.Error:
        logger.exception("Failed to clear search index for %s/%s", provider, session_id)


__all__ = [
    "clear_session",
    "hydrate_sessions",
    "prune_to_sessions",
    "save_session",
    "session_fingerprint",
]
