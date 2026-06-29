# Session Portal

Session Portal is a local CustomTkinter desktop app for browsing, previewing, renaming, deleting, and resuming local AI sessions from this machine. It currently scans Claude Code, Codex, Grok, and GitHub Copilot CLI sessions discovered during provider onboarding and only shows rows that can be resumed.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **LLM**: the local harness plus the specific language model recorded in the session file, such as `Claude Code / glm-5.2`, `Codex / gpt-5.5`, or `Grok / grok-composer-2.5-fast`. If the session did not record one, Session Portal shows the harness with `Unknown`.
- **Provider**: the local tool or harness that created the session, such as Claude Code, Codex, Grok, or GitHub Copilot CLI.

## App

- Code: `Codebase/v2`
- README: `App/README.md`
- Codebase: `Codebase/README.md`
- Launcher: `Codebase/session_portal.pyw`
- Console launcher: `Codebase/session_portal.py`
- Legacy V1 rollback: `Codebase/legacy/session_portal_v1.py`
- One-step installer: `install.ps1`
- Repo-folder launcher: `launch_session_portal.bat`

## Run

Clone the repo and run commands from the repo root:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Install dependencies and create a Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After install, use the Desktop shortcut named **Session Portal** for future launches.

Manual no-console launch:

```powershell
pyw .\Codebase\session_portal.pyw
```

Users can also double-click `launch_session_portal.bat` from the repo folder.

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

## Local Data

- Claude Code sessions: `%USERPROFILE%\.claude`
- Codex sessions: `%USERPROFILE%\.codex`
- Grok sessions: `%USERPROFILE%\.grok`
- GitHub Copilot CLI sessions: `%USERPROFILE%\.copilot\session-state`
- AMP CLI threads: detected from `%USERPROFILE%\.amp`, `%USERPROFILE%\.config\amp`, `%USERPROFILE%\.local\share\amp`, `%LOCALAPPDATA%\amp`, and loaded through `amp threads list --json`
- Provider choices: `Codebase/v2/settings.json`
- Custom display names: `Codebase/v2/renames.json`
- Error log: `Codebase/v2/session_portal.log`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Resumable Copilot session rows launch GitHub Copilot CLI with `gh copilot -- --resume=<session-id>`.
- Resumable AMP thread rows launch AMP CLI with `amp threads continue <thread-id>`. AMP thread listing uses `amp threads list --json`; full Markdown is fetched only for selected-thread viewing/export because complete AMP thread data is server-backed, not fully stored as local JSONL. Session Portal hides deleted AMP rows locally instead of calling `amp threads delete` because AMP delete is permanent server-side.
- Basic use flow is documented in the public README: launch, choose providers, search/filter/sort, inspect, resume, rename, delete, refresh, and toggle Auto Scan.
- Public README now explains rename and resume step by step: select a row, confirm inspector metadata, use **Rename** for local display names, or use the green provider-specific resume button/double-click/Enter to reopen the terminal chat session.
- Delete mode requires explicit row selection plus a confirmation dialog; Esc or Cancel exits without deleting.
- The public README now explains right-click row actions, delete-mode Select All/Deselect All, Trash restore/delete forever/empty trash, keyboard shortcuts, Clear Dates, sort choices, and why AMP rows do not use the recoverable local delete flow.
- The `Msgs` column shows useful human message counts and can be sorted from the header or sort menu.
- **Clean Empty** moves only currently shown 0-message sessions to Trash after confirmation, respecting active search, provider, and date filters.
- Non-resumable rows are excluded, including cleaned-up history-only records and missing session files.
- Session rows are numbered in the current filtered and sorted order for quick reference.
- The session table uses a singular `LLM` column and shows the actual recorded LLM name when available.
- Clicking table headers toggles sorting for date, LLM, project, and prompt/title.
- Table header hover states keep high-contrast text so sortable columns stay readable.
- The provider filter uses `All Models` as the combined/default view label.
- Scan Sources controls which local tools/folders are scanned; All Models, Claude Code, Codex, Grok, and Copilot filter the discovered session rows.
- A compact Dates calendar button opens date-range controls and filters sessions by last known activity date.
- Auto Scan reruns provider/session discovery every 60 seconds by default and can be toggled from the sidebar.
- Manual Refresh is documented as the immediate update path for new sessions, changed provider choices, renamed rows, and deleted rows.
- The search box prefilters sessions by project, title, or prompt and shows an empty-state hint telling users to start typing.
- Session scanning uses bounded metadata reads so large JSONL histories do not stay in memory during refresh.
- Provider discovery is dynamic for the current Windows user and resolves provider folders from `%USERPROFILE%`.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- The UI uses a CustomTkinter app shell with left-side provider navigation, a table-aligned search rail, a wide numbered session table, and a compact right-side inspector.
- The main workspace avoids a repeated page title; the search box prompts users to start typing to prefilter rows, `Threads` labels the table, and `Local AI Workspace` labels the sidebar subtitle.
- Session table headings and row values use explicit anchors so each label lines up with its column content.
- The session table uses fixed readable column widths and a bottom horizontal scrollbar so long prompts can be read without hiding the LLM, Project, or Date columns.
- The Date column is wide enough for the full `YYYY-MM-DD HH:MM` value.
- The `Msgs` column is a compact fixed-width column for session message counts.
- The layout gives the session table the primary width and keeps the right inspector compact by default.
- The top search area is aligned to the session-table width; date and sort controls sit in the compact inspector-side rail.
- The app uses one fixed high-contrast theme; runtime theme switching is intentionally removed to avoid restart delays.
- Inspector action buttons use the same rounded CustomTkinter style as the sidebar controls.
- Inspector action buttons use high-contrast enabled and disabled text colors for readability.
- Sidebar shortcut text is hidden; inspector metadata labels use compact alignment.
- Inspector metadata always renders first and uses one-line sanitized values across Claude Code, Codex, Grok, and Copilot.
- The inspector preview has its own scrollbar for long prompts or context.
- The app sets its default window to the current screen size and launches maximized so the `Thread / Last Prompt` column is visible by default.
- LLM inventory, model-group controls, memory sections, and non-resumable prompt-history rows are intentionally hidden; the app focuses on resumable sessions.
- Startup keeps the root window hidden until the UI is built and the first scan is complete, avoiding the half-drawn double blink.
- Terminal launch helpers suppress intermediate helper-console flashes while still opening the actual terminal session.
- Terminal launch helpers request maximized terminal windows for resumed sessions.
- Reviewer and QA passed whole-app validation on 2026-06-28. The app compiles, launches visibly, loads only resumable sessions, filters/searches/sorts correctly, previews Claude Code/Codex/Grok metadata, renames safely, handles delete-mode cancellation, and builds correct resume commands.

## V2 Promotion Track

- On 2026-06-29, the `features` Git branch was created and pushed for V2 feature work.
- V2 is now the default app on the promotion branch.
- V2 is the preferred engineering direction because it separates providers, session aggregation, storage, resume launch behavior, trash/recovery, thread viewing, cost estimates, and UI modules.
- V2 now includes rotating local error logging for startup crashes, provider scan failures, CLI-backed provider failures, preview/indexing failures, resume errors, export failures, rename-save failures, and trash/restore problems. Logs are ignored by git and are meant for developer support/debugging, not user-facing app data.
- The V2 provider layer is the desired foundation for Claude Code, Codex, Grok, Copilot, AMP, and future local AI tools, instead of continuing to expand one large `session_portal.py` file.
- V1 remains archived at `Codebase/legacy/session_portal_v1.py` as a temporary rollback reference.
- Current V2 tests pass locally: provider parsing, bounded reads, delete safety, resume-command construction, search indexing, trash/recovery, thread viewing, and cost estimates.
- V2 live smoke test on 2026-06-29 confirmed the app launches maximized, loads the session table, shows the sidebar controls, and keeps cost totals hidden until explicitly computed. A cost-rollup side effect was fixed so message-count scanning no longer caches token costs automatically.
- `Codebase/session_portal.py` and `Codebase/session_portal.pyw` now launch V2.
- The thread viewer now keeps the newest bounded slice of large transcripts and scrolls to the bottom on open so the visible ending matches the inspector's last message. Inspector metadata labels were tightened so the full session GUID stays on the `Session` line.
- Inspector token and cache counts now use compact `M`/`K` formatting so token metadata stays on one line in the right panel.
- Codex thread viewing now streams the full selected rollout file before applying the bounded render tail. This fixes large-session mismatches where the resumed CLI showed newer final messages than **View Thread**.
- Selected threads can now be saved as local Markdown review/audit exports through **Export Thread**. The button opens a Windows Save As dialog so users can choose the destination folder and filename. The default location remains `Codebase/v2/audits/`, exports include metadata plus the readable thread transcript, and generated audit files are git-ignored by default.
- Security check on 2026-06-29 found no embedded API keys or secrets in the repo scan. The main hardening change added path-boundary checks around trash restore, purge, empty-trash, and direct Grok/Copilot provider deletes so edited local state cannot move or delete files outside the app trash or expected provider session folders. Static scanner warnings remain only for intentional `Popen` terminal launches that must stay open for resumed chats.
- Branding update on 2026-06-29 replaced the old small mark with a compact glowing portal-door icon inspired by the provided Session Portal wordmark. The app keeps its high-contrast dark utility UI and borrows only the electric blue/violet accent for the icon, avoiding a full chrome/neon UI theme shift. The mark now appears visibly in the sidebar, loads through both Tk `iconbitmap` and `iconphoto`, and the Desktop shortcut points at `session_portal.ico` to avoid stale Windows icon-cache behavior.
- Taskbar identity update on 2026-06-29 added a Windows AppUserModelID in the Python-hosted app and stamps the same identity onto the Desktop shortcut, so fresh shortcut launches appear as **Session Portal** in the Windows taskbar instead of generic Python.
- AMP performance/deletion update on 2026-06-29 keeps AMP refresh, preview, and search on fast `amp threads list --json` metadata. Full Markdown is fetched only for **View Thread** or **Export Thread** on one selected AMP thread. AMP Delete now appears as **Hide AMP Row** for selected AMP threads, shows an inspector warning, and hides rows locally through `Codebase/v2/hidden_sessions.json` instead of calling AMP's permanent server-side delete.
- Usability update on 2026-06-29 added hover tooltips for the brand area, provider filters, source scanning, refresh, clean-empty, auto-scan, trash, cost estimate, search, date range, sort menu, session table, inspector preview, and inspector actions. The public README now documents those tooltips plus the **Export Thread** flow for saving review/audit Markdown files.
- Public README cleanup on 2026-06-29 rewrote the root README as a clean open-source landing page with accurate install, update, uninstall, launch, provider, privacy, usage, export, trash, logging, and development sections. `App/README.md` now acts as a shorter app-focused companion note.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
