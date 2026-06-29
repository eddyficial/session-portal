"""Copilot provider parse fixture."""
import json

from Codebase.v2.providers import copilot

SID = "00000000-0000-4000-8000-000000000000"


def test_copilot_loads_model_name_cwd_and_events_preview(tmp_path, monkeypatch):
    sessions_root = tmp_path / "session-state"
    session_dir = sessions_root / SID
    session_dir.mkdir(parents=True)
    (session_dir / "workspace.yaml").write_text(
        f"name: Copilot Session\ncwd: {tmp_path}\nupdated_at: 2026-06-01T10:00:00Z\n",
        encoding="utf-8",
    )
    events = session_dir / "events.jsonl"
    events.write_text(
        json.dumps({"type": "session.model_change", "data": {"newModel": "gpt-5"}}) + "\n"
        + json.dumps({"type": "user.message",
                      "data": {"content": "<current_datetime>\n\nHello copilot"}}) + "\n"
        + json.dumps({"type": "assistant.message", "data": {"model": "gpt-5"}}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(copilot, "COPILOT_SESSIONS_DIR", sessions_root)

    sessions = copilot.CopilotProvider().load_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    assert s.provider == "copilot"
    assert s.model == "gpt-5"
    assert s.model_group == "Copilot / gpt-5"
    assert s.display == "Copilot Session"
    assert s.project == str(tmp_path)
    assert s.message_count == 1

    preview = copilot.CopilotProvider().preview(s)
    assert preview.first == "Hello copilot"
    assert preview.message_count == 1