#!/usr/bin/env python3
import calendar
import json
import os
import shutil
import subprocess
import tkinter as tk
import customtkinter as ctk
from urllib.parse import unquote
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ────────────────────────────────────────────────────────────────────
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
COPILOT_DIR = Path.home() / ".copilot"
COPILOT_SESSIONS_DIR = COPILOT_DIR / "session-state"
APPDATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
LOCALAPPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
RENAMES_FILE = Path(__file__).parent / "renames.json"
SETTINGS_FILE = Path(__file__).parent / "settings.json"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MAX_METADATA_SCAN_BYTES = 2 * 1024 * 1024
MAX_JSON_LINE_CHARS = 400_000
MAX_PREVIEW_MESSAGE_CHARS = 600

PROVIDER_OPTIONS = {
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
        "paths": [COPILOT_DIR, COPILOT_SESSIONS_DIR, LOCALAPPDATA_DIR / "copilot", LOCALAPPDATA_DIR / "GitHub CLI" / "copilot"],
        "commands": ["gh"],
    },
}

OTHER_AI_TOOLS = {
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
        "paths": [Path.home() / ".continue", APPDATA_DIR / "Code" / "User" / "globalStorage" / "continue.continue"],
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


def _candidate_detected(info: dict) -> bool:
    for path in info.get("paths", []):
        try:
            if Path(path).exists():
                return True
        except OSError:
            continue
    return any(shutil.which(command) for command in info.get("commands", []))


def provider_detected(key: str) -> bool:
    info = PROVIDER_OPTIONS.get(key)
    return bool(info and _candidate_detected(info))


def provider_label(key: str) -> str:
    return PROVIDER_OPTIONS.get(key, {}).get("label", key.title())


def provider_key_for_label(label: str) -> str:
    for key, info in PROVIDER_OPTIONS.items():
        if info.get("label") == label:
            return key
    return ""


def session_model_label(session: dict) -> str:
    model = (session.get("model") or "").strip()
    if not model or (model.startswith("<") and model.endswith(">")):
        model = "Unknown"
    return f"{provider_label(session.get('_source', ''))} / {model}"


def discover_other_ai_tools() -> list[dict]:
    found = []
    for key, info in OTHER_AI_TOOLS.items():
        if _candidate_detected(info):
            found.append({"key": key, "label": info["label"]})
    return found


def _clip_preview_text(text: str, limit: int = MAX_PREVIEW_MESSAGE_CHARS) -> str:
    text = " ".join((text or "").split())
    return text[:limit]


def _remember_first_last(first: str | None, last: str | None, count: int, text: str):
    text = _clip_preview_text(text)
    if not text:
        return first, last, count
    if first is None:
        first = text
    else:
        last = text
    return first, last, count + 1


def _iter_jsonl_records(fp: Path, max_bytes: int | None = None):
    read_bytes = 0
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                read_bytes += len(line.encode("utf-8", errors="ignore"))
                if max_bytes is not None and read_bytes > max_bytes:
                    break
                line = line.strip()
                if not line or len(line) > MAX_JSON_LINE_CHARS:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


# ── Claude session loading ────────────────────────────────────────────────────

def _scan_claude_files() -> dict:
    """Return {sessionId: Path} for every Claude session file on disk."""
    index = {}
    if not PROJECTS_DIR.exists():
        return index
    for proj_dir in PROJECTS_DIR.iterdir():
        if not proj_dir.is_dir():
            continue
        for f in proj_dir.iterdir():
            if f.suffix == ".jsonl" and f.is_file():
                sid = f.stem
                if len(sid) == 36 and sid.count("-") == 4:
                    index[sid] = f
    return index


def _decode_claude_project_dir(path: Path) -> str:
    """Best-effort decode for Claude project folder names like C--Users-username."""
    name = path.name
    if len(name) > 3 and name[1:3] == "--" and name[0].isalpha():
        decoded = f"{name[0].upper()}:\\" + name[3:].replace("-", "\\")
        return decoded
    return str(path)


def _get_claude_cwd(fp: Path) -> str:
    """Return the real cwd recorded by Claude in a session jsonl file."""
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        cwd = rec.get("cwd")
        if cwd and Path(cwd).exists():
            return cwd

    decoded = _decode_claude_project_dir(fp.parent)
    return decoded if Path(decoded).exists() else str(fp.parent)

def _get_claude_ai_title(fp: Path) -> str:
    """Return Claude's generated session title when present."""
    title = ""
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        if rec.get("type") == "ai-title":
            ai_title = rec.get("aiTitle") or rec.get("title")
            if isinstance(ai_title, str) and ai_title.strip():
                title = ai_title.strip()
    return title

def _get_claude_model(fp: Path) -> str:
    """Return the last Claude model found in a bounded metadata scan."""
    model = ""
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        message = rec.get("message")
        if rec.get("type") == "assistant" and isinstance(message, dict):
            value = message.get("model")
            if isinstance(value, str) and value.strip():
                model = value.strip()
    return model

def model_group_label(source: str, model: str = "") -> str:
    model = (model or "").strip()
    if model.startswith("<") and model.endswith(">"):
        model = ""
    if source == "claude":
        lower = model.lower()
        if "opus" in lower:
            return "Claude Code / Opus"
        if "sonnet" in lower:
            return "Claude Code / Sonnet"
        if "haiku" in lower:
            return "Claude Code / Haiku"
        return f"Claude Code / {model}" if model else "Claude Code / Unknown"
    if source == "codex":
        return f"OpenAI / {model}" if model else "OpenAI / Codex"
    return model or "Unknown"


def _looks_like_claude_transcript_context(text: str) -> bool:
    """Detect PeriCode/Claude transcript context pasted back as a prompt."""
    compact = " ".join(text.split())
    return (
        "[system] Vault working directory:" in compact
        and " You:" in compact
        and " PeriCode:" in compact
    )


def _extract_claude_human_prompt(rec: dict) -> str:
    """Return a human-entered Claude prompt, skipping tool/meta user records."""
    if rec.get("type") != "user":
        return ""
    if rec.get("isMeta") or rec.get("toolUseResult") or rec.get("attachment"):
        return ""

    message = rec.get("message")
    if not isinstance(message, dict) or message.get("role") != "user":
        return ""

    content = message.get("content", "")
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "tool_result" or part.get("tool_use_id"):
                    return ""
                if part.get("type") == "text":
                    parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        text = " ".join(parts).strip()
    else:
        return ""

    if not text:
        return ""
    if text.startswith("<system-reminder>") or text.startswith("<local-command"):
        return ""
    if _looks_like_claude_transcript_context(text):
        return ""
    return text


def load_claude_sessions() -> list:
    file_index = _scan_claude_files()

    history: dict = {}
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    sid = rec.get("sessionId")
                    if not sid:
                        continue
                    ts = rec.get("timestamp", 0)
                    if sid not in history or ts > history[sid]["timestamp"]:
                        history[sid] = rec
                except json.JSONDecodeError:
                    continue

    result = []
    for sid, fp in file_index.items():
        ai_title = _get_claude_ai_title(fp)
        model = _get_claude_model(fp)
        cwd = _get_claude_cwd(fp)
        entry = dict(history[sid]) if sid in history else {
            "sessionId": sid,
            "project": cwd,
            "display": "",
            "timestamp": int(fp.stat().st_mtime * 1000),
        }
        entry["project"] = cwd
        if ai_title:
            entry["display"] = ai_title
        entry["_file"] = str(fp)
        entry["_resumable"] = True
        entry["_source"] = "claude"
        entry["model"] = model
        entry["model_group"] = model_group_label("claude", model)
        result.append(entry)

    resumable_ids = set(file_index.keys())
    for sid, rec in history.items():
        if sid not in resumable_ids:
            entry = dict(rec)
            entry["_resumable"] = False
            entry["_source"] = "claude"
            entry["model"] = entry.get("model", "")
            entry["model_group"] = model_group_label("claude", entry.get("model", ""))
            result.append(entry)

    return result


def get_claude_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}

    first = None
    last = None
    count = 0
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    for rec in _iter_jsonl_records(fp):
        text = _extract_claude_human_prompt(rec)
        if text:
            first, last, count = _remember_first_last(first, last, count, text)
            continue
        if rec.get("type") == "assistant" and isinstance(rec.get("message"), dict):
            usage = rec["message"].get("usage", {})
            if usage:
                tokens["input"] += usage.get("input_tokens", 0)
                tokens["output"] += usage.get("output_tokens", 0)
                tokens["cache_read"] += usage.get("cache_read_input_tokens", 0)
                tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0)

    return first, last, count, tokens

def _find_codex_exe() -> str:
    """Return path to the Codex Desktop exe, or empty string if not found."""
    candidates = [
        CODEX_PROGRAMS_EXE_DIR / "codex.exe",
        CODEX_EXE_DIR / "codex.exe",
    ]
    if CODEX_EXE_DIR.exists():
        for d in sorted(CODEX_EXE_DIR.iterdir(), reverse=True):
            candidates.append(d / "codex.exe")
    found = shutil.which("codex")
    if found:
        candidates.append(Path(found))
    for exe in candidates:
        if exe.is_file():
            return str(exe)
    return ""


def _find_claude_exe() -> str:
    """Return path to Claude executable, or command name if available on PATH."""
    found = shutil.which("claude")
    return found or "claude"


def _has_windows_terminal() -> bool:
    return shutil.which("wt") is not None


def _ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _start_powershell(cwd: str, command: str):
    cwd = cwd or str(Path.home())
    if not Path(cwd).exists():
        raise FileNotFoundError(f"Session working directory does not exist: {cwd}")
    startup = f"Set-Location -LiteralPath {_ps_single_quote(cwd)}; {command}"
    if _has_windows_terminal():
        subprocess.Popen(["wt", "--maximized", "-d", cwd, "powershell", "-NoExit", "-Command", startup], creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([
            "cmd", "/c", "start", "", "/MAX", "powershell", "-NoExit", "-Command", startup,
        ], creationflags=CREATE_NO_WINDOW)


def _start_cmd(cwd: str, command: str):
    cwd = cwd or str(Path.home())
    if not Path(cwd).exists():
        raise FileNotFoundError(f"Session working directory does not exist: {cwd}")
    if _has_windows_terminal():
        subprocess.Popen(["wt", "--maximized", "-d", cwd, "cmd", "/k", command], creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([
            "cmd", "/c", "start", "", "/D", cwd, "/MAX", "cmd", "/k", command,
        ], creationflags=CREATE_NO_WINDOW)


def _get_codex_first_message(fp: Path) -> str:
    """Return the first non-system user message text from a Codex session file."""
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        if rec.get("type") == "response_item":
            payload = rec.get("payload", {})
            if (isinstance(payload, dict)
                    and payload.get("type") == "message"
                    and payload.get("role") == "user"):
                for part in payload.get("content", []):
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        text = part.get("text", "").strip()
                        if _is_human_codex_text(text):
                            return _clip_preview_text(text)
    return ""


def _is_human_codex_text(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    lowered = text.lower()
    if text.startswith("<"):
        return False
    if lowered.startswith("# agents.md instructions"):
        return False
    if "<instructions>" in lowered or "</instructions>" in lowered:
        return False
    if "## mcp-first rule" in lowered or "## open requests" in lowered:
        return False
    if "[system]" in lowered or "vault working directory:" in lowered:
        return False
    return True


def _clean_display_text(text: str) -> str:
    text = (text or "").strip()
    if not _is_human_codex_text(text):
        return ""
    return _clip_preview_text(text)


# ── Codex session loading ─────────────────────────────────────────────────────

def _get_codex_model(fp: Path) -> str:
    """Return the last Codex/OpenAI model found in a bounded metadata scan."""
    model = ""
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        payload = rec.get("payload")
        if not isinstance(payload, dict):
            continue
        value = payload.get("model")
        if isinstance(value, str) and value.strip():
            model = value.strip()
        settings = payload.get("collaboration_mode", {}).get("settings", {})
        value = settings.get("model") if isinstance(settings, dict) else ""
        if isinstance(value, str) and value.strip():
            model = value.strip()
    return model

def _scan_codex_files() -> dict:
    """Return {sessionId: Path} for every Codex session file on disk."""
    index = {}
    if not CODEX_SESSIONS_DIR.exists():
        return index
    for f in CODEX_SESSIONS_DIR.rglob("rollout-*.jsonl"):
        # filename: rollout-2026-04-28T12-26-45-<uuid>.jsonl
        # uuid is the last 36 chars before .jsonl
        stem = f.stem
        sid = stem[-36:]
        if len(sid) == 36 and sid.count("-") == 4:
            index[sid] = f
    return index


def load_codex_sessions() -> list:
    file_index = _scan_codex_files()

    index: dict = {}
    if CODEX_INDEX_FILE.exists():
        with open(CODEX_INDEX_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    sid = rec.get("id")
                    if sid:
                        index[sid] = rec
                except json.JSONDecodeError:
                    continue

    result = []
    all_ids = set(file_index.keys()) | set(index.keys())
    for sid in all_ids:
        rec = index.get(sid, {})
        fp = file_index.get(sid)

        ts = 0
        updated_at = rec.get("updated_at", "")
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                ts = int(dt.timestamp() * 1000)
            except ValueError:
                pass
        if not ts and fp:
            ts = int(fp.stat().st_mtime * 1000)

        cwd = _get_codex_cwd(fp) if fp else ""
        model = _get_codex_model(fp) if fp else ""

        display = _clean_display_text(rec.get("thread_name", ""))
        if not display and fp:
            display = _clean_display_text(_get_codex_first_message(fp))

        entry = {
            "sessionId": sid,
            "project": cwd or str(fp.parent) if fp else "",
            "display": display,
            "timestamp": ts,
            "model": model,
            "model_group": model_group_label("codex", model),
            "_source": "codex",
            "_resumable": fp is not None,
        }
        if fp:
            entry["_file"] = str(fp)

        result.append(entry)

    return result


def _get_codex_cwd(fp: Path) -> str:
    for rec in _iter_jsonl_records(fp, max_bytes=MAX_METADATA_SCAN_BYTES):
        if rec.get("type") == "turn_context":
            return rec.get("payload", {}).get("cwd", "")
    return ""

def get_codex_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}

    first = None
    last = None
    count = 0
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    for rec in _iter_jsonl_records(fp):
        rtype = rec.get("type")
        payload = rec.get("payload", {})

        if rtype == "response_item" and isinstance(payload, dict):
            if payload.get("type") == "message" and payload.get("role") == "user":
                for part in payload.get("content", []):
                    if isinstance(part, dict) and part.get("type") == "input_text":
                        text = part.get("text", "").strip()
                        if _is_human_codex_text(text):
                            first, last, count = _remember_first_last(first, last, count, text)
        elif rtype == "event_msg" and isinstance(payload, dict):
            if payload.get("type") == "token_count":
                info = payload.get("info") or {}
                usage = info.get("last_token_usage") or info.get("total_token_usage") or {}
                tokens["input"] += usage.get("input_tokens", 0)
                tokens["output"] += usage.get("output_tokens", 0)
                tokens["cache_read"] += usage.get("cached_input_tokens", 0)

    return first, last, count, tokens

def load_renames() -> dict:
    if RENAMES_FILE.exists():
        try:
            return json.loads(RENAMES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_renames(renames: dict):
    RENAMES_FILE.write_text(json.dumps(renames, indent=2), encoding="utf-8")


def delete_claude_session(session: dict):
    sid = session["sessionId"]
    if "_file" in session:
        try:
            Path(session["_file"]).unlink(missing_ok=True)
        except OSError:
            pass
    if HISTORY_FILE.exists():
        lines = []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        rec = json.loads(stripped)
                        if rec.get("sessionId") != sid:
                            lines.append(stripped)
                    except json.JSONDecodeError:
                        lines.append(stripped)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        except OSError:
            pass


def delete_codex_session(session: dict):
    sid = session["sessionId"]
    exe = _find_codex_exe()
    if exe:
        try:
            subprocess.run([exe, "delete", sid], capture_output=True, timeout=10)
        except Exception:
            pass
    if "_file" in session:
        try:
            Path(session["_file"]).unlink(missing_ok=True)
        except OSError:
            pass


# ── Unified loader ────────────────────────────────────────────────────────────

def delete_grok_session(session: dict):
    session_dir = Path(session.get("_session_dir", ""))
    if session_dir.exists() and session_dir.is_dir():
        try:
            shutil.rmtree(session_dir)
        except OSError:
            pass


def _parse_iso_ms(value: str) -> int:
    if not value:
        return 0
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    except ValueError:
        return 0


def _decode_grok_cwd(encoded: str) -> str:
    return unquote(encoded)


def _extract_grok_user_text(content) -> str:
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        text = " ".join(parts).strip()
    else:
        return ""

    if "<user_query>" in text and "</user_query>" in text:
        text = text.split("<user_query>", 1)[1].split("</user_query>", 1)[0].strip()
    if text.startswith("<user_info>") or text.startswith("<rules>") or text.startswith("<system-reminder>"):
        return ""
    return text


def _get_grok_preview_from_chat(fp: Path):
    first = None
    last = None
    count = 0
    for rec in _iter_jsonl_records(fp):
        if rec.get("type") == "user":
            text = _extract_grok_user_text(rec.get("content", ""))
            if text:
                first, last, count = _remember_first_last(first, last, count, text)
    return first, last, count, {}

def load_grok_sessions() -> list:
    if not GROK_SESSIONS_DIR.exists():
        return []

    entries = []
    for session_dir in GROK_SESSIONS_DIR.rglob("*"):
        if not session_dir.is_dir():
            continue
        summary_file = session_dir / "summary.json"
        chat_file = session_dir / "chat_history.jsonl"
        if not summary_file.exists() and not chat_file.exists():
            continue

        sid = session_dir.name
        if len(sid) != 36 or sid.count("-") != 4:
            continue

        summary = {}
        if summary_file.exists():
            try:
                summary = json.loads(summary_file.read_text(encoding="utf-8"))
            except Exception:
                summary = {}

        info = summary.get("info", {}) if isinstance(summary, dict) else {}
        cwd = info.get("cwd", "")
        if not cwd:
            cwd = _decode_grok_cwd(session_dir.parent.name)

        model = summary.get("current_model_id", "") or ""
        display = (
            summary.get("generated_title")
            or summary.get("session_summary")
            or ""
        )
        if not display and chat_file.exists():
            first, _, _, _ = _get_grok_preview_from_chat(chat_file)
            display = first or ""

        ts = (
            _parse_iso_ms(summary.get("last_active_at", ""))
            or _parse_iso_ms(summary.get("updated_at", ""))
            or int(session_dir.stat().st_mtime * 1000)
        )

        entries.append({
            "sessionId": sid,
            "project": cwd,
            "display": display,
            "timestamp": ts,
            "model": model,
            "model_group": f"Grok / {model}" if model else "Grok / Unknown",
            "_file": str(chat_file if chat_file.exists() else summary_file),
            "_session_dir": str(session_dir),
            "_source": "grok",
            "_resumable": True,
        })

    return entries


def get_grok_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}
    if fp.name == "chat_history.jsonl":
        return _get_grok_preview_from_chat(fp)
    try:
        text = fp.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        text = ""
    return text[:4000], None, len(text.splitlines()), {}


def _find_grok_exe() -> str:
    found = shutil.which("grok")
    if found:
        return found
    if GROK_EXE.exists():
        return str(GROK_EXE)
    return "grok"


def resume_grok(project: str, sid: str):
    exe = _find_grok_exe()
    command = (
        f"& {_ps_single_quote(exe)} --resume {_ps_single_quote(sid)}"
        if "\\" in exe
        else f"{exe} --resume {_ps_single_quote(sid)}"
    )
    _start_powershell(project or str(Path.home()), command)


def open_grok_file(session: dict):
    fp = Path(session.get("_file", ""))
    if fp.exists():
        subprocess.Popen(["notepad.exe", str(fp)])


def _read_simple_yaml(fp: Path) -> dict:
    data = {}
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or ":" not in stripped:
                    continue
                key, value = stripped.split(":", 1)
                data[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


def _extract_copilot_user_text(rec: dict) -> str:
    if rec.get("type") != "user.message":
        return ""
    data = rec.get("data", {})
    if not isinstance(data, dict):
        return ""
    text = data.get("content", "")
    if not isinstance(text, str):
        return ""
    if "<current_datetime>" in text:
        parts = text.split("\n\n", 1)
        text = parts[1] if len(parts) > 1 else text
    if "<system_reminder>" in text:
        text = text.split("<system_reminder>", 1)[0]
    return text.strip()


def _get_copilot_preview_from_events(fp: Path, max_bytes: int | None = None):
    first = None
    last = None
    count = 0
    model = ""
    for rec in _iter_jsonl_records(fp, max_bytes=max_bytes):
        if rec.get("type") == "session.model_change":
            data = rec.get("data", {})
            if isinstance(data, dict) and data.get("newModel"):
                model = str(data.get("newModel", "")).strip()
        elif rec.get("type") == "assistant.message":
            data = rec.get("data", {})
            if isinstance(data, dict) and data.get("model"):
                model = str(data.get("model", "")).strip()
        text = _extract_copilot_user_text(rec)
        if text:
            first, last, count = _remember_first_last(first, last, count, text)

    return first, last, count, {}, model

def load_copilot_sessions() -> list:
    if not COPILOT_SESSIONS_DIR.exists():
        return []

    entries = []
    for session_dir in COPILOT_SESSIONS_DIR.iterdir():
        if not session_dir.is_dir():
            continue
        sid = session_dir.name
        if len(sid) != 36 or sid.count("-") != 4:
            continue

        workspace_file = session_dir / "workspace.yaml"
        events_file = session_dir / "events.jsonl"
        if not workspace_file.exists():
            continue

        workspace = _read_simple_yaml(workspace_file)
        cwd = workspace.get("cwd", "")
        display = workspace.get("name", "")
        model = ""
        count = 0
        if events_file.exists():
            first, _, count, _, model = _get_copilot_preview_from_events(events_file)
            if not display:
                display = first or ""

        ts = (
            _parse_iso_ms(workspace.get("updated_at", ""))
            or _parse_iso_ms(workspace.get("created_at", ""))
            or int(session_dir.stat().st_mtime * 1000)
        )

        entries.append({
            "sessionId": sid,
            "project": cwd,
            "display": display,
            "timestamp": ts,
            "model": model or "Copilot",
            "model_group": f"Copilot / {model}" if model else "Copilot / Unknown",
            "_file": str(events_file if events_file.exists() else workspace_file),
            "_session_dir": str(session_dir),
            "_source": "copilot",
            "_resumable": True,
            "_message_count": count,
        })

    return entries


def get_copilot_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}
    if fp.name == "events.jsonl":
        first, last, count, tokens, _model = _get_copilot_preview_from_events(fp)
        return first, last, count, tokens
    text = fp.read_text(encoding="utf-8", errors="replace").strip()
    return text[:4000], None, session.get("_message_count", 0), {}


def delete_copilot_session(session: dict):
    session_dir = Path(session.get("_session_dir", ""))
    if session_dir.exists() and session_dir.is_dir():
        try:
            shutil.rmtree(session_dir)
        except OSError:
            pass


def resume_copilot(project: str, sid: str):
    cwd = project or str(Path.home())
    command = f"gh copilot -- -C {_ps_single_quote(cwd)} --resume={_ps_single_quote(sid)}"
    _start_powershell(cwd, command)


SESSION_LOADERS = {
    "claude": load_claude_sessions,
    "codex": load_codex_sessions,
    "grok": load_grok_sessions,
    "copilot": load_copilot_sessions,
}

PREVIEW_LOADERS = {
    "claude": get_claude_preview,
    "codex": get_codex_preview,
    "grok": get_grok_preview,
    "copilot": get_copilot_preview,
}

DELETE_HANDLERS = {
    "claude": delete_claude_session,
    "codex": delete_codex_session,
    "grok": delete_grok_session,
    "copilot": delete_copilot_session,
}


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


def save_settings(settings: dict):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def load_sessions(settings: dict | None = None) -> list:
    settings = settings or load_settings()
    providers = settings.get("providers", {})
    sessions = []
    for key, loader in SESSION_LOADERS.items():
        if providers.get(key, provider_detected(key)):
            sessions += loader()
    renames = load_renames()
    for s in sessions:
        if s["sessionId"] in renames:
            s["display"] = renames[s["sessionId"]]
    sessions = [s for s in sessions if s.get("_resumable", False)]
    return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)


def get_session_preview(session: dict):
    loader = PREVIEW_LOADERS.get(session.get("_source", "claude"), get_claude_preview)
    return loader(session)


# ── Launch helpers ────────────────────────────────────────────────────────────

def resume_claude(project: str, sid: str):
    exe = _find_claude_exe()
    command = (
        f"& {_ps_single_quote(exe)} --no-chrome --resume {_ps_single_quote(sid)}"
        if "\\" in exe
        else f"{exe} --no-chrome --resume {_ps_single_quote(sid)}"
    )
    _start_powershell(project or str(Path.home()), command)


def resume_codex(project: str, sid: str):
    exe = _find_codex_exe()
    cwd = project or str(Path.home())
    cmd = (
        f"& {_ps_single_quote(exe)} resume --cd {_ps_single_quote(cwd)} {_ps_single_quote(sid)}"
        if exe
        else f"codex resume --cd {_ps_single_quote(cwd)} {_ps_single_quote(sid)}"
    )
    _start_powershell(cwd, cmd)


def open_codex(project: str = ""):
    cwd = project or str(Path.home())
    exe = _find_codex_exe()
    cmd = f"& \"{exe}\"" if exe else "codex"
    _start_powershell(cwd, cmd)


# ── UI ────────────────────────────────────────────────────────────────────────

RESUME_HANDLERS = {
    "claude": resume_claude,
    "codex": resume_codex,
    "grok": resume_grok,
    "copilot": resume_copilot,
}


class SessionPortal:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Session Portal")
        self.root.minsize(1220, 640)
        self._apply_default_window_size()

        self.settings = load_settings()
        self.all_sessions: list = []
        self.filtered_sessions: list = []
        self.sort_var = tk.StringVar(value="Newest")
        self.source_var = tk.StringVar(value="All Models")
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.auto_scan_var = tk.BooleanVar(value=bool(self.settings.get("auto_scan_enabled", True)))
        self._auto_scan_after_id = None
        self._delete_mode = False
        self._checked_ids: set = set()

        self._apply_theme()
        self._ensure_onboarding()
        self._build_ui_modern()
        self._load_data()
        self._schedule_auto_scan()
        self.root.deiconify()
        self._apply_default_window_size()
        self.root.lift()

    def _apply_default_window_size(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if screen_w > 0 and screen_h > 0:
            self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

    def _sync_toolbar_to_table_width(self, _event=None):
        if not all(hasattr(self, name) for name in ("toolbar_row", "toolbar_controls", "list_frame")):
            return
        row_width = self.toolbar_row.winfo_width()
        table_width = self.list_frame.winfo_width()
        if row_width <= 1 or table_width <= 1:
            return
        gap = 10
        controls_width = max(320, row_width - table_width - gap)
        self.toolbar_controls.configure(width=controls_width)

    def _ensure_onboarding(self):
        if not self.settings.get("onboarding_complete"):
            self._show_onboarding(first_run=True)

    def _provider_detected(self, key: str) -> bool:
        return provider_detected(key)

    def _show_onboarding(self, first_run=False):
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Scan Sources")
        dialog.configure(bg=self.bg)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Choose What Session Portal Should Discover",
            bg=self.bg,
            fg=self.blue,
            font=("Consolas", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 4))

        tk.Label(
            dialog,
            text="Found sources can be enabled now. Other detected AI tools are listed below when session support is not available yet.",
            bg=self.bg,
            fg=self.muted,
            font=("Consolas", 9),
        ).pack(anchor="w", padx=18, pady=(0, 12))

        vars_by_key = {}
        providers = self.settings.get("providers", {})
        for key, info in PROVIDER_OPTIONS.items():
            detected = self._provider_detected(key)
            initial = detected if not self.settings.get("onboarding_complete") else providers.get(key, detected)
            var = tk.BooleanVar(value=initial)
            vars_by_key[key] = var
            row = tk.Frame(dialog, bg=self.surface, padx=10, pady=7)
            row.pack(fill=tk.X, padx=18, pady=3)
            tk.Checkbutton(
                row,
                text=info["label"],
                variable=var,
                bg=self.surface,
                fg=self.text,
                activebackground=self.surface,
                activeforeground=self.text,
                selectcolor=self.overlay,
                font=("Consolas", 10, "bold"),
            ).pack(side=tk.LEFT)
            status = "found" if detected else "not found"
            tk.Label(
                row,
                text=f"{info['description']}  [{status}]",
                bg=self.surface,
                fg=self.green if detected else self.muted,
                font=("Consolas", 9),
            ).pack(side=tk.LEFT, padx=(10, 0))

        other_tools = discover_other_ai_tools()
        if other_tools:
            tk.Label(
                dialog,
                text="Other Local AI Tools Found",
                bg=self.bg,
                fg=self.blue,
                font=("Consolas", 10, "bold"),
            ).pack(anchor="w", padx=18, pady=(12, 4))
            for tool in other_tools:
                row = tk.Frame(dialog, bg=self.surface, padx=10, pady=6)
                row.pack(fill=tk.X, padx=18, pady=2)
                tk.Label(
                    row,
                    text=tool["label"],
                    bg=self.surface,
                    fg=self.text,
                    font=("Consolas", 10, "bold"),
                ).pack(side=tk.LEFT)
                tk.Label(
                    row,
                    text="detected; session resume support not available yet",
                    bg=self.surface,
                    fg=self.muted,
                    font=("Consolas", 9),
                ).pack(side=tk.LEFT, padx=(10, 0))

        btns = tk.Frame(dialog, bg=self.bg, pady=14, padx=18)
        btns.pack(fill=tk.X)

        def select_found():
            for key, var in vars_by_key.items():
                var.set(self._provider_detected(key))

        def select_all():
            for var in vars_by_key.values():
                var.set(True)

        def save_and_close():
            self.settings["providers"] = {key: var.get() for key, var in vars_by_key.items()}
            self.settings["onboarding_complete"] = True
            save_settings(self.settings)
            dialog.destroy()

        tk.Button(
            btns,
            text="Select Found",
            command=select_found,
            bg=self.overlay,
            fg=self.text,
            relief=tk.FLAT,
            padx=10,
            pady=5,
        ).pack(side=tk.LEFT)
        tk.Button(
            btns,
            text="Select All",
            command=select_all,
            bg=self.overlay,
            fg=self.text,
            relief=tk.FLAT,
            padx=10,
            pady=5,
        ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Button(
            btns,
            text="Save",
            command=save_and_close,
            bg=self.blue,
            fg=self.bg,
            relief=tk.FLAT,
            padx=18,
            pady=5,
            font=("Consolas", 10, "bold"),
        ).pack(side=tk.RIGHT)

        if first_run:
            dialog.protocol("WM_DELETE_WINDOW", save_and_close)
        self.root.wait_window(dialog)

    def _apply_theme(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        palette = APP_PALETTE
        self.font_family = "Consolas"
        self.font_size = 11

        self.bg = palette["bg"]
        self.bg_deep = palette["bg_deep"]
        self.surface = palette["surface"]
        self.surface_2 = palette["surface_2"]
        self.overlay = palette["overlay"]
        self.bar = palette["bar"]
        self.muted = palette["muted"]
        self.text = palette["text"]
        self.blue = "#9fc5ff"
        self.green = "#b8f7b3"
        self.yellow = "#ffe7a3"
        self.pink = "#ff7ad9"
        self.purple = "#d8b4ff"
        self.danger = "#ff4d6d"
        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.bg)
        style.configure("TLabel", background=self.bg, foreground=self.text, font=self._font())
        style.configure(
            "Treeview",
            background=self.surface,
            foreground=self.text,
            fieldbackground=self.surface,
            font=self._font(),
            rowheight=max(26, self.font_size + 18),
        )
        style.configure(
            "Treeview.Heading",
            background=self.overlay,
            foreground=self.text,
            font=self._font(weight="bold"),
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[
                ("pressed", self.blue),
                ("active", self.surface_2),
            ],
            foreground=[
                ("pressed", self.bg_deep),
                ("active", "#ffffff"),
            ],
            relief=[("pressed", "flat"), ("active", "flat")],
        )
        style.map(
            "Treeview",
            background=[("selected", self.overlay)],
            foreground=[("selected", self.text)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=self.overlay,
            troughcolor=self.surface,
            bordercolor=self.bg,
            arrowcolor=self.text,
        )

    def _font(self, delta: int = 0, weight: str | None = None):
        size = max(8, self.font_size + delta)
        return (self.font_family, size, weight) if weight else (self.font_family, size)

    def _set_source_filter(self, label: str):
        self.source_var.set(label)
        self._apply_filter()

    def _refresh_source_buttons(self):
        if not hasattr(self, "source_buttons"):
            return
        for label, button in self.source_buttons.items():
            active = self.source_var.get() == label
            button.configure(
                fg_color=self.blue if active else self.surface_2,
                text_color=self.bg_deep if active else self.text,
                hover_color=self.blue if active else self.overlay,
            )

    def _source_filter_labels(self) -> list[str]:
        labels = ["All Models"]
        enabled = self.settings.get("providers", {})
        session_sources = {s.get("_source") for s in self.all_sessions}
        for key, info in PROVIDER_OPTIONS.items():
            if key in session_sources or (enabled.get(key, True) and self._provider_detected(key)):
                labels.append(info["label"])
        return labels

    def _build_source_buttons(self):
        if not hasattr(self, "source_buttons_frame"):
            return
        for child in self.source_buttons_frame.winfo_children():
            child.destroy()
        self.source_buttons = {}
        labels = self._source_filter_labels()
        if self.source_var.get() not in labels:
            self.source_var.set("All Models")
        for label in labels:
            btn = ctk.CTkButton(
                self.source_buttons_frame,
                text=label,
                anchor="w",
                height=34,
                corner_radius=6,
                font=self._font(1, "bold"),
                command=lambda value=label: self._set_source_filter(value),
            )
            btn.pack(fill=tk.X, pady=3)
            self.source_buttons[label] = btn
        self._refresh_source_buttons()

    def _build_ui_modern(self):
        app = ctk.CTkFrame(self.root, fg_color=self.bg_deep, corner_radius=0)
        app.pack(fill=tk.BOTH, expand=True)

        sidebar = ctk.CTkFrame(app, width=178, fg_color=self.bg_deep, corner_radius=0)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="Session\nPortal",
            justify="left",
            text_color=self.text,
            font=self._font(10, "bold"),
        ).pack(anchor="w", padx=18, pady=(20, 8))
        ctk.CTkLabel(
            sidebar,
            text="Local AI Workspace",
            text_color=self.text,
            font=self._font(),
        ).pack(anchor="w", padx=18, pady=(0, 20))

        self.source_buttons_frame = ctk.CTkFrame(sidebar, fg_color=self.bg_deep, corner_radius=0)
        self.source_buttons_frame.pack(fill=tk.X, padx=14)
        self.source_buttons = {}
        self._build_source_buttons()

        ctk.CTkButton(
            sidebar,
            text="Scan Sources",
            anchor="w",
            height=34,
            corner_radius=6,
            fg_color=self.surface_2,
            hover_color=self.overlay,
            text_color=self.text,
            font=self._font(1),
            command=self._edit_sources,
        ).pack(fill=tk.X, padx=14, pady=(20, 3))

        ctk.CTkButton(
            sidebar,
            text="Refresh",
            anchor="w",
            height=34,
            corner_radius=6,
            fg_color=self.surface_2,
            hover_color=self.overlay,
            text_color=self.text,
            font=self._font(1),
            command=self._load_data,
        ).pack(fill=tk.X, padx=14, pady=3)

        self.auto_scan_btn = ctk.CTkButton(
            sidebar,
            text="Auto Scan: ON" if self.auto_scan_var.get() else "Auto Scan: OFF",
            anchor="w",
            height=34,
            corner_radius=6,
            fg_color=self.surface_2,
            hover_color=self.overlay,
            text_color=self.text,
            font=self._font(1),
            command=self._toggle_auto_scan,
        )
        self.auto_scan_btn.pack(fill=tk.X, padx=14, pady=3)
        self._refresh_auto_scan_button()

        workspace = ctk.CTkFrame(app, fg_color=self.bg, corner_radius=0)
        workspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header = ctk.CTkFrame(workspace, fg_color=self.bg, corner_radius=0)
        header.pack(fill=tk.X, padx=14, pady=(14, 6))
        self.count_label = ctk.CTkLabel(header, text="", text_color=self.text, font=self._font())
        self.count_label.pack(side=tk.RIGHT)

        self.toolbar_row = ctk.CTkFrame(workspace, fg_color=self.bg, corner_radius=0, height=38)
        self.toolbar_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        self.toolbar_row.pack_propagate(False)

        self.top_bar = ctk.CTkFrame(self.toolbar_row, fg_color=self.bg, corner_radius=0, height=38)
        self.top_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        top = self.top_bar

        self.toolbar_controls = ctk.CTkFrame(self.toolbar_row, fg_color=self.bg, corner_radius=0, width=360, height=38)
        self.toolbar_controls.pack(side=tk.RIGHT, fill=tk.Y)
        self.toolbar_controls.pack_propagate(False)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.date_from_var.trace_add("write", self._on_search)
        self.date_to_var.trace_add("write", self._on_search)
        self.date_from_var.trace_add("write", lambda *_: self._refresh_date_buttons())
        self.date_to_var.trace_add("write", lambda *_: self._refresh_date_buttons())
        self.search_entry = ctk.CTkEntry(
            top,
            width=520,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            border_width=0,
            text_color=self.text,
            placeholder_text="Start typing to prefilter by project, title, or prompt",
            placeholder_text_color=self.muted,
            font=self._font(2),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_entry_change)
        self.date_range_btn = ctk.CTkButton(
            self.toolbar_controls,
            text="Dates: Any",
            width=164,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            text_color=self.text,
            hover_color=self.overlay,
            font=self._font(weight="bold"),
            command=self._open_date_range_picker,
        )
        self.date_range_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        sort_menu = ctk.CTkOptionMenu(
            self.toolbar_controls,
            variable=self.sort_var,
            values=[
                "Newest",
                "Oldest",
                "LLM A-Z",
                "LLM Z-A",
                "Project A-Z",
                "Project Z-A",
                "Prompt A-Z",
                "Prompt Z-A",
            ],
            command=lambda _: self._apply_filter(),
            width=142,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            button_color=self.overlay,
            button_hover_color=self.blue,
            dropdown_fg_color=self.surface,
            dropdown_hover_color=self.overlay,
            text_color=self.text,
            font=self._font(1),
        )
        sort_menu.pack(side=tk.RIGHT)

        self.delete_bar = tk.Frame(workspace, bg=self.overlay, pady=6, padx=12)
        tk.Label(self.delete_bar, text="DELETE MODE",
                 bg=self.overlay, fg=self.text,
                 font=self._font(weight="bold")).pack(side=tk.LEFT, padx=(0, 12))
        self.select_all_btn = tk.Button(
            self.delete_bar,
            text="Select All",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface_2,
            font=self._font(),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._toggle_select_all,
        )
        self.select_all_btn.pack(side=tk.LEFT)
        self.confirm_delete_btn = tk.Button(
            self.delete_bar,
            text="Delete 0 Selected",
            bg=self.bg,
            fg=self.danger,
            activebackground=self.surface,
            font=self._font(weight="bold"),
            relief=tk.FLAT,
            padx=12,
            pady=2,
            cursor="hand2",
            command=self._confirm_delete,
            state=tk.DISABLED,
        )
        self.confirm_delete_btn.pack(side=tk.RIGHT)
        tk.Button(
            self.delete_bar,
            text="Cancel",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface_2,
            font=self._font(),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._exit_delete_mode,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        self.paned = tk.PanedWindow(workspace, orient=tk.HORIZONTAL,
                                    bg=self.bg, sashwidth=5, sashpad=0,
                                    relief=tk.FLAT, borderwidth=0)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))
        paned = self.paned

        list_frame = tk.Frame(paned, bg=self.bg)
        self.list_frame = list_frame
        paned.add(list_frame, width=1320, minsize=900)

        list_header = tk.Frame(list_frame, bg=self.bg, pady=4)
        list_header.pack(fill=tk.X)
        tk.Label(
            list_header,
            text="Threads",
            bg=self.bg,
            fg=self.blue,
            font=self._font(1, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            list_header,
            text="Numbered, filtered, and sorted.",
            bg=self.bg,
            fg=self.text,
            font=self._font(-1),
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.tree = ttk.Treeview(
            list_frame,
            columns=("check", "number", "source", "project", "date", "preview"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("check", text="", anchor=tk.W)
        self.tree.heading("number", text="#", anchor=tk.E, command=lambda: self._toggle_sort("Oldest", "Newest"))
        self.tree.heading("source", text="LLM", anchor=tk.W, command=lambda: self._toggle_sort("LLM A-Z", "LLM Z-A"))
        self.tree.heading("project", text="Project", anchor=tk.W, command=lambda: self._toggle_sort("Project A-Z", "Project Z-A"))
        self.tree.heading("date", text="Date", anchor=tk.W, command=lambda: self._toggle_sort("Oldest", "Newest"))
        self.tree.heading("preview", text="    Thread / Last Prompt", anchor=tk.W, command=lambda: self._toggle_sort("Prompt A-Z", "Prompt Z-A"))
        self.tree.column("check", width=0, minwidth=0, stretch=False, anchor=tk.W)
        self.tree.column("number", width=42, minwidth=38, stretch=False, anchor=tk.E)
        self.tree.column("source", width=230, minwidth=180, stretch=False, anchor=tk.W)
        self.tree.column("project", width=250, minwidth=160, stretch=False, anchor=tk.W)
        self.tree.column("date", width=135, minwidth=100, stretch=False, anchor=tk.W)
        self.tree.column("preview", width=950, minwidth=420, stretch=False, anchor=tk.W)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.tag_configure("gone", foreground=self.muted)
        self.tree.tag_configure("codex", foreground=self.yellow)
        self.tree.tag_configure("grok", foreground=self.pink)
        self.tree.tag_configure("copilot", foreground=self.purple)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_action)
        self.tree.bind("<Return>", self._on_action)
        self.tree.bind("<Button-3>", self._on_right_click)

        right = tk.Frame(paned, bg=self.bg)
        paned.add(right, width=360, minsize=320)
        self.toolbar_row.bind("<Configure>", self._sync_toolbar_to_table_width)
        list_frame.bind("<Configure>", self._sync_toolbar_to_table_width)
        self.root.after_idle(self._sync_toolbar_to_table_width)

        preview_header = tk.Frame(right, bg=self.bg, pady=4)
        preview_header.pack(fill=tk.X)
        tk.Label(preview_header, text="Inspector", bg=self.bg, fg=self.blue,
                 font=self._font(1, "bold")).pack(side=tk.LEFT)
        tk.Label(preview_header, text="Metadata and first/last prompt.", bg=self.bg,
                 fg=self.text, font=self._font(-1)).pack(side=tk.LEFT, padx=(10, 0))

        preview_frame = tk.Frame(right, bg=self.surface)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        self.preview = tk.Text(
            preview_frame,
            bg=self.surface,
            fg=self.text,
            font=self._font(),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            state=tk.DISABLED,
            cursor="arrow",
        )
        preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview.yview)
        self.preview.configure(yscrollcommand=preview_scrollbar.set)
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.preview.tag_configure("label", foreground=self.blue, font=self._font(weight="bold"))
        self.preview.tag_configure("dim", foreground=self.muted)
        self.preview.tag_configure("message", foreground=self.green)
        self.preview.tag_configure("codex", foreground=self.yellow)
        self.preview.tag_configure("grok", foreground=self.pink)
        self.preview.tag_configure("copilot", foreground=self.purple)

        btn_frame = ctk.CTkFrame(right, fg_color=self.bg, corner_radius=0)
        btn_frame.pack(fill=tk.X)
        self.action_btn = ctk.CTkButton(
            btn_frame,
            text="Resume Session",
            fg_color=self.green,
            hover_color="#c8f7c5",
            text_color="#000000",
            text_color_disabled="#000000",
            font=self._font(1, "bold"),
            corner_radius=6,
            height=40,
            width=164,
            command=self._on_action,
            state=tk.DISABLED,
        )
        self.action_btn.pack(side=tk.RIGHT, pady=8)
        self.rename_btn = ctk.CTkButton(
            btn_frame,
            text="Rename",
            fg_color=self.surface_2,
            hover_color=self.overlay,
            text_color=self.text,
            text_color_disabled="#f2f5ff",
            font=self._font(weight="bold"),
            corner_radius=6,
            height=40,
            width=88,
            command=self._rename_session,
            state=tk.DISABLED,
        )
        self.rename_btn.pack(side=tk.LEFT, pady=8)
        self.delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            fg_color=self.danger,
            hover_color="#ff7a90",
            text_color="#ffffff",
            text_color_disabled="#ffffff",
            font=self._font(weight="bold"),
            corner_radius=6,
            height=40,
            width=88,
            command=self._enter_delete_mode,
            state=tk.DISABLED,
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(6, 0), pady=8)

        bar = tk.Frame(workspace, bg=self.bar, pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            bar,
            text="  Double-click or Enter to act  |  r refresh  |  q quit",
            bg=self.bar,
            fg=self.text,
            font=self._font(-1),
        ).pack(side=tk.LEFT)

        self.root.bind("<r>", lambda e: self._load_data() if not self._delete_mode else None)
        self.root.bind("q", lambda e: self.root.quit())
        self.root.bind("<Escape>", lambda e: self._exit_delete_mode() if self._delete_mode else None)
        self._refresh_source_buttons()
        self._refresh_date_buttons()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.bar, pady=9, padx=14)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Session Portal",
            bg=self.bar,
            fg=self.text,
            font=("Consolas", 14, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="Dynamic local session sources",
            bg=self.bar,
            fg=self.muted,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT, padx=(12, 0))
        self.count_label = tk.Label(header, text="", bg=self.bar, fg=self.text,
                                    font=("Consolas", 10))
        self.count_label.pack(side=tk.RIGHT)

        self.top_bar = tk.Frame(self.root, bg=self.bg, pady=8, padx=12)
        self.top_bar.pack(fill=tk.X)
        top = self.top_bar

        tk.Label(top, text="Search:", bg=self.bg, fg=self.blue,
                 font=("Consolas", 11)).pack(side=tk.LEFT, padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = tk.Entry(
            top,
            textvariable=self.search_var,
            bg=self.surface,
            fg=self.text,
            insertbackground=self.text,
            font=("Consolas", 11),
            relief=tk.FLAT,
            bd=6,
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sort_menu = tk.OptionMenu(top, self.sort_var,
                                  "Date ↓", "Date ↑", "Project A→Z", "Project Z→A",
                                  command=lambda _: self._apply_filter())
        sort_menu.config(bg=self.surface, fg=self.text, activebackground=self.overlay,
                         activeforeground=self.text, highlightthickness=0,
                         relief=tk.FLAT, font=("Consolas", 10), bd=0)
        sort_menu["menu"].config(bg=self.surface, fg=self.text,
                                 activebackground=self.overlay, activeforeground=self.text,
                                 font=("Consolas", 10))
        sort_menu.pack(side=tk.RIGHT, padx=(8, 4))

        source_menu = tk.OptionMenu(top, self.source_var,
                                    *self._source_filter_labels(),
                                    command=lambda _: self._apply_filter())
        source_menu.config(bg=self.surface, fg=self.text, activebackground=self.overlay,
                           activeforeground=self.text, highlightthickness=0,
                           relief=tk.FLAT, font=("Consolas", 10), bd=0)
        source_menu["menu"].config(bg=self.surface, fg=self.text,
                                   activebackground=self.overlay, activeforeground=self.text,
                                   font=("Consolas", 10))
        source_menu.pack(side=tk.RIGHT, padx=(0, 4))

        tk.Button(
            top,
            text="Refresh",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface,
            activeforeground=self.text,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._load_data,
        ).pack(side=tk.RIGHT, padx=(0, 4))

        tk.Button(
            top,
            text="Scan Sources",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface,
            activeforeground=self.text,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._edit_sources,
        ).pack(side=tk.RIGHT, padx=(0, 4))

        self.delete_bar = tk.Frame(self.root, bg=self.overlay, pady=6, padx=12)
        tk.Label(self.delete_bar, text="DELETE MODE",
                 bg=self.overlay, fg=self.text,
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=(0, 12))
        self.select_all_btn = tk.Button(
            self.delete_bar,
            text="Select All",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface_2,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._toggle_select_all,
        )
        self.select_all_btn.pack(side=tk.LEFT)
        self.confirm_delete_btn = tk.Button(
            self.delete_bar,
            text="Delete 0 Selected",
            bg=self.bg,
            fg="#f38ba8",
            activebackground=self.surface,
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=2,
            cursor="hand2",
            command=self._confirm_delete,
            state=tk.DISABLED,
        )
        self.confirm_delete_btn.pack(side=tk.RIGHT)
        tk.Button(
            self.delete_bar,
            text="Cancel",
            bg=self.overlay,
            fg=self.text,
            activebackground=self.surface_2,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._exit_delete_mode,
        ).pack(side=tk.RIGHT, padx=(0, 8))

        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                                    bg=self.bg, sashwidth=5, sashpad=0,
                                    relief=tk.FLAT, borderwidth=0)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        paned = self.paned

        list_frame = tk.Frame(paned, bg=self.bg)
        paned.add(list_frame, width=1320, minsize=900)

        list_header = tk.Frame(list_frame, bg=self.bg, pady=4)
        list_header.pack(fill=tk.X)
        tk.Label(
            list_header,
            text="Threads",
            bg=self.bg,
            fg=self.blue,
            font=("Consolas", 11, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            list_header,
            text="Filtered, sorted, and numbered.",
            bg=self.bg,
            fg=self.muted,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.tree = ttk.Treeview(
            list_frame,
            columns=("check", "number", "source", "project", "date", "preview"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("check", text="", anchor=tk.W)
        self.tree.heading("number", text="#", anchor=tk.E)
        self.tree.heading("source", text="LLM", anchor=tk.W)
        self.tree.heading("project", text="Project", anchor=tk.W)
        self.tree.heading("date", text="Date", anchor=tk.W)
        self.tree.heading("preview", text="    Thread / Last Prompt", anchor=tk.W)
        self.tree.column("check", width=0, minwidth=0, stretch=False, anchor=tk.W)
        self.tree.column("number", width=44, minwidth=38, stretch=False, anchor=tk.E)
        self.tree.column("source", width=230, minwidth=180, stretch=False, anchor=tk.W)
        self.tree.column("project", width=250, minwidth=160, stretch=False, anchor=tk.W)
        self.tree.column("date", width=135, minwidth=100, stretch=False, anchor=tk.W)
        self.tree.column("preview", width=950, minwidth=420, stretch=False, anchor=tk.W)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.tag_configure("gone", foreground=self.muted)
        self.tree.tag_configure("codex", foreground=self.yellow)
        self.tree.tag_configure("grok", foreground="#ff99cc")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_action)
        self.tree.bind("<Return>", self._on_action)
        self.tree.bind("<Button-3>", self._on_right_click)

        right = tk.Frame(paned, bg=self.bg)
        paned.add(right, width=360, minsize=320)

        preview_header = tk.Frame(right, bg=self.bg, pady=4)
        preview_header.pack(fill=tk.X)
        tk.Label(preview_header, text="Preview", bg=self.bg, fg=self.blue,
                 font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        tk.Label(preview_header, text="Metadata and first/last prompt.", bg=self.bg,
                 fg=self.muted, font=("Consolas", 9)).pack(side=tk.LEFT, padx=(10, 0))

        self.preview = tk.Text(
            right,
            bg=self.surface,
            fg=self.text,
            font=("Consolas", 10),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=12,
            pady=10,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview.tag_configure("label", foreground=self.blue, font=("Consolas", 10, "bold"))
        self.preview.tag_configure("dim", foreground=self.muted)
        self.preview.tag_configure("message", foreground=self.green)
        self.preview.tag_configure("codex", foreground=self.yellow)

        btn_frame = tk.Frame(right, bg=self.bg, pady=8)
        btn_frame.pack(fill=tk.X)
        self.action_btn = tk.Button(
            btn_frame,
            text="Resume Session",
            bg=self.blue,
            fg=self.bg,
            font=("Consolas", 11, "bold"),
            relief=tk.FLAT,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._on_action,
            state=tk.DISABLED,
        )
        self.action_btn.pack(side=tk.RIGHT)
        self.rename_btn = tk.Button(
            btn_frame,
            text="Rename",
            bg=self.overlay,
            fg=self.text,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._rename_session,
            state=tk.DISABLED,
        )
        self.rename_btn.pack(side=tk.LEFT)
        self.delete_btn = tk.Button(
            btn_frame,
            text="Delete",
            bg="#f38ba8",
            fg=self.bg,
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._enter_delete_mode,
            state=tk.DISABLED,
        )
        self.delete_btn.pack(side=tk.LEFT, padx=(6, 0))

        bar = tk.Frame(self.root, bg=self.bar, pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            bar,
            text="  Double-click or Enter to act  |  r refresh  |  q quit",
            bg=self.bar,
            fg=self.text,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT)

        self.root.bind("<r>", lambda e: self._load_data() if not self._delete_mode else None)
        self.root.bind("q", lambda e: self.root.quit())
        self.root.bind("<Escape>", lambda e: self._exit_delete_mode() if self._delete_mode else None)

    def _load_data(self):
        self.settings = load_settings()
        self.auto_scan_var.set(bool(self.settings.get("auto_scan_enabled", True)))
        self.all_sessions = load_sessions(self.settings)
        self._build_source_buttons()
        self._apply_filter()
        self._refresh_auto_scan_button()

    def _edit_sources(self):
        self._show_onboarding(first_run=False)
        self._load_data()

    def _toggle_auto_scan(self):
        enabled = not self.auto_scan_var.get()
        self.auto_scan_var.set(enabled)
        self.settings["auto_scan_enabled"] = enabled
        save_settings(self.settings)
        self._refresh_auto_scan_button()
        if enabled:
            self._auto_scan()
        elif self._auto_scan_after_id:
            self.root.after_cancel(self._auto_scan_after_id)
            self._auto_scan_after_id = None

    def _refresh_auto_scan_button(self):
        if not hasattr(self, "auto_scan_btn"):
            return
        enabled = self.auto_scan_var.get()
        self.auto_scan_btn.configure(
            text="Auto Scan: ON" if enabled else "Auto Scan: OFF",
            fg_color=self.blue if enabled else self.surface_2,
            text_color=self.bg_deep if enabled else self.text,
            hover_color=self.blue if enabled else self.overlay,
        )

    def _schedule_auto_scan(self):
        if self._auto_scan_after_id:
            self.root.after_cancel(self._auto_scan_after_id)
            self._auto_scan_after_id = None
        if not self.auto_scan_var.get():
            return
        interval = int(self.settings.get("auto_scan_interval_ms", 15000) or 15000)
        self._auto_scan_after_id = self.root.after(max(5000, interval), self._auto_scan)

    def _auto_scan(self):
        self._auto_scan_after_id = None
        try:
            if not self._delete_mode:
                selected = self.tree.selection()[0] if hasattr(self, "tree") and self.tree.selection() else ""
                self._load_data()
                if selected and selected in self.tree.get_children():
                    self.tree.selection_set(selected)
        finally:
            self._schedule_auto_scan()

    def _on_search(self, *_):
        self._apply_filter()

    def _on_search_entry_change(self, _event=None):
        self.search_var.set(self.search_entry.get())

    def _toggle_sort(self, ascending: str, descending: str):
        self.sort_var.set(ascending if self.sort_var.get() == descending else descending)
        self._apply_filter()

    def _parse_date_filter(self, value: str, end_of_day: bool = False):
        value = value.strip()
        if not value:
            return None
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        return int(dt.timestamp() * 1000)

    def _refresh_date_buttons(self):
        if hasattr(self, "date_range_btn"):
            start = self.date_from_var.get() or "Any"
            end = self.date_to_var.get() or "Any"
            text = "Dates: Any" if start == "Any" and end == "Any" else "Dates: Custom"
            self.date_range_btn.configure(text=text)

    def _open_date_range_picker(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Date Range")
        dialog.configure(bg=self.bg)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        body = tk.Frame(dialog, bg=self.bg, padx=16, pady=16)
        body.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            body,
            text="Date Range",
            bg=self.bg,
            fg=self.text,
            font=self._font(2, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        start_value = tk.StringVar(value=self.date_from_var.get() or "Any")
        end_value = tk.StringVar(value=self.date_to_var.get() or "Any")
        active_target = tk.StringVar(value="from")

        def sync_labels():
            start_value.set(self.date_from_var.get() or "Any")
            end_value.set(self.date_to_var.get() or "Any")

        month_seed = self.date_from_var.get() or self.date_to_var.get()
        try:
            seed_date = datetime.strptime(month_seed, "%Y-%m-%d")
        except ValueError:
            seed_date = datetime.now()
        month_var = tk.IntVar(value=seed_date.month)
        year_var = tk.IntVar(value=seed_date.year)

        def row(label: str, value_var: tk.StringVar, target_name: str):
            frame = tk.Frame(body, bg=self.surface, padx=10, pady=8)
            frame.pack(fill=tk.X, pady=4)
            tk.Label(
                frame,
                text=label,
                bg=self.surface,
                fg=self.blue,
                font=self._font(weight="bold"),
                width=8,
                anchor="w",
            ).pack(side=tk.LEFT)
            tk.Label(
                frame,
                textvariable=value_var,
                bg=self.surface,
                fg=self.text,
                font=self._font(weight="bold"),
                width=12,
                anchor="w",
            ).pack(side=tk.LEFT, padx=(8, 10))
            tk.Button(
                frame,
                text="Select",
                bg=self.overlay,
                fg=self.text,
                activebackground=self.surface_2,
                activeforeground=self.text,
                relief=tk.FLAT,
                padx=12,
                command=lambda: (active_target.set(target_name), render_calendar()),
            ).pack(side=tk.RIGHT)

        row("From", start_value, "from")
        row("To", end_value, "to")

        calendar_panel = tk.Frame(body, bg=self.bg)
        calendar_panel.pack(fill=tk.X, pady=(10, 0))
        calendar_header = tk.Frame(calendar_panel, bg=self.bg)
        calendar_header.pack(fill=tk.X, pady=(0, 8))
        active_label = tk.Label(
            calendar_header,
            text="",
            bg=self.bg,
            fg=self.blue,
            font=self._font(weight="bold"),
            anchor="w",
        )
        active_label.pack(side=tk.LEFT)
        month_label = tk.Label(
            calendar_header,
            text="",
            bg=self.bg,
            fg=self.text,
            font=self._font(weight="bold"),
            width=16,
        )
        month_label.pack(side=tk.LEFT, expand=True)
        grid = tk.Frame(calendar_panel, bg=self.bg)
        grid.pack()

        def shift_month(delta: int):
            month = month_var.get() + delta
            year = year_var.get()
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
            month_var.set(month)
            year_var.set(year)
            render_calendar()

        tk.Button(
            calendar_header,
            text="<",
            bg=self.surface,
            fg=self.text,
            activebackground=self.overlay,
            activeforeground=self.text,
            relief=tk.FLAT,
            width=4,
            command=lambda: shift_month(-1),
        ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            calendar_header,
            text=">",
            bg=self.surface,
            fg=self.text,
            activebackground=self.overlay,
            activeforeground=self.text,
            relief=tk.FLAT,
            width=4,
            command=lambda: shift_month(1),
        ).pack(side=tk.LEFT)

        def choose_day(day: int):
            value = f"{year_var.get():04d}-{month_var.get():02d}-{day:02d}"
            if active_target.get() == "from":
                self.date_from_var.set(value)
                active_target.set("to")
            else:
                self.date_to_var.set(value)
            sync_labels()
            render_calendar()

        def render_calendar():
            for child in grid.winfo_children():
                child.destroy()
            year = year_var.get()
            month = month_var.get()
            active_label.config(text=f"Choosing {'From' if active_target.get() == 'from' else 'To'}")
            month_label.config(text=f"{calendar.month_name[month]} {year}")
            selected_value = self.date_from_var.get() if active_target.get() == "from" else self.date_to_var.get()
            for col, day_name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
                tk.Label(
                    grid,
                    text=day_name,
                    bg=self.bg,
                    fg=self.blue,
                    font=self._font(-1, "bold"),
                    width=4,
                ).grid(row=0, column=col, padx=2, pady=(0, 4))
            for row_index, week in enumerate(calendar.monthcalendar(year, month), start=1):
                for col, day in enumerate(week):
                    if not day:
                        tk.Label(grid, text="", bg=self.bg, width=4).grid(row=row_index, column=col, padx=2, pady=2)
                        continue
                    date_value = f"{year:04d}-{month:02d}-{day:02d}"
                    is_selected = selected_value == date_value
                    tk.Button(
                        grid,
                        text=str(day),
                        bg=self.blue if is_selected else self.surface,
                        fg=self.bg_deep if is_selected else self.text,
                        activebackground=self.overlay,
                        activeforeground=self.text,
                        relief=tk.FLAT,
                        width=4,
                        command=lambda value=day: choose_day(value),
                    ).grid(row=row_index, column=col, padx=2, pady=2)

        footer = tk.Frame(body, bg=self.bg)
        footer.pack(fill=tk.X, pady=(12, 0))
        tk.Button(
            footer,
            text="Clear Dates",
            bg=self.surface_2,
            fg=self.text,
            activebackground=self.overlay,
            activeforeground=self.text,
            relief=tk.FLAT,
            padx=12,
            command=lambda: (self._clear_date_filter(), sync_labels(), render_calendar()),
        ).pack(side=tk.LEFT)
        tk.Button(
            footer,
            text="Done",
            bg=self.green,
            fg="#000000",
            activebackground="#c8f7c5",
            activeforeground="#000000",
            relief=tk.FLAT,
            padx=16,
            command=dialog.destroy,
        ).pack(side=tk.RIGHT)

        render_calendar()
        dialog.update_idletasks()
        if hasattr(self, "date_range_btn"):
            anchor = self.date_range_btn
            x = anchor.winfo_rootx()
            y = anchor.winfo_rooty() + anchor.winfo_height() + 6
            screen_width = self.root.winfo_screenwidth()
            if x + dialog.winfo_width() > screen_width - 12:
                x = max(12, screen_width - dialog.winfo_width() - 12)
        else:
            x = self.root.winfo_x() + max(80, (self.root.winfo_width() - dialog.winfo_width()) // 2)
            y = self.root.winfo_y() + 120
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()

    def _clear_date_filter(self):
        self.date_from_var.set("")
        self.date_to_var.set("")
        self._apply_filter()

    def _apply_filter(self):
        source_filter = self.source_var.get()
        query = self.search_var.get().lower()
        from_ms = self._parse_date_filter(self.date_from_var.get())
        to_ms = self._parse_date_filter(self.date_to_var.get(), end_of_day=True)
        if from_ms is not None and to_ms is not None and from_ms > to_ms:
            from_ms, to_ms = to_ms, from_ms

        pool = self.all_sessions

        source_key = provider_key_for_label(source_filter)
        if source_key:
            pool = [s for s in pool if s.get("_source") == source_key]
        if query:
            pool = [
                s for s in pool
                if query in s.get("project", "").lower()
                or query in s.get("display", "").lower()
            ]
        if from_ms is not None:
            pool = [s for s in pool if s.get("timestamp", 0) >= from_ms]
        if to_ms is not None:
            pool = [s for s in pool if s.get("timestamp", 0) <= to_ms]

        sort = self.sort_var.get()
        if sort.startswith("Newest") or sort.startswith("Date"):
            pool = sorted(pool, key=lambda s: s.get("timestamp", 0), reverse=True)
        elif sort.startswith("Oldest"):
            pool = sorted(pool, key=lambda s: s.get("timestamp", 0))
        elif sort in ("Model A-Z", "LLM A-Z"):
            pool = sorted(pool, key=lambda s: session_model_label(s).lower())
        elif sort in ("Model Z-A", "LLM Z-A"):
            pool = sorted(pool, key=lambda s: session_model_label(s).lower(), reverse=True)
        elif sort.startswith("Project A"):
            pool = sorted(pool, key=lambda s: os.path.basename(s.get("project", "")).lower())
        elif sort.startswith("Project Z"):
            pool = sorted(pool, key=lambda s: os.path.basename(s.get("project", "")).lower(), reverse=True)
        elif sort == "Prompt A-Z":
            pool = sorted(pool, key=lambda s: (s.get("display", "") or "").lower())
        elif sort == "Prompt Z-A":
            pool = sorted(pool, key=lambda s: (s.get("display", "") or "").lower(), reverse=True)

        self.filtered_sessions = pool
        self._refresh_list()
        self._refresh_source_buttons()

        total = len(self.all_sessions)
        shown = len(self.filtered_sessions)
        counts = []
        for key, info in PROVIDER_OPTIONS.items():
            count = sum(1 for s in self.filtered_sessions if s.get("_source") == key)
            if count:
                counts.append(f"{info['label']} {count}")
        count_text = "  ".join(counts)
        self.count_label.configure(
            text=f"{shown} of {total} shown" + (f"  |  {count_text}" if count_text else "")
        )

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row_num, s in enumerate(self.filtered_sessions, start=1):
            src = s.get("_source", "claude")
            project = s.get("project", "")
            display_title = s.get("display", "") or ""
            project_short = os.path.basename(project) or project
            ts = s.get("timestamp", 0)
            date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d  %H:%M") if ts else ""
            display = "    " + (display_title or "")[:90]

            if src == "grok":
                tag = ("grok",)
            elif src == "codex":
                tag = ("codex",)
            elif src == "copilot":
                tag = ("copilot",)
            else:
                tag = ()

            model_label = session_model_label(s)
            check = "x" if s["sessionId"] in self._checked_ids else ""
            self.tree.insert("", tk.END, iid=s["sessionId"],
                             values=(check, row_num, model_label, project_short, date_str, display),
                             tags=tag)

    def _on_select(self, _event=None):
        if self._delete_mode:
            return
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s["sessionId"] == sid), None)
        if not session:
            return
        self._show_preview(session)

        src = session.get("_source", "claude")
        if src == "grok":
            self.action_btn.configure(text="Resume Grok", fg_color=self.green,
                                      text_color="#000000", state=tk.NORMAL)
        elif src == "copilot":
            self.action_btn.configure(text="Resume Copilot", fg_color=self.green,
                                      text_color="#000000", state=tk.NORMAL)
        elif src == "codex":
            self.action_btn.configure(text="Resume Codex", fg_color=self.green,
                                      text_color="#000000", state=tk.NORMAL)
        elif src == "claude":
            self.action_btn.configure(text="Resume Claude Code", fg_color=self.green,
                                      text_color="#000000", state=tk.NORMAL)
        else:
            self.action_btn.configure(text=f"Resume {provider_label(src)}", fg_color=self.green,
                                      text_color="#000000", state=tk.NORMAL if src in RESUME_HANDLERS else tk.DISABLED)
        self.rename_btn.configure(state=tk.NORMAL)
        self.delete_btn.configure(state=tk.NORMAL)

    def _show_preview(self, session: dict):
        first, last, count, tokens = get_session_preview(session)

        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)

        src = session.get("_source", "claude")
        if src == "grok":
            src_tag = "grok"
        elif src == "copilot":
            src_tag = "copilot"
        elif src == "codex":
            src_tag = "codex"
        else:
            src_tag = "dim"

        def row(label, value, tag="dim"):
            value = " ".join(str(value or "").split())
            self.preview.insert(tk.END, f"{label:<11}", "label")
            self.preview.insert(tk.END, f"{value}\n", tag)

        ts = session.get("timestamp", 0)
        date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d  %H:%M:%S") if ts else ""

        row("LLM", session_model_label(session), src_tag)
        row("Provider", provider_label(src), src_tag)
        if session.get("display"):
            row("Title", session.get("display", ""), src_tag)
        row("Project", session.get("project", ""))
        row("Session", session.get("sessionId", ""))
        row("Date", date_str)

        if src == "grok":
            row("Messages", str(count))
        elif src == "codex":
            row("Thread", session.get("display", ""), "codex")
            row("Messages", str(count) if "_file" in session else "n/a")
        else:
            row("Messages", str(count))

        if tokens.get("input") or tokens.get("output"):
            total = tokens["input"] + tokens["output"]
            row("Tokens", f"{total:,}  (in {tokens['input']:,}  out {tokens['output']:,})")
            if tokens.get("cache_read") or tokens.get("cache_write"):
                row("Cache", f"read {tokens['cache_read']:,}  write {tokens.get('cache_write', 0):,}")

        if first:
            self.preview.insert(tk.END, "\n── First message ──\n", "label")
            self.preview.insert(tk.END,
                                first[:600] + (" …" if len(first) > 600 else "") + "\n",
                                "message")
        if last:
            self.preview.insert(tk.END, "\n── Last message ──\n", "label")
            self.preview.insert(tk.END,
                                last[:600] + (" …" if len(last) > 600 else "") + "\n",
                                "message")

        self.preview.config(state=tk.DISABLED)

    def _on_action(self, _event=None):
        if self._delete_mode:
            return
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s["sessionId"] == sid), None)
        if not session:
            return

        src = session.get("_source", "claude")
        try:
            handler = RESUME_HANDLERS.get(src)
            if handler:
                handler(session.get("project", str(Path.home())), sid)
        except Exception as exc:
            messagebox.showerror("Action failed", str(exc))

    def _on_tree_click(self, event):
        if not self._delete_mode:
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if row in self._checked_ids:
            self._checked_ids.discard(row)
        else:
            self._checked_ids.add(row)
        self._update_delete_bar()
        self._refresh_list()
        return "break"

    def _on_right_click(self, event):
        if self._delete_mode:
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        self._on_select()
        n = len(self.filtered_sessions)
        menu = tk.Menu(self.root, tearoff=0,
                       bg=self.surface, fg=self.text,
                       activebackground=self.overlay, activeforeground=self.text,
                       font=("Consolas", 10))
        menu.add_command(label="Rename", command=self._rename_session)
        menu.add_separator()
        menu.add_command(label="Delete This Session",
                         command=lambda sid=row: self._enter_delete_mode(pre_check_sid=sid))
        menu.add_command(label=f"Delete All {n} Shown",
                         command=lambda: self._enter_delete_mode(pre_check_all=True))
        menu.tk_popup(event.x_root, event.y_root)

    def _rename_session(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s["sessionId"] == sid), None)
        if not session:
            return
        current = session.get("display", "") or ""
        new_name = simpledialog.askstring(
            "Rename Session", "New name (blank to clear custom name):",
            initialvalue=current, parent=self.root
        )
        if new_name is None:
            return
        new_name = new_name.strip()
        renames = load_renames()
        if new_name:
            renames[sid] = new_name
        else:
            renames.pop(sid, None)
        save_renames(renames)
        session["display"] = new_name or current
        self._refresh_list()
        self.tree.selection_set(sid)
        self._on_select()

    def _enter_delete_mode(self, pre_check_sid=None, pre_check_all=False):
        self._delete_mode = True
        self._checked_ids = set()
        if pre_check_all:
            self._checked_ids = {s["sessionId"] for s in self.filtered_sessions}
        elif pre_check_sid:
            self._checked_ids = {pre_check_sid}
        else:
            sel = self.tree.selection()
            if sel:
                self._checked_ids = {sel[0]}
        self.delete_bar.pack(fill=tk.X, after=getattr(self, "toolbar_row", self.top_bar))
        self.tree.column("check", width=45, minwidth=45)
        self.delete_btn.configure(state=tk.DISABLED)
        self.rename_btn.configure(state=tk.DISABLED)
        self.action_btn.configure(state=tk.DISABLED)
        self._refresh_list()
        self._update_delete_bar()

    def _exit_delete_mode(self):
        self._delete_mode = False
        self._checked_ids = set()
        self.delete_bar.pack_forget()
        self.tree.column("check", width=0, minwidth=0)
        self._refresh_list()
        self.delete_btn.configure(state=tk.DISABLED)
        self.rename_btn.configure(state=tk.DISABLED)
        self.action_btn.configure(state=tk.DISABLED)

    def _toggle_select_all(self):
        total = len(self.filtered_sessions)
        if len(self._checked_ids) >= total:
            self._checked_ids = set()
        else:
            self._checked_ids = {s["sessionId"] for s in self.filtered_sessions}
        self._update_delete_bar()
        self._refresh_list()

    def _update_delete_bar(self):
        n = sum(1 for s in self.filtered_sessions if s["sessionId"] in self._checked_ids)
        total = len(self.filtered_sessions)
        self.confirm_delete_btn.config(
            text=f"Delete {n} Selected",
            state=tk.NORMAL if n > 0 else tk.DISABLED,
        )
        self.select_all_btn.config(
            text="Deselect All" if n == total and total > 0 else "Select All"
        )

    def _confirm_delete(self):
        to_delete = [s for s in self.filtered_sessions
                     if s["sessionId"] in self._checked_ids]
        n = len(to_delete)
        if n == 0:
            return
        if not messagebox.askyesno(
                "Confirm Delete",
                f"Permanently delete {n} session{'s' if n > 1 else ''}?\n\nThis cannot be undone.",
                icon="warning"):
            return
        renames = load_renames()
        for session in to_delete:
            src = session.get("_source", "claude")
            handler = DELETE_HANDLERS.get(src, delete_claude_session)
            handler(session)
            renames.pop(session["sessionId"], None)
        save_renames(renames)
        self._exit_delete_mode()
        self._load_data()


def main():
    root = tk.Tk()
    root.withdraw()
    SessionPortal(root)
    root.mainloop()


if __name__ == "__main__":
    main()
