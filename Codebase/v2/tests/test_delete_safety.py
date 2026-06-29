"""Delete-safety tests: only the targeted session's files are removed.

Uses real provider ``delete()`` implementations against temp directories so
the on-disk behavior (rmtree for grok/copilot, unlink for claude/codex) is
exercised without touching the user's real session folders.
"""
import json
from pathlib import Path

from Codebase.v2.models import Session
from Codebase.v2.providers import claude, codex, copilot, grok


def _mk(provider: str, **kw) -> Session:
    base = dict(
        id="00000000-0000-4000-8000-000000000000",
        provider=provider,
        project="C:/proj",
    )
    base.update(kw)
    return Session(**base)


def test_grok_delete_removes_only_targeted_dir(tmp_path, monkeypatch):
    keep = tmp_path / "keep-session"
    gone = tmp_path / "gone-session"
    keep.mkdir()
    gone.mkdir()
    (keep / "summary.json").write_text("{}", encoding="utf-8")
    (gone / "summary.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(grok, "GROK_SESSIONS_DIR", tmp_path)
    session = _mk("grok", session_dir=str(gone))
    grok.GrokProvider().delete(session)

    assert not gone.exists()
    assert keep.exists()                       # other session untouched
    assert (keep / "summary.json").exists()


def test_copilot_delete_removes_only_targeted_dir(tmp_path, monkeypatch):
    keep = tmp_path / "keep"
    gone = tmp_path / "gone"
    keep.mkdir()
    gone.mkdir()
    (keep / "workspace.yaml").write_text("name: keep\n", encoding="utf-8")
    (gone / "workspace.yaml").write_text("name: gone\n", encoding="utf-8")

    monkeypatch.setattr(copilot, "COPILOT_SESSIONS_DIR", tmp_path)
    session = _mk("copilot", session_dir=str(gone))
    copilot.CopilotProvider().delete(session)

    assert not gone.exists()
    assert keep.exists()


def test_grok_delete_rejects_path_outside_session_root(tmp_path, monkeypatch):
    session_root = tmp_path / "grok-root"
    outside = tmp_path / "outside"
    session_root.mkdir()
    outside.mkdir()
    monkeypatch.setattr(grok, "GROK_SESSIONS_DIR", session_root)

    grok.GrokProvider().delete(_mk("grok", session_dir=str(outside)))

    assert outside.exists()


def test_copilot_delete_rejects_path_outside_session_root(tmp_path, monkeypatch):
    session_root = tmp_path / "copilot-root"
    outside = tmp_path / "outside"
    session_root.mkdir()
    outside.mkdir()
    monkeypatch.setattr(copilot, "COPILOT_SESSIONS_DIR", session_root)

    copilot.CopilotProvider().delete(_mk("copilot", session_dir=str(outside)))

    assert outside.exists()


def test_claude_delete_unlinks_file_and_filters_history(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    proj.mkdir()
    target = proj / "00000000-0000-4000-8000-000000000000.jsonl"
    other = proj / "11111111-1111-4111-8111-111111111111.jsonl"
    target.write_text('{"type":"user"}\n', encoding="utf-8")
    other.write_text('{"type":"user"}\n', encoding="utf-8")

    history = tmp_path / "history.jsonl"
    history.write_text(
        json.dumps({"sessionId": "00000000-0000-4000-8000-000000000000", "timestamp": 1}) + "\n"
        + json.dumps({"sessionId": "11111111-1111-4111-8111-111111111111", "timestamp": 2}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(claude, "HISTORY_FILE", history)
    session = _mk("claude", source_file=str(target))
    claude.ClaudeProvider().delete(session)

    assert not target.exists()
    assert other.exists()                       # sibling session file untouched
    remaining = [json.loads(l) for l in history.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert [r["sessionId"] for r in remaining] == ["11111111-1111-4111-8111-111111111111"]


def test_codex_delete_unlinks_file(monkeypatch, tmp_path):
    target = tmp_path / "rollout-2026-01-01T00-00-00-00000000-0000-4000-8000-000000000000.jsonl"
    other = tmp_path / "rollout-2026-01-01T00-00-00-11111111-1111-4111-8111-111111111111.jsonl"
    target.write_text("{}", encoding="utf-8")
    other.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(codex, "find_codex_exe", lambda: "")  # skip subprocess delete call
    session = _mk("codex", source_file=str(target))
    codex.CodexProvider().delete(session)

    assert not target.exists()
    assert other.exists()
