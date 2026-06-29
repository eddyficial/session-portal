"""v2 UI package — customtkinter view layer.

The UI is split into builders (sidebar, table, inspector, onboarding,
date_picker) and a controller (:mod:`Codebase.v2.ui.app`). Builders set widget
attributes on the app; the app owns state and event handlers. No provider
parsing happens here — the UI only calls ``sessions.load_sessions()`` and
``resume.launch()``.
"""