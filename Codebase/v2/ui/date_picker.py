"""Date-range picker dialog (ported faithfully from v1)."""
from __future__ import annotations

import calendar
import tkinter as tk
from datetime import datetime


def open_date_range_picker(app) -> None:
    dialog = tk.Toplevel(app.root)
    dialog.title("Choose Date Range")
    dialog.configure(bg=app.bg)
    dialog.transient(app.root)
    dialog.grab_set()
    dialog.resizable(False, False)

    body = tk.Frame(dialog, bg=app.bg, padx=16, pady=16)
    body.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        body,
        text="Date Range",
        bg=app.bg,
        fg=app.text,
        font=app._font(2, "bold"),
    ).pack(anchor="w", pady=(0, 10))

    start_value = tk.StringVar(value=app.date_from_var.get() or "Any")
    end_value = tk.StringVar(value=app.date_to_var.get() or "Any")
    active_target = tk.StringVar(value="from")

    def sync_labels():
        start_value.set(app.date_from_var.get() or "Any")
        end_value.set(app.date_to_var.get() or "Any")

    month_seed = app.date_from_var.get() or app.date_to_var.get()
    try:
        seed_date = datetime.strptime(month_seed, "%Y-%m-%d")
    except ValueError:
        seed_date = datetime.now()
    month_var = tk.IntVar(value=seed_date.month)
    year_var = tk.IntVar(value=seed_date.year)

    def row(label: str, value_var: tk.StringVar, target_name: str):
        frame = tk.Frame(body, bg=app.surface, padx=10, pady=8)
        frame.pack(fill=tk.X, pady=4)
        tk.Label(frame, text=label, bg=app.surface, fg=app.blue,
                 font=app._font(weight="bold"), width=8, anchor="w").pack(side=tk.LEFT)
        tk.Label(frame, textvariable=value_var, bg=app.surface, fg=app.text,
                 font=app._font(weight="bold"), width=12, anchor="w").pack(side=tk.LEFT, padx=(8, 10))
        tk.Button(frame, text="Select", bg=app.overlay, fg=app.text,
                  activebackground=app.surface_2, activeforeground=app.text,
                  relief=tk.FLAT, padx=12,
                  command=lambda: (active_target.set(target_name), render_calendar())).pack(side=tk.RIGHT)

    row("From", start_value, "from")
    row("To", end_value, "to")

    calendar_panel = tk.Frame(body, bg=app.bg)
    calendar_panel.pack(fill=tk.X, pady=(10, 0))
    calendar_header = tk.Frame(calendar_panel, bg=app.bg)
    calendar_header.pack(fill=tk.X, pady=(0, 8))
    active_label = tk.Label(calendar_header, text="", bg=app.bg, fg=app.blue,
                            font=app._font(weight="bold"), anchor="w")
    active_label.pack(side=tk.LEFT)
    month_label = tk.Label(calendar_header, text="", bg=app.bg, fg=app.text,
                           font=app._font(weight="bold"), width=16)
    month_label.pack(side=tk.LEFT, expand=True)
    grid = tk.Frame(calendar_panel, bg=app.bg)
    grid.pack()

    def shift_month(delta: int):
        month = month_var.get() + delta
        year = year_var.get()
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        month_var.set(month)
        year_var.set(year)
        render_calendar()

    tk.Button(calendar_header, text="<", bg=app.surface, fg=app.text,
              activebackground=app.overlay, activeforeground=app.text,
              relief=tk.FLAT, width=4, command=lambda: shift_month(-1)).pack(side=tk.LEFT, padx=(0, 6))
    tk.Button(calendar_header, text=">", bg=app.surface, fg=app.text,
              activebackground=app.overlay, activeforeground=app.text,
              relief=tk.FLAT, width=4, command=lambda: shift_month(1)).pack(side=tk.LEFT)

    def choose_day(day: int):
        value = f"{year_var.get():04d}-{month_var.get():02d}-{day:02d}"
        if active_target.get() == "from":
            app.date_from_var.set(value)
            active_target.set("to")
        else:
            app.date_to_var.set(value)
        sync_labels()
        render_calendar()

    def render_calendar():
        for child in grid.winfo_children():
            child.destroy()
        year = year_var.get()
        month = month_var.get()
        active_label.config(text=f"Choosing {'From' if active_target.get() == 'from' else 'To'}")
        month_label.config(text=f"{calendar.month_name[month]} {year}")
        selected_value = app.date_from_var.get() if active_target.get() == "from" else app.date_to_var.get()
        for col, day_name in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            tk.Label(grid, text=day_name, bg=app.bg, fg=app.blue,
                     font=app._font(-1, "bold"), width=4).grid(row=0, column=col, padx=2, pady=(0, 4))
        for row_index, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for col, day in enumerate(week):
                if not day:
                    tk.Label(grid, text="", bg=app.bg, width=4).grid(row=row_index, column=col, padx=2, pady=2)
                    continue
                date_value = f"{year:04d}-{month:02d}-{day:02d}"
                is_selected = selected_value == date_value
                tk.Button(grid, text=str(day), bg=app.blue if is_selected else app.surface,
                          fg=app.bg_deep if is_selected else app.text,
                          activebackground=app.overlay, activeforeground=app.text,
                          relief=tk.FLAT, width=4,
                          command=lambda value=day: choose_day(value)).grid(row=row_index, column=col, padx=2, pady=2)

    footer = tk.Frame(body, bg=app.bg)
    footer.pack(fill=tk.X, pady=(12, 0))
    tk.Button(footer, text="Clear Dates", bg=app.surface_2, fg=app.text,
              activebackground=app.overlay, activeforeground=app.text, relief=tk.FLAT, padx=12,
              command=lambda: (app._clear_date_filter(), sync_labels(), render_calendar())).pack(side=tk.LEFT)
    tk.Button(footer, text="Done", bg=app.green, fg="#000000",
              activebackground="#c8f7c5", activeforeground="#000000", relief=tk.FLAT, padx=16,
              command=dialog.destroy).pack(side=tk.RIGHT)

    render_calendar()
    dialog.update_idletasks()
    if hasattr(app, "date_range_btn"):
        anchor = app.date_range_btn
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 6
        screen_width = app.root.winfo_screenwidth()
        if x + dialog.winfo_width() > screen_width - 12:
            x = max(12, screen_width - dialog.winfo_width() - 12)
    else:
        x = app.root.winfo_x() + max(80, (app.root.winfo_width() - dialog.winfo_width()) // 2)
        y = app.root.winfo_y() + 120
    dialog.geometry(f"+{x}+{y}")
    dialog.wait_window()