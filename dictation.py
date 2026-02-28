#!/usr/bin/env python3
"""
System-wide Windows dictation tool.

Press Ctrl+Shift+D to start recording, press again to stop.
Transcribes via OpenAI Whisper API and pastes into the active text input.
"""

import ctypes
from ctypes import wintypes
import os
import sys
import subprocess
import tempfile
import threading
import time
import winsound

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
# State
# ---------------------------------------------------------------------------

is_recording = False
audio_chunks = []
stream = None
lock = threading.Lock()

# ---------------------------------------------------------------------------
# Audio + visual feedback
# ---------------------------------------------------------------------------

def play_sound(name: str) -> None:
    """Play a Windows system sound asynchronously."""
    # Map friendly names to Windows system sounds
    sounds = {
        "Bottle": "SystemExclamation",
    }
    alias = sounds.get(name, "SystemDefault")
    try:
        winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        pass


def notify(title: str, message: str) -> None:
    """Show a Windows toast notification."""
    # Use PowerShell to trigger a Windows toast notification
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null; "
        f"$xml = '<toast><visual><binding template=\"ToastText02\"><text id=\"1\">{title}</text><text id=\"2\">{message}</text></binding></visual></toast>'; "
        "$doc = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$doc.LoadXml($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Dictation Tool').Show("
        "[Windows.UI.Notifications.ToastNotification]::new($doc))"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", ps_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def _audio_callback(indata: np.ndarray, frames: int, time_info, status) -> None:
    if status:
        print(f"sounddevice status: {status}", file=sys.stderr)
    audio_chunks.append(indata.copy())


def start_recording() -> None:
    global stream, audio_chunks
    audio_chunks = []
    play_sound("Bottle")
    notify("Dictation", "Recording... press Ctrl+Shift+D to stop")
    print("Recording... press Ctrl+Shift+D to stop")
    # Delay so the sound finishes before the audio input stream takes over
    time.sleep(0.8)
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        callback=_audio_callback,
    )
    stream.start()


def stop_recording() -> None:
    global stream
    if stream is not None:
        stream.stop()
        stream.close()
        stream = None
    play_sound("Bottle")
    notify("Dictation", "Stopped - transcribing...")
    print("Stopped recording - transcribing...")

# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe(audio: np.ndarray) -> str:
    """Write audio to a temp WAV file, send to OpenAI, return text."""
    tmp = os.path.join(tempfile.gettempdir(), "dictation_recording.wav")
    wavfile.write(tmp, SAMPLE_RATE, audio)

    with open(tmp, "rb") as f:
        result = client.audio.transcriptions.create(
            model=MODEL,
            file=f,
            response_format="text",
            language="da",
        )

    os.remove(tmp)
    return result.strip() if isinstance(result, str) else result.text.strip()

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
# Toggle handler (runs transcription in a thread)
# ---------------------------------------------------------------------------

def _process_recording() -> None:
    """Transcribe the recorded audio and inject the result."""
    if not audio_chunks:
        print("No audio captured.", file=sys.stderr)
        return

    audio = np.concatenate(audio_chunks, axis=0)
    duration = len(audio) / SAMPLE_RATE
    if duration < 0.3:
        print("Recording too short, skipping.", file=sys.stderr)
        return

    try:
        text = transcribe(audio)
        if text:
            print(f"Transcribed: {text}")
            # Show a short preview in the notification
            preview = text[:80] + ("..." if len(text) > 80 else "")
            notify("Dictation", preview)
            inject_text(text)
        else:
            print("Empty transcription result.", file=sys.stderr)
    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)


def on_toggle() -> None:
    global is_recording
    with lock:
        if not is_recording:
            is_recording = True
            start_recording()
        else:
            is_recording = False
            stop_recording()
            # Process in background thread so hotkey listener stays responsive
            threading.Thread(target=_process_recording, daemon=True).start()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 50)
    print("  Dictation Tool")
    print(f"  Hotkey: {HOTKEY}")
    print(f"  Model:  {MODEL}")
    print("  Press Ctrl+C to quit")
    print("=" * 50)

    with keyboard.GlobalHotKeys({HOTKEY: on_toggle}) as hotkey_listener:
        try:
            hotkey_listener.join()
        except KeyboardInterrupt:
            print("\nExiting.")


if __name__ == "__main__":
    main()
