"""Left sidebar builder — branding, provider filter buttons, and actions."""
from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from PIL import Image

from ..config import APP_ICON_PNG
from .tooltips import add_tooltip


def build_sidebar(app, parent):
    sidebar = ctk.CTkFrame(parent, fg_color=app.bg_deep, corner_radius=0)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)
    sidebar.configure(width=178)

    brand = ctk.CTkFrame(sidebar, fg_color=app.bg_deep, corner_radius=0)
    brand.pack(fill=tk.X, padx=14, pady=(18, 8))
    if APP_ICON_PNG.exists():
        try:
            app.sidebar_logo_image = ctk.CTkImage(
                light_image=Image.open(APP_ICON_PNG),
                dark_image=Image.open(APP_ICON_PNG),
                size=(38, 38),
            )
            ctk.CTkLabel(brand, image=app.sidebar_logo_image, text="").pack(side=tk.LEFT, padx=(0, 10))
        except OSError:
            app.sidebar_logo_image = None
    ctk.CTkLabel(
        brand,
        text="Session\nPortal",
        justify="left",
        text_color=app.text,
        font=app._font(10, "bold"),
    ).pack(side=tk.LEFT)
    add_tooltip(brand, "Session Portal helps you find, inspect, and resume local AI terminal sessions.")
    subtitle = ctk.CTkLabel(
        sidebar,
        text="Resume Your Sessions",
        text_color=app.text,
        font=app._font(),
    )
    subtitle.pack(anchor="center", fill=tk.X, padx=14, pady=(0, 20))
    add_tooltip(subtitle, "Select a saved session, inspect it, then resume it in its original working folder.")

    app.source_buttons_frame = ctk.CTkFrame(sidebar, fg_color=app.bg_deep, corner_radius=0)
    app.source_buttons_frame.pack(fill=tk.X, padx=14)
    app.source_buttons = {}
    app._build_source_buttons()

    scan_btn = ctk.CTkButton(
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
    )
    scan_btn.pack(fill=tk.X, padx=14, pady=(20, 3))
    add_tooltip(scan_btn, "Choose which supported local AI tools Session Portal should scan.")

    refresh_btn = ctk.CTkButton(
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
    )
    refresh_btn.pack(fill=tk.X, padx=14, pady=3)
    add_tooltip(refresh_btn, "Rescan local session files immediately.")

    clean_btn = ctk.CTkButton(
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
    )
    clean_btn.pack(fill=tk.X, padx=14, pady=3)
    add_tooltip(clean_btn, "Delete currently shown sessions with zero messages after confirmation.")

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
    add_tooltip(app.auto_scan_btn, "Toggle automatic rescans for newly created or changed sessions.")

    trash_btn = ctk.CTkButton(
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
    )
    trash_btn.pack(fill=tk.X, padx=14, pady=3)
    add_tooltip(trash_btn, "Open recoverable deleted sessions. Restore or permanently purge from there.")

    cost_btn = ctk.CTkButton(
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
    )
    cost_btn.pack(fill=tk.X, padx=14, pady=3)
    add_tooltip(cost_btn, "Estimate token costs for sessions with recorded token usage. No network call is made.")

    return sidebar
