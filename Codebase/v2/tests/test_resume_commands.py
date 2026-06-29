"""Resume-command construction tests (no subprocess spawned).

Asserts the exact PowerShell line each provider builds, with the exe-discovery
functions monkeypatched to deterministic values so the tests are stable on any
machine.
"""
from Codebase.v2.models import Session
from Codebase.v2.providers import amp, claude, codex, copilot, grok


def _mk(provider: str, **kw) -> Session:
    base = dict(
        id="00000000-0000-4000-8000-000000000000",
        provider=provider,
        project=r"C:\proj",
    )
    base.update(kw)
    return Session(**base)


def test_claude_resume_command_uses_no_chrome(monkeypatch):
    monkeypatch.setattr(claude, "find_claude_exe", lambda: "claude")
    cmd = claude.ClaudeProvider().resume_command(_mk("claude"))
    assert cmd.cwd == r"C:\proj"
    assert cmd.shell_command == "claude --no-chrome --resume '00000000-0000-4000-8000-000000000000'"


def test_claude_resume_command_backslash_exe_is_call_operator(monkeypatch):
    monkeypatch.setattr(claude, "find_claude_exe", lambda: r"C:\tools\claude.exe")
    cmd = claude.ClaudeProvider().resume_command(_mk("claude", project=""))
    assert cmd.cwd  # falls back to home, never empty
    assert cmd.shell_command == (
        r"& 'C:\tools\claude.exe' --no-chrome --resume '00000000-0000-4000-8000-000000000000'"
    )


def test_codex_resume_command_with_exe(monkeypatch):
    monkeypatch.setattr(codex, "find_codex_exe", lambda: r"C:\codex\codex.exe")
    cmd = codex.CodexProvider().resume_command(_mk("codex"))
    assert cmd.cwd == r"C:\proj"
    assert cmd.shell_command == (
        r"& 'C:\codex\codex.exe' resume --cd 'C:\proj' '00000000-0000-4000-8000-000000000000'"
    )


def test_codex_resume_command_without_exe(monkeypatch):
    monkeypatch.setattr(codex, "find_codex_exe", lambda: "")
    cmd = codex.CodexProvider().resume_command(_mk("codex"))
    assert cmd.shell_command == (
        "codex resume --cd 'C:\\proj' '00000000-0000-4000-8000-000000000000'"
    )


def test_grok_resume_command(monkeypatch):
    monkeypatch.setattr(grok, "find_grok_exe", lambda: "grok")
    cmd = grok.GrokProvider().resume_command(_mk("grok"))
    assert cmd.shell_command == "grok --resume '00000000-0000-4000-8000-000000000000'"


def test_grok_resume_command_backslash_exe(monkeypatch):
    monkeypatch.setattr(grok, "find_grok_exe", lambda: r"C:\grok\grok.exe")
    cmd = grok.GrokProvider().resume_command(_mk("grok"))
    assert cmd.shell_command == (
        r"& 'C:\grok\grok.exe' --resume '00000000-0000-4000-8000-000000000000'"
    )


def test_copilot_resume_command():
    cmd = copilot.CopilotProvider().resume_command(_mk("copilot"))
    assert cmd.cwd == r"C:\proj"
    assert cmd.shell_command == (
        r"gh copilot -- -C 'C:\proj' --resume='00000000-0000-4000-8000-000000000000'"
    )


def test_amp_resume_command(monkeypatch):
    monkeypatch.setattr(amp, "find_amp_exe", lambda: "amp")
    cmd = amp.AmpProvider().resume_command(_mk("amp", id="T-123"))
    assert cmd.cwd == r"C:\proj"
    assert cmd.shell_command == "amp threads continue 'T-123'"


def test_resume_command_cwd_falls_back_to_home_when_project_blank():
    cmd = copilot.CopilotProvider().resume_command(_mk("copilot", project=""))
    assert cmd.cwd  # never empty
    assert cmd.cwd != r"C:\proj"
