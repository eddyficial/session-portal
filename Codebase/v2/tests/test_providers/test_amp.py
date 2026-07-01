"""AMP provider CLI parsing."""
import json
import subprocess

from Codebase.v2.models import Session
from Codebase.v2.providers import amp


def _completed(stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess(["amp"], returncode, stdout=stdout, stderr="")


def test_amp_loads_threads_from_cli_json(monkeypatch):
    payload = [{
        "id": "T-123",
        "title": "Fix the thing",
        "updated": "2026-06-29T09:39:40.774Z",
        "tree": "file:///c%3A/Users/example/project",
        "messageCount": 4,
    }]
    monkeypatch.setattr(amp, "_run_amp", lambda args, timeout=15: _completed(json.dumps(payload)))

    sessions = amp.AmpProvider().load_sessions()

    assert len(sessions) == 1
    s = sessions[0]
    assert s.id == "T-123"
    assert s.provider == "amp"
    assert s.project == r"c:\Users\example\project"
    assert s.display == "Fix the thing"
    assert s.message_count == 4


def test_amp_preview_stays_fast_and_thread_uses_markdown(monkeypatch):
    markdown = """---
title: Example
---

# Example

## User

first request

## Assistant

done

## User

last request
"""
    calls = []

    def fake_run(args, timeout=30):
        calls.append(args)
        return _completed(markdown)

    monkeypatch.setattr(amp, "_run_amp", fake_run)
    session = Session(id="T-123", provider="amp", project="", display="Example", message_count=2)

    preview = amp.AmpProvider().preview(session)
    assert calls == []
    assert preview.first == "Example"
    assert preview.last is None
    assert preview.message_count == 2

    thread = amp.AmpProvider().collect_thread(session)

    assert calls == [["threads", "markdown", "T-123"]]
    assert [m.role for m in thread] == ["user", "assistant", "user"]


def test_amp_search_messages_do_not_fetch_markdown(monkeypatch):
    calls = []
    monkeypatch.setattr(amp, "_run_amp", lambda args, timeout=30: calls.append(args) or _completed(""))
    session = Session(id="T-123", provider="amp", project="C:/proj", display="Example", message_count=2)

    messages = amp.AmpProvider().collect_messages(session)

    assert calls == []
    assert messages == ["C:/proj", "Example", "T-123"]
