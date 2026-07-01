"""Provider registry — the single place that lists resumable providers.

Adding a 5th provider means: write a ``Provider`` implementation and append it
to :data:`PROVIDERS`. Nothing else in the app changes.
"""
from __future__ import annotations

from .amp import AmpProvider
from .base import Provider
from .claude import ClaudeProvider
from .codex import CodexProvider
from .copilot import CopilotProvider
from .grok import GrokProvider

PROVIDERS: list[Provider] = [
    ClaudeProvider(),
    CodexProvider(),
    GrokProvider(),
    CopilotProvider(),
    AmpProvider(),
]

_BY_KEY = {p.key: p for p in PROVIDERS}


def get_provider(key: str) -> Provider | None:
    return _BY_KEY.get(key)


def detected_provider_keys() -> list[str]:
    return [p.key for p in PROVIDERS if p.detected()]
