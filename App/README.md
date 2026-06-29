# Session Portal

Session Portal is a local Windows desktop app for finding, previewing, exporting, cleaning, and resuming AI CLI sessions from one place.

It scans the current user's machine for supported AI coding tools, shows only resumable sessions, and opens selected sessions back in their recorded working folder.

## Supported Providers

- Claude Code
- Codex
- Grok CLI
- GitHub Copilot CLI
- AMP CLI

Other local AI tools may be detected during onboarding, but only tools with implemented session loaders appear in the main session list.

## Core Actions

- Search sessions by project, title, date, provider, or prompt text
- Preview metadata, first prompt, last prompt, token counts, and message counts
- Resume a session in the folder where it originally ran
- View a read-only transcript before resuming
- Export a Markdown copy of a thread for review or audit records
- Rename sessions locally without changing provider files
- Move supported local sessions to a recoverable Trash
- Hide AMP threads locally without calling AMP's permanent server delete
- Clean currently shown empty sessions

## Install

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After installation, launch **Session Portal** from the Desktop shortcut.

## Launch

```powershell
pyw .\Codebase\session_portal.pyw
```

The `.pyw` launcher starts the app without opening an extra console window.

The Desktop shortcut uses the bundled Session Portal icon and app identity so Windows shows Session Portal in the taskbar instead of generic Python.

## Update

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipDependencies
```

Run the full installer again if dependencies changed:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Uninstall

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

To also remove Session Portal local data inside the cloned repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1 -RemoveLocalData
```

## How To Use

1. Launch Session Portal.
2. Choose providers on first launch and click **Save**.
3. Use the sidebar to filter by provider.
4. Use search, Dates, and sorting to narrow the list.
5. Select a row to inspect metadata and first/last prompt.
6. Double-click, press `Enter`, or click the green resume button to resume.
7. Use **View Thread** for a read-only transcript.
8. Use **Export Thread** to save a Markdown copy.
9. Use **Rename** to create a local display name.
10. Use **Delete** to move supported local sessions to Trash. For AMP, the button becomes **Hide AMP Row** and hides the row only in Session Portal.
11. Use **Clean Empty** to move currently shown `0` message sessions to Trash.
12. Use **Trash** to restore or permanently purge deleted sessions.

## Table Columns

- `#`: row number in the current filtered and sorted list
- `LLM`: provider plus recorded model
- `Project`: folder name where the session ran
- `Date`: last known activity
- `Msgs`: useful human message count
- `Thread / Last Prompt`: title, thread name, or useful prompt text

## Local Files

```text
Codebase/v2/settings.json
Codebase/v2/renames.json
Codebase/v2/hidden_sessions.json
Codebase/v2/audits/
Codebase/v2/.trash/
Codebase/v2/session_portal.log
```

These files are user-specific and ignored by git.

## Notes

- Session Portal is local-first and does not require an API service.
- AMP delete hides rows locally because AMP threads are server-backed and provider deletion is permanent.
- The error log records startup crashes, provider scan failures, failed CLI calls, resume failures, export failures, rename-save failures, and trash/restore problems.
- The public root README contains the full install, usage, development, and security notes.
