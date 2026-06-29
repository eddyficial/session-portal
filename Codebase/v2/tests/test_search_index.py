"""Full-text search index tests."""
import json

from Codebase.v2 import sessions
from Codebase.v2.providers import claude

SID = "00000000-0000-4000-8000-000000000000"


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

    ss = claude.ClaudeProvider().load_sessions()
    sessions.ensure_search_index(ss)
    first_blob = ss[0].search_blob
    built_again = sessions.ensure_search_index(ss)
    assert built_again == 0                 # already indexed, not rebuilt
    assert ss[0].search_blob == first_blob