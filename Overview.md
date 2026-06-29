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
project: Session Portal
repository_path: C:\Operynth\Projects\session-portal\Codebase
business_area: platform
lifecycle: active
repository: Not applicable
technology:
  - Markdown
dependencies:
  - Not applicable
skills:
  - Knowledge Management
services:
  - Obsidian
related_notes:
  - Index.md
related:
  - Index.md
---

# Session Portal

Session Portal is a local Tkinter desktop app for browsing, previewing, renaming, deleting, and resuming local AI sessions from this machine. It currently scans Claude, Codex, Grok, and supported local prompt-history files discovered during source onboarding.

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
- Source choices: `C:\Operynth\Projects\session-portal\Codebase\settings.json`
- Custom display names: `C:\Operynth\Projects\session-portal\Codebase\renames.json`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Grok prompt-history rows are read-only file entries and open directly in Notepad.
- Session rows are numbered in the current filtered and sorted order for quick reference.
- The source filter uses `Models` as the combined/default view label.
- Ollama prompt-history rows are labeled as `Ollama`.
- The UI is organized into a header/status bar, controls row, sessions list, preview panel, and quiet footer.
- The app launches wide enough for the `Thread / Last Prompt` column to be visible by default.
- Model inventory, model-group controls, and memory sections are intentionally hidden; the app focuses on sessions and prompt history.
- Startup keeps the root window hidden until the UI is built and the first scan is complete, avoiding the half-drawn double blink.
- Terminal launch helpers suppress intermediate helper-console flashes while still opening the actual terminal session.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
