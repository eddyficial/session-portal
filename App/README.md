# Session Portal App

Session Portal is a local Windows desktop app for finding, previewing, renaming, deleting, and resuming Claude Code, Codex, Grok, and GitHub Copilot CLI sessions on this machine. It uses a CustomTkinter shell and only shows sessions that can be resumed.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **LLM**: the local harness plus the specific language model recorded in the session file, such as `Claude Code / glm-5.2`, `Codex / gpt-5.5`, or `Grok / grok-composer-2.5-fast`. If the session did not record one, Session Portal shows the harness with `Unknown`.
- **Provider**: the local tool or harness that created the session, such as Claude Code, Codex, Grok, or GitHub Copilot CLI.

## Launch

Clone the repo and run commands from the repository root:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Install dependencies and create a Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After this, use the Desktop shortcut named **Session Portal** for future launches.

Use the no-console launcher manually:

```powershell
pyw .\Codebase\session_portal.pyw
```

Or double-click `launch_session_portal.bat` from the repo folder.

Double-clicking `session_portal.pyw` opens the Tkinter app directly without first opening a `cmd` or Windows Terminal tab.

If the UI dependency is missing:

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
```

Shortcut only:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_desktop_shortcut.ps1
```

Uninstall shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

## What It Shows

- Claude Code sessions from `%USERPROFILE%\.claude`
- Codex sessions from `%USERPROFILE%\.codex`
- Grok sessions from `%USERPROFILE%\.grok\sessions`
- GitHub Copilot CLI sessions from `%USERPROFILE%\.copilot\session-state`
- Generated titles when available
- Project folders where sessions were originally run
- Actual LLM names from session files when available
- Row numbers for quick visual reference in the current filtered/sorted list
- Message counts in the `Msgs` column
- First and last human prompts
- Token counts when the session files include usage data

## Main Actions

- Choose enabled providers during first-run onboarding
- See other detected local AI tools during onboarding when session resume support is not available yet
- Search sessions by project, title, or prompt; the empty search box prompts users to start typing to prefilter rows
- Filter sessions by activity date range with the compact Dates calendar button
- Filter by All Models, Claude Code, Codex, Grok, or Copilot
- Toggle Auto Scan to keep supported session discovery fresh while the app is open
- Reopen provider selection later with the Scan Sources button
- Sort by date, LLM, project, or prompt/title from the sort menu or by clicking table headers
- Sort by message count from the `Msgs` header or sort menu
- Use the left provider sidebar, table-aligned search rail, wide numbered sessions table, and compact right inspector layout
- The main workspace avoids a repeated page title; the search box prompts users to start typing to prefilter rows, `Threads` labels the table, and `Local AI Workspace` labels the sidebar subtitle.
- Preview session metadata and prompts
- Scroll long inspector previews independently in the right panel
- Resume a session in its recorded working directory with the terminal opened maximized
- Resume Grok sessions with `grok --resume <session-id>`
- Resume Copilot sessions with `gh copilot -- --resume=<session-id>`
- Rename sessions locally
- Delete selected sessions
- Clean currently shown empty sessions with **Clean Empty Msgs** after confirmation

## Use Flow

1. Launch `Codebase/session_portal.pyw`.
2. On first launch, choose which providers to scan and click Save.
3. Use the left sidebar to filter all sessions or one provider.
4. Use the search box to find a project, title, or prompt.
5. Use the Dates calendar button to filter by last activity date when needed.
6. Click table headers or the sort menu to change ordering.
7. Select a row to inspect metadata and first/last prompt.
8. Double-click, press Enter, or click the resume button to reopen the session in a maximized terminal.
9. Use Rename to store a local display name in `Codebase/renames.json`.
10. Use Delete to enter delete mode, select one or more rows, click Delete Selected, and confirm the warning dialog.
11. Use Esc or Cancel to leave delete mode without deleting.
12. Use **Clean Empty Msgs** to remove currently shown sessions with no useful human messages after confirmation.

## Rename And Resume

To rename a session:

1. Select one row.
2. Click **Rename** at the bottom of the inspector panel.
3. Type the display name you want.
4. Click **OK**.

The rename is local to Session Portal and is saved in `Codebase/renames.json`. It does not edit the provider's original session file. To remove a custom rename, open **Rename**, clear the text box, and click **OK**.

To resume a session:

1. Select one row.
2. Confirm the metadata in the right inspector.
3. Click the green provider-specific resume button, such as **Resume Claude Code**, **Resume Codex**, **Resume Grok**, or **Resume Copilot**.

The app opens a maximized terminal in the session's recorded working directory and runs the provider resume command. Double-clicking a row or pressing `Enter` also resumes the selected terminal chat session.

Auto Scan refreshes provider/session discovery every 60 seconds by default. The sidebar toggle can turn it off when the user wants only manual Refresh behavior. Manual Refresh is used when the user wants new sessions, renamed rows, deleted rows, or changed provider choices to appear immediately.

## Codebase

- Main app: `Codebase/session_portal.py`
- No-console launcher: `Codebase/session_portal.pyw`
- Dependency file: `Codebase/requirements.txt`
- One-step installer: `install.ps1`
- Repo-folder launcher: `launch_session_portal.bat`
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
- The app sets its default window to the current screen size and launches maximized so the `Thread / Last Prompt` column is visible without resizing.
- The current UI uses CustomTkinter for the app frame, sidebar, search, filters, and sort controls while retaining the stable Tk table and preview internals.
- Session table headings are explicitly aligned to their row columns.
- The session table uses fixed readable column widths and a bottom horizontal scrollbar so long prompts can be read without hiding the LLM, Project, or Date columns.
- The Date column is wide enough for the full `YYYY-MM-DD HH:MM` value.
- The `Msgs` column shows useful human message counts and supports sorting.
- The layout gives the session table the primary width and keeps the right inspector compact by default.
- The top search area is aligned to the session-table width; date and sort controls sit in the compact inspector-side rail.
- The session table uses a singular `LLM` column and shows actual recorded LLM names when available.
- Clicking table headers toggles sorting for date, LLM, project, and prompt/title.
- Table header hover states keep high-contrast text so sortable columns stay readable.
- The app uses one fixed high-contrast theme; runtime theme switching is intentionally removed to avoid restart delays.
- Inspector action buttons use the same rounded CustomTkinter style as the sidebar controls.
- Inspector action buttons use high-contrast enabled and disabled text colors for readability.
- Sidebar shortcut text is hidden; inspector metadata labels use compact alignment.
- Inspector metadata always renders first and uses one-line sanitized values across Claude Code, Codex, Grok, and Copilot.
- The inspector preview has its own scrollbar for long prompts or context.
- Session launch helpers suppress intermediate helper-console flashes while still opening the real terminal window.
- Session launch helpers request maximized terminal windows for resumed sessions.
- First launch opens provider onboarding so the user can choose which local tools to scan. Saved choices are reused on later launches.
- Provider discovery is dynamic for the current Windows user and resolves local session folders from `%USERPROFILE%`.
- Auto Scan reruns provider/session discovery every 60 seconds by default and can be toggled from the sidebar.
- Session scanning uses bounded metadata reads so large JSONL histories do not stay in memory during refresh.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- Scan Sources controls which local tools/folders are scanned; All Models, Claude Code, Codex, Grok, and Copilot are filters for already discovered session rows.
- Non-resumable rows are excluded from the list, including cleaned-up history-only records and missing session files.
- Restart the app after code edits; the Refresh button reloads session data, not Python source code.
- The app intentionally hides model inventory, model-group controls, memory sections, and non-resumable prompt-history rows.
- The app does not require an API service.
