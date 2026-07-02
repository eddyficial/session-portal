"""Full-text search index tests."""
import json

from Codebase.v2 import search_index, sessions
from Codebase.v2.providers import claude

SID = "00000000-0000-4000-8000-000000000000"
ONLY_CLAUDE = {"providers": {"amp": False, "claude": True, "codex": False, "copilot": False, "grok": False}}


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_search_index_matches_mid_conversation_term(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "start the session"}},
        {"type": "assistant", "message": {"role": "assistant", "model": "claude-opus-4",
          "usage": {"input_tokens": 1, "output_tokens": 1}}},
        {"type": "user", "message": {"role": "user", "content": "now fix the auth bug in login"}},
        {"type": "user", "message": {"role": "user", "content": "ship it"}},
    ])
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(search_index, "SEARCH_INDEX_FILE", tmp_path / "session_index.sqlite3")

    ss = claude.ClaudeProvider().load_sessions()
    assert len(ss) == 1
    built = sessions.ensure_search_index(ss)
    assert built == 1

    blob = ss[0].search_blob
    assert "auth bug" in blob
    # first/last only would be "start the session" / "ship it" — neither has "auth bug"
    assert "auth bug" not in (ss[0].display or "").lower()

    # filter-style match
    matches = [s for s in ss if "auth bug" in s.search_blob]
    assert matches == ss


def test_ensure_search_index_is_idempotent(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    (proj_dir / f"{SID}.jsonl").write_text(
        json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(search_index, "SEARCH_INDEX_FILE", tmp_path / "session_index.sqlite3")

    ss = claude.ClaudeProvider().load_sessions()
    sessions.ensure_search_index(ss)
    first_blob = ss[0].search_blob
    built_again = sessions.ensure_search_index(ss)
    assert built_again == 0                 # already indexed, not rebuilt
    assert ss[0].search_blob == first_blob


def test_search_index_persists_between_loads(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "persistent banana marker"}},
    ])
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(search_index, "SEARCH_INDEX_FILE", tmp_path / "session_index.sqlite3")

    first_load = claude.ClaudeProvider().load_sessions()
    assert sessions.ensure_search_index(first_load) == 1

    second_load = sessions.load_sessions(ONLY_CLAUDE)
    assert second_load[0].search_blob
    assert "persistent banana marker" in second_load[0].search_blob
    assert sessions.ensure_search_index(second_load) == 0


def test_search_index_rebuilds_when_source_file_changes(tmp_path, monkeypatch):
    projects = tmp_path / "projects"
    proj_dir = projects / "C--proj"
    proj_dir.mkdir(parents=True)
    fp = proj_dir / f"{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "old marker"}},
    ])
    monkeypatch.setattr(claude, "PROJECTS_DIR", projects)
    monkeypatch.setattr(claude, "HISTORY_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(search_index, "SEARCH_INDEX_FILE", tmp_path / "session_index.sqlite3")

    first_load = sessions.load_sessions(ONLY_CLAUDE)
    assert sessions.ensure_search_index(first_load) == 1
    assert "old marker" in first_load[0].search_blob

    _write_jsonl(fp, [
        {"type": "user", "message": {"role": "user", "content": "new marker"}},
        {"type": "user", "message": {"role": "user", "content": "extra text changes size"}},
    ])

    second_load = sessions.load_sessions(ONLY_CLAUDE)
    assert second_load[0].search_blob == ""
    assert sessions.ensure_search_index(second_load) == 1
    assert "new marker" in second_load[0].search_blob
    assert "old marker" not in second_load[0].search_blob
