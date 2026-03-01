"""Settings window with tabs: API Key, Settings, History, About."""

import os
import threading
import tkinter as tk
from tkinter import ttk

from .clipboard import set_clipboard
from .config import (
    ConfigManager, ENV_FILE, get_input_devices,
    is_startup_enabled, set_startup_enabled,
)

# ---------------------------------------------------------------------------
# Dark theme colors (match overlay)
# ---------------------------------------------------------------------------

_BG = "#2d2d2d"
_BG_DARK = "#1a1a1a"
_BG_ENTRY = "#3a3a3a"
_FG = "#e5e5e5"
_FG_DIM = "#a3a3a3"
_FG_MUTED = "#737373"
_ACCENT = "#fbbf24"
_ACCENT_GREEN = "#4ade80"
_ACCENT_RED = "#f87171"
_BTN_BG = "#404040"
_BTN_HOVER = "#505050"


def _apply_dark_theme(root: tk.Toplevel) -> None:
    """Configure ttk styles for dark theme."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=_BG, foreground=_FG,
                    fieldbackground=_BG_ENTRY, borderwidth=0,
                    font=("Segoe UI", 9))
    style.configure("TNotebook", background=_BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=_BG_DARK, foreground=_FG_DIM,
                    padding=[14, 6], font=("Segoe UI", 9))
    style.map("TNotebook.Tab",
              background=[("selected", _BG)],
              foreground=[("selected", _FG)])
    style.configure("TFrame", background=_BG)
    style.configure("TLabel", background=_BG, foreground=_FG)
    style.configure("TButton", background=_BTN_BG, foreground=_FG,
                    padding=[12, 6])
    style.map("TButton",
              background=[("active", _BTN_HOVER)])
    style.configure("TCheckbutton", background=_BG, foreground=_FG)
    style.map("TCheckbutton",
              background=[("active", _BG)])
    style.configure("TCombobox", fieldbackground=_BG_ENTRY, foreground=_FG,
                    background=_BTN_BG, arrowcolor=_FG)
    style.configure("TScale", background=_BG, troughcolor=_BG_ENTRY)
    style.configure("TLabelframe", background=_BG, foreground=_FG_DIM)
    style.configure("TLabelframe.Label", background=_BG, foreground=_FG_DIM)
    style.configure("Dim.TLabel", foreground=_FG_MUTED)
    style.configure("Accent.TLabel", foreground=_ACCENT)
    style.configure("Green.TLabel", foreground=_ACCENT_GREEN)
    style.configure("Red.TLabel", foreground=_ACCENT_RED)
    style.configure("Section.TLabel", foreground=_FG_DIM,
                    font=("Segoe UI", 9, "bold"))
    style.configure("TEntry", fieldbackground=_BG_ENTRY, foreground=_FG)


# ---------------------------------------------------------------------------
# SettingsWindow
# ---------------------------------------------------------------------------


class SettingsWindow:
    """Reusable settings window with show/hide pattern."""

    def __init__(self, overlay_root: tk.Tk, config: ConfigManager,
                 *, on_api_key_saved=None, engine=None, overlay=None) -> None:
        self._overlay_root = overlay_root
        self._config = config
        self._on_api_key_saved = on_api_key_saved
        self._engine = engine
        self._overlay = overlay
        self._win: tk.Toplevel | None = None
        self._built = False

    # -- Show / hide --

    def show(self, tab_index: int = 0) -> None:
        if self._win is not None and self._built:
            try:
                self._win.deiconify()
                self._win.lift()
                self._win.focus_force()
                if hasattr(self, "_notebook"):
                    self._notebook.select(tab_index)
                return
            except tk.TclError:
                self._win = None
                self._built = False

        self._build(tab_index)

    def hide(self) -> None:
        if self._win is not None:
            try:
                self._win.withdraw()
            except tk.TclError:
                pass

    def _on_close(self) -> None:
        self.hide()

    # -- Build window --

    def _build(self, initial_tab: int = 0) -> None:
        win = tk.Toplevel(self._overlay_root)
        win.title("Dictation — Settings")
        win.geometry("520x560")
        win.minsize(460, 420)
        win.config(bg=_BG)
        win.protocol("WM_DELETE_WINDOW", self._on_close)
        self._win = win
        self._built = True

        _apply_dark_theme(win)

        self._notebook = nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_api_key_tab(nb)
        self._build_settings_tab(nb)
        self._build_history_tab(nb)
        self._build_about_tab(nb)

        nb.select(initial_tab)

        # Center on screen
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        ww = win.winfo_width()
        wh = win.winfo_height()
        win.geometry(f"+{(sw - ww) // 2}+{(sh - wh) // 2}")

        win.lift()
        win.focus_force()

    # -----------------------------------------------------------------------
    # Tab 1: API Key
    # -----------------------------------------------------------------------

    def _build_api_key_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb)
        nb.add(frame, text="  API Key  ")

        inner = ttk.Frame(frame)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ttk.Label(inner, text="OpenAI API Key",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(inner, text="Required for transcription and smart formatting.",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 16))

        # Key input row
        key_frame = ttk.Frame(inner)
        key_frame.pack(fill="x", pady=(0, 8))

        self._key_var = tk.StringVar(value=self._load_env_key())
        self._key_show = False
        self._key_entry = ttk.Entry(key_frame, textvariable=self._key_var,
                                     show="*", font=("Consolas", 10))
        self._key_entry.pack(side="left", fill="x", expand=True, ipady=4)

        self._toggle_btn = ttk.Button(key_frame, text="Show",
                                       command=self._toggle_key_visibility,
                                       width=6)
        self._toggle_btn.pack(side="left", padx=(8, 0))

        # Buttons row
        btn_frame = ttk.Frame(inner)
        btn_frame.pack(fill="x", pady=(8, 0))

        self._save_btn = ttk.Button(btn_frame, text="Save & Validate",
                                     command=self._save_api_key)
        self._save_btn.pack(side="left")

        self._key_status = ttk.Label(btn_frame, text="", style="Dim.TLabel")
        self._key_status.pack(side="left", padx=(16, 0))

        # Help text
        ttk.Label(inner,
                  text="Get your API key from platform.openai.com/api-keys",
                  style="Dim.TLabel").pack(anchor="w", pady=(24, 0))
        ttk.Label(inner,
                  text="The key is stored in the .env file next to the app.",
                  style="Dim.TLabel").pack(anchor="w", pady=(4, 0))

    def _load_env_key(self) -> str:
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OPENAI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        return val
        except FileNotFoundError:
            pass
        return os.getenv("OPENAI_API_KEY", "")

    def _toggle_key_visibility(self) -> None:
        self._key_show = not self._key_show
        self._key_entry.config(show="" if self._key_show else "*")
        self._toggle_btn.config(text="Hide" if self._key_show else "Show")

    def _save_api_key(self) -> None:
        key = self._key_var.get().strip()
        if not key:
            self._key_status.config(text="Key cannot be empty", style="Red.TLabel")
            return

        self._key_status.config(text="Validating...", style="Accent.TLabel")
        self._save_btn.config(state="disabled")

        def validate():
            valid = False
            try:
                from openai import OpenAI
                test = OpenAI(api_key=key, timeout=10.0)
                test.models.list()
                valid = True
            except Exception:
                pass

            def update_ui():
                self._save_btn.config(state="normal")
                if valid:
                    self._write_env_key(key)
                    self._key_status.config(text="Saved & validated!",
                                            style="Green.TLabel")
                    if self._on_api_key_saved:
                        self._on_api_key_saved(key)
                else:
                    self._key_status.config(text="Invalid key — check and retry",
                                            style="Red.TLabel")

            self._overlay_root.after(0, update_ui)

        threading.Thread(target=validate, daemon=True).start()

    def _write_env_key(self, key: str) -> None:
        lines = []
        found = False
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass

        new_lines = []
        for line in lines:
            if line.strip().startswith("OPENAI_API_KEY="):
                new_lines.append(f'OPENAI_API_KEY="{key}"\n')
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f'OPENAI_API_KEY="{key}"\n')

        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    # -----------------------------------------------------------------------
    # Tab 2: Settings
    # -----------------------------------------------------------------------

    def _build_settings_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb)
        nb.add(frame, text="  Settings  ")

        # Scrollable content
        canvas = tk.Canvas(frame, bg=_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        cfg = self._config

        # --- Transcription section ---
        ttk.Label(scroll_frame, text="TRANSCRIPTION",
                  style="Section.TLabel").pack(anchor="w", pady=(8, 6))

        self._smart_fmt_var = tk.BooleanVar(value=cfg.get("smart_format", True))
        ttk.Checkbutton(
            scroll_frame, text="Smart formatting (GPT punctuation cleanup)",
            variable=self._smart_fmt_var,
            command=lambda: cfg.set("smart_format", self._smart_fmt_var.get()) or cfg.save(),
        ).pack(anchor="w", pady=2)

        self._silence_var = tk.BooleanVar(value=cfg.get("silence_detection", True))
        ttk.Checkbutton(
            scroll_frame, text="Auto-stop on silence",
            variable=self._silence_var,
            command=lambda: cfg.set("silence_detection", self._silence_var.get()) or cfg.save(),
        ).pack(anchor="w", pady=2)

        # Silence duration slider
        dur_frame = ttk.Frame(scroll_frame)
        dur_frame.pack(fill="x", pady=(2, 8), padx=(20, 0))
        ttk.Label(dur_frame, text="Silence duration:", style="Dim.TLabel").pack(side="left")
        self._silence_dur_var = tk.DoubleVar(value=cfg.get("silence_duration", 2.0))
        self._silence_dur_label = ttk.Label(dur_frame,
                                             text=f"{self._silence_dur_var.get():.1f}s")
        self._silence_dur_label.pack(side="right")
        dur_scale = ttk.Scale(dur_frame, from_=0.5, to=10.0,
                               variable=self._silence_dur_var,
                               command=self._on_silence_dur_changed)
        dur_scale.pack(side="right", fill="x", expand=True, padx=(8, 8))

        self._auto_copy_var = tk.BooleanVar(value=cfg.get("auto_copy", False))
        ttk.Checkbutton(
            scroll_frame, text="Copy only (don't auto-paste)",
            variable=self._auto_copy_var,
            command=lambda: cfg.set("auto_copy", self._auto_copy_var.get()) or cfg.save(),
        ).pack(anchor="w", pady=2)

        # --- Overlay section ---
        ttk.Label(scroll_frame, text="OVERLAY",
                  style="Section.TLabel").pack(anchor="w", pady=(16, 6))

        self._visible_var = tk.BooleanVar(value=cfg.get("visible", True))
        ttk.Checkbutton(
            scroll_frame, text="Show overlay",
            variable=self._visible_var,
            command=self._on_visible_changed,
        ).pack(anchor="w", pady=2)

        self._pinned_var = tk.BooleanVar(value=cfg.get("pinned", False))
        ttk.Checkbutton(
            scroll_frame, text="Pin overlay position (disable drag)",
            variable=self._pinned_var,
            command=lambda: cfg.set("pinned", self._pinned_var.get()) or cfg.save(),
        ).pack(anchor="w", pady=2)

        # Overlay size
        size_frame = ttk.Frame(scroll_frame)
        size_frame.pack(fill="x", pady=(2, 8), padx=(0, 0))
        ttk.Label(size_frame, text="Overlay size:").pack(side="left")
        self._size_var = tk.StringVar(value=cfg.get("overlay_size", "normal"))
        size_combo = ttk.Combobox(size_frame, textvariable=self._size_var,
                                   values=["small", "normal", "large"],
                                   state="readonly", width=12)
        size_combo.pack(side="left", padx=(8, 0))
        size_combo.bind("<<ComboboxSelected>>", self._on_size_changed)

        # --- Microphone section ---
        ttk.Label(scroll_frame, text="MICROPHONE",
                  style="Section.TLabel").pack(anchor="w", pady=(16, 6))

        mic_frame = ttk.Frame(scroll_frame)
        mic_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(mic_frame, text="Input device:").pack(side="left")

        devices = get_input_devices()
        dev_names = ["System default"] + [name for _, name in devices]
        dev_indices = [None] + [idx for idx, _ in devices]
        self._dev_indices = dev_indices

        current_dev = cfg.get("device_index")
        current_name = "System default"
        for idx, name in devices:
            if idx == current_dev:
                current_name = name
                break

        self._mic_var = tk.StringVar(value=current_name)
        mic_combo = ttk.Combobox(mic_frame, textvariable=self._mic_var,
                                  values=dev_names, state="readonly", width=35)
        mic_combo.pack(side="left", padx=(8, 0))
        mic_combo.bind("<<ComboboxSelected>>", self._on_mic_changed)

        # --- Behavior section ---
        ttk.Label(scroll_frame, text="BEHAVIOR",
                  style="Section.TLabel").pack(anchor="w", pady=(16, 6))

        self._quiet_var = tk.BooleanVar(value=cfg.get("quiet", False))
        ttk.Checkbutton(
            scroll_frame, text="Mute sounds",
            variable=self._quiet_var,
            command=self._on_quiet_changed,
        ).pack(anchor="w", pady=2)

        # --- Advanced section ---
        ttk.Label(scroll_frame, text="ADVANCED",
                  style="Section.TLabel").pack(anchor="w", pady=(16, 6))

        self._startup_var = tk.BooleanVar(value=is_startup_enabled())
        ttk.Checkbutton(
            scroll_frame, text="Start at Windows startup",
            variable=self._startup_var,
            command=self._on_startup_changed,
        ).pack(anchor="w", pady=2)

        self._log_var = tk.BooleanVar(value=cfg.get("log_to_file", False))
        ttk.Checkbutton(
            scroll_frame, text="Log to file",
            variable=self._log_var,
            command=lambda: cfg.set("log_to_file", self._log_var.get()) or cfg.save(),
        ).pack(anchor="w", pady=2)

    def _on_silence_dur_changed(self, val) -> None:
        v = round(float(val), 1)
        self._silence_dur_label.config(text=f"{v:.1f}s")
        self._config.set("silence_duration", v)
        self._config.save()

    def _on_visible_changed(self) -> None:
        desired = self._visible_var.get()
        if self._overlay and desired != self._overlay._visible:
            self._overlay.toggle_visible()
        self._config.set("visible", desired)
        self._config.save()

    def _on_size_changed(self, event=None) -> None:
        size = self._size_var.get()
        self._config.set("overlay_size", size)
        self._config.save()
        if self._overlay:
            self._overlay.resize(size)

    def _on_mic_changed(self, event=None) -> None:
        idx = self._mic_var.get()
        sel_index = None
        devices = get_input_devices()
        if idx != "System default":
            for dev_idx, name in devices:
                if name == idx:
                    sel_index = dev_idx
                    break
        self._config.set("device_index", sel_index)
        self._config.save()

    def _on_quiet_changed(self) -> None:
        import dictation.overlay as _overlay_mod
        _overlay_mod.quiet_mode = self._quiet_var.get()
        self._config.set("quiet", self._quiet_var.get())
        self._config.save()

    def _on_startup_changed(self) -> None:
        enabled = self._startup_var.get()
        set_startup_enabled(enabled)
        self._config.set("start_at_startup", enabled)
        self._config.save()

    # -----------------------------------------------------------------------
    # Tab 3: History
    # -----------------------------------------------------------------------

    def _build_history_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb)
        nb.add(frame, text="  History  ")

        # Toolbar
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill="x", padx=12, pady=(12, 4))

        # Search
        ttk.Label(toolbar, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self._search_var,
                                  width=25)
        search_entry.pack(side="left", padx=(6, 12))

        self._search_debounce_id = None
        self._search_var.trace_add("write", self._on_search_changed)

        # Buttons
        ttk.Button(toolbar, text="Export", command=self._on_export_history).pack(side="right", padx=(4, 0))
        ttk.Button(toolbar, text="Clear All", command=self._on_clear_history).pack(side="right", padx=(4, 0))

        # History list
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._hist_canvas = tk.Canvas(list_frame, bg=_BG_DARK,
                                       highlightthickness=0)
        hist_scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                        command=self._hist_canvas.yview)
        self._hist_scroll_frame = ttk.Frame(self._hist_canvas)
        self._hist_scroll_frame.bind(
            "<Configure>",
            lambda e: self._hist_canvas.configure(
                scrollregion=self._hist_canvas.bbox("all")),
        )
        self._hist_canvas.create_window((0, 0), window=self._hist_scroll_frame,
                                         anchor="nw")
        self._hist_canvas.configure(yscrollcommand=hist_scrollbar.set)
        self._hist_canvas.pack(side="left", fill="both", expand=True)
        hist_scrollbar.pack(side="right", fill="y")

        self._populate_history()

    def _on_search_changed(self, *args) -> None:
        if self._search_debounce_id is not None:
            self._overlay_root.after_cancel(self._search_debounce_id)
        self._search_debounce_id = self._overlay_root.after(
            200, self._populate_history)

    def _populate_history(self) -> None:
        for widget in self._hist_scroll_frame.winfo_children():
            widget.destroy()

        engine = self._engine
        if engine is None:
            ttk.Label(self._hist_scroll_frame,
                      text="Engine not available", style="Dim.TLabel").pack(pady=20)
            return

        history = engine.history
        query = self._search_var.get().strip().lower() if hasattr(self, "_search_var") else ""

        if not history:
            ttk.Label(self._hist_scroll_frame,
                      text="No transcriptions yet", style="Dim.TLabel").pack(pady=20)
            return

        last_date = None
        for idx, (ts, text) in enumerate(reversed(history)):
            real_idx = len(history) - 1 - idx
            if query and query not in text.lower():
                continue

            date_str = ts.strftime("%Y-%m-%d")
            if date_str != last_date:
                last_date = date_str
                date_label = tk.Label(
                    self._hist_scroll_frame, text=ts.strftime("%A %d %b %Y"),
                    bg=_BG_DARK, fg=_FG_MUTED, font=("Segoe UI", 8),
                    anchor="w",
                )
                date_label.pack(fill="x", padx=8, pady=(8, 2))

            entry_frame = tk.Frame(self._hist_scroll_frame, bg="#262626",
                                   cursor="hand2")
            entry_frame.pack(fill="x", padx=4, pady=1)

            time_lbl = tk.Label(
                entry_frame, text=ts.strftime("%H:%M"), bg="#262626",
                fg=_FG_MUTED, font=("Segoe UI", 8), anchor="nw",
            )
            time_lbl.pack(side="left", padx=(8, 6), pady=4)

            text_lbl = tk.Label(
                entry_frame, text=text, bg="#262626", fg=_FG,
                font=("Segoe UI", 9), anchor="w",
                wraplength=360, justify="left",
            )
            text_lbl.pack(side="left", fill="x", expand=True, padx=(0, 8),
                          pady=4)

            # Left-click to copy
            for widget in (entry_frame, time_lbl, text_lbl):
                widget.bind(
                    "<Button-1>",
                    lambda e, t=text: self._copy_history_entry(t),
                )
                # Right-click to delete
                widget.bind(
                    "<Button-3>",
                    lambda e, ri=real_idx: self._delete_history_entry(ri),
                )

    def _copy_history_entry(self, text: str) -> None:
        set_clipboard(text)

    def _delete_history_entry(self, idx: int) -> None:
        if self._engine:
            self._engine._delete_history_entry(idx)
            self._populate_history()

    def _on_export_history(self) -> None:
        if self._engine:
            self._engine.export_history()

    def _on_clear_history(self) -> None:
        if self._engine:
            self._engine.clear_history()
            self._populate_history()

    # -----------------------------------------------------------------------
    # Tab 4: About
    # -----------------------------------------------------------------------

    def _build_about_tab(self, nb: ttk.Notebook) -> None:
        frame = ttk.Frame(nb)
        nb.add(frame, text="  About  ")

        inner = ttk.Frame(frame)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ttk.Label(inner, text="Dictation Tool",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 4))
        ttk.Label(inner, text="System-wide Windows dictation with AI formatting",
                  style="Dim.TLabel").pack(anchor="w", pady=(0, 20))

        # Keyboard shortcuts
        ttk.Label(inner, text="KEYBOARD SHORTCUTS",
                  style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        shortcuts = [
            ("Ctrl+Shift+D", "Toggle recording"),
            ("Ctrl+Shift+Space", "Hold to record"),
            ("Ctrl+Shift+A", "Record (append mode)"),
            ("Ctrl+Shift+H", "Show history"),
            ("Ctrl+Shift+Z", "Undo last paste"),
            ("Ctrl+Shift+Escape", "Cancel recording"),
            ("Double-click overlay", "Copy last transcription"),
            ("Drag overlay", "Move overlay position"),
        ]

        for key, desc in shortcuts:
            row = ttk.Frame(inner)
            row.pack(fill="x", pady=1)
            key_lbl = tk.Label(row, text=key, bg=_BG, fg=_ACCENT,
                               font=("Consolas", 9), width=22, anchor="w")
            key_lbl.pack(side="left")
            tk.Label(row, text=desc, bg=_BG, fg=_FG,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")

        # Session statistics
        ttk.Label(inner, text="SESSION STATISTICS",
                  style="Section.TLabel").pack(anchor="w", pady=(20, 8))

        if self._engine:
            stats_text = (
                f"Transcriptions: {self._engine.session_count}\n"
                f"Words: {self._engine.session_words}\n"
                f"History entries: {len(self._engine.history)}"
            )
        else:
            stats_text = "Engine not started"

        self._stats_label = tk.Label(inner, text=stats_text, bg=_BG, fg=_FG,
                                      font=("Segoe UI", 9), justify="left",
                                      anchor="nw")
        self._stats_label.pack(anchor="w")
