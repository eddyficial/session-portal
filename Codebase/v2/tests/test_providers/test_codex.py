"""Codex provider parse fixture."""
import json

from Codebase.v2.providers import codex

SID = "00000000-0000-4000-8000-000000000000"


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_codex_loads_model_cwd_first_message_and_tokens(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fp = sessions_dir / f"rollout-2026-04-28T12-26-45-{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "turn_context", "payload": {"cwd": str(tmp_path)}},
        {"type": "response_item", "payload": {"model": "gpt-5.5-test"}},
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "Build the thing"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "# agents.md instructions ..."}]}},
        {"type": "event_msg", "payload": {"type": "token_count",
          "info": {"last_token_usage": {"input_tokens": 7, "output_tokens": 9, "cached_input_tokens": 2}}}},
    ])

    monkeypatch.setattr(codex, "CODEX_SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(codex, "CODEX_INDEX_FILE", tmp_path / "session_index.jsonl")

    sessions = codex.CodexProvider().load_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    assert s.provider == "codex"
    assert s.resumable is True
    assert s.model == "gpt-5.5-test"
    assert s.model_group == "OpenAI / gpt-5.5-test"
    assert s.project == str(tmp_path)
    assert s.display == "Build the thing"

    preview = codex.CodexProvider().preview(s)
    assert preview.first == "Build the thing"
    assert preview.message_count == 1   # the agents.md line is filtered as non-human
    assert preview.tokens.input == 7
    assert preview.tokens.output == 9
    assert preview.tokens.cache_read == 2