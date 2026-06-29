# Session Portal

Session Portal is a local CustomTkinter desktop app for browsing, previewing, renaming, deleting, and resuming local AI sessions from this machine. It currently scans Claude, Codex, and Grok sessions discovered during source onboarding and only shows rows that can be resumed.

## App

- Code: `Codebase/session_portal.py`
- README: `App/README.md`
- Codebase: `Codebase/README.md`
- Launcher: `Codebase/session_portal.pyw`

## Run

Clone the repo and run commands from the repo root:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

```powershell
pyw .\Codebase\session_portal.pyw
```

Install the UI dependency if needed:

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
```

Optional desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_desktop_shortcut.ps1
```

## Local Data

- Claude sessions: `%USERPROFILE%\.claude`
- Codex sessions: `%USERPROFILE%\.codex`
- Grok sessions: `%USERPROFILE%\.grok`
- Source choices: `Codebase/settings.json`
- Custom display names: `Codebase/renames.json`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Non-resumable rows are excluded, including cleaned-up history-only records and missing session files.
- Session rows are numbered in the current filtered and sorted order for quick reference.
- The source filter uses `All Models` as the combined/default view label.
- Scan Sources controls which local tools/folders are scanned; All Models, Claude, Codex, and Grok filter the discovered rows.
- Source discovery is dynamic for the current Windows user and resolves provider folders from `%USERPROFILE%`.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- The UI uses a CustomTkinter app shell with left-side source navigation, a top search/sort rail, a wide numbered session table, and a right-side inspector.
- Session table headings and row values use explicit anchors so each label lines up with its column content.
- The app uses one fixed high-contrast theme; runtime theme switching is intentionally removed to avoid restart delays.
- Inspector action buttons use the same rounded CustomTkinter style as the sidebar controls.
- Sidebar shortcut text is hidden; inspector metadata labels use compact alignment.
- Inspector metadata always renders first and uses one-line sanitized values across Claude, Codex, and Grok.
- The app launches maximized so the `Thread / Last Prompt` column is visible by default.
- Model inventory, model-group controls, memory sections, and non-resumable prompt-history rows are intentionally hidden; the app focuses on resumable sessions.
- Startup keeps the root window hidden until the UI is built and the first scan is complete, avoiding the half-drawn double blink.
- Terminal launch helpers suppress intermediate helper-console flashes while still opening the actual terminal session.
- Terminal launch helpers request maximized terminal windows for resumed sessions.
- Reviewer and QA passed whole-app validation on 2026-06-28. The app compiles, launches visibly, loads only resumable sessions, filters/searches/sorts correctly, previews Claude/Codex/Grok metadata, renames safely, handles delete-mode cancellation, and builds correct resume commands.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
