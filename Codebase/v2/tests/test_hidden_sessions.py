"""Local hide-list tests for server-backed providers such as AMP."""

from Codebase.v2.models import Session
from Codebase.v2 import sessions, storage


def test_load_sessions_filters_hidden_provider_ids(monkeypatch, tmp_path):
    hidden_file = tmp_path / "hidden_sessions.json"
    monkeypatch.setattr(storage, "HIDDEN_SESSIONS_FILE", hidden_file)
    monkeypatch.setattr(sessions, "load_hidden_sessions", storage.load_hidden_sessions)

    amp_session = Session(id="T-123", provider="amp", project="C:/p", display="hidden")
    visible_session = Session(id="T-456", provider="amp", project="C:/p", display="visible")

    class FakeProvider:
        key = "amp"

        def detected(self):
            return True

        def load_sessions(self):
            return [amp_session, visible_session]

    monkeypatch.setattr(sessions, "PROVIDERS", [FakeProvider()])
    storage.hide_session("amp", "T-123")

    loaded = sessions.load_sessions({"providers": {"amp": True}})

    assert [s.id for s in loaded] == ["T-456"]
