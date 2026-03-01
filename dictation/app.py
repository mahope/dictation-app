"""Main entry point — orchestrates startup, first-run flow, and shutdown."""

import os
import sys
import threading

from dotenv import load_dotenv

from .config import (
    ConfigManager, TeeWriter, LOG_FILE, ENV_FILE, MODEL,
    is_startup_enabled, set_startup_enabled,
)
from .engine import DictationEngine, initialize_openai
from .hotkeys import HotkeyManager
from .overlay import DictationOverlay
import dictation.overlay as _overlay_mod


def _run_headless() -> None:
    """Run in headless IPC mode (used as Tauri sidecar)."""
    from .ipc import JsonIpc

    # Redirect all print() to stderr so stdout is clean for IPC
    sys.stdout = sys.stderr

    load_dotenv(ENV_FILE)
    config = ConfigManager()
    _overlay_mod.quiet_mode = config.get("quiet", False)

    ipc = JsonIpc(config)

    # Create overlay (tkinter) — still needed for visual feedback
    overlay = DictationOverlay(config)
    ipc.set_overlay(overlay)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    has_valid_key = bool(api_key) and api_key != "your-api-key-here"

    if has_valid_key:
        initialize_openai(api_key)
        engine = DictationEngine(overlay, config)
        config.add_listener(engine.on_config_changed)
        ipc.set_engine(engine)

        hotkeys = HotkeyManager(engine)
        hotkeys.start()

    # Start reading IPC commands from stdin
    ipc.start_reader()

    # Signal readiness
    ipc.emit("ready")
    if has_valid_key:
        ipc.emit_config()

    print("Headless engine started.", file=sys.stderr, flush=True)

    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        config.save()
        print("Headless engine exited.", file=sys.stderr, flush=True)


def main() -> None:
    # Check for --headless flag (sidecar mode)
    if "--headless" in sys.argv:
        _run_headless()
        return

    from .settings_gui import SettingsWindow
    from .tray import setup_tray

    # Load .env
    load_dotenv(ENV_FILE)

    config = ConfigManager()
    _overlay_mod.quiet_mode = config.get("quiet", False)

    # Set up file logging if enabled
    if config.get("log_to_file"):
        try:
            lf = open(LOG_FILE, "a", encoding="utf-8")
            sys.stdout = TeeWriter(sys.stdout, lf)
            sys.stderr = TeeWriter(sys.stderr, lf)
        except Exception:
            pass

    # Sync startup registry
    if config.get("start_at_startup") and not is_startup_enabled():
        set_startup_enabled(True)

    print("=" * 50, flush=True)
    print("  Dictation Tool", flush=True)
    print("  Toggle:     Ctrl+Shift+D", flush=True)
    print("  Hold:       Ctrl+Shift+Space", flush=True)
    print("  Append:     Ctrl+Shift+A", flush=True)
    print("  Cancel:     Ctrl+Shift+Escape", flush=True)
    print("  Undo:       Ctrl+Shift+Z", flush=True)
    print("  History:    Ctrl+Shift+H", flush=True)
    print(f"  Model:      {MODEL}", flush=True)
    print("  Language:   Danish + English (auto)", flush=True)
    print("  Dbl-click overlay to copy last", flush=True)
    print("  Right-click tray icon for settings", flush=True)
    print("=" * 50, flush=True)

    # Always create overlay (it owns the tkinter mainloop)
    overlay = DictationOverlay(config)

    # Check for valid API key
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    has_valid_key = bool(api_key) and api_key != "your-api-key-here"

    # Mutable container so nested functions can share state
    state = {
        "engine": None,
        "hotkeys": None,
        "tray": None,
        "settings": None,
    }

    def start_engine(key: str) -> None:
        """Initialize OpenAI and start engine, hotkeys, tray."""
        initialize_openai(key)

        engine = DictationEngine(overlay, config)
        config.add_listener(engine.on_config_changed)
        state["engine"] = engine

        hotkeys = HotkeyManager(engine)
        hotkeys.start()
        state["hotkeys"] = hotkeys

        # Build settings window (reusable, hidden by default)
        settings = SettingsWindow(
            overlay.root, config,
            on_api_key_saved=on_api_key_saved,
            engine=engine,
            overlay=overlay,
        )
        state["settings"] = settings

        tray = setup_tray(engine, overlay, config,
                          on_open_settings=lambda: settings.show())
        tray_thread = threading.Thread(target=tray.run, daemon=True)
        tray_thread.start()
        state["tray"] = tray

        print("Engine started.", flush=True)

    def on_api_key_saved(key: str) -> None:
        """Called from SettingsWindow when user saves a validated key."""
        os.environ["OPENAI_API_KEY"] = key
        if state["engine"] is None:
            # First-run: start everything
            start_engine(key)
        else:
            # Re-init OpenAI clients with new key
            initialize_openai(key)
            print("API key updated.", flush=True)

    if has_valid_key:
        start_engine(api_key)
    else:
        # First-run: show settings window on API Key tab
        print("No API key found — opening settings...", flush=True)
        settings = SettingsWindow(
            overlay.root, config,
            on_api_key_saved=on_api_key_saved,
            engine=None,
            overlay=overlay,
        )
        state["settings"] = settings
        overlay.root.after(100, lambda: settings.show(tab_index=0))

    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...", flush=True)
        config.save()
        engine = state.get("engine")
        if engine and engine.stream is not None:
            try:
                engine.stream.stop()
                engine.stream.close()
            except Exception:
                pass
        tray = state.get("tray")
        if tray:
            try:
                tray.stop()
            except Exception:
                pass
        print("Exited.", flush=True)
