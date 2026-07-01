"""Local, static token-pricing estimates for the cost rollup.

No network. Rates are per 1,000,000 tokens, USD, approximate list prices for
the model families Session Portal sees. This is an *estimate* for personal
cost awareness, not a billing source. A model is matched by substring against
:attr:`Session.model`; unknown models fall back to a conservative default.
"""
from __future__ import annotations

from .models import Session

# per-1M-token rates: (input, output, cache_read, cache_write)
_RATES: list[tuple[str, float, float, float, float]] = [
    ("opus",   15.0, 75.0,  1.50, 18.75),
    ("sonnet",  3.0, 15.0,  0.30,  3.75),
    ("haiku",   0.80, 4.0,  0.08,  1.0),
    ("gpt-5",   1.25, 10.0, 0.125, 1.25),
    ("gpt-4.1", 2.50, 10.0, 0.625, 2.50),
    ("gpt-4o",  2.50, 10.0, 1.25,  2.50),
]

# Conservative fallback when the model is unknown.
_FALLBACK = (1.0, 5.0, 0.10, 1.0)


def _rates_for(model: str) -> tuple[float, float, float, float]:
    lower = (model or "").lower()
    for needle, *rates in _RATES:
        if needle in lower:
            return tuple(rates)  # type: ignore[return-value]
    return _FALLBACK


def session_cost(session: Session) -> float | None:
    """Estimate USD cost from cached tokens. None if no tokens available."""
    tokens = session.tokens
    if tokens is None:
        return None
    if not (tokens.input or tokens.output or tokens.cache_read or tokens.cache_write):
        return None
    in_r, out_r, cr_r, cw_r = _rates_for(session.model)
    cost = (
        tokens.input * in_r
        + tokens.output * out_r
        + tokens.cache_read * cr_r
        + tokens.cache_write * cw_r
    ) / 1_000_000
    return round(cost, 4)


def total_cost(sessions) -> tuple[float, int]:
    """Sum cost over sessions that have cached tokens. Returns (total, costed_count)."""
    total = 0.0
    costed = 0
    for s in sessions:
        c = session_cost(s)
        if c is not None:
            total += c
            costed += 1
    return round(total, 2), costed