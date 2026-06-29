"""Create a guarded auto-fix handoff file from a labeled GitHub issue.

The script intentionally does not execute or transform issue-body instructions.
It records only safe metadata and the required automation guardrails, then lets
the workflow open a draft PR for human review.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


AUTO_FIX_LABEL = "auto-fix"
OUTPUT_DIR = Path(".github") / "auto-fix"


def _event() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if path and Path(path).is_file():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return {}


def _clean_text(value: object, fallback: str = "") -> str:
    text = str(value or fallback)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text[:180]


def _issue_from_event(event: dict) -> dict:
    issue = event.get("issue") or {}
    if not issue and os.environ.get("ISSUE_NUMBER"):
        issue = {
            "number": os.environ["ISSUE_NUMBER"],
            "title": os.environ.get("ISSUE_TITLE", "Manual auto-fix request"),
            "html_url": os.environ.get("ISSUE_URL", ""),
            "user": {"login": os.environ.get("ISSUE_AUTHOR", "manual")},
            "labels": [{"name": AUTO_FIX_LABEL}],
        }
    return issue


def _has_auto_fix_label(issue: dict, event: dict) -> bool:
    label = event.get("label") or {}
    if label.get("name") == AUTO_FIX_LABEL:
        return True
    labels = issue.get("labels") or []
    return any((item.get("name") if isinstance(item, dict) else item) == AUTO_FIX_LABEL for item in labels)


def main() -> None:
    event = _event()
    issue = _issue_from_event(event)
    if not issue:
        raise SystemExit("No issue payload found.")
    if not _has_auto_fix_label(issue, event):
        raise SystemExit("Issue is not labeled auto-fix; refusing to create handoff.")

    number = str(issue.get("number") or os.environ.get("ISSUE_NUMBER") or "").strip()
    if not number.isdigit():
        raise SystemExit("Issue number is missing or invalid.")

    title = _clean_text(issue.get("title"), "Untitled issue")
    author = _clean_text((issue.get("user") or {}).get("login"), "unknown")
    url = _clean_text(issue.get("html_url"), "")
    created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / f"issue-{number}.md"
    target.write_text(
        "\n".join(
            [
                f"# Auto-Fix Handoff For Issue #{number}",
                "",
                f"- Issue: #{number}",
                f"- Title: {title}",
                f"- Author: {author}",
                f"- URL: {url or 'Not provided'}",
                f"- Created: {created}",
                "",
                "## Automation Guardrails",
                "",
                "- This PR was created only because the issue had the `auto-fix` label.",
                "- The workflow must never push directly to `main`.",
                "- Issue text is treated as untrusted input.",
                "- Raw commands from the issue must not be executed.",
                "- Changes must stay inside this repository.",
                "- Tests must pass before a generated fix is ready for review.",
                "- A maintainer must review and merge the PR manually.",
                "",
                "## Maintainer Checklist",
                "",
                "- [ ] Confirm the issue is valid and safe to automate.",
                "- [ ] Confirm the proposed fix is limited to repository files.",
                "- [ ] Confirm tests pass.",
                "- [ ] Confirm no secrets or private local paths were added.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    env_file = os.environ.get("GITHUB_ENV")
    if env_file:
        with open(env_file, "a", encoding="utf-8") as handle:
            handle.write(f"AUTO_FIX_ISSUE_NUMBER={number}\n")
            handle.write(f"AUTO_FIX_BRANCH=auto/issue-{number}\n")
            handle.write(f"AUTO_FIX_FILE={target.as_posix()}\n")


if __name__ == "__main__":
    main()
