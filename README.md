# Session Portal

Session Portal is a local Windows desktop app for browsing, previewing, renaming, deleting, and resuming AI coding sessions on the current user's machine.

The app discovers supported resumable sessions dynamically from the signed-in user's home directory:

- Claude Code: `%USERPROFILE%\.claude`
- Codex: `%USERPROFILE%\.codex`
- Grok: `%USERPROFILE%\.grok`
- GitHub Copilot CLI: `%USERPROFILE%\.copilot`

No API service is required. Session Portal reads local session files and opens resumable sessions in their recorded working directories.
If a session does not have a valid recorded working directory, Session Portal falls back to the current user's home folder.

Onboarding also checks for other common local AI tools, such as Cursor, Windsurf, Gemini CLI, Continue, Aider, Ollama, and LM Studio. Those tools are listed when found, but Session Portal only shows resumable session rows for providers with implemented session loaders.

## Terminology

- **Session**: a resumable local conversation or work state. Each row in the app is a session.
- **Thread**: the conversation title or prompt shown for a session.
- **LLM**: the local harness plus the specific language model recorded in the session file, such as `Claude Code / glm-5.2`, `Codex / gpt-5.5`, or `Grok / grok-composer-2.5-fast`. If the session did not record one, Session Portal shows the harness with `Unknown`.
- **Provider**: the local tool or harness that created the session, such as Claude Code, Codex, Grok, or GitHub Copilot CLI.

## Install

Clone the repo and run commands from the repo root:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Path examples in this README use `%USERPROFILE%` or placeholders such as `<your-username>`. Replace placeholders with your own Windows user folder if you prefer absolute paths. For example:

```text
C:\Users\<your-username>\session-portal
```

Install dependencies and create a Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After this, launch Session Portal from the Desktop shortcut named **Session Portal**.

If you only want to install dependencies without creating a shortcut:

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
```

If you only want to recreate the Desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_desktop_shortcut.ps1
```

## Uninstall

Session Portal is portable. To uninstall it, delete the cloned `session-portal` folder.

If you created the desktop shortcut, remove it with:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1
```

To also remove local Session Portal preferences from the cloned folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_desktop_shortcut.ps1 -RemoveLocalData
```

This does not delete Claude Code, Codex, Grok, Copilot, or any AI session folders under `%USERPROFILE%`.

## Run

Use the no-console launcher:

```powershell
pyw .\Codebase\session_portal.pyw
```

Or double-click:

```text
launch_session_portal.bat
```

Or run the main script:

```powershell
py -3 .\Codebase\session_portal.py
```

## First Launch

1. Start the app with `pyw .\Codebase\session_portal.pyw`.
2. Choose which providers Session Portal should scan.
3. Leave detected providers checked if you want their sessions in the app.
4. Click **Save**.

You can reopen this provider selection later with **Scan Sources** in the left sidebar.

## How To Use

### Browse Sessions

Each row in the table is one resumable session. The table shows:

- `#`: row number in the current filtered/sorted list
- `LLM`: harness plus recorded model, or harness plus `Unknown` when the session did not record a model
- `Project`: folder name where the session was originally run
- `Date`: last known session activity
- `Msgs`: useful human message count found in the session
- `Thread / Last Prompt`: generated title, thread name, or first useful prompt

Click a row once to show details in the right inspector.

### Search

Use the search box at the top to prefilter sessions by project name, title, or prompt text. When the box is empty, it shows the hint `Start typing to prefilter by project, title, or prompt`.

Clear the search box to return to the full list.

### Date Range

Use the **Dates** calendar button to show sessions from a specific period.

1. Click **Dates: Any**.
2. Choose a **From** date and a **To** date from the popup calendar controls.
3. Leave either side as **Any** for an open-ended range.
4. Click **Clear Dates** in the popup to remove the date filter.

The date range uses each session's last known activity date. The top button shows **Dates: Custom** when a date filter is active.

### Filter By Provider

Use the left sidebar buttons:

- **All Models** shows every discovered resumable session.
- **Claude Code**, **Codex**, **Grok**, and **Copilot** show only that provider when available.

Provider buttons appear only when the provider is enabled and detected, or when that provider already has sessions loaded.

### Sort

Use the sort menu in the top-right, or click table headers.

Available sorts:

- Newest
- Oldest
- LLM A-Z
- LLM Z-A
- Project A-Z
- Project Z-A
- Prompt A-Z
- Prompt Z-A

### Preview A Session

Select any row. The right inspector shows:

- LLM
- Provider
- Title when available
- Project path
- Session ID
- Date
- Message count
- Token count when available
- First and last useful prompt

Long previews have their own scrollbar.

### Resume A Session

1. Select a session row.
2. Check the inspector on the right to confirm it is the session you want.
3. Click the green resume button at the bottom right. The button label changes based on the selected provider, such as **Resume Claude Code**, **Resume Codex**, **Resume Grok**, or **Resume Copilot**.
4. Session Portal opens a maximized terminal in the recorded working directory and runs the provider's resume command.

You can also double-click a row or press `Enter`.

If the recorded working directory no longer exists, the app falls back to the current user's home folder when possible.

### Rename A Session

1. Select a row.
2. Click **Rename** at the bottom of the inspector panel.
3. Enter a new display name in the popup.
4. Click **OK** to save it.

The new name appears in the table's `Thread / Last Prompt` column and helps you recognize the session later.

To remove a custom name:

1. Select the renamed row.
2. Click **Rename**.
3. Clear the text box.
4. Click **OK**.

The original title or prompt will show again.

Renames are saved locally in `Codebase/renames.json`. They do not modify the provider's original session file.

### Delete Sessions

Deleting removes the local session records used by the provider. This cannot be undone.

To delete one session:

1. Select a row.
2. Click **Delete**.
3. Confirm delete mode opens with that row selected.
4. Click **Delete 1 Selected**.
5. Confirm the warning dialog.

To delete multiple sessions:

1. Click **Delete** or right-click a row and choose a delete option.
2. In delete mode, click rows to select or unselect them.
3. Use **Select All** if you want every currently shown row.
4. Click **Delete N Selected**.
5. Confirm the warning dialog.

Press `Esc` or click **Cancel** to leave delete mode without deleting.

### Clean Empty Sessions

Use **Clean Empty Msgs** in the left sidebar to clear sessions that show `0` in the `Msgs` column.

1. Apply any search, provider, or date filters you want.
2. Click **Clean Empty Msgs**.
3. Review the confirmation dialog.
4. Confirm only if you want to permanently delete every currently shown session with `0` messages.

The cleanup respects the current filters. For example, if the sidebar is filtered to **Claude Code**, it only targets shown Claude Code rows with `0` messages.

### Refresh And Auto Scan

- **Refresh** manually reloads provider/session data.
- **Auto Scan: ON** reloads discovery every 60 seconds while the app is open.
- Click **Auto Scan: ON/OFF** to toggle automatic scanning.

Auto Scan is useful when you create a new Claude Code, Codex, Grok, or Copilot session while Session Portal is already open.

Use **Refresh** when:

- You just created or resumed a session and want it to appear immediately.
- You changed provider choices with **Scan Sources**.
- A session title, rename, or delete does not appear updated yet.
- You turned Auto Scan off and want a manual update.

Use **Auto Scan** when:

- You want Session Portal to keep checking for new supported sessions in the background.
- You are actively working in Claude Code, Codex, Grok, or Copilot while Session Portal stays open.
- You do not want to restart the app just to see newly created sessions.

### Keyboard Shortcuts

- `Enter`: resume the selected terminal chat session
- Double-click: resume the selected terminal chat session
- `r`: refresh sessions
- `q`: quit
- `Esc`: cancel delete mode

## Features

- First-run provider selection for local session providers
- Dynamic provider discovery based on the current user's installed tools and session folders
- Sidebar filters are generated from enabled/detected supported providers
- Search by project or prompt/title
- Filter by activity date range
- Filter by All Models, Claude Code, Codex, Grok, or Copilot
- Sort by newest, oldest, LLM name, project, or prompt/title
- Show message counts in the `Msgs` column and sort by message count
- Auto Scan refreshes supported provider/session discovery while the app is open
- Preview session metadata plus first/last prompts
- Scroll long inspector previews independently in the right panel
- Resume sessions in their original working directory with the terminal opened maximized
- Rename sessions locally
- Delete selected sessions
- Clean currently shown empty sessions after confirmation

## Local App Data

Session Portal stores local preferences next to the app:

- `Codebase/settings.json`
- `Codebase/renames.json`

These files are ignored by Git because they are user-specific.

## Notes

- Only resumable sessions are shown.
- Theme switching and model inventory views are intentionally omitted to keep the app focused and fast.
- The app is currently designed for Windows.
