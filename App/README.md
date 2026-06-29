# Session Portal App

Session Portal is a local Windows desktop app for finding, previewing, renaming, deleting, and resuming Claude, Codex, and Grok sessions on this machine. It uses a CustomTkinter shell and only shows sessions that can be resumed.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **Model**: the AI engine recorded in the session file, such as `gpt-5.5`, `grok-composer-2.5-fast`, or `glm-5.2`.
- **Provider**: the local tool that created the session, such as Claude, Codex, or Grok.

## Launch

Clone the repo and run commands from the repository root:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Use the no-console launcher:

```powershell
pyw .\Codebase\session_portal.pyw
```

Double-clicking `session_portal.pyw` opens the Tkinter app directly without first opening a `cmd` or Windows Terminal tab.

If the UI dependency is missing:

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
```

Optional desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_desktop_shortcut.ps1
```

Uninstall shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

## What It Shows

- Claude sessions from `%USERPROFILE%\.claude`
- Codex sessions from `%USERPROFILE%\.codex`
- Grok sessions from `%USERPROFILE%\.grok\sessions`
- Generated titles when available
- Project folders where sessions were originally run
- Actual model names from session files when available
- Row numbers for quick visual reference in the current filtered/sorted list
- First and last human prompts
- Token counts when the session files include usage data

## Main Actions

- Choose enabled providers during first-run onboarding
- See other detected local AI tools during onboarding when session resume support is not available yet
- Search sessions by project or title
- Filter by All Models, Claude, Codex, or Grok
- Reopen provider selection later with the Scan Sources button
- Sort by date, model, project, or prompt/title from the sort menu or by clicking table headers
- Use the left provider sidebar, top search/sort rail, numbered sessions table, and right inspector layout
- Preview session metadata and prompts
- Scroll long inspector previews independently in the right panel
- Resume a session in its recorded working directory with the terminal opened maximized
- Resume Grok sessions with `grok --resume <session-id>`
- Rename sessions locally
- Delete selected sessions

## Codebase

- Main app: `Codebase/session_portal.py`
- No-console launcher: `Codebase/session_portal.pyw`
- Dependency file: `Codebase/requirements.txt`
- Codebase README: `Codebase/README.md`

## Local Files

- App folder: `App`
- Codebase folder: `Codebase`
- Saved provider choices: `Codebase/settings.json`
- Custom names file: `Codebase/renames.json`

## Current Notes

- Vault notes must stay current when the app changes. Update this README and the project overview with any meaningful behavior, launch, provider discovery, or file-layout change.
- Use `session_portal.pyw` for normal launching.
- The root window stays hidden during initial UI construction and session scanning, then appears once to avoid startup flicker.
- The app launches maximized by default so the `Thread / Last Prompt` column is visible without resizing.
- The current UI uses CustomTkinter for the app frame, sidebar, search, filters, and sort controls while retaining the stable Tk table and preview internals.
- Session table headings are explicitly aligned to their row columns.
- The session table uses a singular `Model` column and shows actual recorded model names when available.
- Clicking table headers toggles sorting for date, model, project, and prompt/title.
- Table header hover states keep high-contrast text so sortable columns stay readable.
- The app uses one fixed high-contrast theme; runtime theme switching is intentionally removed to avoid restart delays.
- Inspector action buttons use the same rounded CustomTkinter style as the sidebar controls.
- Inspector action buttons use high-contrast enabled and disabled text colors for readability.
- Sidebar shortcut text is hidden; inspector metadata labels use compact alignment.
- Inspector metadata always renders first and uses one-line sanitized values across Claude, Codex, and Grok.
- The inspector preview has its own scrollbar for long prompts or context.
- Session launch helpers suppress intermediate helper-console flashes while still opening the real terminal window.
- Session launch helpers request maximized terminal windows for resumed sessions.
- First launch opens provider onboarding so the user can choose which local tools to scan. Saved choices are reused on later launches.
- Provider discovery is dynamic for the current Windows user and resolves local session folders from `%USERPROFILE%`.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- Scan Sources controls which local tools/folders are scanned; All Models, Claude, Codex, and Grok are filters for already discovered session rows.
- Non-resumable rows are excluded from the list, including cleaned-up history-only records and missing session files.
- Restart the app after code edits; the Refresh button reloads session data, not Python source code.
- The app intentionally hides model inventory, model-group controls, memory sections, and non-resumable prompt-history rows.
- The app does not require an API service.
