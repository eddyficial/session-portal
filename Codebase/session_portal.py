#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tkinter as tk
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
OLLAMA_DIR = Path.home() / ".ollama"
OLLAMA_HISTORY_FILE = OLLAMA_DIR / "history"
LM_STUDIO_DIR = Path.home() / "AppData" / "Roaming" / "LM Studio"
LM_STUDIO_MODELS_DIR = Path.home() / ".lmstudio" / "models"
GROK_DIR = Path.home() / ".grok"
GROK_SESSIONS_DIR = GROK_DIR / "sessions"
GROK_MODELS_FILE = GROK_DIR / "models_cache.json"
GROK_EXE = GROK_DIR / "bin" / "grok.exe"
RENAMES_FILE = Path(__file__).parent / "renames.json"
SETTINGS_FILE = Path(__file__).parent / "settings.json"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

PROVIDER_OPTIONS = {
    "claude": {
        "label": "Claude",
        "description": "Claude Code sessions and history",
        "path": str(CLAUDE_DIR),
    },
    "codex": {
        "label": "Codex",
        "description": "Codex sessions",
        "path": str(CODEX_DIR),
    },
    "grok": {
        "label": "Grok",
        "description": "Grok CLI sessions and prompt history",
        "path": str(GROK_DIR),
    },
    "ollama": {
        "label": "Ollama",
        "description": "Ollama prompt history when found",
        "path": str(OLLAMA_DIR),
    },
    "lm_studio": {
        "label": "LM Studio",
        "description": "LM Studio local data when supported",
        "path": str(LM_STUDIO_DIR),
    },
}

DEFAULT_SETTINGS = {
    "onboarding_complete": False,
    "providers": {key: True for key in PROVIDER_OPTIONS},
}


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
    """Best-effort decode for Claude project folder names like C--Users-eddyo."""
    name = path.name
    if name.startswith("C--"):
        decoded = "C:\\" + name[3:].replace("-", "\\")
        return decoded
    return str(path)


def _get_claude_cwd(fp: Path) -> str:
    """Return the real cwd recorded by Claude in a session jsonl file."""
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    cwd = rec.get("cwd")
                    if cwd and Path(cwd).exists():
                        return cwd
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    decoded = _decode_claude_project_dir(fp.parent)
    return decoded if Path(decoded).exists() else str(fp.parent)


def _get_claude_ai_title(fp: Path) -> str:
    """Return Claude's generated session title when present."""
    title = ""
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "ai-title":
                        ai_title = rec.get("aiTitle") or rec.get("title")
                        if isinstance(ai_title, str) and ai_title.strip():
                            title = ai_title.strip()
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return title


def _get_claude_model(fp: Path) -> str:
    """Return the last Claude model recorded in a session file."""
    model = ""
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    message = rec.get("message")
                    if rec.get("type") == "assistant" and isinstance(message, dict):
                        value = message.get("model")
                        if isinstance(value, str) and value.strip():
                            model = value.strip()
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return model


def model_group_label(source: str, model: str = "") -> str:
    model = (model or "").strip()
    if model.startswith("<") and model.endswith(">"):
        model = ""
    if source == "llm":
        return model or "Local LLM"
    if source == "claude":
        lower = model.lower()
        if "opus" in lower:
            return "Claude / Opus"
        if "sonnet" in lower:
            return "Claude / Sonnet"
        if "haiku" in lower:
            return "Claude / Haiku"
        return f"Claude / {model}" if model else "Claude / Unknown"
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
        entry = dict(history[sid]) if sid in history else {
            "sessionId": sid,
            "project": _get_claude_cwd(fp),
            "display": "",
            "timestamp": int(fp.stat().st_mtime * 1000),
        }
        entry["project"] = _get_claude_cwd(fp)
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

    user_messages = []
    last_prompt = ""
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "last-prompt":
                        prompt = rec.get("lastPrompt")
                        if (
                                isinstance(prompt, str)
                                and prompt.strip()
                                and not _looks_like_claude_transcript_context(prompt)):
                            last_prompt = prompt.strip()
                    elif rec.get("type") == "user":
                        text = _extract_claude_human_prompt(rec)
                        if text:
                            user_messages.append(text)
                    elif (rec.get("type") == "assistant"
                            and isinstance(rec.get("message"), dict)):
                        usage = rec["message"].get("usage", {})
                        if usage:
                            tokens["input"] += usage.get("input_tokens", 0)
                            tokens["output"] += usage.get("output_tokens", 0)
                            tokens["cache_read"] += usage.get("cache_read_input_tokens", 0)
                            tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    first = user_messages[0] if user_messages else None
    last = last_prompt or (user_messages[-1] if len(user_messages) > 1 else None)
    if first and last == first:
        last = None
    return first, last, len(user_messages), tokens


# ── Codex helpers ────────────────────────────────────────────────────────────

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
        subprocess.Popen(["wt", "-d", cwd, "powershell", "-NoExit", "-Command", startup], creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([
            "cmd", "/c", "start", "", "powershell", "-NoExit", "-Command", startup,
        ], creationflags=CREATE_NO_WINDOW)


def _start_cmd(cwd: str, command: str):
    cwd = cwd or str(Path.home())
    if not Path(cwd).exists():
        raise FileNotFoundError(f"Session working directory does not exist: {cwd}")
    if _has_windows_terminal():
        subprocess.Popen(["wt", "-d", cwd, "cmd", "/k", command], creationflags=CREATE_NO_WINDOW)
    else:
        subprocess.Popen([
            "cmd", "/c", "start", "", "/D", cwd, "cmd", "/k", command,
        ], creationflags=CREATE_NO_WINDOW)


def _get_codex_first_message(fp: Path) -> str:
    """Return the first non-system user message text from a Codex session file."""
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "response_item":
                        payload = rec.get("payload", {})
                        if (isinstance(payload, dict)
                                and payload.get("type") == "message"
                                and payload.get("role") == "user"):
                            for part in payload.get("content", []):
                                if isinstance(part, dict) and part.get("type") == "input_text":
                                    text = part.get("text", "").strip()
                                    if text and not text.startswith("<"):
                                        return text
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return ""


# ── Codex session loading ─────────────────────────────────────────────────────

def _get_codex_model(fp: Path) -> str:
    """Return the last Codex/OpenAI model recorded in a rollout file."""
    model = ""
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
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
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
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

        display = rec.get("thread_name", "")
        if not display and fp:
            display = _get_codex_first_message(fp)

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
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("type") == "turn_context":
                        return rec.get("payload", {}).get("cwd", "")
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return ""


def get_codex_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}

    user_messages = []
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rtype = rec.get("type")
                    payload = rec.get("payload", {})

                    if rtype == "response_item" and isinstance(payload, dict):
                        if (payload.get("type") == "message"
                                and payload.get("role") == "user"):
                            for part in payload.get("content", []):
                                if isinstance(part, dict) and part.get("type") == "input_text":
                                    text = part.get("text", "").strip()
                                    if text and not text.startswith("<"):
                                        user_messages.append(text)

                    elif rtype == "event_msg" and isinstance(payload, dict):
                        if payload.get("type") == "token_count":
                            info = payload.get("info") or {}
                            usage = info.get("last_token_usage") or info.get("total_token_usage") or {}
                            tokens["input"] += usage.get("input_tokens", 0)
                            tokens["output"] += usage.get("output_tokens", 0)
                            tokens["cache_read"] += usage.get("cached_input_tokens", 0)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    first = user_messages[0] if user_messages else None
    last = user_messages[-1] if len(user_messages) > 1 else None
    return first, last, len(user_messages), tokens


# ── Rename / delete helpers ───────────────────────────────────────────────────

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
    user_messages = []
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") == "user":
                    text = _extract_grok_user_text(rec.get("content", ""))
                    if text:
                        user_messages.append(text)
    except OSError:
        pass

    first = user_messages[0] if user_messages else None
    last = user_messages[-1] if len(user_messages) > 1 else None
    return first, last, len(user_messages), {}


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

    for history_file in GROK_SESSIONS_DIR.rglob("prompt_history.jsonl"):
        cwd = _decode_grok_cwd(history_file.parent.name)
        entries.append({
            "sessionId": "grok-history:" + history_file.parent.name,
            "project": cwd,
            "display": "Grok prompt history",
            "timestamp": int(history_file.stat().st_mtime * 1000),
            "model": "Grok / History",
            "model_group": "Grok / History",
            "_file": str(history_file),
            "_source": "grok",
            "_resumable": False,
        })

    return entries


def get_grok_preview(session: dict):
    fp = Path(session["_file"]) if "_file" in session else None
    if not fp or not fp.exists():
        return None, None, 0, {}
    if fp.name == "prompt_history.jsonl":
        prompts = []
        try:
            for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    prompt = rec.get("prompt", "")
                    if prompt:
                        prompts.append(prompt)
                except json.JSONDecodeError:
                    prompts.append(line)
        except OSError:
            prompts = []
        return "\n".join(prompts[:80]), None, len(prompts), {}
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


def _parse_ollama_list() -> list:
    exe = shutil.which("ollama")
    if not exe:
        return []
    try:
        proc = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=10)
    except Exception:
        return []
    if proc.returncode != 0:
        return []

    models = []
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name = parts[0]
        model_id = parts[1]
        size = ""
        if len(parts) >= 4:
            size = " ".join(parts[2:4])
        modified = " ".join(parts[4:]) if len(parts) > 4 else ""
        models.append({
            "name": name,
            "id": model_id,
            "size": size,
            "modified": modified,
        })
    return models


def _parse_ollama_running() -> set:
    exe = shutil.which("ollama")
    if not exe:
        return set()
    try:
        proc = subprocess.run([exe, "ps"], capture_output=True, text=True, timeout=10)
    except Exception:
        return set()
    if proc.returncode != 0:
        return set()
    running = set()
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if line:
            running.add(line.split()[0])
    return running


def load_llm_entries(settings: dict | None = None) -> list:
    settings = settings or load_settings()
    providers = settings.get("providers", {})
    entries = []

    if providers.get("ollama", True):
        if OLLAMA_HISTORY_FILE.exists():
            entries.append({
                "sessionId": "llm:ollama:history",
                "project": "Ollama history",
                "display": "Ollama prompt history",
                "timestamp": int(OLLAMA_HISTORY_FILE.stat().st_mtime * 1000),
                "model": "Ollama / History",
                "model_group": "Ollama / History",
                "_file": str(OLLAMA_HISTORY_FILE),
                "_source": "llm",
                "_provider": "Ollama",
                "_status": "history",
                "_resumable": False,
            })

    return entries


def get_llm_preview(session: dict):
    if session.get("_status") == "history" and session.get("_file"):
        fp = Path(session["_file"])
        try:
            text = fp.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            text = ""
        return text[:4000], None, len(text.splitlines()), {}

    rows = [
        f"Provider: {session.get('_provider', '')}",
        f"Status: {session.get('_status', '')}",
    ]
    if session.get("_model_id"):
        rows.append(f"ID: {session.get('_model_id')}")
    if session.get("_size"):
        rows.append(f"Size: {session.get('_size')}")
    if session.get("_modified"):
        rows.append(f"Modified: {session.get('_modified')}")
    if session.get("_file"):
        rows.append(f"Path: {session.get('_file')}")
    return "\n".join(rows), None, len(rows), {}


def open_llm_item(session: dict):
    fp = Path(session.get("_file", ""))
    if fp.exists():
        os.startfile(str(fp))
    elif session.get("_provider") == "Ollama" and OLLAMA_DIR.exists():
        os.startfile(str(OLLAMA_DIR))


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
    if providers.get("claude", True):
        sessions += load_claude_sessions()
    if providers.get("codex", True):
        sessions += load_codex_sessions()
    if providers.get("grok", True):
        sessions += load_grok_sessions()
    if providers.get("ollama", True) or providers.get("lm_studio", True) or providers.get("grok", True):
        sessions += load_llm_entries(settings)
    renames = load_renames()
    for s in sessions:
        if s["sessionId"] in renames:
            s["display"] = renames[s["sessionId"]]
    return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)


def get_session_preview(session: dict):
    if session.get("_source") == "grok":
        return get_grok_preview(session)
    if session.get("_source") == "llm":
        return get_llm_preview(session)
    if session.get("_source") == "codex":
        return get_codex_preview(session)
    return get_claude_preview(session)


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

class SessionPortal:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Session Portal")
        self.root.geometry("1440x810+0+0")
        self.root.minsize(1220, 640)

        self.settings = load_settings()
        self.all_sessions: list = []
        self.filtered_sessions: list = []
        self.sort_var = tk.StringVar(value="Date ↓")
        self.show_history_var = tk.BooleanVar(value=False)
        self.source_var = tk.StringVar(value="Models")
        self._delete_mode = False
        self._checked_ids: set = set()

        self._apply_theme()
        self._ensure_onboarding()
        self._build_ui()
        self._load_data()
        self.root.deiconify()
        self.root.lift()

    def _ensure_onboarding(self):
        if not self.settings.get("onboarding_complete"):
            self._show_onboarding(first_run=True)

    def _provider_detected(self, key: str) -> bool:
        path = Path(PROVIDER_OPTIONS[key]["path"])
        if key == "lm_studio":
            return LM_STUDIO_DIR.exists() or LM_STUDIO_MODELS_DIR.exists()
        if key == "ollama":
            return OLLAMA_DIR.exists() or shutil.which("ollama") is not None
        return path.exists()

    def _show_onboarding(self, first_run=False):
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Sources")
        dialog.configure(bg=self.bg)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(
            dialog,
            text="Choose what Session Portal should discover",
            bg=self.bg,
            fg=self.blue,
            font=("Consolas", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 4))

        tk.Label(
            dialog,
            text="Choices are saved locally and used on every Refresh.",
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
            text="Found Only",
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
        self.bg = "#1e1e2e"
        self.surface = "#313244"
        self.overlay = "#45475a"
        self.muted = "#6c7086"
        self.text = "#cdd6f4"
        self.blue = "#89b4fa"
        self.green = "#a6e3a1"
        self.yellow = "#f9e2af"
        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.bg)
        style.configure("TLabel", background=self.bg, foreground=self.text, font=("Consolas", 10))
        style.configure(
            "Treeview",
            background=self.surface,
            foreground=self.text,
            fieldbackground=self.surface,
            font=("Consolas", 10),
            rowheight=26,
        )
        style.configure(
            "Treeview.Heading",
            background=self.overlay,
            foreground=self.text,
            font=("Consolas", 10, "bold"),
            relief="flat",
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

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#181825", pady=9, padx=14)
        header.pack(fill=tk.X)
        tk.Label(
            header,
            text="Session Portal",
            bg="#181825",
            fg=self.text,
            font=("Consolas", 14, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="Claude  |  Codex  |  Grok",
            bg="#181825",
            fg=self.muted,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT, padx=(12, 0))
        self.count_label = tk.Label(header, text="", bg="#181825", fg=self.muted,
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
        self.search_entry.focus()

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
                                    "Models", "Claude", "Codex", "Grok", "Ollama",
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

        self.history_btn = tk.Button(
            top,
            text="History: OFF",
            bg=self.overlay,
            fg=self.muted,
            activebackground=self.surface,
            activeforeground=self.text,
            font=("Consolas", 10),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._toggle_history,
        )
        self.history_btn.pack(side=tk.RIGHT, padx=(0, 4))

        tk.Button(
            top,
            text="Sources",
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

        self.delete_bar = tk.Frame(self.root, bg="#45475a", pady=6, padx=12)
        tk.Label(self.delete_bar, text="DELETE MODE",
                 bg="#45475a", fg=self.bg,
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=(0, 12))
        self.select_all_btn = tk.Button(
            self.delete_bar,
            text="Select All",
            bg="#45475a",
            fg=self.bg,
            activebackground=self.overlay,
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
            bg="#45475a",
            fg=self.bg,
            activebackground=self.overlay,
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
        paned.add(list_frame, width=910, minsize=650)

        list_header = tk.Frame(list_frame, bg=self.bg, pady=4)
        list_header.pack(fill=tk.X)
        tk.Label(
            list_header,
            text="Sessions",
            bg=self.bg,
            fg=self.blue,
            font=("Consolas", 11, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            list_header,
            text="filtered, sorted, numbered",
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
        self.tree.heading("check", text="")
        self.tree.heading("number", text="#")
        self.tree.heading("source", text="Source")
        self.tree.heading("project", text="Project")
        self.tree.heading("date", text="Date")
        self.tree.heading("preview", text="Thread / Last Prompt")
        self.tree.column("check", width=0, minwidth=0, stretch=False)
        self.tree.column("number", width=44, minwidth=38, stretch=False, anchor=tk.E)
        self.tree.column("source", width=58, minwidth=50, stretch=False)
        self.tree.column("project", width=150, minwidth=90, stretch=False)
        self.tree.column("date", width=135, minwidth=100, stretch=False)
        self.tree.column("preview", width=480, minwidth=260)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.tag_configure("gone", foreground="#45475a")
        self.tree.tag_configure("codex", foreground=self.yellow)
        self.tree.tag_configure("grok", foreground="#ff99cc")
        self.tree.tag_configure("llm", foreground=self.blue)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<Double-1>", self._on_action)
        self.tree.bind("<Return>", self._on_action)
        self.tree.bind("<Button-3>", self._on_right_click)

        right = tk.Frame(paned, bg=self.bg)
        paned.add(right, minsize=360)

        preview_header = tk.Frame(right, bg=self.bg, pady=4)
        preview_header.pack(fill=tk.X)
        tk.Label(preview_header, text="Preview", bg=self.bg, fg=self.blue,
                 font=("Consolas", 11, "bold")).pack(side=tk.LEFT)
        tk.Label(preview_header, text="metadata and first/last prompt", bg=self.bg,
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

        bar = tk.Frame(self.root, bg="#181825", pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            bar,
            text="  Double-click or Enter to act  |  r refresh  |  q quit",
            bg="#181825",
            fg=self.muted,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT)

        self.root.bind("<r>", lambda e: self._load_data() if not self._delete_mode else None)
        self.root.bind("q", lambda e: self.root.quit())
        self.root.bind("<Escape>", lambda e: self._exit_delete_mode() if self._delete_mode else None)

    def _load_data(self):
        self.settings = load_settings()
        self.all_sessions = load_sessions(self.settings)
        self._apply_filter()

    def _edit_sources(self):
        self._show_onboarding(first_run=False)
        self._load_data()

    def _toggle_history(self):
        self.show_history_var.set(not self.show_history_var.get())
        on = self.show_history_var.get()
        self.history_btn.config(text="History: ON" if on else "History: OFF",
                                fg=self.blue if on else self.muted)
        self._apply_filter()

    def _on_search(self, *_):
        self._apply_filter()

    def _apply_filter(self):
        show_history = self.show_history_var.get()
        source_filter = self.source_var.get()
        query = self.search_var.get().lower()

        pool = self.all_sessions

        if source_filter == "Claude":
            pool = [s for s in pool if s.get("_source") == "claude"]
        elif source_filter == "Codex":
            pool = [s for s in pool if s.get("_source") == "codex"]
        elif source_filter == "Grok":
            pool = [s for s in pool if s.get("_source") == "grok"]
        elif source_filter == "Ollama":
            pool = [s for s in pool if s.get("_source") == "llm"]

        if query:
            pool = [
                s for s in pool
                if query in s.get("project", "").lower()
                or query in s.get("display", "").lower()
            ]

        if not show_history:
            pool = [s for s in pool
                    if s.get("_source") in ("codex", "grok", "llm") or s.get("_resumable", False)]

        sort = self.sort_var.get()
        if sort == "Date ↓":
            pool = sorted(pool, key=lambda s: s.get("timestamp", 0), reverse=True)
        elif sort == "Date ↑":
            pool = sorted(pool, key=lambda s: s.get("timestamp", 0))
        elif sort == "Project A→Z":
            pool = sorted(pool, key=lambda s: os.path.basename(s.get("project", "")).lower())
        elif sort == "Project Z→A":
            pool = sorted(pool, key=lambda s: os.path.basename(s.get("project", "")).lower(), reverse=True)

        self.filtered_sessions = pool
        self._refresh_list()

        total = len(self.all_sessions)
        shown = len(self.filtered_sessions)
        n_claude = sum(1 for s in self.filtered_sessions if s.get("_source") == "claude")
        n_codex = sum(1 for s in self.filtered_sessions if s.get("_source") == "codex")
        n_grok = sum(1 for s in self.filtered_sessions if s.get("_source") == "grok")
        n_llm = sum(1 for s in self.filtered_sessions if s.get("_source") == "llm")
        self.count_label.config(
            text=f"{shown} of {total} shown  |  Claude {n_claude}  Codex {n_codex}  Grok {n_grok}  Ollama {n_llm}"
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
            display = (display_title or "")[:90]

            if src == "llm":
                tag = ("llm",)
            elif src == "grok":
                tag = ("grok",)
            elif src == "codex":
                tag = ("codex",)
            elif not s.get("_resumable", True):
                tag = ("gone",)
            else:
                tag = ()

            if src == "llm":
                source_label = "Ollama"
            elif src == "grok":
                source_label = "Grok"
            elif src == "codex":
                source_label = "Codex"
            else:
                source_label = "Claude"
            check = "x" if s["sessionId"] in self._checked_ids else ""
            self.tree.insert("", tk.END, iid=s["sessionId"],
                             values=(check, row_num, source_label, project_short, date_str, display),
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
        if src == "llm":
            self.action_btn.config(text="Open Ollama History", bg=self.blue,
                                   fg=self.bg, state=tk.NORMAL)
            self.rename_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            return
        if src == "grok" and session.get("_resumable"):
            self.action_btn.config(text="Resume Grok", bg="#ff99cc",
                                   fg=self.bg, state=tk.NORMAL)
        elif src == "grok":
            self.action_btn.config(text="Open Grok History", bg="#ff99cc",
                                   fg=self.bg, state=tk.NORMAL)
            self.rename_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            return
        if src == "codex" and session.get("_resumable"):
            self.action_btn.config(text="Resume Codex", bg=self.yellow,
                                   fg=self.bg, state=tk.NORMAL)
        elif src == "codex":
            self.action_btn.config(text="Resume Codex", bg=self.yellow,
                                   fg=self.bg, state=tk.DISABLED)
        elif src == "claude" and session.get("_resumable"):
            self.action_btn.config(text="Resume Session", bg=self.blue,
                                   fg=self.bg, state=tk.NORMAL)
        else:
            self.action_btn.config(text="Resume Session", bg=self.blue,
                                   fg=self.bg, state=tk.DISABLED)
        self.rename_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def _show_preview(self, session: dict):
        first, last, count, tokens = get_session_preview(session)

        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)

        src = session.get("_source", "claude")
        if src == "llm":
            src_tag = "llm"
        elif src == "grok":
            src_tag = "grok"
        elif src == "codex":
            src_tag = "codex"
        else:
            src_tag = "dim"

        def row(label, value, tag="dim"):
            self.preview.insert(tk.END, f"{label:<14}", "label")
            self.preview.insert(tk.END, f"{value}\n", tag)

        ts = session.get("timestamp", 0)
        date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d  %H:%M:%S") if ts else ""

        if src == "llm":
            row("Source", "Ollama", src_tag)
        elif src == "grok":
            row("Source", "Grok", src_tag)
        else:
            row("Source", "Codex" if src == "codex" else "Claude", src_tag)
        if session.get("display"):
            row("Title", session.get("display", ""), src_tag)
        row("Project", session.get("project", ""))
        row("Session ID", session.get("sessionId", ""))
        row("Date", date_str)

        if src == "llm":
            row("Provider", session.get("_provider", ""), src_tag)
            row("Status", session.get("_status", ""), src_tag)
            row("Details", str(count))
        elif src == "grok":
            row("Messages", str(count))
        elif src == "codex":
            row("Thread", session.get("display", ""), "codex")
            row("Messages", str(count) if "_file" in session else "n/a")
        else:
            row("Messages", str(count) if session.get("_resumable") else "n/a (file cleaned up)")

        if tokens.get("input") or tokens.get("output"):
            total = tokens["input"] + tokens["output"]
            row("Tokens", f"{total:,}  (in {tokens['input']:,}  out {tokens['output']:,})")
            if tokens.get("cache_read") or tokens.get("cache_write"):
                row("Cache", f"read {tokens['cache_read']:,}  write {tokens.get('cache_write', 0):,}")

        if src == "claude" and not session.get("_resumable"):
            self.preview.insert(tk.END, "\n⚠  Conversation file no longer on disk — history only.\n", "dim")
        elif src == "codex" and not session.get("_resumable"):
            self.preview.insert(tk.END, "\n⚠  Session file not found — cannot resume.\n", "codex")

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
            if src == "llm":
                open_llm_item(session)
            elif src == "grok" and session.get("_resumable"):
                resume_grok(session.get("project", ""), sid)
            elif src == "grok":
                open_grok_file(session)
            elif src == "codex" and session.get("_resumable"):
                resume_codex(session.get("project", ""), sid)
            elif src == "claude" and session.get("_resumable"):
                resume_claude(session.get("project", "C:\\"), sid)
        except Exception as exc:
            messagebox.showerror("Action failed", str(exc))

    def _on_tree_click(self, event):
        if not self._delete_mode:
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return
        session = next((s for s in self.filtered_sessions if s["sessionId"] == row), None)
        if session and (session.get("_source") in ("llm",)
                        or (session.get("_source") == "grok" and not session.get("_resumable"))):
            return "break"
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
        session = next((s for s in self.filtered_sessions if s["sessionId"] == row), None)
        if session and (session.get("_source") in ("llm",)
                        or (session.get("_source") == "grok" and not session.get("_resumable"))):
            menu = tk.Menu(self.root, tearoff=0,
                           bg=self.surface, fg=self.text,
                           activebackground=self.overlay, activeforeground=self.text,
                           font=("Consolas", 10))
            if session.get("_source") == "llm":
                label = "Open Ollama History"
            elif session.get("_source") == "grok":
                label = "Open Grok History"
            menu.add_command(label=label, command=self._on_action)
            menu.tk_popup(event.x_root, event.y_root)
            return
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
            self._checked_ids = {s["sessionId"] for s in self.filtered_sessions
                                 if s.get("_source") not in ("llm",)
                                 and not (s.get("_source") == "grok" and not s.get("_resumable"))}
        elif pre_check_sid:
            self._checked_ids = {pre_check_sid}
        else:
            sel = self.tree.selection()
            if sel:
                self._checked_ids = {sel[0]}
        self.delete_bar.pack(fill=tk.X, after=self.top_bar)
        self.tree.column("check", width=45, minwidth=45)
        self.delete_btn.config(state=tk.DISABLED)
        self.rename_btn.config(state=tk.DISABLED)
        self.action_btn.config(state=tk.DISABLED)
        self._refresh_list()
        self._update_delete_bar()

    def _exit_delete_mode(self):
        self._delete_mode = False
        self._checked_ids = set()
        self.delete_bar.pack_forget()
        self.tree.column("check", width=0, minwidth=0)
        self._refresh_list()
        self.delete_btn.config(state=tk.DISABLED)
        self.rename_btn.config(state=tk.DISABLED)
        self.action_btn.config(state=tk.DISABLED)

    def _toggle_select_all(self):
        total = len(self.filtered_sessions)
        if len(self._checked_ids) >= total:
            self._checked_ids = set()
        else:
            self._checked_ids = {s["sessionId"] for s in self.filtered_sessions
                                 if s.get("_source") not in ("llm",)
                                 and not (s.get("_source") == "grok" and not s.get("_resumable"))}
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
                     if s["sessionId"] in self._checked_ids
                     and s.get("_source") not in ("llm",)
                     and not (s.get("_source") == "grok" and not s.get("_resumable"))]
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
            if src == "codex":
                delete_codex_session(session)
            elif src == "grok":
                delete_grok_session(session)
            else:
                delete_claude_session(session)
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
