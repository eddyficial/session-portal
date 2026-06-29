"""Session Portal v2 entrypoint."""
from __future__ import annotations

import ctypes
import sys
import tkinter as tk

from .config import APP_USER_MODEL_ID
from .logging_setup import configure_logging, get_logger
from .ui.app import SessionPortalApp


def apply_windows_app_identity() -> None:
    """Give Windows a stable taskbar identity for the Python-hosted app."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        # Icon setup should never prevent the app itself from opening.
        return


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    try:
        logger.info("Starting Session Portal v2")
        apply_windows_app_identity()
        root = tk.Tk()
        root.withdraw()
        SessionPortalApp(root)
        root.mainloop()
    except Exception:
        logger.exception("Session Portal crashed")
        raise


if __name__ == "__main__":
    main()
