"""Read-only full-thread viewer dialog.

Opens a scrollable transcript of a session's messages without resuming it
(no terminal spawned). Rendered from the provider's :meth:`collect_thread`.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..providers.base import MAX_THREAD_CHARS
from ..providers.registry import get_provider


def open_thread_viewer(app, session) -> None:
    provider = get_provider(session.provider)
    if provider is None:
        return
    msgs = provider.collect_thread(session)

    dialog = tk.Toplevel(app.root)
    dialog.title(f"Thread — {session.display or session.id[:8]}")
    dialog.configure(bg=app.bg)
    dialog.transient(app.root)
    dialog.geometry("900x680")

    header = tk.Frame(dialog, bg=app.bar, pady=6, padx=12)
    header.pack(fill=tk.X)
    tk.Label(header, text=f"{session.display or '(untitled)'}", bg=app.bar, fg=app.text,
             font=app._font(2, "bold")).pack(side=tk.LEFT)
    tk.Label(header, text=f"  {len(msgs)} messages  ·  {session.provider}",
             bg=app.bar, fg=app.muted, font=app._font(-1)).pack(side=tk.LEFT, padx=(8, 0))

    body = tk.Frame(dialog, bg=app.bg)
    body.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

    text = tk.Text(
        body, bg=app.surface, fg=app.text, font=app._font(),
        wrap=tk.WORD, relief=tk.FLAT, padx=14, pady=12, state=tk.DISABLED, cursor="arrow",
    )
    vsb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=text.yview)
    text.configure(yscrollcommand=vsb.set)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    text.tag_configure("user_label", foreground=app.green, font=app._font(weight="bold"))
    text.tag_configure("asst_label", foreground=app.blue, font=app._font(weight="bold"))
    text.tag_configure("user", foreground=app.green)
    text.tag_configure("assistant", foreground=app.text)
    text.tag_configure("dim", foreground=app.muted)

    total = 0
    text.config(state=tk.NORMAL)
    if not msgs:
        text.insert(tk.END, "No readable messages found for this session.\n", "dim")
    for m in msgs:
        if m.role == "user":
            text.insert(tk.END, "You\n", "user_label")
            text.insert(tk.END, m.text + "\n\n", "user")
        else:
            label = f"Assistant · {m.model}" if m.model else "Assistant"
            text.insert(tk.END, label + "\n", "asst_label")
            text.insert(tk.END, m.text + "\n\n", "assistant")
        total += len(m.text)
    if total >= MAX_THREAD_CHARS:
        text.insert(tk.END, "— transcript truncated (very large session) —\n", "dim")
    text.see(tk.END)
    text.config(state=tk.DISABLED)

    footer = tk.Frame(dialog, bg=app.bg, pady=6)
    footer.pack(fill=tk.X)
    tk.Button(footer, text="Close", bg=app.overlay, fg=app.text, relief=tk.FLAT,
              padx=16, pady=4, command=dialog.destroy).pack(side=tk.RIGHT)
    dialog.update_idletasks()
    text.config(state=tk.NORMAL)
    text.see(tk.END)
    text.config(state=tk.DISABLED)
    dialog.geometry("900x680")
    dialog.after(50, lambda: text.yview_moveto(1.0))
