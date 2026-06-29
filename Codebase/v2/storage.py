"""v2-local settings.json and renames.json read/write.

These files live under ``Codebase/v2/`` so v1's ``Codebase/settings.json``
and ``Codebase/renames.json`` are never read or written by v2.
"""
from __future__ import annotations

import json

from .config import DEFAULT_SETTINGS, PROVIDER_OPTIONS, RENAMES_FILE, SETTINGS_FILE


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
            pass
    return settings


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def load_renames() -> dict:
    if RENAMES_FILE.exists():
        try:
            return json.loads(RENAMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_renames(renames: dict) -> None:
    RENAMES_FILE.write_text(json.dumps(renames, indent=2), encoding="utf-8")