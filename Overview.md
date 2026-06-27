---
id: session-portal
title: Session Portal
type: project
owner: Operynth
status: active
created: 2026-06-26
updated: 2026-06-26
tags:
  - app
  - desktop
  - sessions
  - codex
  - claude
  - grok
  - llm-memory
project: Session Portal
repository_path: C:\Operynth\Projects\session-portal\Codebase
business_area: platform
lifecycle: active
---

# Session Portal

Session Portal is a local Tkinter desktop app for browsing, previewing, renaming, deleting, and resuming local AI sessions from this machine. It currently scans Claude, Codex, Grok, Claude memory/context files, Codex memories, and supported local prompt-history files discovered during source onboarding.

## App

- Code: [[Projects/session-portal/Codebase/session_portal.py|session_portal.py]]
- README: [[Projects/session-portal/App/README|App README]]
- Codebase: [[Projects/session-portal/Codebase/README|Codebase README]]
- Launcher: `C:\Operynth\Projects\session-portal\Codebase\session_portal.pyw`

## Run

```powershell
cd C:\Operynth\Projects\session-portal\Codebase
pyw .\session_portal.pyw
```

## Local Data

- Claude sessions: `%USERPROFILE%\.claude`
- Codex sessions: `%USERPROFILE%\.codex`
- Grok sessions and prompt history: `%USERPROFILE%\.grok`
- Claude memories/context: `%USERPROFILE%\.claude\CLAUDE.md`, `%USERPROFILE%\.claude\agents`, `%USERPROFILE%\.claude\commands`, and top-level `%USERPROFILE%\.claude\skills` entries
- Codex memories: `%USERPROFILE%\.codex\memories`
- Source choices: `C:\Operynth\Projects\session-portal\Codebase\settings.json`
- Custom display names: `C:\Operynth\Projects\session-portal\Codebase\renames.json`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Grok prompt-history rows are read-only file entries and open directly in Notepad.
- Model inventory and model-group controls are intentionally hidden; the app focuses on sessions, memories, and prompt history.
- Startup keeps the root window hidden until the UI is built and the first scan is complete, avoiding the half-drawn double blink.
- Terminal launch helpers suppress intermediate helper-console flashes while still opening the actual terminal session.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
