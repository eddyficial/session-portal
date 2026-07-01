"""Scan Sources / onboarding dialog builder.

Mirrors v1's onboarding modal: per-provider checkboxes with found/not-found
status, plus a read-only list of other detected local AI tools.
"""
from __future__ import annotations

import tkinter as tk

from ..config import PROVIDER_OPTIONS, discover_other_ai_tools, provider_detected
from ..storage import save_settings


def show_onboarding(app, first_run: bool = False) -> None:
    dialog = tk.Toplevel(app.root)
    dialog.title("Choose Scan Sources")
    dialog.configure(bg=app.bg)
    dialog.transient(app.root)
    dialog.grab_set()
    dialog.resizable(False, False)

    tk.Label(
        dialog,
        text="Choose What Session Portal Should Discover",
        bg=app.bg,
        fg=app.blue,
        font=("Consolas", 12, "bold"),
    ).pack(anchor="w", padx=18, pady=(16, 4))

    tk.Label(
        dialog,
        text="Found sources can be enabled now. Other detected AI tools are listed below when session support is not available yet.",
        bg=app.bg,
        fg=app.muted,
        font=("Consolas", 9),
    ).pack(anchor="w", padx=18, pady=(0, 12))

    vars_by_key: dict[str, tk.BooleanVar] = {}
    providers = app.settings.get("providers", {})
    for key, info in PROVIDER_OPTIONS.items():
        detected = provider_detected(key)
        initial = detected if not app.settings.get("onboarding_complete") else providers.get(key, detected)
        var = tk.BooleanVar(value=initial)
        vars_by_key[key] = var
        row = tk.Frame(dialog, bg=app.surface, padx=10, pady=7)
        row.pack(fill=tk.X, padx=18, pady=3)
        tk.Checkbutton(
            row,
            text=info["label"],
            variable=var,
            bg=app.surface,
            fg=app.text,
            activebackground=app.surface,
            activeforeground=app.text,
            selectcolor=app.overlay,
            font=("Consolas", 10, "bold"),
        ).pack(side=tk.LEFT)
        status = "found" if detected else "not found"
        tk.Label(
            row,
            text=f"{info['description']}  [{status}]",
            bg=app.surface,
            fg=app.green if detected else app.muted,
            font=("Consolas", 9),
        ).pack(side=tk.LEFT, padx=(10, 0))

    other_tools = discover_other_ai_tools()
    if other_tools:
        tk.Label(
            dialog,
            text="Other Local AI Tools Found",
            bg=app.bg,
            fg=app.blue,
            font=("Consolas", 10, "bold"),
        ).pack(anchor="w", padx=18, pady=(12, 4))
        for tool in other_tools:
            row = tk.Frame(dialog, bg=app.surface, padx=10, pady=6)
            row.pack(fill=tk.X, padx=18, pady=2)
            tk.Label(
                row,
                text=tool["label"],
                bg=app.surface,
                fg=app.text,
                font=("Consolas", 10, "bold"),
            ).pack(side=tk.LEFT)
            tk.Label(
                row,
                text="detected; session resume support not available yet",
                bg=app.surface,
                fg=app.muted,
                font=("Consolas", 9),
            ).pack(side=tk.LEFT, padx=(10, 0))

    btns = tk.Frame(dialog, bg=app.bg, pady=14, padx=18)
    btns.pack(fill=tk.X)

    def select_found():
        for key, var in vars_by_key.items():
            var.set(provider_detected(key))

    def select_all():
        for var in vars_by_key.values():
            var.set(True)

    def save_and_close():
        app.settings["providers"] = {key: var.get() for key, var in vars_by_key.items()}
        app.settings["onboarding_complete"] = True
        save_settings(app.settings)
        dialog.destroy()

    tk.Button(btns, text="Select Found", command=select_found, bg=app.overlay,
              fg=app.text, relief=tk.FLAT, padx=10, pady=5).pack(side=tk.LEFT)
    tk.Button(btns, text="Select All", command=select_all, bg=app.overlay,
              fg=app.text, relief=tk.FLAT, padx=10, pady=5).pack(side=tk.LEFT, padx=(8, 0))
    tk.Button(btns, text="Save", command=save_and_close, bg=app.blue, fg=app.bg,
              relief=tk.FLAT, padx=18, pady=5, font=("Consolas", 10, "bold")).pack(side=tk.RIGHT)

    if first_run:
        dialog.protocol("WM_DELETE_WINDOW", save_and_close)
    app.root.wait_window(dialog)