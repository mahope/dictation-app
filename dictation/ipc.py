"""JSON-lines IPC handler for headless (sidecar) mode.

Reads commands from stdin, dispatches to engine/config, and emits events on
stdout.  All regular print() output is redirected to stderr so stdout stays
clean for the IPC protocol.
"""

import json
import sys
import threading
from datetime import datetime


class JsonIpc:
    """Bidirectional JSON-lines IPC over stdin/stdout."""

    def __init__(self, config, engine=None, overlay=None):
        self._config = config
        self._engine = engine
        self._overlay = overlay
        self._original_stdout = sys.__stdout__

    def set_engine(self, engine):
        self._engine = engine

    def set_overlay(self, overlay):
        self._overlay = overlay

    # -- Outbound events (Python → Tauri) --

    def emit(self, event: str, **kwargs):
        """Send a JSON event to Tauri via stdout."""
        msg = {"event": event}
        msg.update(kwargs)
        try:
            line = json.dumps(msg, ensure_ascii=False, default=str)
            self._original_stdout.write(line + "\n")
            self._original_stdout.flush()
        except Exception:
            pass

    def emit_config(self):
        self.emit("config", data=self._config.as_dict())

    def emit_history(self):
        if self._engine is None:
            self.emit("history", data=[])
            return
        entries = [
            [ts.isoformat(), text] for ts, text in self._engine.history
        ]
        self.emit("history", data=entries)

    def emit_stats(self):
        if self._engine is None:
            self.emit("stats", data={"count": 0, "words": 0, "history": 0})
            return
        self.emit("stats", data={
            "count": self._engine.session_count,
            "words": self._engine.session_words,
            "history": len(self._engine.history),
        })

    def emit_devices(self):
        from .config import get_input_devices
        devices = get_input_devices()
        self.emit("devices", data=devices)

    def emit_state(self, state_name: str):
        self.emit("state_changed", state=state_name)

    # -- Inbound commands (Tauri → Python) --

    def _dispatch(self, msg: dict):
        """Handle a single inbound command."""
        cmd = msg.get("cmd", "")

        if cmd == "get_config":
            self.emit_config()

        elif cmd == "set_config":
            key = msg.get("key")
            value = msg.get("value")
            if key is not None:
                self._config.set(key, value)
                self._config.save()
                self.emit_config()

        elif cmd == "get_history":
            self.emit_history()

        elif cmd == "delete_history":
            index = msg.get("index")
            if self._engine and index is not None:
                try:
                    self._engine._delete_history_entry(index)
                except (IndexError, AttributeError):
                    pass
            self.emit_history()

        elif cmd == "clear_history":
            if self._engine:
                self._engine.clear_history()
            self.emit_history()

        elif cmd == "export_history":
            if self._engine:
                self._engine.export_history()

        elif cmd == "get_devices":
            self.emit_devices()

        elif cmd == "get_stats":
            self.emit_stats()

        elif cmd == "toggle_overlay":
            if self._overlay:
                current = self._config.get("visible", True)
                new_val = not current
                self._config.set("visible", new_val)
                self._config.save()
                if new_val:
                    self._overlay.root.after(0, self._overlay.root.deiconify)
                else:
                    self._overlay.root.after(0, self._overlay.root.withdraw)

        else:
            self.emit("error", message=f"unknown command: {cmd}")

    def start_reader(self):
        """Start reading JSON-lines from stdin in a background thread."""
        def reader():
            try:
                for line in sys.stdin:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                        self._dispatch(msg)
                    except json.JSONDecodeError:
                        self.emit("error", message=f"invalid JSON: {line}")
            except Exception:
                pass  # stdin closed

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        return t
