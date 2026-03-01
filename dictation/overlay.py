"""Floating overlay widget with equalizer visualization."""

import ctypes
import math
import threading
import time
import tkinter as tk
import winsound
from datetime import datetime
from enum import Enum, auto

from .clipboard import set_clipboard

# ---------------------------------------------------------------------------
# App state enum
# ---------------------------------------------------------------------------


class AppState(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()


# ---------------------------------------------------------------------------
# Overlay size presets
# ---------------------------------------------------------------------------

SIZE_PRESETS = {
    "small": {"box": 32, "corner": 8, "bar_w": 2, "bar_gap": 2,
              "bar_max": 14, "bar_min": 3, "bar_count": 5},
    "normal": {"box": 40, "corner": 10, "bar_w": 3, "bar_gap": 3,
               "bar_max": 18, "bar_min": 4, "bar_count": 5},
    "large": {"box": 52, "corner": 13, "bar_w": 4, "bar_gap": 4,
              "bar_max": 24, "bar_min": 5, "bar_count": 5},
}

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COLOR_BG_IDLE = "#2d2d2d"
COLOR_BG_REC = "#451a1a"
COLOR_BG_TRANS = "#422006"
COLOR_BG_SUCCESS = "#0a2e14"
COLOR_BAR_IDLE = "#737373"
COLOR_BAR_REC = "#f87171"
COLOR_BAR_TRANS = "#fbbf24"
COLOR_BAR_SUCCESS = "#4ade80"

_BEEP_START = (800, 80)
_BEEP_STOP = (600, 80)

# Module-level quiet flag (toggled via tray / settings)
quiet_mode = False


def _beep(freq: int, duration: int) -> None:
    if quiet_mode:
        return
    threading.Thread(target=winsound.Beep, args=(freq, duration), daemon=True).start()


# ---------------------------------------------------------------------------
# Win32 window style constants
# ---------------------------------------------------------------------------

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008
_MARGIN = 20


# ---------------------------------------------------------------------------
# DictationOverlay
# ---------------------------------------------------------------------------


class DictationOverlay:
    """Draggable rounded box with equalizer icon showing dictation state."""

    def __init__(self, config) -> None:
        self._config = config
        self.root = tk.Tk()
        self.root.title("Dictation")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self._trans_color = "#f0f0f0"
        self.root.config(bg=self._trans_color)
        self.root.attributes("-transparentcolor", self._trans_color)

        # Load size preset
        size_name = config.get("overlay_size", "normal")
        self._preset = SIZE_PRESETS.get(size_name, SIZE_PRESETS["normal"])
        self._box = self._preset["box"]

        self.canvas = tk.Canvas(
            self.root, width=self._box, height=self._box,
            bg=self._trans_color, highlightthickness=0, bd=0,
        )
        self.canvas.pack()

        self._bg_parts: list[int] = []
        self._bars: list[int] = []
        self._draw_all()

        # Position: saved config or default top-right
        screen_w = self.root.winfo_screenwidth()
        ox = config.get("overlay_x")
        oy = config.get("overlay_y")
        x = ox if ox is not None else (screen_w - self._box - _MARGIN)
        y = oy if oy is not None else _MARGIN
        self.root.geometry(f"{self._box}x{self._box}+{x}+{y}")

        # Drag
        self._drag_x = 0
        self._drag_y = 0
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)

        # Tooltip
        self._tooltip: tk.Toplevel | None = None
        self.canvas.bind("<Enter>", self._show_tooltip)
        self.canvas.bind("<Leave>", self._hide_tooltip)

        self.root.after(10, self._apply_no_activate)

        self._animation_id: str | None = None
        self._state = AppState.IDLE
        self._history_win: tk.Toplevel | None = None
        self._preview_win: tk.Toplevel | None = None
        self._shortcuts_win: tk.Toplevel | None = None
        self._visible = config.get("visible", True)
        if not self._visible:
            self.root.withdraw()

        # Real audio levels (pushed by engine)
        self._audio_levels: list[float] = [0.0] * self._preset["bar_count"]

        # Callbacks (wired by engine)
        self.on_double_click_cb = None
        self.on_history_delete_cb = None

        # For smart tooltip
        self._last_text_preview: str = ""

    def _draw_all(self) -> None:
        """Draw or redraw background + bars for current preset."""
        self.canvas.delete("all")
        p = self._preset
        self._bg_parts = self._draw_rounded_rect(
            0, 0, p["box"], p["box"], p["corner"],
            fill=COLOR_BG_IDLE, outline="",
        )
        total_w = p["bar_count"] * p["bar_w"] + (p["bar_count"] - 1) * p["bar_gap"]
        start_x = (p["box"] - total_w) // 2
        cy = p["box"] // 2
        idle_bars = self._idle_bars()
        self._bars = []
        for i in range(p["bar_count"]):
            x = start_x + i * (p["bar_w"] + p["bar_gap"])
            h = idle_bars[i]
            bar = self.canvas.create_rectangle(
                x, cy - h // 2, x + p["bar_w"], cy + h // 2,
                fill=COLOR_BAR_IDLE, outline="",
            )
            self._bars.append(bar)

    def _idle_bars(self) -> list[int]:
        p = self._preset
        mid = p["bar_max"]
        low = (p["bar_min"] + p["bar_max"]) // 2
        base = p["bar_min"] + 1
        return [base, low, mid, low, base]

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs) -> list[int]:
        return [
            self.canvas.create_oval(x1, y1, x1 + 2 * r, y1 + 2 * r, **kwargs),
            self.canvas.create_oval(x2 - 2 * r, y1, x2, y1 + 2 * r, **kwargs),
            self.canvas.create_oval(x1, y2 - 2 * r, x1 + 2 * r, y2, **kwargs),
            self.canvas.create_oval(x2 - 2 * r, y2 - 2 * r, x2, y2, **kwargs),
            self.canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs),
            self.canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs),
        ]

    def _set_bg_color(self, color: str) -> None:
        for item in self._bg_parts:
            self.canvas.itemconfig(item, fill=color)

    def _set_bar_heights(self, heights: list[int], color: str) -> None:
        p = self._preset
        cy = p["box"] // 2
        total_w = p["bar_count"] * p["bar_w"] + (p["bar_count"] - 1) * p["bar_gap"]
        start_x = (p["box"] - total_w) // 2
        for i, bar in enumerate(self._bars):
            h = heights[i] if i < len(heights) else p["bar_min"]
            x = start_x + i * (p["bar_w"] + p["bar_gap"])
            self.canvas.coords(bar, x, cy - h // 2, x + p["bar_w"], cy + h // 2)
            self.canvas.itemconfig(bar, fill=color)

    def set_audio_levels(self, levels: list[float]) -> None:
        self._audio_levels = levels

    # -- Tooltip (smart: shows last text + shortcuts) --

    def _show_tooltip(self, event=None) -> None:
        if self._tooltip is not None:
            return
        try:
            self._tooltip = tw = tk.Toplevel(self.root)
            tw.overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.config(bg="#1a1a1a")

            if self._last_text_preview:
                preview = self._last_text_preview[:60]
                if len(self._last_text_preview) > 60:
                    preview += "..."
                tk.Label(
                    tw, text=preview, bg="#1a1a1a", fg="#e5e5e5",
                    font=("Segoe UI", 9), anchor="w",
                    wraplength=280, justify="left",
                ).pack(padx=10, pady=(6, 2))
                tk.Frame(tw, bg="#333", height=1).pack(fill="x", padx=10, pady=2)

            tk.Label(
                tw, text="D toggle | Space hold | Esc cancel | A append",
                bg="#1a1a1a", fg="#737373", font=("Segoe UI", 8),
            ).pack(padx=10, pady=(2, 6))

            bx = self.root.winfo_x()
            by = self.root.winfo_y()
            tw.update_idletasks()
            tw.geometry(
                f"+{bx - tw.winfo_width() - 6}"
                f"+{by + (self._box - tw.winfo_height()) // 2}"
            )
        except Exception:
            self._tooltip = None

    def _hide_tooltip(self, event=None) -> None:
        if self._tooltip is not None:
            self._tooltip.destroy()
            self._tooltip = None

    # -- Drag (with pin support) --

    def _on_drag_start(self, event) -> None:
        if self._config.get("pinned"):
            return
        self._drag_x = event.x
        self._drag_y = event.y
        self._hide_tooltip()

    def _on_drag_motion(self, event) -> None:
        if self._config.get("pinned"):
            return
        x = self.root.winfo_x() + (event.x - self._drag_x)
        y = self.root.winfo_y() + (event.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")
        self._config["overlay_x"] = x
        self._config["overlay_y"] = y

    def _on_double_click(self, event) -> None:
        if self.on_double_click_cb:
            self.on_double_click_cb()

    # -- Window flags --

    def _apply_no_activate(self) -> None:
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass
        self._reassert_topmost()

    def _reassert_topmost(self) -> None:
        try:
            if self._visible:
                self.root.attributes("-topmost", False)
                self.root.attributes("-topmost", True)
        except Exception:
            pass
        self.root.after(30_000, self._reassert_topmost)

    # -- Visibility --

    def toggle_visible(self) -> None:
        self.root.after(0, self._toggle_visible)

    def _toggle_visible(self) -> None:
        if self._visible:
            self.root.withdraw()
            self._visible = False
        else:
            self.root.deiconify()
            self._visible = True
        self._config["visible"] = self._visible

    # -- State + smooth transitions --

    def set_state(self, state: AppState) -> None:
        self.root.after(0, self._apply_state, state)

    def flash_success(self) -> None:
        self.root.after(0, self._do_flash_success)

    def _do_flash_success(self) -> None:
        self._set_bg_color(COLOR_BG_SUCCESS)
        self._set_bar_heights(self._idle_bars(), COLOR_BAR_SUCCESS)
        self.root.after(400, self._end_flash_success)

    def _end_flash_success(self) -> None:
        if self._state == AppState.IDLE:
            self._set_bg_color(COLOR_BG_IDLE)
            self._set_bar_heights(self._idle_bars(), COLOR_BAR_IDLE)
            self._fade_to(0.9)

    def _apply_state(self, state: AppState) -> None:
        self._state = state
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None

        if state == AppState.IDLE:
            self._set_bg_color(COLOR_BG_IDLE)
            self._set_bar_heights(self._idle_bars(), COLOR_BAR_IDLE)
            self._fade_to(0.9)
        elif state == AppState.RECORDING:
            _beep(*_BEEP_START)
            self._fade_to(1.0)
            self._set_bg_color(COLOR_BG_REC)
            self._animate_recording()
        elif state == AppState.TRANSCRIBING:
            _beep(*_BEEP_STOP)
            self._fade_to(1.0)
            self._set_bg_color(COLOR_BG_TRANS)
            self._animate_transcribing()

    def _fade_to(self, target: float, steps: int = 6) -> None:
        try:
            current = float(self.root.attributes("-alpha"))
        except Exception:
            current = 1.0
        if abs(current - target) < 0.02:
            self.root.attributes("-alpha", target)
            return
        delta = (target - current) / steps
        self._fade_step(current + delta, delta, steps - 1, target)

    def _fade_step(self, val: float, delta: float, remaining: int,
                   target: float) -> None:
        try:
            self.root.attributes("-alpha", val)
        except Exception:
            return
        if remaining <= 0:
            self.root.attributes("-alpha", target)
            return
        self.root.after(25, self._fade_step, val + delta, delta,
                        remaining - 1, target)

    # -- Animations --

    def _animate_recording(self) -> None:
        p = self._preset
        heights = []
        for lvl in self._audio_levels:
            h = int(p["bar_min"] + (p["bar_max"] - p["bar_min"]) * min(lvl, 1.0))
            heights.append(max(p["bar_min"], h))
        self._set_bar_heights(heights, COLOR_BAR_REC)
        self._animation_id = self.root.after(80, self._animate_recording)

    def _animate_transcribing(self) -> None:
        p = self._preset
        t = time.time() * 3
        heights = [
            int(p["bar_min"] + (p["bar_max"] - p["bar_min"])
                * 0.5 * (1 + math.sin(t + i * 0.8)))
            for i in range(p["bar_count"])
        ]
        self._set_bar_heights(heights, COLOR_BAR_TRANS)
        self._animation_id = self.root.after(80, self._animate_transcribing)

    # -- Text preview popup --

    def show_preview(self, text: str) -> None:
        self.root.after(0, self._show_preview, text)

    def _show_preview(self, text: str) -> None:
        self._hide_preview()
        try:
            pw = tk.Toplevel(self.root)
            pw.overrideredirect(True)
            pw.attributes("-topmost", True)
            pw.config(bg="#1a1a1a")
            preview = text[:120] + ("..." if len(text) > 120 else "")
            tk.Label(
                pw, text=preview, bg="#1a1a1a", fg="#e5e5e5",
                font=("Segoe UI", 9), padx=12, pady=8,
                wraplength=300, justify="left",
            ).pack()
            pw.update_idletasks()
            bx = self.root.winfo_x()
            by = self.root.winfo_y() + self._box + 8
            pw.geometry(f"+{bx - pw.winfo_width() + self._box}+{by}")
            self._preview_win = pw
            self.root.after(3000, self._hide_preview)
        except Exception:
            pass

    def _hide_preview(self) -> None:
        if self._preview_win:
            try:
                self._preview_win.destroy()
            except Exception:
                pass
            self._preview_win = None

    # -- Resize --

    def resize(self, size_name: str) -> None:
        self.root.after(0, self._do_resize, size_name)

    def _do_resize(self, size_name: str) -> None:
        preset = SIZE_PRESETS.get(size_name)
        if not preset:
            return
        self._preset = preset
        self._box = preset["box"]
        self._audio_levels = [0.0] * preset["bar_count"]
        self.canvas.config(width=self._box, height=self._box)
        self._draw_all()
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{self._box}x{self._box}+{x}+{y}")
        if self._state == AppState.IDLE:
            self._set_bg_color(COLOR_BG_IDLE)
            self._set_bar_heights(self._idle_bars(), COLOR_BAR_IDLE)

    # -- History popup --

    def show_history(self, history: list[tuple[datetime, str]]) -> None:
        self.root.after(0, self._build_history_popup, history)

    def _build_history_popup(self, history: list[tuple[datetime, str]]) -> None:
        if self._history_win is not None:
            self._close_history()
            return

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.config(bg="#1a1a1a")
        self._history_win = win

        _W = 360

        title_frame = tk.Frame(win, bg="#1a1a1a")
        title_frame.pack(fill="x", padx=12, pady=(10, 4))
        tk.Label(
            title_frame, text="History", bg="#1a1a1a", fg="#a3a3a3",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        close_btn = tk.Label(
            title_frame, text=" X ", bg="#1a1a1a", fg="#737373",
            font=("Segoe UI", 9), cursor="hand2",
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._close_history())

        if not history:
            tk.Label(
                win, text="No transcriptions yet", bg="#1a1a1a", fg="#525252",
                font=("Segoe UI", 9), pady=20,
            ).pack()
        else:
            canvas = tk.Canvas(win, bg="#1a1a1a", highlightthickness=0, bd=0,
                               width=_W)
            scrollbar = tk.Scrollbar(win, orient="vertical",
                                     command=canvas.yview)
            scroll_frame = tk.Frame(canvas, bg="#1a1a1a")
            scroll_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
            )
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            last_date = None
            for idx, (ts, text) in enumerate(reversed(history)):
                real_idx = len(history) - 1 - idx
                date_str = ts.strftime("%Y-%m-%d")
                if date_str != last_date:
                    last_date = date_str
                    tk.Label(
                        scroll_frame, text=ts.strftime("%A %d %b %Y"),
                        bg="#1a1a1a", fg="#525252",
                        font=("Segoe UI", 8), anchor="w",
                    ).pack(fill="x", padx=12, pady=(8, 2))

                entry_frame = tk.Frame(scroll_frame, bg="#262626",
                                       cursor="hand2")
                entry_frame.pack(fill="x", padx=8, pady=2)
                tk.Label(
                    entry_frame, text=ts.strftime("%H:%M"), bg="#262626",
                    fg="#737373", font=("Segoe UI", 8), anchor="nw",
                ).pack(side="left", padx=(8, 6), pady=4)
                lbl = tk.Label(
                    entry_frame, text=text, bg="#262626", fg="#e5e5e5",
                    font=("Segoe UI", 9), anchor="w",
                    wraplength=260, justify="left",
                )
                lbl.pack(side="left", fill="x", expand=True, padx=(0, 8),
                         pady=4)
                for widget in (entry_frame, lbl):
                    widget.bind(
                        "<Button-1>",
                        lambda e, t=text: self._copy_from_history(t),
                    )
                    widget.bind(
                        "<Button-3>",
                        lambda e, ri=real_idx: self._delete_history_entry(ri),
                    )

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)

        win.update_idletasks()
        bx = self.root.winfo_x()
        by = self.root.winfo_y()
        win_h = min(win.winfo_height(), 420)
        win.geometry(f"{_W}x{win_h}+{bx - _W - 8}+{by}")

    def _copy_from_history(self, text: str) -> None:
        set_clipboard(text)
        self._close_history()

    def _delete_history_entry(self, real_idx: int) -> None:
        if self.on_history_delete_cb:
            self.on_history_delete_cb(real_idx)
        self._close_history()

    def _close_history(self) -> None:
        if self._history_win is not None:
            try:
                self.root.unbind_all("<MouseWheel>")
                self._history_win.destroy()
            except Exception:
                pass
            self._history_win = None

    # -- Shortcuts dialog --

    def show_shortcuts(self) -> None:
        self.root.after(0, self._build_shortcuts)

    def _build_shortcuts(self) -> None:
        if self._shortcuts_win is not None:
            try:
                self._shortcuts_win.destroy()
            except Exception:
                pass
            self._shortcuts_win = None
            return

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.config(bg="#1a1a1a")
        self._shortcuts_win = win

        tk.Label(
            win, text="Keyboard Shortcuts", bg="#1a1a1a", fg="#a3a3a3",
            font=("Segoe UI", 11, "bold"),
        ).pack(padx=20, pady=(16, 8))

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
            row = tk.Frame(win, bg="#1a1a1a")
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(
                row, text=key, bg="#1a1a1a", fg="#fbbf24",
                font=("Consolas", 9), width=22, anchor="w",
            ).pack(side="left")
            tk.Label(
                row, text=desc, bg="#1a1a1a", fg="#d4d4d4",
                font=("Segoe UI", 9), anchor="w",
            ).pack(side="left")

        close_btn = tk.Label(
            win, text="Close", bg="#333", fg="#e5e5e5",
            font=("Segoe UI", 9), padx=16, pady=6, cursor="hand2",
        )
        close_btn.pack(pady=(12, 16))
        close_btn.bind("<Button-1>", lambda e: self._close_shortcuts())

        win.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        ww = win.winfo_width()
        wh = win.winfo_height()
        win.geometry(f"+{(sw - ww) // 2}+{(sh - wh) // 2}")

    def _close_shortcuts(self) -> None:
        if self._shortcuts_win:
            try:
                self._shortcuts_win.destroy()
            except Exception:
                pass
            self._shortcuts_win = None

    # -- Run / quit --

    def run(self) -> None:
        self.root.mainloop()

    def quit(self) -> None:
        self.root.after(0, self.root.destroy)
