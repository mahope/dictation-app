"""Global hotkey manager using pynput."""

import sys

from pynput import keyboard

from .engine import DictationEngine


class HotkeyManager:
    def __init__(self, engine: DictationEngine) -> None:
        self.engine = engine
        self._pressed: set = set()
        self._hold_active = False

    def _mods_held(self) -> bool:
        has_ctrl = (keyboard.Key.ctrl_l in self._pressed
                    or keyboard.Key.ctrl_r in self._pressed)
        has_shift = (keyboard.Key.shift_l in self._pressed
                     or keyboard.Key.shift_r in self._pressed)
        return has_ctrl and has_shift

    @staticmethod
    def _key_char(key) -> str | None:
        try:
            vk = getattr(key, "vk", None)
            if vk and 65 <= vk <= 90:
                return chr(vk).lower()
        except Exception:
            pass
        return None

    def on_press(self, key) -> None:
        try:
            self._pressed.add(key)
            if not self._mods_held():
                return
            ch = self._key_char(key)
            if ch == "d":
                self.engine.on_toggle()
            elif ch == "h":
                self.engine.overlay.show_history(self.engine.history)
            elif ch == "a":
                self.engine.on_toggle(append=True)
            elif ch == "z":
                self.engine.on_undo()
            elif key == keyboard.Key.space and not self._hold_active:
                self._hold_active = True
                self.engine.on_hold_start()
            elif key == keyboard.Key.esc:
                self.engine.on_cancel()
        except Exception as e:
            print(f"Hotkey press error: {e}", file=sys.stderr, flush=True)

    def on_release(self, key) -> None:
        try:
            self._pressed.discard(key)
            if key == keyboard.Key.space and self._hold_active:
                self._hold_active = False
                self.engine.on_hold_stop()
        except Exception as e:
            print(f"Hotkey release error: {e}", file=sys.stderr, flush=True)

    def start(self) -> None:
        listener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release,
        )
        listener.daemon = True
        listener.start()
