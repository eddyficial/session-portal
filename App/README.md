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
---

# Session Portal App

Session Portal is a local Windows desktop app for finding, previewing, renaming, deleting, and resuming Claude, Codex, and Grok sessions on this machine. It also indexes local memory notes and local LLM inventories for quick lookup.

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
- Codex memories from `%USERPROFILE%\.codex\memories`
- Claude memories/context from `%USERPROFILE%\.claude\CLAUDE.md`, agents, commands, and top-level skill files
- Grok prompt history from `%USERPROFILE%\.grok\sessions`
- Local LLM prompt history when a provider exposes a readable history file
- Generated titles when available
- Project folders where sessions were originally run
- First and last human prompts
- Token counts when the session files include usage data

## Main Actions

- Choose enabled LLM sources during first-run onboarding
- Search sessions by project or title
- Filter by Claude, Codex, Grok, Memory, LLMs, or all items
- Reopen source selection later with the Sources button
- Sort by date or project
- Preview session metadata and prompts
- Resume a session in its recorded working directory
- Resume Grok sessions with `grok --resume <session-id>`
- Open Grok prompt-history rows directly in Notepad
- Open memory markdown files
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
- Session launch helpers suppress intermediate helper-console flashes while still opening the real terminal window.
- First launch opens source onboarding so the user can choose which local LLM tools to scan. Saved choices are reused on later launches.
- Claude Memory is a separate source choice from Claude sessions. It indexes the global `CLAUDE.md`, `agents/*.md`, `commands/*.md`, and one top-level entry file per installed Claude skill.
- Restart the app after code edits; the Refresh button reloads session data, not Python source code.
- The app intentionally hides model inventory and model-group controls. It focuses on sessions, memories, and prompt history.
- Grok prompt-history rows are read-only and open directly in Notepad; Grok session rows can be resumed.
- Memory items are read-only in the app; they can be opened but not renamed or deleted from Session Portal.
- The app does not require an API service.
