"""AMP CLI thread provider.

AMP stores some local state, but resumable thread metadata is exposed most
reliably through the AMP CLI itself. This provider keeps refresh bounded by
using ``amp threads list --json`` and only asks for full Markdown when a user
previews, searches, views, or exports one selected thread.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from ..config import AMP_DATA_DIR, AMP_DIR, AMP_LOCALAPPDATA_DIR, CREATE_NO_WINDOW
from ..logging_setup import get_logger
from ..models import Preview, ResumeCommand, Session, ThreadMessage
from ..resume import find_amp_exe, ps_single_quote
from .base import (
    MAX_THREAD_CHARS,
    clip_preview_text,
    keep_thread_tail,
)

AMP_LIST_LIMIT = 500
AMP_TIMEOUT_SECONDS = 15
logger = get_logger(__name__)


def _run_amp(args: list[str], timeout: int = AMP_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    """Run an AMP CLI command used for server-backed thread data."""
    return subprocess.run(
        ["amp", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )


def _tree_to_path(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = urlparse(value)
        if parsed.scheme == "file":
            path = unquote(parsed.path)
            if len(path) >= 3 and path[0] == "/" and path[2] == ":":
                path = path[1:]
            return path.replace("/", "\\")
    except Exception:
        pass
    return value


def _parse_iso_ms(value: str) -> int:
    if not value:
        return 0
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except ValueError:
        return 0


def _markdown_messages(text: str) -> list[ThreadMessage]:
    messages: list[ThreadMessage] = []
    role = ""
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf, role
        body = "\n".join(buf).strip()
        if role and body:
            messages.append(ThreadMessage(role, clip_preview_text(body, limit=4000)))
        buf = []

    in_frontmatter = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line == "---" and not messages and not role:
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("## User"):
            flush()
            role = "user"
            continue
        if line.startswith("## Assistant"):
            flush()
            role = "assistant"
            continue
        if line.startswith("## "):
            flush()
            role = ""
            continue
        if role:
            buf.append(line)
    flush()
    return messages


class AmpProvider:
    key = "amp"
    label = "AMP"

    def detected(self) -> bool:
        return bool(
            shutil.which("amp")
            or AMP_DIR.exists()
            or AMP_DATA_DIR.exists()
            or AMP_LOCALAPPDATA_DIR.exists()
        )

    def _thread_markdown(self, sid: str) -> str:
        try:
            proc = _run_amp(["threads", "markdown", sid], timeout=30)
        except (OSError, subprocess.SubprocessError):
            logger.exception("AMP markdown command failed for thread %s", sid)
            return ""
        if proc.returncode != 0:
            logger.warning("AMP markdown command returned %s for thread %s: %s", proc.returncode, sid, proc.stderr)
            return ""
        return proc.stdout or ""

    def load_sessions(self) -> list[Session]:
        try:
            proc = _run_amp(["threads", "list", "--json", "--limit", str(AMP_LIST_LIMIT)])
        except (OSError, subprocess.SubprocessError):
            logger.exception("AMP thread list command failed")
            return []
        if proc.returncode != 0:
            logger.warning("AMP thread list returned %s: %s", proc.returncode, proc.stderr)
            return []
        try:
            rows = json.loads(proc.stdout)
        except json.JSONDecodeError:
            logger.exception("AMP thread list returned invalid JSON")
            return []
        if not isinstance(rows, list):
            return []

        sessions: list[Session] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            sid = str(row.get("id") or "").strip()
            if not sid:
                continue
            title = str(row.get("title") or "").strip()
            project = _tree_to_path(str(row.get("tree") or ""))
            count = row.get("messageCount")
            try:
                message_count = int(count)
            except (TypeError, ValueError):
                message_count = 0
            sessions.append(Session(
                id=sid,
                provider="amp",
                project=project,
                model="AMP",
                model_group="AMP / AMP",
                display=title or sid,
                timestamp=_parse_iso_ms(str(row.get("updated") or "")),
                resumable=True,
                message_count=message_count,
            ))
        return sessions

    def preview(self, session: Session) -> Preview:
        return Preview(
            first=session.display or None,
            last=None,
            message_count=session.message_count or 0,
        )

    def collect_messages(self, session: Session) -> list[str]:
        # Search should stay fast. Full AMP Markdown is fetched only for one
        # selected thread in View Thread / Export Thread.
        return [session.project or "", session.display or "", session.id]

    def collect_thread(self, session: Session) -> list[ThreadMessage]:
        markdown = self._thread_markdown(session.id)
        if not markdown:
            return []
        msgs: list[ThreadMessage] = []
        total = 0
        for msg in _markdown_messages(markdown):
            msgs.append(msg)
            total += len(msg.text)
            total = keep_thread_tail(msgs, total)
            if total > MAX_THREAD_CHARS:
                break
        return msgs

    def delete(self, session: Session) -> None:
        # AMP delete is permanent server-side. The UI records a local hidden id
        # instead of calling this provider hook.
        return None

    def resume_command(self, session: Session) -> ResumeCommand:
        cwd = session.project or str(Path.home())
        exe = find_amp_exe()
        base = f"& {ps_single_quote(exe)}" if "\\" in exe or "/" in exe else exe
        return ResumeCommand(
            cwd=cwd,
            shell_command=f"{base} threads continue {ps_single_quote(session.id)}",
        )


__all__ = ["AmpProvider"]
