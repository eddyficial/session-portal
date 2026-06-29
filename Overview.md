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
- Provider choices: `Codebase/v2/settings.json`
- Custom display names: `Codebase/v2/renames.json`

## Behavior Notes

- Resumable Grok session rows launch Grok with `grok --resume`.
- Resumable Copilot session rows launch GitHub Copilot CLI with `gh copilot -- --resume=<session-id>`.
- Basic use flow is documented in the public README: launch, choose providers, search/filter/sort, inspect, resume, rename, delete, refresh, and toggle Auto Scan.
- Public README now explains rename and resume step by step: select a row, confirm inspector metadata, use **Rename** for local display names, or use the green provider-specific resume button/double-click/Enter to reopen the terminal chat session.
- Delete mode requires explicit row selection plus a confirmation dialog; Esc or Cancel exits without deleting.
- The `Msgs` column shows useful human message counts and can be sorted from the header or sort menu.
- **Clean Empty Msgs** deletes only currently shown 0-message sessions after confirmation, respecting active search, provider, and date filters.
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
- The V2 provider layer is the desired foundation for Claude Code, Codex, Grok, Copilot, and future local AI tools, instead of continuing to expand one large `session_portal.py` file.
- V1 remains archived at `Codebase/legacy/session_portal_v1.py` as a temporary rollback reference.
- Current V2 tests pass locally: provider parsing, bounded reads, delete safety, resume-command construction, search indexing, trash/recovery, thread viewing, and cost estimates.
- V2 live smoke test on 2026-06-29 confirmed the app launches maximized, loads the session table, shows the sidebar controls, and keeps cost totals hidden until explicitly computed. A cost-rollup side effect was fixed so message-count scanning no longer caches token costs automatically.
- `Codebase/session_portal.py` and `Codebase/session_portal.pyw` now launch V2.
- The thread viewer now keeps the newest bounded slice of large transcripts and scrolls to the bottom on open so the visible ending matches the inspector's last message. Inspector metadata labels were tightened so the full session GUID stays on the `Session` line.
- Inspector token and cache counts now use compact `M`/`K` formatting so token metadata stays on one line in the right panel.
- Codex thread viewing now streams the full selected rollout file before applying the bounded render tail. This fixes large-session mismatches where the resumed CLI showed newer final messages than **View Thread**.
- Selected threads can now be saved as local Markdown audit exports through **Save Audit**. Exports live under `Codebase/v2/audits/`, include metadata plus the readable thread transcript, and are git-ignored by default.

## Future Product Direction

Session Portal can grow from a local session manager into an **AI Workspace**: a local command center for searching, auditing, resuming, organizing, and transferring context across the AI tools a user already runs on their machine.

The durable product thesis:

- Session Portal v1/V2 manages resumable sessions.
- The next product layer should preserve **continuity across AI tools**.
- The unique value is not another chat surface; it is a cross-provider workspace that explains what happened, why it happened, where the work lives, and how to continue it safely.

Potential future build areas:

- **Universal thread index**: normalize Claude Code, Codex, Grok, Copilot, and future providers into one schema for provider, model, project, messages, tool calls, files, cost, and timestamps.
- **Universal search**: search across every AI conversation from one place.
- **Semantic search**: find ideas, decisions, blockers, or features even when the exact words do not match.
- **Project view**: group all sessions by project folder and show timeline, latest activity, summaries, open tasks, and related sessions.
- **Audit layer**: preserve selected threads, file changes, commands, tool calls, decisions, and final outcomes for reviewing AI actions.
- **Automatic project summaries**: generate durable project state from related sessions, including what changed, what remains, and what the next agent should know.
- **Conversation timelines**: visualize work across time, provider, model, and project.
- **Cost analytics**: show provider/model/project costs, token totals, expensive sessions, and cost trends.
- **Session branching**: fork a conversation into a new provider or a new task path while preserving source context.
- **Shared project memory**: extract durable decisions and facts that Claude Code, Codex, Grok, Copilot, and future tools can reuse.
- **One-click provider switching**: continue a session in another provider with the right context package and working directory.
- **Knowledge graph**: link related sessions, files, decisions, bugs, tasks, and projects.
- **Automatic tagging and organization**: tag sessions by topic, project, risk, status, cost, provider, and outcome.

Suggested roadmap order:

1. Universal thread index.
2. Semantic search.
3. Project view.
4. Audit layer.
5. Memory and knowledge graph.
6. Provider switching.
7. Cost and productivity analytics.

Naming note: keep **Session Portal** for the public V1/V2 utility, but evaluate a broader product name such as **AI Workspace**, **Session OS**, **ThreadOS**, **ContextVault**, **Agent Workspace**, or **Operynth Session OS** if the product expands into cross-provider continuity.

## Operating Rule

- Always update this vault when the app changes. Code edits should be reflected in the project overview and app README so the vault remains the source of truth for what exists, how it runs, and what changed.
