"""Configuration management, constants, startup registry, and log tee."""

import json
import os
import sys
import winreg

# ---------------------------------------------------------------------------
# Paths — resolved relative to the *top-level* entry point (dictation.py)
# so that .env / config.json / history.json stay next to the executable.
# ---------------------------------------------------------------------------

if getattr(sys, "frozen", False):
    # PyInstaller onefile: exe location
    _DIR = os.path.dirname(sys.executable)
else:
    _DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORY_FILE = os.path.join(_DIR, "history.json")
HISTORY_MAX = 200
CONFIG_FILE = os.path.join(_DIR, "config.json")
LOG_FILE = os.path.join(_DIR, "dictation.log")
ENV_FILE = os.path.join(_DIR, ".env")

SAMPLE_RATE = 16000
MODEL = "gpt-4o-transcribe"

_SILENCE_RMS_THRESHOLD = 300

# ---------------------------------------------------------------------------
# Default config values
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG = {
    "smart_format": True,
    "device_index": None,
    "overlay_x": None,
    "overlay_y": None,
    "visible": True,
    "silence_detection": True,
    "silence_duration": 2.0,
    "start_at_startup": False,
    "quiet": False,
    "auto_copy": False,
    "pinned": False,
    "overlay_size": "normal",
    "log_to_file": False,
}

# ---------------------------------------------------------------------------
# ConfigManager — observable config wrapper
# ---------------------------------------------------------------------------


class ConfigManager:
    """Observable wrapper around the config dict.

    Supports ``get`` / ``set`` with listener notifications so that engine,
    overlay, and tray can react to changes in real-time (e.g. from the
    settings GUI).
    """

    def __init__(self) -> None:
        self._data: dict = _load_config()
        self._listeners: list = []

    # -- dict-like access --

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        old = self._data.get(key)
        self._data[key] = value
        if old != value:
            self._notify(key, value)

    def update(self, mapping: dict) -> None:
        for k, v in mapping.items():
            self.set(k, v)

    def as_dict(self) -> dict:
        return dict(self._data)

    # -- Listener support --

    def add_listener(self, callback) -> None:
        """Register ``callback(key, value)`` to be called on changes."""
        self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        self._listeners = [cb for cb in self._listeners if cb is not callback]

    def _notify(self, key: str, value) -> None:
        for cb in self._listeners:
            try:
                cb(key, value)
            except Exception as e:
                print(f"Config listener error: {e}", file=sys.stderr, flush=True)

    # -- Persistence --

    def save(self) -> None:
        _save_config(self._data)

    def reload(self) -> None:
        self._data = _load_config()

    # -- Convenience for dict-style access used by existing code --

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self._data


# ---------------------------------------------------------------------------
# Low-level load / save
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        return {**_DEFAULT_CONFIG, **saved}
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return dict(_DEFAULT_CONFIG)


def _save_config(config: dict) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Config save error: {e}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Log tee (optional file logging)
# ---------------------------------------------------------------------------


class TeeWriter:
    """Tee stdout/stderr to a log file while preserving console output."""

    def __init__(self, original, log_file):
        self.original = original
        self.log_file = log_file

    def write(self, msg):
        self.original.write(msg)
        if self.log_file and msg.strip():
            try:
                self.log_file.write(msg)
            except Exception:
                pass

    def flush(self):
        self.original.flush()
        if self.log_file:
            try:
                self.log_file.flush()
            except Exception:
                pass

    @property
    def encoding(self):
        return getattr(self.original, "encoding", "utf-8")


# ---------------------------------------------------------------------------
# Windows startup registry
# ---------------------------------------------------------------------------

_STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_APP_NAME = "DictationTool"


def is_startup_enabled() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, _STARTUP_APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_startup_enabled(enabled: bool) -> None:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE,
        )
        if enabled:
            script = os.path.abspath(os.path.join(_DIR, "dictation.py"))
            cmd = f'pythonw "{script}"'
            winreg.SetValueEx(key, _STARTUP_APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, _STARTUP_APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Startup registry error: {e}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Audio device enumeration (shared between tray and settings_gui)
# ---------------------------------------------------------------------------


def get_input_devices() -> list[tuple[int, str]]:
    import sounddevice as sd
    devices = []
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            name = dev["name"]
            if len(name) > 40:
                name = name[:37] + "..."
            devices.append((i, name))
    return devices
