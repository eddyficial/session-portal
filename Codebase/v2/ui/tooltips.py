"""Small hover tooltips for Tk and CustomTkinter widgets."""
from __future__ import annotations

import tkinter as tk


class Tooltip:
    def __init__(self, widget, text: str, *, delay_ms: int = 500):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self):
        if self._tip or not self.text:
            return
        try:
            x = self.widget.winfo_pointerx() + 14
            y = self.widget.winfo_pointery() + 18
        except tk.TclError:
            return

        tip = tk.Toplevel(self.widget)
        tip.wm_overrideredirect(True)
        tip.configure(bg="#303452")
        try:
            tip.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        label = tk.Label(
            tip,
            text=self.text,
            justify=tk.LEFT,
            bg="#11111b",
            fg="#ffffff",
            activebackground="#11111b",
            activeforeground="#ffffff",
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=6,
            wraplength=320,
            font=("Consolas", 9),
        )
        label.pack()
        tip.update_idletasks()
        width = tip.winfo_reqwidth()
        height = tip.winfo_reqheight()
        screen_w = self.widget.winfo_screenwidth()
        screen_h = self.widget.winfo_screenheight()
        margin = 8
        if x + width + margin > screen_w:
            x = max(margin, self.widget.winfo_pointerx() - width - 14)
        if y + height + margin > screen_h:
            y = max(margin, self.widget.winfo_pointery() - height - 14)
        x = max(margin, min(x, screen_w - width - margin))
        y = max(margin, min(y, screen_h - height - margin))
        tip.wm_geometry(f"+{x}+{y}")
        tip.lift()
        self._tip = tip

    def _hide(self, _event=None):
        self._cancel()
        if self._tip:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None


def add_tooltip(widget, text: str):
    Tooltip(widget, text)
    return widget
