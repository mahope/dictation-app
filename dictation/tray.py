"""System tray icon and menu."""

import sys

from PIL import Image, ImageDraw
import pystray

from .config import (
    ConfigManager, TeeWriter, LOG_FILE, get_input_devices,
    is_startup_enabled, set_startup_enabled,
)
from .engine import DictationEngine
from .overlay import DictationOverlay
import dictation.overlay as _overlay_mod


def _create_tray_icon() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([2, 2, size - 2, size - 2], radius=12,
                           fill="#2d2d2d")
    bar_w, gap, bar_count = 6, 4, 5
    heights = [12, 20, 30, 20, 12]
    total_w = bar_count * bar_w + (bar_count - 1) * gap
    start_x = (size - total_w) // 2
    cy = size // 2
    for i in range(bar_count):
        x = start_x + i * (bar_w + gap)
        h = heights[i]
        draw.rounded_rectangle(
            [x, cy - h // 2, x + bar_w, cy + h // 2],
            radius=2, fill="#a3a3a3",
        )
    return img




def setup_tray(
    engine: DictationEngine,
    overlay: DictationOverlay,
    config: ConfigManager,
    *,
    on_open_settings=None,
) -> pystray.Icon:

    def on_toggle_overlay(icon, item):
        overlay.toggle_visible()
        config.save()

    def on_toggle_format(icon, item):
        config.set("smart_format", not config.get("smart_format", True))
        config.save()

    def on_toggle_silence(icon, item):
        config.set("silence_detection", not config.get("silence_detection", True))
        config.save()

    def on_toggle_quiet(icon, item):
        _overlay_mod.quiet_mode = not _overlay_mod.quiet_mode
        config.set("quiet", _overlay_mod.quiet_mode)
        config.save()

    def on_toggle_auto_copy(icon, item):
        config.set("auto_copy", not config.get("auto_copy", False))
        config.save()

    def on_toggle_pinned(icon, item):
        config.set("pinned", not config.get("pinned", False))
        config.save()

    def on_show_history(icon, item):
        overlay.show_history(engine.history)

    def on_clear_history(icon, item):
        engine.clear_history()

    def on_export_history(icon, item):
        engine.export_history()

    def on_show_shortcuts(icon, item):
        overlay.show_shortcuts()

    def on_select_device(index):
        def callback(icon, item):
            config.set("device_index", index)
            config.save()
        return callback

    def on_select_default_device(icon, item):
        config.set("device_index", None)
        config.save()

    def on_select_size(size_name):
        def callback(icon, item):
            config.set("overlay_size", size_name)
            config.save()
            overlay.resize(size_name)
        return callback

    def on_toggle_startup(icon, item):
        currently = is_startup_enabled()
        set_startup_enabled(not currently)
        config.set("start_at_startup", not currently)
        config.save()

    def on_toggle_logging(icon, item):
        new_val = not config.get("log_to_file", False)
        config.set("log_to_file", new_val)
        config.save()
        if new_val:
            try:
                lf = open(LOG_FILE, "a", encoding="utf-8")
                sys.stdout = TeeWriter(sys.stdout, lf)
                sys.stderr = TeeWriter(sys.stderr, lf)
                print(f"Logging enabled -> {LOG_FILE}", flush=True)
            except Exception:
                pass
        else:
            if isinstance(sys.stdout, TeeWriter):
                if sys.stdout.log_file:
                    sys.stdout.log_file.close()
                sys.stdout = sys.stdout.original
            if isinstance(sys.stderr, TeeWriter):
                if sys.stderr.log_file:
                    sys.stderr.log_file.close()
                sys.stderr = sys.stderr.original
            print("Logging disabled.", flush=True)

    def on_settings(icon, item):
        if on_open_settings:
            overlay.root.after(0, on_open_settings)

    def on_quit(icon, item):
        config.save()
        icon.stop()
        overlay.quit()

    def get_mic_menu():
        devices = get_input_devices()
        items = [
            pystray.MenuItem(
                "System default", on_select_default_device,
                checked=lambda item: engine.device_index is None,
            ),
        ]
        for idx, name in devices:
            items.append(pystray.MenuItem(
                name, on_select_device(idx),
                checked=lambda item, i=idx: engine.device_index == i,
            ))
        return pystray.Menu(*items)

    def get_size_menu():
        return pystray.Menu(
            pystray.MenuItem(
                "Small", on_select_size("small"),
                checked=lambda item: config.get("overlay_size") == "small",
            ),
            pystray.MenuItem(
                "Normal", on_select_size("normal"),
                checked=lambda item: config.get("overlay_size", "normal") == "normal",
            ),
            pystray.MenuItem(
                "Large", on_select_size("large"),
                checked=lambda item: config.get("overlay_size") == "large",
            ),
        )

    menu = pystray.Menu(
        pystray.MenuItem("Settings...", on_settings, default=True),
        pystray.MenuItem("Show/Hide overlay", on_toggle_overlay),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Smart formatting", on_toggle_format,
            checked=lambda item: config.get("smart_format", True),
        ),
        pystray.MenuItem(
            "Auto-stop on silence", on_toggle_silence,
            checked=lambda item: config.get("silence_detection", True),
        ),
        pystray.MenuItem(
            "Copy only (no paste)", on_toggle_auto_copy,
            checked=lambda item: config.get("auto_copy", False),
        ),
        pystray.MenuItem(
            "Mute sounds", on_toggle_quiet,
            checked=lambda item: _overlay_mod.quiet_mode,
        ),
        pystray.MenuItem(
            "Pin overlay position", on_toggle_pinned,
            checked=lambda item: config.get("pinned", False),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Microphone", get_mic_menu()),
        pystray.MenuItem("Overlay size", get_size_menu()),
        pystray.MenuItem(
            "Start at Windows startup", on_toggle_startup,
            checked=lambda item: is_startup_enabled(),
        ),
        pystray.MenuItem(
            "Log to file", on_toggle_logging,
            checked=lambda item: config.get("log_to_file", False),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("History (Ctrl+Shift+H)", on_show_history),
        pystray.MenuItem("Export history to Desktop", on_export_history),
        pystray.MenuItem("Clear history", on_clear_history),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Keyboard shortcuts", on_show_shortcuts),
        pystray.MenuItem("Quit", on_quit),
    )

    stats = (f"Dictation Tool | Session: {engine.session_count} "
             f"transcriptions, {engine.session_words} words")
    return pystray.Icon("Dictation", _create_tray_icon(), stats, menu)
