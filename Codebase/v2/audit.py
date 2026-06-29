"""Local audit exports for selected session threads."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .config import AUDIT_DIR, provider_label
from .models import Session, ThreadMessage
from .providers.base import session_model_label
from .providers.registry import get_provider


def _safe_filename(value: str, fallback: str = "session") -> str:
    value = " ".join((value or "").split()).strip() or fallback
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    return (value or fallback)[:80]


def _markdown_value(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text.replace("|", "\\|")


def _render_messages(messages: list[ThreadMessage]) -> str:
    if not messages:
        return "_No readable messages found for this session._\n"

    parts: list[str] = []
    for index, message in enumerate(messages, start=1):
        if message.role == "user":
            label = "User"
        else:
            label = f"Assistant ({message.model})" if message.model else "Assistant"
        parts.append(f"## {index}. {label}\n\n{message.text.strip()}\n")
    return "\n".join(parts).strip() + "\n"


def default_audit_filename(session: Session) -> str:
    """Return a safe default Markdown filename for a session audit export."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    title = session.display or session.id
    return f"{stamp}-{_safe_filename(provider_label(session.provider))}-{_safe_filename(title)}.md"


def export_session_audit(
    session: Session,
    export_dir: Path | None = None,
    export_path: Path | None = None,
) -> Path:
    """Write a local Markdown audit export for one selected session."""
    provider = get_provider(session.provider)
    if provider is None:
        raise ValueError(f"Unsupported provider: {session.provider}")

    messages = provider.collect_thread(session)
    preview = provider.preview(session)
    if export_path is not None:
        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = export_dir or AUDIT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / default_audit_filename(session)

    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = session.display or session.id

    source_file = session.source_file or ""
    session_date = (
        datetime.fromtimestamp(session.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if session.timestamp else ""
    )
    content = [
        "# Session Audit Export",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Exported At | {_markdown_value(exported_at)} |",
        f"| LLM | {_markdown_value(session_model_label(session))} |",
        f"| Provider | {_markdown_value(provider_label(session.provider))} |",
        f"| Title | {_markdown_value(title)} |",
        f"| Project | {_markdown_value(session.project)} |",
        f"| Session | {_markdown_value(session.id)} |",
        f"| Session Date | {_markdown_value(session_date)} |",
        f"| Messages | {_markdown_value(preview.message_count or len(messages))} |",
        f"| Source File | {_markdown_value(source_file)} |",
        "",
        "# Thread",
        "",
        _render_messages(messages),
    ]
    path.write_text("\n".join(content), encoding="utf-8")
    return path


__all__ = ["default_audit_filename", "export_session_audit"]
