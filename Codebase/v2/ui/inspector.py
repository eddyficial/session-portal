"""Right inspector builder — metadata preview and action buttons."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from tkinter import ttk

from .tooltips import add_tooltip


def build_inspector(app, parent):
    right = tk.Frame(parent, bg=app.bg)
    parent.add(right, width=360, minsize=320)

    preview_header = tk.Frame(right, bg=app.bg, pady=4)
    preview_header.pack(fill=tk.X)
    tk.Label(preview_header, text="Inspector", bg=app.bg, fg=app.blue,
             font=app._font(1, "bold")).pack(side=tk.LEFT)
    tk.Label(preview_header, text="Metadata and first/last prompt.", bg=app.bg,
             fg=app.text, font=app._font(-1)).pack(side=tk.LEFT, padx=(10, 0))
    add_tooltip(preview_header, "Shows metadata, token counts, and the first and last prompt for the selected session.")

    preview_frame = tk.Frame(right, bg=app.surface)
    preview_frame.pack(fill=tk.BOTH, expand=True)

    app.preview = tk.Text(
        preview_frame,
        bg=app.surface,
        fg=app.text,
        font=app._font(),
        wrap=tk.WORD,
        relief=tk.FLAT,
        padx=12,
        pady=10,
        state=tk.DISABLED,
        cursor="arrow",
    )
    preview_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=app.preview.yview)
    app.preview.configure(yscrollcommand=preview_scrollbar.set)
    app.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    add_tooltip(app.preview, "Read-only preview of the selected session. Use View Thread for a longer transcript view.")
    app.preview.tag_configure("label", foreground=app.blue, font=app._font(weight="bold"))
    app.preview.tag_configure("dim", foreground=app.muted)
    app.preview.tag_configure("message", foreground=app.green)
    app.preview.tag_configure("codex", foreground=app.yellow)
    app.preview.tag_configure("grok", foreground=app.pink)
    app.preview.tag_configure("copilot", foreground=app.purple)

    btn_frame = ctk.CTkFrame(right, fg_color=app.bg, corner_radius=0)
    btn_frame.pack(fill=tk.X, pady=(6, 8))
    for col in range(2):
        btn_frame.grid_columnconfigure(col, weight=1, uniform="inspector_actions")

    app.rename_btn = ctk.CTkButton(
        btn_frame,
        text="Rename",
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        text_color_disabled="#f2f5ff",
        font=app._font(weight="bold"),
        corner_radius=6,
        height=38,
        command=app._rename_session,
        state=tk.DISABLED,
    )
    app.rename_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))
    add_tooltip(app.rename_btn, "Give this session a local display name. This does not rename provider files.")
    app.thread_btn = ctk.CTkButton(
        btn_frame,
        text="View Thread",
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        text_color_disabled="#f2f5ff",
        font=app._font(weight="bold"),
        corner_radius=6,
        height=38,
        command=app._view_thread,
        state=tk.DISABLED,
    )
    app.thread_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))
    add_tooltip(app.thread_btn, "Open a read-only transcript view for the selected session.")
    app.audit_btn = ctk.CTkButton(
        btn_frame,
        text="Export Thread",
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        text_color_disabled="#f2f5ff",
        font=app._font(weight="bold"),
        corner_radius=6,
        height=38,
        command=app._save_audit,
        state=tk.DISABLED,
    )
    app.audit_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(0, 6))
    add_tooltip(app.audit_btn, "Export the selected thread to a Markdown file for review or audit records.")
    app.delete_btn = ctk.CTkButton(
        btn_frame,
        text="Delete",
        fg_color=app.danger,
        hover_color="#ff7a90",
        text_color="#ffffff",
        text_color_disabled="#ffffff",
        font=app._font(weight="bold"),
        corner_radius=6,
        height=38,
        command=app._enter_delete_mode,
        state=tk.DISABLED,
    )
    app.delete_btn.grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(0, 6))
    add_tooltip(app.delete_btn, "Move the selected session to Session Portal trash after confirmation.")
    app.action_btn = ctk.CTkButton(
        btn_frame,
        text="Resume Session",
        fg_color=app.green,
        hover_color="#c8f7c5",
        text_color="#000000",
        text_color_disabled="#000000",
        font=app._font(1, "bold"),
        corner_radius=6,
        height=40,
        command=app._on_action,
        state=tk.DISABLED,
    )
    app.action_btn.grid(row=2, column=0, columnspan=2, sticky="ew")
    add_tooltip(app.action_btn, "Resume the selected terminal chat session in its recorded working folder.")

    return right
