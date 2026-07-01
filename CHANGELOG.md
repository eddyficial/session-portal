# Changelog

All notable changes to Session Portal will be documented here.

This project uses public GitHub releases for packaged ZIP downloads.

## Unreleased

### Added

- Contributor guide.
- Pull request template.
- Code of conduct.
- Development dependency manifest.
- Ruff lint configuration.
- CI lint step.
- CI coverage XML artifact.
- CI packaged ZIP smoke test.
- GitHub Actions release packaging workflow.
- Visible app version in the sidebar.
- Release checksum asset for the packaged ZIP.

## v1.0.0 - 2026-07-01

### Added

- First packaged public release.
- Local-first Windows desktop app for AI CLI session management.
- Provider support for Claude Code, Codex, GitHub Copilot CLI, Grok CLI, and AMP CLI.
- Provider filters, search, date filtering, sortable columns, and message counts.
- Inspector preview with metadata, first message, last message, token counts, and cost estimates when available.
- Read-only thread viewer for reviewing longer transcripts before resuming.
- Markdown thread export with user-selected save location.
- Resume launch in the session's recorded working folder.
- Recoverable Trash for supported local providers.
- Local hide behavior for AMP rows instead of permanent server-side deletion.
- Clean Empty action for currently shown zero-message sessions.
- Auto Scan for newly available sessions.
- Desktop shortcut installer and uninstaller.
- GitHub Actions test workflow.
- Guarded auto-fix draft PR workflow.

### Security

- Local app data, exports, logs, rename files, hidden session files, and trash data are ignored by git.
- Public screenshots use synthetic demo data.
