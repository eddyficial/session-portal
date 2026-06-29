"""Session Portal v2 application controller.

Owns UI state and event handlers. Builds the window from the
:mod:`Codebase.v2.ui` builders and drives providers only through
:mod:`Codebase.v2.sessions` and :mod:`Codebase.v2.resume` — no parsing here.
"""
from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk

from ..config import (
    ACCENT,
    APP_ICON,
    APP_ICON_PNG,
    APP_PALETTE,
    PROVIDER_OPTIONS,
    provider_detected,
    provider_key_for_label,
    provider_label,
)
from ..models import Session
from ..pricing import session_cost as _session_cost, total_cost as _total_cost
from ..providers.base import session_model_label
from ..providers.registry import get_provider
from ..resume import launch as launch_resume
from ..sessions import (
    ensure_search_index,
    get_session_message_count,
    get_session_preview,
    load_sessions,
)
from ..storage import load_renames, load_settings, save_renames, save_settings
from . import date_picker, inspector, onboarding, sidebar, table
from .tooltips import add_tooltip


def compact_number(value: int) -> str:
    value = int(value or 0)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.1f}K"
    return f"{sign}{value}"


class SessionPortalApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Session Portal")
        if APP_ICON.exists():
            try:
                self.root.iconbitmap(str(APP_ICON))
            except tk.TclError:
                pass
        self._window_icon_image = None
        if APP_ICON_PNG.exists():
            try:
                self._window_icon_image = tk.PhotoImage(file=str(APP_ICON_PNG))
                self.root.iconphoto(True, self._window_icon_image)
            except tk.TclError:
                self._window_icon_image = None
        self.root.minsize(1220, 640)
        self._apply_default_window_size()

        self.settings = load_settings()
        self.all_sessions: list[Session] = []
        self.filtered_sessions: list[Session] = []
        self.sort_var = tk.StringVar(value="Newest")
        self.source_var = tk.StringVar(value="All Models")
        self.date_from_var = tk.StringVar()
        self.date_to_var = tk.StringVar()
        self.auto_scan_var = tk.BooleanVar(value=bool(self.settings.get("auto_scan_enabled", True)))
        self._auto_scan_after_id = None
        self._delete_mode = False
        self._checked_ids: set[str] = set()

        self._apply_theme()
        self._ensure_onboarding()
        self._build_ui()
        self._load_data()
        self._schedule_auto_scan()
        self.root.deiconify()
        self._apply_default_window_size()
        self.root.lift()

    # ── window / theme ──────────────────────────────────────────────────────
    def _apply_default_window_size(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if screen_w > 0 and screen_h > 0:
            self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

    def _apply_theme(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        palette = APP_PALETTE
        self.font_family = "Consolas"
        self.font_size = 11

        self.bg = palette["bg"]
        self.bg_deep = palette["bg_deep"]
        self.surface = palette["surface"]
        self.surface_2 = palette["surface_2"]
        self.overlay = palette["overlay"]
        self.bar = palette["bar"]
        self.muted = palette["muted"]
        self.text = palette["text"]
        self.blue = ACCENT["blue"]
        self.green = ACCENT["green"]
        self.yellow = ACCENT["yellow"]
        self.pink = ACCENT["pink"]
        self.purple = ACCENT["purple"]
        self.danger = ACCENT["danger"]
        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.bg)
        style.configure("TLabel", background=self.bg, foreground=self.text, font=self._font())
        style.configure(
            "Treeview",
            background=self.surface,
            foreground=self.text,
            fieldbackground=self.surface,
            font=self._font(),
            rowheight=max(26, self.font_size + 18),
        )
        style.configure(
            "Treeview.Heading",
            background=self.overlay,
            foreground=self.text,
            font=self._font(weight="bold"),
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("pressed", self.blue), ("active", self.surface_2)],
            foreground=[("pressed", self.bg_deep), ("active", "#ffffff")],
            relief=[("pressed", "flat"), ("active", "flat")],
        )
        style.map("Treeview", background=[("selected", self.overlay)], foreground=[("selected", self.text)])
        style.configure(
            "Vertical.TScrollbar",
            background=self.overlay,
            troughcolor=self.surface,
            bordercolor=self.bg,
            arrowcolor=self.text,
        )

    def _font(self, delta: int = 0, weight: str | None = None):
        size = max(8, self.font_size + delta)
        return (self.font_family, size, weight) if weight else (self.font_family, size)

    # ── onboarding ──────────────────────────────────────────────────────────
    def _ensure_onboarding(self):
        if not self.settings.get("onboarding_complete"):
            self._show_onboarding(first_run=True)

    def _show_onboarding(self, first_run: bool = False):
        onboarding.show_onboarding(self, first_run=first_run)

    def _edit_sources(self):
        self._show_onboarding(first_run=False)
        self._load_data()

    # ── source filter buttons ───────────────────────────────────────────────
    def _set_source_filter(self, label: str):
        self.source_var.set(label)
        self._apply_filter()

    def _refresh_source_buttons(self):
        if not hasattr(self, "source_buttons"):
            return
        for label, button in self.source_buttons.items():
            active = self.source_var.get() == label
            button.configure(
                fg_color=self.blue if active else self.surface_2,
                text_color=self.bg_deep if active else self.text,
                hover_color=self.blue if active else self.overlay,
            )

    def _source_filter_labels(self) -> list[str]:
        labels = ["All Models"]
        enabled = self.settings.get("providers", {})
        session_sources = {s.provider for s in self.all_sessions}
        for key, info in PROVIDER_OPTIONS.items():
            if key in session_sources or (enabled.get(key, True) and provider_detected(key)):
                labels.append(info["label"])
        return labels

    def _build_source_buttons(self):
        if not hasattr(self, "source_buttons_frame"):
            return
        for child in self.source_buttons_frame.winfo_children():
            child.destroy()
        self.source_buttons = {}
        labels = self._source_filter_labels()
        if self.source_var.get() not in labels:
            self.source_var.set("All Models")
        for label in labels:
            btn = ctk.CTkButton(
                self.source_buttons_frame,
                text=label,
                anchor="w",
                height=34,
                corner_radius=6,
                font=self._font(1, "bold"),
                command=lambda value=label: self._set_source_filter(value),
            )
            btn.pack(fill=tk.X, pady=3)
            tip = (
                "Show sessions from every enabled provider."
                if label == "All Models"
                else f"Show only {label} sessions."
            )
            add_tooltip(btn, tip)
            self.source_buttons[label] = btn
        self._refresh_source_buttons()

    # ── UI build ────────────────────────────────────────────────────────────
    def _build_ui(self):
        app = ctk.CTkFrame(self.root, fg_color=self.bg_deep, corner_radius=0)
        app.pack(fill=tk.BOTH, expand=True)

        sidebar.build_sidebar(self, app)

        workspace = ctk.CTkFrame(app, fg_color=self.bg, corner_radius=0)
        workspace.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header = ctk.CTkFrame(workspace, fg_color=self.bg, corner_radius=0)
        header.pack(fill=tk.X, padx=14, pady=(14, 6))
        self.count_label = ctk.CTkLabel(header, text="", text_color=self.text, font=self._font())
        self.count_label.pack(side=tk.RIGHT)
        add_tooltip(self.count_label, "Shows how many sessions are currently visible and how many each provider contributed.")

        self.toolbar_row = ctk.CTkFrame(workspace, fg_color=self.bg, corner_radius=0, height=38)
        self.toolbar_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        self.toolbar_row.pack_propagate(False)

        self.top_bar = ctk.CTkFrame(self.toolbar_row, fg_color=self.bg, corner_radius=0, height=38)
        self.top_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.toolbar_controls = ctk.CTkFrame(self.toolbar_row, fg_color=self.bg, corner_radius=0, width=360, height=38)
        self.toolbar_controls.pack(side=tk.RIGHT, fill=tk.Y)
        self.toolbar_controls.pack_propagate(False)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.date_from_var.trace_add("write", self._on_search)
        self.date_to_var.trace_add("write", self._on_search)
        self.date_from_var.trace_add("write", lambda *_: self._refresh_date_buttons())
        self.date_to_var.trace_add("write", lambda *_: self._refresh_date_buttons())
        self.search_entry = ctk.CTkEntry(
            self.top_bar,
            width=520,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            border_width=0,
            text_color=self.text,
            placeholder_text="Start typing to prefilter by project, title, or prompt",
            placeholder_text_color=self.muted,
            font=self._font(2),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_search_entry_change)
        add_tooltip(self.search_entry, "Type to filter sessions by project, title, first prompt, or last prompt.")
        self.date_range_btn = ctk.CTkButton(
            self.toolbar_controls,
            text="Dates: Any",
            width=164,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            text_color=self.text,
            hover_color=self.overlay,
            font=self._font(weight="bold"),
            command=self._open_date_range_picker,
        )
        self.date_range_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        add_tooltip(self.date_range_btn, "Filter sessions by last activity date using a calendar range.")

        self.sort_menu = ctk.CTkOptionMenu(
            self.toolbar_controls,
            variable=self.sort_var,
            values=[
                "Newest", "Oldest",
                "LLM A-Z", "LLM Z-A",
                "Project A-Z", "Project Z-A",
                "Msgs Low-High", "Msgs High-Low",
                "Prompt A-Z", "Prompt Z-A",
            ],
            command=lambda _: self._apply_filter(),
            width=142,
            height=38,
            corner_radius=6,
            fg_color=self.surface,
            button_color=self.overlay,
            button_hover_color=self.blue,
            dropdown_fg_color=self.surface,
            dropdown_hover_color=self.overlay,
            text_color=self.text,
            font=self._font(1),
        )
        self.sort_menu.pack(side=tk.RIGHT)
        add_tooltip(self.sort_menu, "Choose how the session list is sorted.")

        self._build_delete_bar(workspace)

        self.paned = tk.PanedWindow(workspace, orient=tk.HORIZONTAL,
                                    bg=self.bg, sashwidth=5, sashpad=0,
                                    relief=tk.FLAT, borderwidth=0)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        table.build_table(self, self.paned)
        inspector.build_inspector(self, self.paned)

        self.toolbar_row.bind("<Configure>", self._sync_toolbar_to_table_width)
        self.list_frame.bind("<Configure>", self._sync_toolbar_to_table_width)
        self.root.after_idle(self._sync_toolbar_to_table_width)

        bar = tk.Frame(workspace, bg=self.bar, pady=4)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(
            bar,
            text="  Double-click or Enter to resume terminal chat session  |  R Refresh  |  Q Quit",
            bg=self.bar,
            fg=self.text,
            font=self._font(-1),
        ).pack(side=tk.LEFT)

        self.root.bind("<r>", lambda e: self._load_data() if not self._delete_mode else None)
        self.root.bind("<R>", lambda e: self._load_data() if not self._delete_mode else None)
        self.root.bind("q", lambda e: self.root.quit())
        self.root.bind("Q", lambda e: self.root.quit())
        self.root.bind("<Escape>", lambda e: self._exit_delete_mode() if self._delete_mode else None)
        self._refresh_source_buttons()
        self._refresh_date_buttons()

    def _build_delete_bar(self, workspace):
        self.delete_bar = tk.Frame(workspace, bg=self.overlay, pady=6, padx=12)
        tk.Label(self.delete_bar, text="DELETE MODE", bg=self.overlay, fg=self.text,
                 font=self._font(weight="bold")).pack(side=tk.LEFT, padx=(0, 12))
        self.select_all_btn = tk.Button(
            self.delete_bar, text="Select All", bg=self.overlay, fg=self.text,
            activebackground=self.surface_2, font=self._font(), relief=tk.FLAT,
            padx=10, pady=2, cursor="hand2", command=self._toggle_select_all,
        )
        self.select_all_btn.pack(side=tk.LEFT)
        add_tooltip(self.select_all_btn, "Select or clear all currently shown sessions in delete mode.")
        self.confirm_delete_btn = tk.Button(
            self.delete_bar, text="Delete 0 Selected", bg=self.bg, fg=self.danger,
            activebackground=self.surface, font=self._font(weight="bold"), relief=tk.FLAT,
            padx=12, pady=2, cursor="hand2", command=self._confirm_delete, state=tk.DISABLED,
        )
        self.confirm_delete_btn.pack(side=tk.RIGHT)
        add_tooltip(self.confirm_delete_btn, "Move selected sessions to Session Portal trash after confirmation.")
        cancel_delete_btn = tk.Button(
            self.delete_bar, text="Cancel", bg=self.overlay, fg=self.text,
            activebackground=self.surface_2, font=self._font(), relief=tk.FLAT,
            padx=10, pady=2, cursor="hand2", command=self._exit_delete_mode,
        )
        cancel_delete_btn.pack(side=tk.RIGHT, padx=(0, 8))
        add_tooltip(cancel_delete_btn, "Leave delete mode without deleting anything.")

    def _sync_toolbar_to_table_width(self, _event=None):
        if not all(hasattr(self, name) for name in ("toolbar_row", "toolbar_controls", "list_frame")):
            return
        row_width = self.toolbar_row.winfo_width()
        table_width = self.list_frame.winfo_width()
        if row_width <= 1 or table_width <= 1:
            return
        gap = 10
        controls_width = max(320, row_width - table_width - gap)
        self.toolbar_controls.configure(width=controls_width)

    # ── data / autoscan ─────────────────────────────────────────────────────
    def _load_data(self):
        self.settings = load_settings()
        self.auto_scan_var.set(bool(self.settings.get("auto_scan_enabled", True)))
        self.all_sessions = load_sessions(self.settings)
        self._build_source_buttons()
        self._apply_filter()
        self._refresh_auto_scan_button()

    def _toggle_auto_scan(self):
        enabled = not self.auto_scan_var.get()
        self.auto_scan_var.set(enabled)
        self.settings["auto_scan_enabled"] = enabled
        save_settings(self.settings)
        self._refresh_auto_scan_button()
        if enabled:
            self._auto_scan()
        elif self._auto_scan_after_id:
            self.root.after_cancel(self._auto_scan_after_id)
            self._auto_scan_after_id = None

    def _refresh_auto_scan_button(self):
        if not hasattr(self, "auto_scan_btn"):
            return
        enabled = self.auto_scan_var.get()
        self.auto_scan_btn.configure(
            text="Auto Scan: ON" if enabled else "Auto Scan: OFF",
            fg_color=self.blue if enabled else self.surface_2,
            text_color=self.bg_deep if enabled else self.text,
            hover_color=self.blue if enabled else self.overlay,
        )

    def _schedule_auto_scan(self):
        if self._auto_scan_after_id:
            self.root.after_cancel(self._auto_scan_after_id)
            self._auto_scan_after_id = None
        if not self.auto_scan_var.get():
            return
        interval = int(self.settings.get("auto_scan_interval_ms", 15000) or 15000)
        self._auto_scan_after_id = self.root.after(max(5000, interval), self._auto_scan)

    def _auto_scan(self):
        self._auto_scan_after_id = None
        try:
            if not self._delete_mode:
                selected = self.tree.selection()[0] if hasattr(self, "tree") and self.tree.selection() else ""
                self._load_data()
                if selected and selected in self.tree.get_children():
                    self.tree.selection_set(selected)
        finally:
            self._schedule_auto_scan()

    # ── search / sort / date ────────────────────────────────────────────────
    def _on_search(self, *_):
        self._apply_filter()

    def _on_search_entry_change(self, _event=None):
        self.search_var.set(self.search_entry.get())

    def _toggle_sort(self, ascending: str, descending: str):
        self.sort_var.set(ascending if self.sort_var.get() == descending else descending)
        self._apply_filter()

    def _parse_date_filter(self, value: str, end_of_day: bool = False):
        value = value.strip()
        if not value:
            return None
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        return int(dt.timestamp() * 1000)

    def _refresh_date_buttons(self):
        if hasattr(self, "date_range_btn"):
            start = self.date_from_var.get() or "Any"
            end = self.date_to_var.get() or "Any"
            text = "Dates: Any" if start == "Any" and end == "Any" else "Dates: Custom"
            self.date_range_btn.configure(text=text)

    def _open_date_range_picker(self):
        date_picker.open_date_range_picker(self)

    def _clear_date_filter(self):
        self.date_from_var.set("")
        self.date_to_var.set("")
        self._apply_filter()

    # ── filter + render ──────────────────────────────────────────────────────
    def _apply_filter(self):
        source_filter = self.source_var.get()
        query = self.search_var.get().lower()
        from_ms = self._parse_date_filter(self.date_from_var.get())
        to_ms = self._parse_date_filter(self.date_to_var.get(), end_of_day=True)
        if from_ms is not None and to_ms is not None and from_ms > to_ms:
            from_ms, to_ms = to_ms, from_ms

        pool = self.all_sessions

        source_key = provider_key_for_label(source_filter)
        if source_key:
            pool = [s for s in pool if s.provider == source_key]
        if query:
            if any(not s.search_blob for s in pool):
                self.count_label.configure(text="Indexing sessions…")
                self.root.update_idletasks()
                ensure_search_index(pool)
            pool = [s for s in pool if query in s.search_blob]
        if from_ms is not None:
            pool = [s for s in pool if s.timestamp >= from_ms]
        if to_ms is not None:
            pool = [s for s in pool if s.timestamp <= to_ms]

        sort = self.sort_var.get()
        if sort.startswith("Newest") or sort.startswith("Date"):
            pool = sorted(pool, key=lambda s: s.timestamp, reverse=True)
        elif sort.startswith("Oldest"):
            pool = sorted(pool, key=lambda s: s.timestamp)
        elif sort in ("Model A-Z", "LLM A-Z"):
            pool = sorted(pool, key=lambda s: session_model_label(s).lower())
        elif sort in ("Model Z-A", "LLM Z-A"):
            pool = sorted(pool, key=lambda s: session_model_label(s).lower(), reverse=True)
        elif sort.startswith("Project A"):
            pool = sorted(pool, key=lambda s: os.path.basename(s.project or "").lower())
        elif sort.startswith("Project Z"):
            pool = sorted(pool, key=lambda s: os.path.basename(s.project or "").lower(), reverse=True)
        elif sort == "Prompt A-Z":
            pool = sorted(pool, key=lambda s: (s.display or "").lower())
        elif sort == "Prompt Z-A":
            pool = sorted(pool, key=lambda s: (s.display or "").lower(), reverse=True)
        elif sort == "Msgs Low-High":
            pool = sorted(pool, key=get_session_message_count)
        elif sort == "Msgs High-Low":
            pool = sorted(pool, key=get_session_message_count, reverse=True)

        self.filtered_sessions = pool
        self._refresh_list()
        self._refresh_source_buttons()

        total = len(self.all_sessions)
        shown = len(self.filtered_sessions)
        counts = []
        for key, info in PROVIDER_OPTIONS.items():
            count = sum(1 for s in self.filtered_sessions if s.provider == key)
            if count:
                counts.append(f"{info['label']} {count}")
        count_text = "  ".join(counts)
        cost_total, costed = _total_cost(self.filtered_sessions)
        cost_str = f"  |  ~${cost_total:,.2f} ({costed} costed)" if costed else ""
        self.count_label.configure(
            text=f"{shown} of {total} shown" + (f"  |  {count_text}" if count_text else "") + cost_str
        )

    def _compute_costs(self):
        """One-time scan: populate cached tokens for all shown sessions."""
        pool = self.filtered_sessions
        if not pool:
            return
        self.count_label.configure(text=f"Computing costs for {len(pool)} sessions…")
        self.root.update_idletasks()
        for s in pool:
            if s.tokens is None:
                try:
                    get_session_preview(s)
                except Exception:
                    pass
        self._apply_filter()

    def _refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row_num, s in enumerate(self.filtered_sessions, start=1):
            src = s.provider
            project = s.project or ""
            display_title = s.display or ""
            project_short = os.path.basename(project) or project
            ts = s.timestamp
            date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d  %H:%M") if ts else ""
            message_count = get_session_message_count(s)
            display = "    " + (display_title)[:90]

            if src == "grok":
                tag = ("grok",)
            elif src == "codex":
                tag = ("codex",)
            elif src == "copilot":
                tag = ("copilot",)
            elif src == "amp":
                tag = ("amp",)
            else:
                tag = ()

            model_label = session_model_label(s)
            check = "x" if s.id in self._checked_ids else ""
            self.tree.insert("", tk.END, iid=s.id,
                             values=(check, row_num, model_label, project_short, date_str, message_count, display),
                             tags=tag)

    # ── selection / preview / resume ────────────────────────────────────────
    def _on_select(self, _event=None):
        if self._delete_mode:
            return
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s.id == sid), None)
        if not session:
            return
        self._show_preview(session)

        src = session.provider
        label = {
            "grok": "Resume Grok",
            "copilot": "Resume Copilot",
            "codex": "Resume Codex",
            "claude": "Resume Claude Code",
            "amp": "Resume AMP",
        }.get(src, f"Resume {provider_label(src)}")
        self.action_btn.configure(text=label, fg_color=self.green,
                                  text_color="#000000", state=tk.NORMAL)
        self.rename_btn.configure(state=tk.NORMAL)
        self.delete_btn.configure(state=tk.DISABLED if src == "amp" else tk.NORMAL)
        if hasattr(self, "audit_btn"):
            self.audit_btn.configure(state=tk.NORMAL)
        if hasattr(self, "thread_btn"):
            self.thread_btn.configure(state=tk.NORMAL)

    def _view_thread(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s.id == sid), None)
        if not session:
            return
        from . import thread_viewer
        thread_viewer.open_thread_viewer(self, session)

    def _save_audit(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s.id == sid), None)
        if not session:
            return
        try:
            from ..audit import default_audit_filename, export_session_audit
            from ..config import AUDIT_DIR

            target = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Thread",
                initialdir=str(AUDIT_DIR),
                initialfile=default_audit_filename(session),
                defaultextension=".md",
                filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not target:
                return
            path = export_session_audit(session, export_path=Path(target))
        except Exception as exc:
            messagebox.showerror("Audit export failed", str(exc))
            return
        messagebox.showinfo("Thread exported", f"Saved thread export:\n\n{path}")

    def _show_preview(self, session: Session):
        preview = get_session_preview(session)
        first, last, count = preview.first, preview.last, preview.message_count
        tokens = preview.tokens

        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)

        src = session.provider
        if src == "grok":
            src_tag = "grok"
        elif src == "copilot":
            src_tag = "copilot"
        elif src == "codex":
            src_tag = "codex"
        else:
            src_tag = "dim"

        def row(label, value, tag="dim"):
            value = " ".join(str(value or "").split())
            self.preview.insert(tk.END, f"{label:<8} ", "label")
            self.preview.insert(tk.END, f"{value}\n", tag)

        ts = session.timestamp
        date_str = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d  %H:%M:%S") if ts else ""

        row("LLM", session_model_label(session), src_tag)
        row("Provider", provider_label(src), src_tag)
        if session.display:
            row("Title", session.display, src_tag)
        row("Project", session.project, src_tag)
        row("Session", session.id, src_tag)
        row("Date", date_str, src_tag)

        if src == "grok":
            row("Messages", str(count), src_tag)
        elif src == "codex":
            row("Thread", session.display, "codex")
            row("Messages", str(count) if session.source_file else "n/a", src_tag)
        else:
            row("Messages", str(count), src_tag)

        if tokens.input or tokens.output:
            total = tokens.total()
            row("Tokens", f"{compact_number(total)} (in {compact_number(tokens.input)} out {compact_number(tokens.output)})", src_tag)
            if tokens.cache_read or tokens.cache_write:
                row("Cache", f"read {compact_number(tokens.cache_read)} write {compact_number(tokens.cache_write)}", src_tag)
            cost = _session_cost(session)
            if cost is not None:
                row("Cost", f"~${cost:,.4f}", src_tag)

        if first:
            self.preview.insert(tk.END, "\n── First message ──\n", "label")
            self.preview.insert(tk.END, first[:600] + (" …" if len(first) > 600 else "") + "\n", "message")
        if last:
            self.preview.insert(tk.END, "\n── Last message ──\n", "label")
            self.preview.insert(tk.END, last[:600] + (" …" if len(last) > 600 else "") + "\n", "message")

        self.preview.config(state=tk.DISABLED)

    def _on_action(self, _event=None):
        if self._delete_mode:
            return
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s.id == sid), None)
        if not session:
            return
        provider = get_provider(session.provider)
        if provider is None:
            return
        try:
            launch_resume(provider.resume_command(session))
        except Exception as exc:
            messagebox.showerror("Action failed", str(exc))

    # ── tree interactions ───────────────────────────────────────────────────
    def _on_tree_click(self, event):
        if not self._delete_mode:
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return
        if row in self._checked_ids:
            self._checked_ids.discard(row)
        else:
            self._checked_ids.add(row)
        self._update_delete_bar()
        self._refresh_list()
        return "break"

    def _on_right_click(self, event):
        if self._delete_mode:
            return
        row = self.tree.identify_row(event.y)
        if not row:
            return
        self.tree.selection_set(row)
        self._on_select()
        n = len(self.filtered_sessions)
        menu = tk.Menu(self.root, tearoff=0, bg=self.surface, fg=self.text,
                       activebackground=self.overlay, activeforeground=self.text,
                       font=("Consolas", 10))
        menu.add_command(label="Rename", command=self._rename_session)
        menu.add_separator()
        menu.add_command(label="Delete This Session",
                         command=lambda sid=row: self._enter_delete_mode(pre_check_sid=sid))
        menu.add_command(label=f"Delete All {n} Shown",
                         command=lambda: self._enter_delete_mode(pre_check_all=True))
        menu.tk_popup(event.x_root, event.y_root)

    # ── rename ──────────────────────────────────────────────────────────────
    def _rename_session(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = sel[0]
        session = next((s for s in self.filtered_sessions if s.id == sid), None)
        if not session:
            return
        current = session.display or ""
        new_name = simpledialog.askstring(
            "Rename Session", "New name (blank to clear custom name):",
            initialvalue=current, parent=self.root,
        )
        if new_name is None:
            return
        new_name = new_name.strip()
        renames = load_renames()
        if new_name:
            renames[sid] = new_name
        else:
            renames.pop(sid, None)
        save_renames(renames)
        session.display = new_name or current
        self._refresh_list()
        self.tree.selection_set(sid)
        self._on_select()

    # ── delete mode ────────────────────────────────────────────────────────
    def _enter_delete_mode(self, pre_check_sid=None, pre_check_all=False):
        self._delete_mode = True
        self._checked_ids = set()
        if pre_check_all:
            self._checked_ids = {s.id for s in self.filtered_sessions}
        elif pre_check_sid:
            self._checked_ids = {pre_check_sid}
        else:
            sel = self.tree.selection()
            if sel:
                self._checked_ids = {sel[0]}
        self.delete_bar.pack(fill=tk.X, after=getattr(self, "toolbar_row", self.top_bar))
        self.tree.column("check", width=45, minwidth=45)
        self.delete_btn.configure(state=tk.DISABLED)
        self.rename_btn.configure(state=tk.DISABLED)
        self.action_btn.configure(state=tk.DISABLED)
        if hasattr(self, "audit_btn"):
            self.audit_btn.configure(state=tk.DISABLED)
        if hasattr(self, "thread_btn"):
            self.thread_btn.configure(state=tk.DISABLED)
        self._refresh_list()
        self._update_delete_bar()

    def _exit_delete_mode(self):
        self._delete_mode = False
        self._checked_ids = set()
        self.delete_bar.pack_forget()
        self.tree.column("check", width=0, minwidth=0)
        self._refresh_list()
        self.delete_btn.configure(state=tk.DISABLED)
        self.rename_btn.configure(state=tk.DISABLED)
        self.action_btn.configure(state=tk.DISABLED)
        if hasattr(self, "audit_btn"):
            self.audit_btn.configure(state=tk.DISABLED)
        if hasattr(self, "thread_btn"):
            self.thread_btn.configure(state=tk.DISABLED)

    def _toggle_select_all(self):
        total = len(self.filtered_sessions)
        if len(self._checked_ids) >= total:
            self._checked_ids = set()
        else:
            self._checked_ids = {s.id for s in self.filtered_sessions}
        self._update_delete_bar()
        self._refresh_list()

    def _update_delete_bar(self):
        n = sum(1 for s in self.filtered_sessions if s.id in self._checked_ids)
        total = len(self.filtered_sessions)
        self.confirm_delete_btn.config(
            text=f"Delete {n} Selected",
            state=tk.NORMAL if n > 0 else tk.DISABLED,
        )
        self.select_all_btn.config(
            text="Deselect All" if n == total and total > 0 else "Select All"
        )

    def _delete_sessions(self, to_delete: list[Session]) -> None:
        """Move sessions to the trash bin (recoverable), after confirmation."""
        from .. import trash
        renames = load_renames()
        for session in to_delete:
            trash.trash_session(session)
            renames.pop(session.id, None)
        save_renames(renames)

    def _open_trash(self):
        from . import trash_dialog
        trash_dialog.show_trash_dialog(self)
        self._load_data()

    def _confirm_delete(self):
        to_delete = [s for s in self.filtered_sessions if s.id in self._checked_ids]
        n = len(to_delete)
        if n == 0:
            return
        if not messagebox.askyesno(
                "Move to Trash",
                f"Move {n} session{'s' if n > 1 else ''} to the trash?\n\n"
                "You can restore them from the Trash bin. Use Empty Trash to remove permanently.",
                icon="warning"):
            return
        self._delete_sessions(to_delete)
        self._exit_delete_mode()
        self._load_data()

    def _delete_zero_message_sessions(self):
        if self._delete_mode:
            return
        to_delete = [s for s in self.filtered_sessions if get_session_message_count(s) == 0]
        n = len(to_delete)
        if n == 0:
            messagebox.showinfo("No empty sessions", "No sessions with 0 messages are shown in the current list.")
            return
        if not messagebox.askyesno(
                "Move empty sessions to trash",
                f"Move {n} shown session{'s' if n > 1 else ''} with 0 messages to the trash?\n\n"
                "This uses the current search, provider, and date filters.\n"
                "You can restore them from the Trash bin.",
                icon="warning"):
            return
        self._delete_sessions(to_delete)
        self._checked_ids = set()
        self._load_data()
