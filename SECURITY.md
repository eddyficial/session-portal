# Security Policy

## Supported Versions

The `main` branch is the active supported version of Session Portal.

## Reporting A Vulnerability

Please report security issues by opening a private GitHub security advisory when available, or by contacting the repository owner directly.

Do not publish exploit details publicly until the issue has been reviewed.

## Local Data Notice

Session Portal reads local AI session files from the current user's machine. It does not require an API service and does not intentionally upload session data anywhere.

Users should review the source code before running the app, especially because it can resume and delete local session files.
