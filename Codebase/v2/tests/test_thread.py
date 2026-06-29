"""Thread-collection tests for the read-only viewer."""
import json

from Codebase.v2.providers import claude, codex

SID = "00000000-0000-4000-8000-000000000000"


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_claude_collect_thread_orders_user_and_assistant(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "first question"}},
        {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-4",
          "content": [{"type": "text", "text": "here is the answer"}]}},
        {"type": "user", "message": {"role": "user", "content": "follow up"}},
        {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-4",
          "content": "second answer"}},
    ])
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")

    s = claude.ClaudeProvider().load_sessions()[0]
    msgs = claude.ClaudeProvider().collect_thread(s)
    roles = [m.role for m in msgs]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert msgs[0].text == "first question"
    assert msgs[1].text == "here is the answer"
    assert msgs[1].model == "claude-opus-4"
    assert msgs[3].text == "second answer"


def test_codex_collect_thread_orders_messages(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fp = sessions_dir / f"rollout-2026-04-28T12-26-45-{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "turn_context", "payload": {"cwd": str(tmp_path)}},
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "do the thing"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant",
          "content": [{"type": "output_text", "text": "done"}]}},
    ])
    monkeypatch.setattr(codex, "CODEX_SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(codex, "CODEX_INDEX_FILE", tmp_path / "index.jsonl")

    s = codex.CodexProvider().load_sessions()[0]
    msgs = codex.CodexProvider().collect_thread(s)
    assert [m.role for m in msgs] == ["user", "assistant"]
    assert msgs[1].text == "done"


def test_codex_collect_thread_reads_past_index_cap(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fp = sessions_dir / f"rollout-2026-04-28T12-26-45-{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "turn_context", "payload": {"cwd": str(tmp_path)}},
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "first"}]}},
        {"type": "response_item", "payload": {"type": "function_call_output",
          "output": "x" * 500}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant",
          "content": [{"type": "output_text", "text": "latest cli-visible answer"}]}},
    ])
    monkeypatch.setattr(codex, "CODEX_SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr(codex, "CODEX_INDEX_FILE", tmp_path / "index.jsonl")
    monkeypatch.setattr(codex, "MAX_INDEX_BYTES", 80)

    s = codex.CodexProvider().load_sessions()[0]
    msgs = codex.CodexProvider().collect_thread(s)

    assert msgs[-1].role == "assistant"
    assert msgs[-1].text == "latest cli-visible answer"
