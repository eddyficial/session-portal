"""Resume execution layer.

Providers build :class:`ResumeCommand` value objects; this module is the only
place that actually spawns a terminal. Kept separate so resume-command
construction stays unit-testable (tests assert the command string, no
subprocess) and so a future cross-platform backend can live here without
touching providers.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .config import (
    CODEX_EXE_DIR,
    CODEX_PROGRAMS_EXE_DIR,
    CREATE_NO_WINDOW,
    GROK_EXE,
)
from .models import ResumeCommand


# ── Executable discovery (mirrors v1) ────────────────────────────────────────
def find_codex_exe() -> str:
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


def find_claude_exe() -> str:
    return shutil.which("claude") or "claude"


def find_grok_exe() -> str:
    found = shutil.which("grok")
    if found:
        return found
    if GROK_EXE.exists():
        return str(GROK_EXE)
    return "grok"


def has_windows_terminal() -> bool:
    return shutil.which("wt") is not None


# ── PowerShell single-quoting (mirrors v1) ───────────────────────────────────
def ps_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _start_powershell(cwd: str, command: str) -> None:
    cwd = cwd or str(Path.home())
    if not Path(cwd).exists():
        raise FileNotFoundError(f"Session working directory does not exist: {cwd}")
    startup = f"Set-Location -LiteralPath {ps_single_quote(cwd)}; {command}"
    if has_windows_terminal():
        subprocess.Popen(
            ["wt", "--maximized", "-d", cwd, "powershell", "-NoExit", "-Command", startup],
            creationflags=CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            ["cmd", "/c", "start", "", "/MAX", "powershell", "-NoExit", "-Command", startup],
            creationflags=CREATE_NO_WINDOW,
        )


def launch(cmd: ResumeCommand) -> None:
    """Execute a :class:`ResumeCommand` in a maximized terminal."""
    _start_powershell(cmd.cwd, cmd.shell_command)