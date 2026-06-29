"""Claude provider parse fixture (synthetic, anonymized-shape session file)."""
import json

from Codebase.v2.providers import claude

SID = "00000000-0000-4000-8000-000000000000"


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_claude_loads_model_title_cwd_and_preview(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "Hello there general kenobi"}},
        {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-4-test",
          "usage": {"input_tokens": 10, "output_tokens": 20,
                    "cache_read_input_tokens": 5, "cache_creation_input_tokens": 3}}},
        {"cwd": str(tmp_path)},
        {"type": "ai-title", "aiTitle": "My Cool Session"},
    ])

    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")

    sessions = claude.ClaudeProvider().load_sessions()
    assert len(sessions) == 1
    s = sessions[0]
    assert s.provider == "claude"
    assert s.resumable is True
    assert s.model == "claude-opus-4-test"
    assert s.model_group == "Claude Code / Opus"
    assert s.display == "My Cool Session"
    assert s.project == str(tmp_path)

    preview = claude.ClaudeProvider().preview(s)
    assert preview.first == "Hello there general kenobi"
    assert preview.message_count == 1
    assert preview.tokens.input == 10
    assert preview.tokens.output == 20
    assert preview.tokens.cache_read == 5
    assert preview.tokens.cache_write == 3


def test_claude_skips_meta_and_tool_result_user_records(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "isMeta": True, "message": {"role": "user", "content": "meta junk"}},
        {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result"}]}},
        {"type": "user", "message": {"role": "user", "content": "real prompt"}},
    ])
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")

    s = claude.ClaudeProvider().load_sessions()[0]
    preview = claude.ClaudeProvider().preview(s)
    assert preview.first == "real prompt"
    assert preview.message_count == 1