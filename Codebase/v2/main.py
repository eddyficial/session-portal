"""Session Portal v2 entrypoint."""
from __future__ import annotations

import tkinter as tk

from .logging_setup import configure_logging, get_logger
from .ui.app import SessionPortalApp


def main() -> None:
    configure_logging()
    logger = get_logger(__name__)
    try:
        logger.info("Starting Session Portal v2")
        root = tk.Tk()
        root.withdraw()
        SessionPortalApp(root)
        root.mainloop()
    except Exception:
        logger.exception("Session Portal crashed")
        raise


if __name__ == "__main__":
    main()
