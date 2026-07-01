from Codebase.v2.models import ThreadMessage
from Codebase.v2.providers import base


def test_keep_thread_tail_preserves_newest_messages(monkeypatch):
    monkeypatch.setattr(base, "MAX_THREAD_CHARS", 10)
    msgs = [
        ThreadMessage("user", "oldest"),
        ThreadMessage("assistant", "middle"),
        ThreadMessage("user", "newest"),
    ]

    total = base.keep_thread_tail(msgs, sum(len(m.text) for m in msgs))

    assert total <= 10
    assert [m.text for m in msgs] == ["newest"]
