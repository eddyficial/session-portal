"""Cost / token-rollup tests."""
from Codebase.v2 import pricing, sessions
from Codebase.v2.models import Session, Tokens


def _session(model="claude-opus-4-1", tokens=None):
    s = Session(id="x", provider="claude", project="C:/p", model=model)
    s.tokens = tokens
    return s


def test_cost_none_when_tokens_uncached():
    assert pricing.session_cost(Session(id="x", provider="claude", project="p", model="claude-opus-4")) is None


def test_cost_none_when_zero_tokens():
    assert pricing.session_cost(_session(tokens=Tokens())) is None


def test_cost_uses_opus_rates():
    # 1M input + 1M output at opus ($15/$75) = $90.00
    s = _session(model="claude-opus-4-1", tokens=Tokens(input=1_000_000, output=1_000_000))
    assert pricing.session_cost(s) == 90.0


def test_cost_uses_sonnet_rates():
    # 1M input + 1M output at sonnet ($3/$15) = $18.00
    s = _session(model="claude-sonnet-4", tokens=Tokens(input=1_000_000, output=1_000_000))
    assert pricing.session_cost(s) == 18.0


def test_cost_falls_back_for_unknown_model():
    s = _session(model="glm-5.2", tokens=Tokens(input=1_000_000, output=1_000_000))
    # fallback ($1/$5) = $6.00
    assert pricing.session_cost(s) == 6.0


def test_total_cost_sums_and_counts():
    a = _session(model="claude-opus-4", tokens=Tokens(input=1_000_000, output=0))   # $15
    b = _session(model="claude-sonnet-4", tokens=Tokens(input=0, output=1_000_000))  # $15
    c = _session(model="grok-x", tokens=None)  # not costed
    total, costed = pricing.total_cost([a, b, c])
    assert costed == 2
    assert total == 30.0


def test_get_session_preview_caches_tokens(monkeypatch):
    # A session whose provider preview yields tokens should cache them on the session.
    s = Session(id="00000000-0000-4000-8000-000000000000", provider="claude",
                project="C:/p", model="claude-opus-4", source_file=None)
    # No source file -> preview returns empty Tokens, but still caches the object.
    preview = sessions.get_session_preview(s)
    assert s.tokens is preview.tokens


def test_message_count_does_not_cache_tokens(monkeypatch):
    s = Session(id="00000000-0000-4000-8000-000000000000", provider="claude",
                project="C:/p", model="claude-opus-4", source_file=None)

    count = sessions.get_session_message_count(s)

    assert count == 0
    assert s.tokens is None
