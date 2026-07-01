import json

from Codebase.v2.audit import export_session_audit
from Codebase.v2.models import Session

SID = "00000000-0000-4000-8000-000000000000"


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_export_session_audit_writes_metadata_and_thread(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fp = sessions_dir / f"rollout-2026-04-28T12-26-45-{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "turn_context", "payload": {"cwd": str(tmp_path), "model": "gpt-test"}},
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "why did you do that?"}]}},
        {"type": "response_item", "payload": {"type": "message", "role": "assistant",
          "content": [{"type": "output_text", "text": "because the tests failed"}]}},
    ])
    session = Session(
        id=SID,
        provider="codex",
        project=str(tmp_path),
        model="gpt-test",
        display="Audit me",
        timestamp=1_800_000_000_000,
        source_file=str(fp),
    )

    path = export_session_audit(session, export_dir=tmp_path / "audits")
    text = path.read_text(encoding="utf-8")

    assert path.parent.name == "audits"
    assert path.suffix == ".md"
    assert "# Session Audit Export" in text
    assert "| Provider | Codex |" in text
    assert "| LLM | Codex / gpt-test |" in text
    assert "| Session | 00000000-0000-4000-8000-000000000000 |" in text
    assert "why did you do that?" in text
    assert "because the tests failed" in text


def test_export_session_audit_accepts_exact_save_path(tmp_path):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    fp = sessions_dir / f"rollout-2026-04-28T12-26-45-{SID}.jsonl"
    _write_jsonl(fp, [
        {"type": "response_item", "payload": {"type": "message", "role": "user",
          "content": [{"type": "input_text", "text": "save this where I choose"}]}},
    ])
    session = Session(
        id=SID,
        provider="codex",
        project=str(tmp_path),
        model="gpt-test",
        display="Custom Path",
        timestamp=1_800_000_000_000,
        source_file=str(fp),
    )
    target = tmp_path / "chosen" / "my-session-record.md"

    path = export_session_audit(session, export_path=target)

    assert path == target
    assert target.exists()
    assert "save this where I choose" in target.read_text(encoding="utf-8")
