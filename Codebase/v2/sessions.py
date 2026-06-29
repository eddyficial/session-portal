"""Session aggregator and preview/count helpers.

Pulls enabled/detected providers' sessions together, applies local renames,
keeps only resumable rows, and sorts by timestamp (newest first) — matching
v1's :func:`load_sessions` behavior.
"""
from __future__ import annotations

from .logging_setup import get_logger
from .models import Preview, Session
from .providers.base import session_model_label
from .providers.registry import PROVIDERS, get_provider
from .storage import load_renames, load_settings

logger = get_logger(__name__)


def load_sessions(settings: dict | None = None) -> list[Session]:
    settings = settings or load_settings()
    providers_cfg = settings.get("providers", {})
    sessions: list[Session] = []
    for provider in PROVIDERS:
        enabled = providers_cfg.get(provider.key, provider.detected())
        if enabled:
            # Providers are independent adapters. A bad provider store or
            # missing CLI should be visible in logs without blanking the app.
            try:
                sessions.extend(provider.load_sessions())
            except Exception:
                logger.exception("Provider %s failed while loading sessions", provider.key)

    renames = load_renames()
    for s in sessions:
        if s.id in renames:
            s.display = renames[s.id]

    sessions = [s for s in sessions if s.resumable]
    sessions.sort(key=lambda s: s.timestamp, reverse=True)
    return sessions


def get_session_preview(session: Session) -> Preview:
    provider = get_provider(session.provider)
    if provider is None:
        return Preview()
    try:
        preview = provider.preview(session)
    except Exception:
        logger.exception("Provider %s failed while previewing session %s", session.provider, session.id)
        return Preview()
    # Cache tokens so cost can be computed without re-reading the file.
    session.tokens = preview.tokens
    return preview


def get_session_message_count(session: Session) -> int:
    if isinstance(session.message_count, int):
        return session.message_count
    try:
        provider = get_provider(session.provider)
        preview = provider.preview(session) if provider is not None else Preview()
        count = preview.message_count
    except Exception:
        logger.exception("Failed to count messages for session %s", session.id)
        count = 0
    session.message_count = count
    return count


def ensure_search_index(sessions: list[Session]) -> int:
    """Fill ``search_blob`` for any session missing it. Returns count built.

    The blob is the lowercased concatenation of every human message, built once
    per load and reused across keystrokes. Lazy: only called when a query is
    active so refreshes without searching stay cheap.
    """
    built = 0
    for s in sessions:
        if s.search_blob:
            continue
        provider = get_provider(s.provider)
        if provider is None:
            s.search_blob = " "
            continue
        try:
            texts = provider.collect_messages(s)
        except Exception:
            logger.exception("Provider %s failed while indexing session %s", s.provider, s.id)
            texts = []
        blob = " \n ".join(texts).lower()
        # Always include project + display so the prefilter still works through
        # the same path, and so a session with no extractable messages still
        # matches project/title searches.
        s.search_blob = f"{(s.project or '').lower()} \n {(s.display or '').lower()} \n {blob}"
        built += 1
    return built


__all__ = [
    "load_sessions",
    "get_session_preview",
    "get_session_message_count",
    "ensure_search_index",
    "session_model_label",
]
