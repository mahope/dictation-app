#!/usr/bin/env python3
"""
System-wide Windows dictation tool.

Press Ctrl+Shift+D to start recording, press again to stop.
Transcribes via OpenAI gpt-4o-transcribe and pastes into the active text input.
Shows a small floating overlay (pill) instead of toast notifications.
Supports both Danish and English dictation.
"""

import ctypes
from ctypes import wintypes
from enum import Enum, auto
import os
import sys
import tempfile
import threading
import time
import tkinter as tk

import numpy as np
import scipy.io.wavfile as wavfile
import sounddevice as sd
from dotenv import load_dotenv
from openai import OpenAI
from pynput import keyboard

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY or OPENAI_API_KEY == "your-api-key-here":
    print("ERROR: Set your OPENAI_API_KEY in .env", file=sys.stderr)
    sys.exit(1)

SAMPLE_RATE = 16000  # 16 kHz mono — what Whisper expects
MODEL = "gpt-4o-transcribe"
HOTKEY = "<ctrl>+<shift>+d"

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------


class AppState(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()


# ---------------------------------------------------------------------------
# Floating overlay (pill indicator)
# ---------------------------------------------------------------------------

# Win32 constants for non-activating, tool window
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_TOPMOST = 0x00000008

_PILL_W = 48
_PILL_H = 28
_CORNER = 14  # half of height for full rounding
_MARGIN = 16  # distance from screen edge

_COLOR_IDLE = "#6b7280"       # gray-500
_COLOR_RECORDING = "#ef4444"  # red-500
_COLOR_TRANSCRIBING = "#f59e0b"  # amber-500
_COLOR_TEXT = "#ffffff"


class DictationOverlay:
    """Tiny always-on-top pill overlay that shows dictation state."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Dictation")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.92)

        # Transparent background via a color key
        self._trans_color = "#f0f0f0"
        self.root.config(bg=self._trans_color)
        self.root.attributes("-transparentcolor", self._trans_color)

        # Canvas for the pill shape
        self.canvas = tk.Canvas(
            self.root,
            width=_PILL_W,
            height=_PILL_H,
            bg=self._trans_color,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        # Draw pill
        self._pill = self._rounded_rect(
            2, 2, _PILL_W - 2, _PILL_H - 2, _CORNER, fill=_COLOR_IDLE, outline=""
        )
        # Text label (hidden initially)
        self._text = self.canvas.create_text(
            _PILL_W // 2, _PILL_H // 2,
            text="",
            fill=_COLOR_TEXT,
            font=("Segoe UI", 8, "bold"),
        )

        # Position: top-right corner of primary monitor
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - _PILL_W - _MARGIN
        y = _MARGIN
        self.root.geometry(f"{_PILL_W}x{_PILL_H}+{x}+{y}")

        # After window is mapped, apply Win32 extended styles so we don't steal focus
        self.root.after(10, self._apply_no_activate)

        # Animation state
        self._pulse_on = True
        self._dots_count = 0
        self._animation_id: str | None = None
        self._state = AppState.IDLE

    def _apply_no_activate(self) -> None:
        """Set WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW so the overlay never steals focus."""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass  # non-critical

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def set_state(self, state: AppState) -> None:
        """Thread-safe state update — schedules UI work on the main thread."""
        self.root.after(0, self._apply_state, state)

    def _apply_state(self, state: AppState) -> None:
        self._state = state
        # Cancel any running animation
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None

        if state == AppState.IDLE:
            self.canvas.itemconfig(self._pill, fill=_COLOR_IDLE)
            self.canvas.itemconfig(self._text, text="")
        elif state == AppState.RECORDING:
            self._pulse_on = True
            self.canvas.itemconfig(self._text, text="REC")
            self._animate_recording()
        elif state == AppState.TRANSCRIBING:
            self._dots_count = 0
            self.canvas.itemconfig(self._pill, fill=_COLOR_TRANSCRIBING)
            self._animate_transcribing()

    def _animate_recording(self) -> None:
        """Pulse between red and dark-red."""
        color = _COLOR_RECORDING if self._pulse_on else "#b91c1c"
        self.canvas.itemconfig(self._pill, fill=color)
        self._pulse_on = not self._pulse_on
        self._animation_id = self.root.after(500, self._animate_recording)

    def _animate_transcribing(self) -> None:
        """Cycle through ., .., ..."""
        self._dots_count = (self._dots_count % 3) + 1
        self.canvas.itemconfig(self._text, text="." * self._dots_count)
        self._animation_id = self.root.after(400, self._animate_transcribing)

    def run(self) -> None:
        """Start the tkinter mainloop (must be called from main thread)."""
        self.root.mainloop()

    def quit(self) -> None:
        """Destroy the overlay (thread-safe)."""
        self.root.after(0, self.root.destroy)


# ---------------------------------------------------------------------------
# Text injection (clipboard + Ctrl+V, then restore)
# ---------------------------------------------------------------------------

_CF_UNICODETEXT = 13
_GMEM_MOVEABLE = 0x0002
_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_kernel32.GlobalAlloc.restype = ctypes.c_void_p
_kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
_kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
_user32.GetClipboardData.restype = ctypes.c_void_p
_user32.GetClipboardData.argtypes = [wintypes.UINT]
_user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]


def _get_clipboard() -> str:
    """Read current clipboard contents (plain text, Unicode-safe via Win32)."""
    try:
        _user32.OpenClipboard(0)
        h = _user32.GetClipboardData(_CF_UNICODETEXT)
        if h:
            p = _kernel32.GlobalLock(h)
            text = ctypes.wstring_at(p)
            _kernel32.GlobalUnlock(h)
        else:
            text = ""
        _user32.CloseClipboard()
        return text
    except Exception:
        try:
            _user32.CloseClipboard()
        except Exception:
            pass
        return ""


def _set_clipboard(text: str) -> None:
    """Write text to the clipboard (Unicode-safe via Win32)."""
    try:
        _user32.OpenClipboard(0)
        _user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        h = _kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(data))
        p = _kernel32.GlobalLock(h)
        ctypes.memmove(p, data, len(data))
        _kernel32.GlobalUnlock(h)
        _user32.SetClipboardData(_CF_UNICODETEXT, h)
        _user32.CloseClipboard()
    except Exception as e:
        try:
            _user32.CloseClipboard()
        except Exception:
            pass
        print(f"Clipboard error: {e}", file=sys.stderr)


def inject_text(text: str) -> None:
    """Paste text into the currently focused input, then restore clipboard."""
    original_clipboard = _get_clipboard()

    _set_clipboard(text)
    time.sleep(0.05)  # let pasteboard propagate

    # Simulate Ctrl+V
    kb = keyboard.Controller()
    with kb.pressed(keyboard.Key.ctrl):
        kb.press("v")
        kb.release("v")

    time.sleep(0.25)  # wait for paste to complete

    # Restore original clipboard
    _set_clipboard(original_clipboard)


# ---------------------------------------------------------------------------
# Dictation engine
# ---------------------------------------------------------------------------


class DictationEngine:
    """Manages recording, transcription, and state transitions."""

    def __init__(self, overlay: DictationOverlay) -> None:
        self.overlay = overlay
        self.state = AppState.IDLE
        self.audio_chunks: list[np.ndarray] = []
        self.stream: sd.InputStream | None = None
        self.lock = threading.Lock()

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            print(f"sounddevice status: {status}", file=sys.stderr)
        self.audio_chunks.append(indata.copy())

    def _start_recording(self) -> None:
        self.audio_chunks = []
        self.overlay.set_state(AppState.RECORDING)
        print("Recording... press Ctrl+Shift+D to stop")
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            callback=self._audio_callback,
        )
        self.stream.start()

    def _stop_recording(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.overlay.set_state(AppState.TRANSCRIBING)
        print("Stopped recording - transcribing...")

    def _transcribe(self, audio: np.ndarray) -> str:
        """Write audio to a temp WAV file, send to OpenAI, return text."""
        tmp = os.path.join(tempfile.gettempdir(), "dictation_recording.wav")
        wavfile.write(tmp, SAMPLE_RATE, audio)

        with open(tmp, "rb") as f:
            result = client.audio.transcriptions.create(
                model=MODEL,
                file=f,
                response_format="text",
                prompt="Transcribe exactly as spoken. The speaker may use Danish or English.",
            )

        os.remove(tmp)
        return result.strip() if isinstance(result, str) else result.text.strip()

    def _process_recording(self) -> None:
        """Transcribe the recorded audio and inject the result."""
        try:
            if not self.audio_chunks:
                print("No audio captured.", file=sys.stderr)
                return

            audio = np.concatenate(self.audio_chunks, axis=0)
            duration = len(audio) / SAMPLE_RATE
            if duration < 0.3:
                print("Recording too short, skipping.", file=sys.stderr)
                return

            text = self._transcribe(audio)
            if text:
                print(f"Transcribed: {text}")
                inject_text(text)
            else:
                print("Empty transcription result.", file=sys.stderr)
        except Exception as e:
            print(f"Transcription error: {e}", file=sys.stderr)
        finally:
            self.overlay.set_state(AppState.IDLE)

    def on_toggle(self) -> None:
        with self.lock:
            if self.state != AppState.RECORDING:
                self.state = AppState.RECORDING
                self._start_recording()
            else:
                self.state = AppState.TRANSCRIBING
                self._stop_recording()
                threading.Thread(target=self._process_recording, daemon=True).start()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 50)
    print("  Dictation Tool")
    print(f"  Hotkey: {HOTKEY}")
    print(f"  Model:  {MODEL}")
    print("  Language: Danish + English (auto)")
    print("  Press Ctrl+C to quit")
    print("=" * 50)

    overlay = DictationOverlay()
    engine = DictationEngine(overlay)

    # Start hotkey listener in a daemon thread
    hotkey_listener = keyboard.GlobalHotKeys({HOTKEY: engine.on_toggle})
    hotkey_listener.daemon = True
    hotkey_listener.start()

    # Run tkinter mainloop on the main thread (required by tkinter on Windows)
    try:
        overlay.run()
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
