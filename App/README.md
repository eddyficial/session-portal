---
id: app-session-portal
title: Session Portal App
type: app
status: active
updated: 2026-06-26
tags:
  - desktop-app
  - sessions
  - claude
  - codex
project: App
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
repository_path: Not applicable
business_area: portfolio
lifecycle: active
owner: Operynth
related:
  - Index.md
---

# Session Portal App

Session Portal is a local Windows desktop app for finding, previewing, renaming, deleting, and resuming Claude, Codex, and Grok sessions on this machine. It also indexes supported local prompt-history files for quick lookup.

## Launch

Use the no-console launcher:

```text
C:\Operynth\Projects\session-portal\Codebase\session_portal.pyw
```

Double-clicking `session_portal.pyw` opens the Tkinter app directly without first opening a `cmd` or Windows Terminal tab.

## What It Shows

- Claude sessions from `%USERPROFILE%\.claude`
- Codex sessions from `%USERPROFILE%\.codex`
- Grok sessions from `%USERPROFILE%\.grok\sessions`
- Grok prompt history from `%USERPROFILE%\.grok\sessions`
- Ollama prompt history when available
- Generated titles when available
- Project folders where sessions were originally run
- Row numbers for quick visual reference in the current filtered/sorted list
- First and last human prompts
- Token counts when the session files include usage data

## Main Actions

- Choose enabled sources during first-run onboarding
- Search sessions by project or title
- Filter by Models, Claude, Codex, Grok, or Ollama
- Reopen source selection later with the Sources button
- Sort by date or project
- Use the reorganized header/status bar, controls row, numbered sessions list, and preview panel layout
- Preview session metadata and prompts
- Resume a session in its recorded working directory
- Resume Grok sessions with `grok --resume <session-id>`
- Open Grok prompt-history rows directly in Notepad
- Rename sessions locally
- Delete selected sessions

## Codebase

- Main app: [[Projects/session-portal/Codebase/session_portal.py|session_portal.py]]
- No-console launcher: [[Projects/session-portal/Codebase/session_portal.pyw|session_portal.pyw]]
- Codebase README: [[Projects/session-portal/Codebase/README|Codebase README]]

## Local Files

- App folder: `C:\Operynth\Projects\session-portal\App`
- Codebase folder: `C:\Operynth\Projects\session-portal\Codebase`
- Saved source choices: `C:\Operynth\Projects\session-portal\Codebase\settings.json`
- Custom names file: `C:\Operynth\Projects\session-portal\Codebase\renames.json`

## Current Notes

- Vault notes must stay current when the app changes. Update this README and the project overview with any meaningful behavior, launch, source-discovery, or file-layout change.
- Use `session_portal.pyw` for normal launching.
- The root window stays hidden during initial UI construction and session scanning, then appears once to avoid startup flicker.
- The app launches wide by default so the `Thread / Last Prompt` column is visible without resizing.
- Session launch helpers suppress intermediate helper-console flashes while still opening the real terminal window.
- First launch opens source onboarding so the user can choose which local tools to scan. Saved choices are reused on later launches.
- Restart the app after code edits; the Refresh button reloads session data, not Python source code.
- The app intentionally hides model inventory, model-group controls, and memory sections. It focuses on sessions and prompt history.
- Grok prompt-history rows are read-only and open directly in Notepad; Grok session rows can be resumed.
- The app does not require an API service.
