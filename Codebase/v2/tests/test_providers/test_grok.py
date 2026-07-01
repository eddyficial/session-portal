"""Grok provider parse fixture."""
import json

from Codebase.v2.providers import grok

SID = "00000000-0000-4000-8000-000000000000"


def test_grok_loads_model_title_cwd_and_chat_preview(tmp_path, monkeypatch):
    sessions_root = tmp_path / "sessions"
    session_dir = sessions_root / SID
    session_dir.mkdir(parents=True)
    (session_dir / "summary.json").write_text(json.dumps({
        "info": {"cwd": str(tmp_path)},
        "current_model_id": "grok-composer-2.5-fast",
        "generated_title": "Grok thread",
        "last_active_at": "2026-06-01T10:00:00Z",
    }), encoding="utf-8")
    chat = session_dir / "chat_history.jsonl"
    chat.write_text(
        json.dumps({"type": "user", "content": "First grok prompt"}) + "\n"
        + json.dumps({"type": "user", "content": "<user_query>Real query</user_query>"}) + "\n"
        + json.dumps({"type": "user", "content": [{"type": "text", "text": "list content"}]}) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(grok, "GROK_SESSIONS_DIR", sessions_root)

    sessions = grok.GrokProvider().load_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    assert s.provider == "grok"
    assert s.model_group == "Grok / grok-composer-2.5-fast"
    assert s.display == "Grok thread"
    assert s.project == str(tmp_path)
    from datetime import datetime
    expected_ts = int(datetime.fromisoformat("2026-06-01T10:00:00+00:00").timestamp() * 1000)
    assert s.timestamp == expected_ts

    preview = grok.GrokProvider().preview(s)
    assert preview.first == "First grok prompt"
    assert preview.message_count == 3