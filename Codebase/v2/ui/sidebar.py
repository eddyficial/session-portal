"""Left sidebar builder — branding, provider filter buttons, and actions."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


def build_sidebar(app, parent):
    sidebar = ctk.CTkFrame(parent, fg_color=app.bg_deep, corner_radius=0)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)
    sidebar.configure(width=178)

    ctk.CTkLabel(
        sidebar,
        text="Session\nPortal",
        justify="left",
        text_color=app.text,
        font=app._font(10, "bold"),
    ).pack(anchor="w", padx=18, pady=(20, 8))
    ctk.CTkLabel(
        sidebar,
        text="Local AI Workspace",
        text_color=app.text,
        font=app._font(),
    ).pack(anchor="w", padx=18, pady=(0, 20))

    app.source_buttons_frame = ctk.CTkFrame(sidebar, fg_color=app.bg_deep, corner_radius=0)
    app.source_buttons_frame.pack(fill=tk.X, padx=14)
    app.source_buttons = {}
    app._build_source_buttons()

    ctk.CTkButton(
        sidebar,
        text="Scan Sources",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        font=app._font(1),
        command=app._edit_sources,
    ).pack(fill=tk.X, padx=14, pady=(20, 3))

    ctk.CTkButton(
        sidebar,
        text="Refresh",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        font=app._font(1),
        command=app._load_data,
    ).pack(fill=tk.X, padx=14, pady=3)

    ctk.CTkButton(
        sidebar,
        text="Clean Empty",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.danger,
        text_color=app.text,
        font=app._font(1, "bold"),
        command=app._delete_zero_message_sessions,
    ).pack(fill=tk.X, padx=14, pady=3)

    app.auto_scan_btn = ctk.CTkButton(
        sidebar,
        text="Auto Scan: ON" if app.auto_scan_var.get() else "Auto Scan: OFF",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        font=app._font(1),
        command=app._toggle_auto_scan,
    )
    app.auto_scan_btn.pack(fill=tk.X, padx=14, pady=3)
    app._refresh_auto_scan_button()

    ctk.CTkButton(
        sidebar,
        text="Trash",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        font=app._font(1),
        command=app._open_trash,
    ).pack(fill=tk.X, padx=14, pady=3)

    ctk.CTkButton(
        sidebar,
        text="Compute Costs",
        anchor="w",
        height=34,
        corner_radius=6,
        fg_color=app.surface_2,
        hover_color=app.overlay,
        text_color=app.text,
        font=app._font(1),
        command=app._compute_costs,
    ).pack(fill=tk.X, padx=14, pady=3)

    return sidebar