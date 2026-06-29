# Session Portal

Session Portal is a local Windows desktop app for finding, previewing, exporting, cleaning, and resuming AI CLI sessions from one place.

It scans the current user's machine for supported AI coding tools, shows only resumable sessions, and opens selected sessions back in their recorded working folder.

![Session Portal logo](Codebase/v2/assets/logo_256.png)

## Supported Providers

Session Portal currently supports resumable sessions from:

- Claude Code
- Codex
- Grok CLI
- GitHub Copilot CLI
- AMP CLI

It also detects other local AI tools during onboarding, but only tools with implemented session loaders appear in the main session list.

## Why Use It

AI coding sessions often end up scattered across local JSONL files, CLI state folders, and provider-specific history stores. Session Portal gives you one local dashboard to:

- Find old AI sessions by project, title, date, provider, or prompt text
- Preview metadata, first prompt, last prompt, token counts, and message counts
- Resume a session in the folder where it originally ran
- View a read-only transcript before resuming
- Export a Markdown copy of a thread for review or audit records
- Rename sessions locally without changing provider files
- Move supported local sessions to a recoverable Trash
- Hide AMP threads locally without calling AMP's permanent server delete
- Clean currently shown empty sessions

## Privacy Model

Session Portal is local-first.

- No API service is required.
- No background server is started.
- Session data is read from the current user's local machine.
- Exported threads, local settings, rename files, logs, and trash data are ignored by git.
- Resume actions open local terminal commands for the selected provider.

Review the code before running it, especially because the app can resume and delete local session files.

## Requirements

- Windows
- Python 3
- Git
- Optional: the AI CLI tools you want Session Portal to detect and resume

Python dependencies are listed in:

```text
Codebase/requirements.txt
```

At the moment the app depends on:

```text
customtkinter>=6.0.0
```

## Install

Clone the repo:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Install dependencies and create a Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After installation, launch **Session Portal** from the Desktop shortcut.

Path examples use placeholders such as:

```text
C:\Users\<your-username>\session-portal
```

Replace `<your-username>` with your Windows username if you prefer absolute paths.

## Launch

Use the Desktop shortcut, or run:

```powershell
pyw .\Codebase\session_portal.pyw
```

You can also use:

```powershell
py -3 .\Codebase\session_portal.py
```

The `.pyw` launcher is preferred for normal use because it starts the app without opening an extra console window.

The Desktop shortcut uses the bundled Session Portal icon and app identity so Windows shows Session Portal in the taskbar instead of generic Python.

## Update

From the cloned repo folder:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipDependencies
```

If dependencies changed, run the full installer again:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Uninstall

Remove the Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

To also remove Session Portal's local app data inside the cloned repo:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1 -RemoveLocalData
```

Then delete the cloned `session-portal` folder if you no longer want the app.

This does not delete your Claude Code, Codex, Grok, Copilot, or AMP installation folders.

## First Launch

1. Launch Session Portal.
2. Choose the providers you want the app to scan.
3. Keep detected providers checked if you want their sessions listed.
4. Click **Save**.

You can reopen provider selection later with **Scan Sources**.

## Main Screen

The table shows one resumable session per row.

Columns:

- `#`: row number in the current filtered and sorted list
- `LLM`: provider plus recorded model, such as `Claude Code / glm-5.2`
- `Project`: folder name where the session ran
- `Date`: last known session activity
- `Msgs`: useful human message count
- `Thread / Last Prompt`: title, thread name, or useful prompt text

Click a row to inspect it. Double-click a row or press `Enter` to resume it.

## Search, Filter, And Sort

Use the search box to filter by project, title, or prompt text.

Use **Dates** to select a calendar date range. Leave either side as **Any** for an open-ended range.

Use the left sidebar to filter by provider:

- All Models
- AMP
- Claude Code
- Codex
- Copilot
- Grok

Use the sort menu or click table headers to sort by:

- Newest
- Oldest
- LLM A-Z / Z-A
- Project A-Z / Z-A
- Msgs Low-High / High-Low
- Prompt A-Z / Z-A

## Resume A Session

1. Select a row.
2. Check the right inspector to confirm the session.
3. Click the green resume button.

Session Portal opens a maximized terminal in the recorded working directory and runs the provider's resume command.

If the recorded folder is missing, the app falls back to the current user's home folder when possible.

## View A Thread

1. Select a row.
2. Click **View Thread**.
3. Read the transcript in the popup.
4. Click **Close** when finished.

The thread viewer is read-only and keeps large session rendering bounded so the app stays responsive.

## Export A Thread

Use **Export Thread** when you want a Markdown copy of a session for review, handoff, or audit records.

1. Select a row.
2. Click **Export Thread**.
3. Choose a folder and filename in the Save As dialog.
4. Click **Save**.

The export includes metadata and a readable transcript. It does not modify provider session files.

## Rename A Session

1. Select a row.
2. Click **Rename**.
3. Type a local display name.
4. Click **OK**.

Renames are saved locally in:

```text
Codebase/v2/renames.json
```

They do not modify provider session files. To clear a rename, open **Rename**, empty the field, and click **OK**.

## Delete, Trash, And Clean Empty

Session Portal uses a recoverable Trash for supported local provider files.

To delete:

1. Select a row and click **Delete**, or right-click a row.
2. In delete mode, select one or more rows.
3. Click **Delete Selected**.
4. Confirm the warning dialog.

Open **Trash** to restore deleted local sessions, delete selected trashed sessions forever, or empty the whole Trash.

Use **Clean Empty** to move currently shown sessions with `0` useful messages to Trash. This respects the current provider, search, and date filters.

AMP rows are different. When an AMP row is selected, the app labels the action as **Hide AMP Row**. That hides the row only inside Session Portal by saving the thread ID in `Codebase/v2/hidden_sessions.json`. It does not call `amp threads delete`, because AMP threads are server-backed and provider deletion is permanent.

## Refresh And Auto Scan

- **Refresh** reloads session data immediately.
- **Auto Scan** checks for new supported sessions every 60 seconds while the app is open.
- **Scan Sources** reopens provider selection.

Use Refresh when you just created, renamed, deleted, or resumed a session and want the list updated now.

## Compute Costs

**Compute Costs** estimates cost only when token usage is available in session files. It runs on demand so normal browsing stays fast.

Cost estimates are approximate and provider/model pricing can change.

## Keyboard Shortcuts

- `Enter`: resume selected session
- Double-click: resume selected session
- `R`: refresh sessions
- `Q`: quit
- `Esc`: leave delete mode

## Local Files

Session Portal stores local app data under the cloned repo:

```text
Codebase/v2/settings.json
Codebase/v2/renames.json
Codebase/v2/hidden_sessions.json
Codebase/v2/audits/
Codebase/v2/.trash/
Codebase/v2/session_portal.log
```

These files are user-specific and ignored by git.

The rotating error log records startup crashes, provider scan failures, failed CLI calls, resume failures, export failures, rename-save failures, and trash/restore problems.

## Project Layout

```text
App/                         Public app README and project notes
Codebase/
  requirements.txt           Python dependencies
  session_portal.py          Console launcher
  session_portal.pyw         No-console launcher
  v2/                        Modular app package
  legacy/session_portal_v1.py Legacy rollback reference
install.ps1                  Dependency install + Desktop shortcut
install_desktop_shortcut.ps1 Shortcut installer
uninstall_desktop_shortcut.ps1 Shortcut/local-data uninstall helper
launch_session_portal.bat    Repo-folder launcher
SECURITY.md                  Security policy
```

## Development

Run tests from the repo root:

```powershell
py -3 -m pytest Codebase\v2\tests -q
```

The V2 app is organized into focused modules:

- providers
- session aggregation
- storage
- resume launch logic
- trash/recovery
- thread export
- UI builders

Provider failures are isolated and logged so one broken provider or corrupt session file does not prevent the rest of the app from loading.

AMP is intentionally optimized for normal browsing: refresh, preview, and search use `amp threads list --json` metadata. Session Portal only calls `amp threads markdown <id>` when the user opens **View Thread** or **Export Thread** for one selected AMP thread.

## Guarded Auto-Fix Workflow

Session Portal includes a conservative GitHub issue automation path.

Use it like this:

1. Open or review a GitHub issue.
2. Confirm the issue is safe and reproducible.
3. Add the `auto-fix` label only when automation is allowed.
4. GitHub Actions creates a branch named `auto/issue-<number>`.
5. The workflow writes a guarded handoff file under `.github/auto-fix/`.
6. The workflow runs the test suite.
7. The workflow opens a draft pull request.
8. A maintainer reviews the PR before merge.

Guardrails:

- The workflow never pushes directly to `main`.
- The workflow only runs from an explicit `auto-fix` label or manual workflow dispatch.
- Issue text is treated as untrusted input.
- Raw commands from issue text must not be executed.
- Automation changes must stay inside this repository.
- Tests must pass before the generated PR is ready for review.
- Any future AI/API token must live in GitHub Secrets, never in the repo.

## Security

See [SECURITY.md](SECURITY.md).

In short: Session Portal is a local desktop utility. It does not intentionally upload session contents. Delete, export, and resume actions are explicit user actions.
