"""Clipboard operations and text injection via Ctrl+V."""

import ctypes
from ctypes import wintypes
import sys
import time

from pynput import keyboard

# ---------------------------------------------------------------------------
# Win32 clipboard setup
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

_CLIPBOARD_RETRIES = 5
_CLIPBOARD_DELAY = 0.05


def get_clipboard() -> str:
    for attempt in range(_CLIPBOARD_RETRIES):
        try:
            _user32.OpenClipboard(0)
            try:
                h = _user32.GetClipboardData(_CF_UNICODETEXT)
                if h:
                    p = _kernel32.GlobalLock(h)
                    text = ctypes.wstring_at(p)
                    _kernel32.GlobalUnlock(h)
                else:
                    text = ""
                return text
            finally:
                _user32.CloseClipboard()
        except Exception:
            if attempt < _CLIPBOARD_RETRIES - 1:
                time.sleep(_CLIPBOARD_DELAY)
    return ""


def set_clipboard(text: str) -> None:
    for attempt in range(_CLIPBOARD_RETRIES):
        try:
            _user32.OpenClipboard(0)
            try:
                _user32.EmptyClipboard()
                data = text.encode("utf-16-le") + b"\x00\x00"
                h = _kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(data))
                p = _kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                _kernel32.GlobalUnlock(h)
                _user32.SetClipboardData(_CF_UNICODETEXT, h)
            finally:
                _user32.CloseClipboard()
            return
        except Exception as e:
            if attempt < _CLIPBOARD_RETRIES - 1:
                time.sleep(_CLIPBOARD_DELAY)
            else:
                print(f"Clipboard error after {_CLIPBOARD_RETRIES} attempts: "
                      f"{e}", file=sys.stderr, flush=True)


def inject_text(text: str, copy_only: bool = False) -> None:
    """Set clipboard and optionally paste via Ctrl+V."""
    original_clipboard = get_clipboard()
    set_clipboard(text)
    if copy_only:
        return
    time.sleep(0.05)
    kb = keyboard.Controller()
    with kb.pressed(keyboard.Key.ctrl):
        kb.press("v")
        kb.release("v")
    time.sleep(0.25)
    set_clipboard(original_clipboard)
