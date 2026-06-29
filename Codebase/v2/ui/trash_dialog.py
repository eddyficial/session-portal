"""Trash bin dialog — review, restore, or permanently purge trashed sessions."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import trash


def show_trash_dialog(app) -> None:
    dialog = tk.Toplevel(app.root)
    dialog.title("Trash Bin")
    dialog.configure(bg=app.bg)
    dialog.transient(app.root)
    dialog.grab_set()
    dialog.geometry("820x520")

    header = tk.Frame(dialog, bg=app.bg, padx=14, pady=10)
    header.pack(fill=tk.X)
    tk.Label(header, text="Trash Bin", bg=app.bg, fg=app.blue,
             font=app._font(2, "bold")).pack(side=tk.LEFT)
    hint = tk.Label(header, text="", bg=app.bg, fg=app.muted, font=app._font(-1))
    hint.pack(side=tk.LEFT, padx=(10, 0))

    body = tk.Frame(dialog, bg=app.bg, padx=14)
    body.pack(fill=tk.BOTH, expand=True)

    tree = ttk.Treeview(
        body,
        columns=("provider", "display", "project", "trashed_at"),
        show="headings", selectmode="extended",
    )
    tree.heading("provider", text="Provider")
    tree.heading("display", text="Title / Last Prompt")
    tree.heading("project", text="Project")
    tree.heading("trashed_at", text="Trashed")
    tree.column("provider", width=110, anchor=tk.W)
    tree.column("display", width=300, anchor=tk.W)
    tree.column("project", width=230, anchor=tk.W)
    tree.column("trashed_at", width=150, anchor=tk.W)
    vsb = ttk.Scrollbar(body, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def reload():
        for item in tree.get_children():
            tree.delete(item)
        entries = trash.list_trashed()
        for e in entries:
            tree.insert("", tk.END, iid=e["id"],
                        values=(e.get("provider", ""), e.get("display", ""),
                                e.get("project", ""), e.get("trashed_at", "")))
        hint.config(text=f"{len(entries)} trashed session(s)")

    def restore_selected():
        ids = tree.selection()
        if not ids:
            return
        restored = sum(1 for sid in ids if trash.restore_session(sid))
        reload()
        if restored:
            messagebox_info(app, f"Restored {restored} session(s).")

    def purge_selected():
        ids = tree.selection()
        if not ids:
            return
        if not messagebox_askyesno(
                app, "Delete Forever",
                f"Permanently delete {len(ids)} session(s)? This cannot be undone."):
            return
        purged = sum(1 for sid in ids if trash.purge_session(sid))
        reload()
        if purged:
            messagebox_info(app, f"Permanently deleted {purged} session(s).")

    def empty_all():
        entries = trash.list_trashed()
        if not entries:
            return
        if not messagebox_askyesno(
                app, "Empty Trash",
                f"Permanently delete all {len(entries)} trashed session(s)? This cannot be undone."):
            return
        n = trash.empty_trash()
        reload()
        messagebox_info(app, f"Permanently deleted {n} session(s).")

    # Use tk.messagebox through app to keep styling simple.
    from tkinter import messagebox as mb

    def messagebox_info(_app, msg):
        mb.showinfo("Trash", msg, parent=dialog)

    def messagebox_askyesno(_app, title, msg):
        return mb.askyesno(title, msg, icon="warning", parent=dialog)

    footer = tk.Frame(dialog, bg=app.bg, padx=14, pady=10)
    footer.pack(fill=tk.X)
    tk.Button(footer, text="Restore Selected", bg=app.green, fg="#000000",
              relief=tk.FLAT, padx=14, pady=5, command=restore_selected).pack(side=tk.LEFT)
    tk.Button(footer, text="Delete Forever", bg=app.danger, fg="#ffffff",
              relief=tk.FLAT, padx=14, pady=5, command=purge_selected).pack(side=tk.LEFT, padx=(8, 0))
    tk.Button(footer, text="Empty Trash", bg=app.overlay, fg=app.text,
              relief=tk.FLAT, padx=14, pady=5, command=empty_all).pack(side=tk.LEFT, padx=(8, 0))
    tk.Button(footer, text="Close", bg=app.surface_2, fg=app.text,
              relief=tk.FLAT, padx=14, pady=5, command=dialog.destroy).pack(side=tk.RIGHT)

    reload()
    dialog.wait_window()