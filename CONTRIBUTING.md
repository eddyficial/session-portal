# Contributing To Session Portal

Thanks for helping improve Session Portal. This project is a local-first Windows app for finding, previewing, exporting, cleaning, and resuming AI CLI sessions.

## Development Setup

Clone the repo:

```powershell
git clone https://github.com/eddyficial/session-portal.git
cd session-portal
```

Install runtime and development dependencies:

```powershell
py -3 -m pip install -r .\Codebase\requirements.txt
py -3 -m pip install -r .\requirements-dev.txt
```

Run tests:

```powershell
py -3 -m pytest Codebase\v2\tests -q
```

Run lint:

```powershell
py -3 -m ruff check .
```

Launch the app:

```powershell
pyw .\Codebase\session_portal.pyw
```

## Project Structure

```text
Codebase/session_portal.pyw      No-console launcher
Codebase/v2/                    Current modular app
Codebase/v2/providers/          Provider loaders for AI CLI tools
Codebase/v2/ui/                 Tkinter/customtkinter UI modules
Codebase/v2/tests/              Test suite
App/assets/                     README and social preview screenshots
```

## Provider Contributions

Providers should stay isolated. A new provider should:

- Implement the provider protocol in `Codebase/v2/providers/base.py`.
- Normalize sessions into the shared `Session` model.
- Avoid loading full transcript files during list rendering when metadata is enough.
- Keep delete behavior conservative and recoverable when possible.
- Add tests under `Codebase/v2/tests/test_providers/`.
- Log provider failures without stopping the whole app.

## Pull Requests

Before opening a PR:

- Run `py -3 -m pytest Codebase\v2\tests -q`.
- Run `py -3 -m ruff check .`.
- Add or update tests for provider parsing, resume commands, export behavior, or UI-facing helpers when relevant.
- Update `README.md` when user-facing behavior changes.
- Do not commit local session data, logs, trash, exports, settings, or machine-specific paths.

## Security

Do not paste private session logs, access tokens, local secrets, or user-specific paths into issues or pull requests. See `SECURITY.md` for the security policy.

