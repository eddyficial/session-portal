# Session Portal

Session Portal is a local Windows desktop app for browsing, previewing, renaming, deleting, and resuming AI coding sessions on the current user's machine.

The app discovers supported resumable sessions dynamically from the signed-in user's home directory:

- Claude: `%USERPROFILE%\.claude`
- Codex: `%USERPROFILE%\.codex`
- Grok: `%USERPROFILE%\.grok`

No API service is required. Session Portal reads local session files and opens resumable sessions in their recorded working directories.
If a session does not have a valid recorded working directory, Session Portal falls back to the current user's home folder.

Onboarding also checks for other common local AI tools, such as Cursor, Windsurf, Gemini CLI, Continue, Aider, Ollama, and LM Studio. Those tools are listed when found, but Session Portal only shows resumable session rows for providers with implemented session loaders.

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

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
```

Optional: create a desktop shortcut for easier future launches:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_desktop_shortcut.ps1
```

## Run

Use the no-console launcher:

```powershell
pyw .\Codebase\session_portal.pyw
```

Or run the main script:

```powershell
py -3 .\Codebase\session_portal.py
```

## Features

- First-run source selection for local session providers
- Dynamic source discovery based on the current user's installed tools and session folders
- Sidebar filters are generated from enabled/detected supported providers
- Search by project or prompt/title
- Filter by All Models, Claude, Codex, or Grok
- Sort by newest, oldest, and project name
- Preview session metadata plus first/last prompts
- Resume sessions in their original working directory with the terminal opened maximized
- Rename sessions locally
- Delete selected sessions

## Local App Data

Session Portal stores local preferences next to the app:

- `Codebase/settings.json`
- `Codebase/renames.json`

These files are ignored by Git because they are user-specific.

## Notes

- Only resumable sessions are shown.
- Theme switching and model inventory views are intentionally omitted to keep the app focused and fast.
- The app is currently designed for Windows.
