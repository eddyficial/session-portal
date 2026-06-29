# Session Portal App

Session Portal is a local Windows desktop app for finding, previewing, renaming, deleting, exporting, and resuming Claude Code, Codex, Grok, GitHub Copilot CLI, and AMP CLI sessions on this machine. It uses the modular V2 CustomTkinter shell and only shows sessions that can be resumed.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **LLM**: the local harness plus the specific language model recorded in the session file, such as `Claude Code / glm-5.2`, `Codex / gpt-5.5`, or `Grok / grok-composer-2.5-fast`. If the session did not record one, Session Portal shows the harness with `Unknown`.
- **Provider**: the local tool or harness that created the session, such as Claude Code, Codex, Grok, GitHub Copilot CLI, or AMP CLI.

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

Update from a cloned install:

```powershell
cd %USERPROFILE%\session-portal
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipDependencies
```

## What It Shows

- Claude Code sessions from `%USERPROFILE%\.claude`
- Codex sessions from `%USERPROFILE%\.codex`
- Grok sessions from `%USERPROFILE%\.grok\sessions`
- GitHub Copilot CLI sessions from `%USERPROFILE%\.copilot\session-state`
- AMP CLI threads from `amp threads list --json`; AMP also uses local state under `%USERPROFILE%\.local\share\amp`, `%USERPROFILE%\.config\amp`, `%USERPROFILE%\.amp`, and `%LOCALAPPDATA%\amp`
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
- Filter by All Models, Claude Code, Codex, Grok, Copilot, or AMP
- Provider filters are listed alphabetically after **All Models**
- Toggle Auto Scan to keep supported session discovery fresh while the app is open
- Reopen provider selection later with the Scan Sources button
- Sort by date, LLM, project, or prompt/title from the sort menu or by clicking table headers
- Sort by message count from the `Msgs` header or sort menu
- Use the left provider sidebar, table-aligned search rail, wide numbered sessions table, and compact right inspector layout
- The main workspace avoids a repeated page title; the search box prompts users to start typing to prefilter rows, `Threads` labels the table, and `Resume Your Sessions` labels the sidebar subtitle.
- Hover over buttons, filters, the inspector, and table areas to see short tooltips that explain what each control does
- Preview session metadata, first prompt, last prompt, token counts, and provider details in the inspector
- Open the read-only thread viewer for a selected session
- Export the selected thread as a Markdown file for review, handoff, or AI-action auditing, with a folder and filename chosen by the user
- Scroll long inspector previews independently in the right panel
- Resume a session in its recorded working directory with the terminal opened maximized
- Resume Grok sessions with `grok --resume <session-id>`
- Resume Copilot sessions with `gh copilot -- --resume=<session-id>`
- Resume AMP sessions with `amp threads continue <thread-id>`
- Rename sessions locally
- Delete selected sessions
- Right-click a row to rename, delete that session, or enter delete mode for all currently shown rows
- Clean currently shown empty sessions with **Clean Empty Msgs** after confirmation
- Move deleted sessions into a recoverable Trash before permanent purge
- Restore trashed sessions, delete selected trashed sessions forever, or empty the whole Trash
- Compute approximate local cost estimates only when requested with **Compute Costs**

## Use Flow

1. Launch `Codebase/session_portal.pyw`.
2. On first launch, choose which providers to scan and click Save.
3. Use the left sidebar to filter all sessions or one provider.
4. Use the search box to find a project, title, or prompt.
5. Use the Dates calendar button to filter by last activity date when needed.
6. Click table headers or the sort menu to change ordering.
7. Select a row to inspect metadata and first/last prompt.
8. Double-click, press Enter, or click the resume button to reopen the session in a maximized terminal.
9. Use Rename to store a local display name in `Codebase/v2/renames.json`.
10. Use Delete to enter delete mode, select one or more rows, click Delete Selected, and confirm the warning dialog.
11. Use Esc or Cancel to leave delete mode without deleting.
12. Use **Clean Empty Msgs** to remove currently shown sessions with no useful human messages after confirmation.
13. Use **Export Thread** to open a Save As dialog, choose where the Markdown export should go, and confirm the filename.
14. Use **Trash** to restore deleted sessions or permanently remove trashed sessions.
15. Use `R` to refresh, `Q` to quit, and `Esc` to leave delete mode.

## Rename And Resume

To rename a session:

1. Select one row.
2. Click **Rename** at the bottom of the inspector panel.
3. Type the display name you want.
4. Click **OK**.

The rename is local to Session Portal and is saved in `Codebase/v2/renames.json`. It does not edit the provider's original session file. To remove a custom rename, open **Rename**, clear the text box, and click **OK**.

To resume a session:

1. Select one row.
2. Confirm the metadata in the right inspector.
3. Click the green provider-specific resume button, such as **Resume Claude Code**, **Resume Codex**, **Resume Grok**, **Resume Copilot**, or **Resume AMP**.

The app opens a maximized terminal in the session's recorded working directory and runs the provider resume command. Double-clicking a row or pressing `Enter` also resumes the selected terminal chat session.

## Delete And Trash

To delete sessions:

1. Select one row and click **Delete**, or right-click a row and choose **Delete This Session**.
2. In delete mode, click rows to mark or unmark them.
3. Use **Select All** to mark every currently shown row, or **Deselect All** to clear the marks.
4. Click **Delete Selected**.
5. Confirm the warning dialog.

Deleted sessions go to Session Portal's local Trash when the provider stores local files that can be moved safely. Open **Trash** from the sidebar to restore selected sessions, delete selected trashed sessions forever, or empty the whole Trash. Permanent delete actions cannot be undone.

AMP is different: AMP threads are server-backed, and `amp threads delete` is permanent on the AMP server. For that reason, the normal recoverable **Delete** action is disabled for AMP rows.

To clean empty sessions:

1. Apply any provider, search, or date filters you want.
2. Click **Clean Empty**.
3. Confirm the dialog.

Only currently shown sessions with `0` useful human messages are moved to Trash.

## Export Thread

1. Select one row.
2. Click **Export Thread** in the inspector.
3. Pick a folder in the Save As dialog.
4. Keep the suggested Markdown filename or type a new one.
5. Click **Save**.

The export is a local Markdown file containing the session metadata and readable transcript. It is useful when the user wants to review why an AI tool took certain actions, keep a handoff record, or archive a thread outside the provider's session folder. By default, Session Portal suggests `Codebase/v2/audits/`, but the export can be saved anywhere the user chooses. If the dialog is canceled, nothing is written.

## Tooltips

Most important controls have hover help:

- Sidebar filters explain whether they show all sessions or one provider.
- **Scan Sources** explains that it reopens provider selection and discovery.
- **Refresh** explains that it reloads session data immediately.
- **Clean Empty** explains that it removes currently shown sessions with no useful messages after confirmation.
- **Auto Scan** explains the background refresh behavior.
- **Trash** explains recovery and permanent purge for deleted sessions.
- **Compute Costs** explains that cost estimates are calculated only when requested.
- The search box explains that it filters by project, title, first prompt, or last prompt.
- **Dates** explains calendar date filtering.
- The sort menu explains list ordering.
- The session table explains row selection and sortable columns.
- The inspector and action buttons explain preview, rename, thread viewing, export, delete, and resume behavior.

## Dates And Sorting

Click **Dates** to open the calendar date-range picker. Use **Select** beside **From** or **To**, choose a date from the calendar, then click **Done**. Use **Clear Dates** to remove the date filter and return to all dates.

The sort menu supports newest, oldest, LLM A-Z/Z-A, project A-Z/Z-A, prompt A-Z/Z-A, and message count low-high/high-low. Table headers also toggle sorting for the visible columns.

Auto Scan refreshes provider/session discovery every 60 seconds by default. The sidebar toggle can turn it off when the user wants only manual Refresh behavior. Manual Refresh is used when the user wants new sessions, renamed rows, deleted rows, or changed provider choices to appear immediately.

## Codebase

- Main app: `Codebase/session_portal.py`
- No-console launcher: `Codebase/session_portal.pyw`
- Modular app package: `Codebase/v2`
- Legacy V1 rollback file: `Codebase/legacy/session_portal_v1.py`
- Dependency file: `Codebase/requirements.txt`
- One-step installer: `install.ps1`
- Repo-folder launcher: `launch_session_portal.bat`
- Codebase README: `Codebase/README.md`

## Local Files

- App folder: `App`
- Codebase folder: `Codebase`
- Saved provider choices: `Codebase/v2/settings.json`
- Custom names file: `Codebase/v2/renames.json`
- Default audit export folder: `Codebase/v2/audits`
- Error log: `Codebase/v2/session_portal.log`

The error log is local to the user's install and is ignored by git. It rotates automatically and records startup crashes, provider scan failures, failed CLI calls, resume failures, export failures, rename-save failures, and trash/restore problems. If a user reports a bug, ask them to check this file first.

## Current Notes

- Vault notes must stay current when the app changes. Update this README and the project overview with any meaningful behavior, launch, provider discovery, or file-layout change.
- Use `session_portal.pyw` for normal launching. It starts the modular V2 app.
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
- Provider failures are isolated and logged. One broken provider, corrupt session file, or missing CLI should not stop the rest of the app from loading.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- AMP support uses AMP's own CLI for thread listing, Markdown preview/export content, and resume commands. AMP delete is intentionally not wired to Session Portal trash because `amp threads delete` permanently deletes server-backed threads.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- Scan Sources controls which local tools/folders are scanned; All Models, Claude Code, Codex, Grok, Copilot, and AMP are filters for already discovered session rows.
- Non-resumable rows are excluded from the list, including cleaned-up history-only records and missing session files.
- Restart the app after code edits; the Refresh button reloads session data, not Python source code.
- The app intentionally hides model inventory, model-group controls, memory sections, and non-resumable prompt-history rows.
- The app does not require an API service.
- **Export Thread** opens a native Save As dialog instead of silently writing to only one folder.
