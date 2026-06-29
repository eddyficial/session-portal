"""Recycle-bin tests: trash moves, manifest records, restore + purge work."""
import json

from Codebase.v2 import trash
from Codebase.v2.models import Session

SID = "00000000-0000-4000-8000-000000000000"


def _session(source_file=None, session_dir=None, provider="claude"):
    return Session(id=SID, provider=provider, project="C:/proj",
                   source_file=source_file, session_dir=session_dir)


def test_trash_then_restore_returns_file_to_original_path(tmp_path, monkeypatch):
    monkeypatch.setattr(trash, "TRASH_DIR", tmp_path / "trash")
    monkeypatch.setattr(trash, "MANIFEST_FILE", tmp_path / "trash" / "manifest.json")
    monkeypatch.setattr(trash, "ALLOWED_RESTORE_ROOTS", {"claude": [tmp_path / "sessions"]})
    original = tmp_path / "sessions" / f"{SID}.jsonl"
    original.parent.mkdir()
    original.write_text('{"type":"user"}\n', encoding="utf-8")

    entry = trash.trash_session(_session(source_file=str(original)))
    assert entry is not None
    assert not original.exists()                     # moved out
    assert len(trash.list_trashed()) == 1
    assert trash.list_trashed()[0]["original_path"] == str(original)

    assert trash.restore_session(SID) is True
    assert original.exists()                          # back where it was
    assert trash.list_trashed() == []                 # manifest cleared


def test_trash_dir_session_and_purge(tmp_path, monkeypatch):
    monkeypatch.setattr(trash, "TRASH_DIR", tmp_path / "trash")
    monkeypatch.setattr(trash, "MANIFEST_FILE", tmp_path / "trash" / "manifest.json")
    monkeypatch.setattr(trash, "ALLOWED_RESTORE_ROOTS", {"grok": [tmp_path / "grok-sessions"]})
    sdir = tmp_path / "grok-sessions" / SID
    sdir.mkdir(parents=True)
    (sdir / "summary.json").write_text("{}", encoding="utf-8")
    (sdir / "chat_history.jsonl").write_text('{"type":"user"}\n', encoding="utf-8")

    entry = trash.trash_session(_session(provider="grok", session_dir=str(sdir), source_file=str(sdir / "chat_history.jsonl")))
    assert entry["kind"] == "dir"
    assert not sdir.exists()

    assert trash.purge_session(SID) is True
    assert trash.list_trashed() == []


def test_empty_trash_clears_all(tmp_path, monkeypatch):
    monkeypatch.setattr(trash, "TRASH_DIR", tmp_path / "trash")
    monkeypatch.setattr(trash, "MANIFEST_FILE", tmp_path / "trash" / "manifest.json")
    f1 = tmp_path / "a.jsonl"
    f2 = tmp_path / "b.jsonl"
    f1.write_text("{}", encoding="utf-8")
    f2.write_text("{}", encoding="utf-8")

    trash.trash_session(Session(id="00000000-0000-4000-8000-000000000001", provider="claude",
                                project="C:/p", source_file=str(f1)))
    trash.trash_session(Session(id="00000000-0000-4000-8000-000000000002", provider="claude",
                                project="C:/p", source_file=str(f2)))
    assert len(trash.list_trashed()) == 2

    n = trash.empty_trash()
    assert n == 2
    assert trash.list_trashed() == []


def test_restore_rejects_manifest_path_outside_provider_root(tmp_path, monkeypatch):
    monkeypatch.setattr(trash, "TRASH_DIR", tmp_path / "trash")
    monkeypatch.setattr(trash, "MANIFEST_FILE", tmp_path / "trash" / "manifest.json")
    monkeypatch.setattr(trash, "ALLOWED_RESTORE_ROOTS", {"claude": [tmp_path / "allowed"]})

    trashed = tmp_path / "trash" / "claude" / SID / f"{SID}.jsonl"
    trashed.parent.mkdir(parents=True)
    trashed.write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside" / f"{SID}.jsonl"
    trash.MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    trash.MANIFEST_FILE.write_text(json.dumps([{
        "id": SID,
        "provider": "claude",
        "kind": "file",
        "original_path": str(outside),
        "trashed_path": str(trashed),
    }]), encoding="utf-8")

    assert trash.restore_session(SID) is False
    assert trashed.exists()
    assert not outside.exists()


def test_purge_rejects_manifest_path_outside_trash_root(tmp_path, monkeypatch):
    monkeypatch.setattr(trash, "TRASH_DIR", tmp_path / "trash")
    monkeypatch.setattr(trash, "MANIFEST_FILE", tmp_path / "trash" / "manifest.json")

    outside = tmp_path / "outside.jsonl"
    outside.write_text("{}", encoding="utf-8")
    trash.MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    trash.MANIFEST_FILE.write_text(json.dumps([{
        "id": SID,
        "provider": "claude",
        "kind": "file",
        "original_path": str(tmp_path / "allowed" / f"{SID}.jsonl"),
        "trashed_path": str(outside),
    }]), encoding="utf-8")

    assert trash.purge_session(SID) is False
    assert outside.exists()
