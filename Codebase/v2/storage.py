"""v2-local settings.json and renames.json read/write.

These files live under ``Codebase/v2/`` so v1's ``Codebase/settings.json``
and ``Codebase/renames.json`` are never read or written by v2.
"""
from __future__ import annotations

import json

from .config import DEFAULT_SETTINGS, HIDDEN_SESSIONS_FILE, PROVIDER_OPTIONS, RENAMES_FILE, SETTINGS_FILE
from .logging_setup import get_logger

logger = get_logger(__name__)


def load_settings() -> dict:
    settings = json.loads(json.dumps(DEFAULT_SETTINGS))
    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig"))
            if isinstance(saved, dict):
                settings.update({k: v for k, v in saved.items() if k != "providers"})
                providers = saved.get("providers", {})
                if isinstance(providers, dict):
                    settings["providers"].update({
                        key: bool(value)
                        for key, value in providers.items()
                        if key in PROVIDER_OPTIONS
                    })
        except Exception:
            logger.exception("Failed to load settings from %s; using defaults", SETTINGS_FILE)
    return settings


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def load_renames() -> dict:
    if RENAMES_FILE.exists():
        try:
            return json.loads(RENAMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            logger.exception("Failed to load renames from %s", RENAMES_FILE)
    return {}


def save_renames(renames: dict) -> None:
    RENAMES_FILE.write_text(json.dumps(renames, indent=2), encoding="utf-8")


def load_hidden_sessions() -> dict[str, set[str]]:
    """Return locally hidden session ids by provider.

    This is mainly for server-backed providers such as AMP where Session Portal
    should hide a row locally without calling the provider's permanent delete.
    """
    hidden: dict[str, set[str]] = {}
    if HIDDEN_SESSIONS_FILE.exists():
        try:
            data = json.loads(HIDDEN_SESSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for provider, ids in data.items():
                    if isinstance(ids, list):
                        hidden[str(provider)] = {str(sid) for sid in ids if sid}
        except Exception:
            logger.exception("Failed to load hidden sessions from %s", HIDDEN_SESSIONS_FILE)
    return hidden


def save_hidden_sessions(hidden: dict[str, set[str]]) -> None:
    data = {
        provider: sorted(str(sid) for sid in ids if sid)
        for provider, ids in hidden.items()
        if ids
    }
    HIDDEN_SESSIONS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def hide_session(provider: str, session_id: str) -> None:
    hidden = load_hidden_sessions()
    hidden.setdefault(provider, set()).add(session_id)
    save_hidden_sessions(hidden)
