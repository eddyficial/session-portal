# Session Portal

Session Portal is a local CustomTkinter desktop app for browsing, previewing, renaming, deleting, and resuming local AI sessions from this machine. It currently scans Claude Code, Codex, Grok, and GitHub Copilot CLI sessions discovered during provider onboarding and only shows rows that can be resumed.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **LLM**: the local harness plus the specific language model recorded in the session file, such as `Claude Code / glm-5.2`, `Codex / gpt-5.5`, or `Grok / grok-composer-2.5-fast`. If the session did not record one, Session Portal shows the harness with `Unknown`.
- **Provider**: the local tool or harness that created the session, such as Claude Code, Codex, Grok, or GitHub Copilot CLI.

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

Uninstall shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

## Local Data

- Claude Code sessions: `%USERPROFILE%\.claude`
- Codex sessions: `%USERPROFILE%\.codex`
- Grok sessions: `%USERPROFILE%\.grok`
- GitHub Copilot CLI sessions: `%USERPROFILE%\.copilot\session-state`
- Provider choices: `Codebase/settings.json`
- Custom display names: `Codebase/renames.json`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Resumable Copilot session rows launch GitHub Copilot CLI with `gh copilot -- --resume=<session-id>`.
- Basic use flow is documented in the public README: launch, choose providers, search/filter/sort, inspect, resume, rename, delete, refresh, and toggle Auto Scan.
- Delete mode requires explicit row selection plus a confirmation dialog; Esc or Cancel exits without deleting.
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
- Session scanning uses bounded metadata reads so large JSONL histories do not stay in memory during refresh.
- Provider discovery is dynamic for the current Windows user and resolves provider folders from `%USERPROFILE%`.
- Sidebar filters are generated from enabled/detected supported providers instead of a fixed source list.
- Other common local AI tools are detected during onboarding, but only providers with session loaders appear in the resumable session list.
- Resume fallback behavior uses the current user's home folder when a session does not have a valid recorded project path.
- The UI uses a CustomTkinter app shell with left-side provider navigation, a top search/sort rail, a wide numbered session table, and a right-side inspector.
- Session table headings and row values use explicit anchors so each label lines up with its column content.
- The app uses one fixed high-contrast theme; runtime theme switching is intentionally removed to avoid restart delays.
- Inspector action buttons use the same rounded CustomTkinter style as the sidebar controls.
- Inspector action buttons use high-contrast enabled and disabled text colors for readability.
- Sidebar shortcut text is hidden; inspector metadata labels use compact alignment.
- Inspector metadata always renders first and uses one-line sanitized values across Claude Code, Codex, Grok, and Copilot.
- The inspector preview has its own scrollbar for long prompts or context.
- The app launches maximized so the `Thread / Last Prompt` column is visible by default.
- LLM inventory, model-group controls, memory sections, and non-resumable prompt-history rows are intentionally hidden; the app focuses on resumable sessions.
- Startup keeps the root window hidden until the UI is built and the first scan is complete, avoiding the half-drawn double blink.
- Terminal launch helpers suppress intermediate helper-console flashes while still opening the actual terminal session.
- Terminal launch helpers request maximized terminal windows for resumed sessions.
- Reviewer and QA passed whole-app validation on 2026-06-28. The app compiles, launches visibly, loads only resumable sessions, filters/searches/sorts correctly, previews Claude Code/Codex/Grok metadata, renames safely, handles delete-mode cancellation, and builds correct resume commands.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
