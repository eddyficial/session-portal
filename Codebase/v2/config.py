"""Paths, constants, provider catalog, and theme palette for v2.

All v2 local data (settings.json, renames.json) lives next to this module
under ``Codebase/v2/`` so v1's files are never touched.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# ── User / provider paths ───────────────────────────────────────────────────
CLAUDE_DIR = Path.home() / ".claude"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
PROJECTS_DIR = CLAUDE_DIR / "projects"

CODEX_DIR = Path.home() / ".codex"
CODEX_INDEX_FILE = CODEX_DIR / "session_index.jsonl"
CODEX_SESSIONS_DIR = CODEX_DIR / "sessions"
CODEX_EXE_DIR = Path.home() / "AppData" / "Local" / "OpenAI" / "Codex" / "bin"
CODEX_PROGRAMS_EXE_DIR = Path.home() / "AppData" / "Local" / "Programs" / "OpenAI" / "Codex" / "bin"

GROK_DIR = Path.home() / ".grok"
GROK_SESSIONS_DIR = GROK_DIR / "sessions"
GROK_MODELS_FILE = GROK_DIR / "models_cache.json"
GROK_EXE = GROK_DIR / "bin" / "grok.exe"

APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
LOCALAPPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))

COPILOT_DIR = Path.home() / ".copilot"
COPILOT_SESSIONS_DIR = COPILOT_DIR / "session-state"

AMP_DIR = Path.home() / ".amp"
AMP_CONFIG_DIR = Path.home() / ".config" / "amp"
AMP_DATA_DIR = Path.home() / ".local" / "share" / "amp"
AMP_LOCALAPPDATA_DIR = LOCALAPPDATA_DIR / "amp"

# v2-local data files (kept inside the v2 package so v1 is untouched).
_V2_DIR = Path(__file__).resolve().parent
RENAMES_FILE = _V2_DIR / "renames.json"
SETTINGS_FILE = _V2_DIR / "settings.json"
TRASH_DIR = _V2_DIR / ".trash"
AUDIT_DIR = _V2_DIR / "audits"
ASSETS_DIR = _V2_DIR / "assets"
APP_ICON = ASSETS_DIR / "session_portal.ico"
APP_ICON_PNG = ASSETS_DIR / "logo_256.png"

# ── Bounded-read safety constants ───────────────────────────────────────────
CREATE_NO_WINDOW = getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0)
MAX_METADATA_SCAN_BYTES = 2 * 1024 * 1024
MAX_JSON_LINE_CHARS = 400_000
MAX_PREVIEW_MESSAGE_CHARS = 600

# ── Provider catalog (resumable sources) ─────────────────────────────────────
PROVIDER_OPTIONS: dict[str, dict] = {
    "claude": {
        "label": "Claude Code",
        "description": "Claude Code sessions and history",
        "path": str(CLAUDE_DIR),
        "paths": [CLAUDE_DIR],
        "commands": ["claude"],
    },
    "codex": {
        "label": "Codex",
        "description": "Codex sessions",
        "path": str(CODEX_DIR),
        "paths": [CODEX_DIR, CODEX_EXE_DIR, CODEX_PROGRAMS_EXE_DIR],
        "commands": ["codex"],
    },
    "grok": {
        "label": "Grok",
        "description": "Grok CLI sessions",
        "path": str(GROK_DIR),
        "paths": [GROK_DIR, GROK_EXE],
        "commands": ["grok"],
    },
    "copilot": {
        "label": "Copilot",
        "description": "GitHub Copilot CLI sessions",
        "path": str(COPILOT_DIR),
        "paths": [COPILOT_DIR, COPILOT_SESSIONS_DIR, LOCALAPPDATA_DIR / "copilot",
                  LOCALAPPDATA_DIR / "GitHub CLI" / "copilot"],
        "commands": ["gh"],
    },
    "amp": {
        "label": "AMP",
        "description": "AMP CLI threads",
        "path": str(AMP_DATA_DIR),
        "paths": [AMP_DIR, AMP_CONFIG_DIR, AMP_DATA_DIR, AMP_LOCALAPPDATA_DIR],
        "commands": ["amp"],
    },
}

# ── Other local AI tools (detected, listed, but not resumable) ───────────────
OTHER_AI_TOOLS: dict[str, dict] = {
    "cursor": {
        "label": "Cursor",
        "paths": [APPDATA_DIR / "Cursor", LOCALAPPDATA_DIR / "Programs" / "Cursor"],
        "commands": ["cursor"],
    },
    "windsurf": {
        "label": "Windsurf",
        "paths": [APPDATA_DIR / "Windsurf", LOCALAPPDATA_DIR / "Programs" / "Windsurf"],
        "commands": ["windsurf"],
    },
    "gemini": {
        "label": "Gemini CLI",
        "paths": [Path.home() / ".gemini"],
        "commands": ["gemini"],
    },
    "continue": {
        "label": "Continue",
        "paths": [Path.home() / ".continue",
                  APPDATA_DIR / "Code" / "User" / "globalStorage" / "continue.continue"],
        "commands": [],
    },
    "aider": {
        "label": "Aider",
        "paths": [Path.home() / ".aider.conf.yml", Path.home() / ".aider.model.settings.yml"],
        "commands": ["aider"],
    },
    "ollama": {
        "label": "Ollama",
        "paths": [Path.home() / ".ollama"],
        "commands": ["ollama"],
    },
    "opencode": {
        "label": "OpenCode",
        "paths": [Path.home() / ".opencode", APPDATA_DIR / "opencode", LOCALAPPDATA_DIR / "opencode"],
        "commands": ["opencode"],
    },
    "qwen": {
        "label": "Qwen Code",
        "paths": [Path.home() / ".qwen", APPDATA_DIR / "qwen-code", LOCALAPPDATA_DIR / "qwen-code"],
        "commands": ["qwen", "qwen-code"],
    },
    "lmstudio": {
        "label": "LM Studio",
        "paths": [Path.home() / ".lmstudio", APPDATA_DIR / "LM Studio"],
        "commands": [],
    },
}

DEFAULT_SETTINGS = {
    "onboarding_complete": False,
    "providers": {key: True for key in PROVIDER_OPTIONS},
    "auto_scan_enabled": True,
    "auto_scan_interval_ms": 60000,
}

# ── Theme ────────────────────────────────────────────────────────────────────
APP_PALETTE = {
    "bg": "#11111b",
    "bg_deep": "#090910",
    "surface": "#242438",
    "surface_2": "#1b1b2b",
    "overlay": "#5f6682",
    "bar": "#090910",
    "muted": "#d4dcf5",
    "text": "#ffffff",
}

ACCENT = {
    "blue": "#9fc5ff",
    "green": "#b8f7b3",
    "yellow": "#ffe7a3",
    "pink": "#ff7ad9",
    "purple": "#d8b4ff",
    "danger": "#ff4d6d",
}


# ── Detection helpers (shared with v1 behavior) ──────────────────────────────
def candidate_detected(info: dict) -> bool:
    for path in info.get("paths", []):
        try:
            if Path(path).exists():
                return True
        except OSError:
            continue
    return any(shutil.which(command) for command in info.get("commands", []))


def provider_detected(key: str) -> bool:
    info = PROVIDER_OPTIONS.get(key)
    return bool(info and candidate_detected(info))


def discover_other_ai_tools() -> list[dict]:
    found = []
    for key, info in OTHER_AI_TOOLS.items():
        if candidate_detected(info):
            found.append({"key": key, "label": info["label"]})
    return found


def provider_label(key: str) -> str:
    return PROVIDER_OPTIONS.get(key, {}).get("label", key.title())


def provider_key_for_label(label: str) -> str:
    for key, info in PROVIDER_OPTIONS.items():
        if info.get("label") == label:
            return key
    return ""
