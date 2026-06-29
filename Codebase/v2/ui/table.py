"""Session table builder — the numbered, filtered, sorted Treeview."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .tooltips import add_tooltip


def build_table(app, parent):
    list_frame = tk.Frame(parent, bg=app.bg)
    app.list_frame = list_frame
    parent.add(list_frame, width=1320, minsize=900)

    list_header = tk.Frame(list_frame, bg=app.bg, pady=4)
    list_header.pack(fill=tk.X)
    tk.Label(
        list_header,
        text="Threads",
        bg=app.bg,
        fg=app.blue,
        font=app._font(1, "bold"),
    ).pack(side=tk.LEFT)
    tk.Label(
        list_header,
        text="Numbered, filtered, and sorted.",
        bg=app.bg,
        fg=app.text,
        font=app._font(-1),
    ).pack(side=tk.LEFT, padx=(10, 0))
    add_tooltip(list_header, "This table lists resumable AI sessions. Click a row to inspect it; double-click or press Enter to resume.")

    app.tree = ttk.Treeview(
        list_frame,
        columns=("check", "number", "source", "project", "date", "messages", "preview"),
        show="headings",
        selectmode="browse",
    )
    app.tree.heading("check", text="", anchor=tk.W)
    app.tree.heading("number", text="#", anchor=tk.E,
                     command=lambda: app._toggle_sort("Oldest", "Newest"))
    app.tree.heading("source", text="LLM", anchor=tk.W,
                     command=lambda: app._toggle_sort("LLM A-Z", "LLM Z-A"))
    app.tree.heading("project", text="Project", anchor=tk.W,
                     command=lambda: app._toggle_sort("Project A-Z", "Project Z-A"))
    app.tree.heading("date", text="Date", anchor=tk.W,
                     command=lambda: app._toggle_sort("Oldest", "Newest"))
    app.tree.heading("messages", text="Msgs", anchor=tk.E,
                     command=lambda: app._toggle_sort("Msgs Low-High", "Msgs High-Low"))
    app.tree.heading("preview", text="    Thread / Last Prompt", anchor=tk.W,
                     command=lambda: app._toggle_sort("Prompt A-Z", "Prompt Z-A"))
    app.tree.column("check", width=0, minwidth=0, stretch=False, anchor=tk.W)
    app.tree.column("number", width=42, minwidth=38, stretch=False, anchor=tk.E)
    app.tree.column("source", width=230, minwidth=180, stretch=False, anchor=tk.W)
    app.tree.column("project", width=250, minwidth=160, stretch=False, anchor=tk.W)
    app.tree.column("date", width=165, minwidth=150, stretch=False, anchor=tk.W)
    app.tree.column("messages", width=64, minwidth=56, stretch=False, anchor=tk.E)
    app.tree.column("preview", width=856, minwidth=420, stretch=False, anchor=tk.W)

    vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=app.tree.yview)
    hsb = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=app.tree.xview)
    app.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    app.tree.tag_configure("gone", foreground=app.muted)
    app.tree.tag_configure("codex", foreground=app.yellow)
    app.tree.tag_configure("grok", foreground=app.pink)
    app.tree.tag_configure("copilot", foreground=app.purple)
    app.tree.tag_configure("amp", foreground=app.blue)
    hsb.pack(side=tk.BOTTOM, fill=tk.X)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    app.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    app.tree.bind("<<TreeviewSelect>>", app._on_select)
    app.tree.bind("<Button-1>", app._on_tree_click)
    app.tree.bind("<Double-1>", app._on_action)
    app.tree.bind("<Return>", app._on_action)
    app.tree.bind("<Button-3>", app._on_right_click)
    add_tooltip(
        app.tree,
        "Click a session to preview it. Column headers sort the list. Double-click or press Enter to resume the selected session.",
    )

    return list_frame
