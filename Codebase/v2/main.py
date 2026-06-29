"""Session Portal v2 entrypoint."""
from __future__ import annotations

import tkinter as tk

from .ui.app import SessionPortalApp


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    SessionPortalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()