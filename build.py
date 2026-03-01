"""
Build the dictation engine — a standalone Windows executable.

Usage:
    python build.py                    # Build dictation-engine.exe (sidecar)
    python build.py --standalone       # Build Dictation.exe (standalone, legacy)

Output:
    dist/dictation-engine.exe   (default — used as Tauri sidecar)
    dist/Dictation.exe          (with --standalone)
"""

import subprocess
import sys
import os

_DIR = os.path.dirname(os.path.abspath(__file__))


def build_engine():
    """Build the sidecar engine executable."""
    icon_path = os.path.join(_DIR, "icon.ico")
    if not os.path.exists(icon_path):
        print("Generating icon...")
        subprocess.check_call([sys.executable, "generate_icon.py"], cwd=_DIR)

    print("Building dictation-engine.exe with PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--name", "dictation-engine",
        "--icon", icon_path,
        "--hidden-import", "pystray._win32",
        "--hidden-import", "scipy.io.wavfile",
        "--hidden-import", "scipy.io",
        "--collect-submodules", "dictation",
        "dictation.py",
    ]

    subprocess.check_call(cmd, cwd=_DIR)

    exe_path = os.path.join(_DIR, "dist", "dictation-engine.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\nBuild complete: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        return exe_path
    else:
        print("Build failed - exe not found.", file=sys.stderr)
        sys.exit(1)


def build_standalone():
    """Build the standalone exe (legacy mode with tray + settings GUI)."""
    icon_path = os.path.join(_DIR, "icon.ico")
    if not os.path.exists(icon_path):
        print("Generating icon...")
        subprocess.check_call([sys.executable, "generate_icon.py"], cwd=_DIR)

    print("Building Dictation.exe with PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--name", "Dictation",
        "--icon", icon_path,
        "--hidden-import", "pystray._win32",
        "--hidden-import", "scipy.io.wavfile",
        "--hidden-import", "scipy.io",
        "--collect-submodules", "dictation",
        "dictation.py",
    ]

    subprocess.check_call(cmd, cwd=_DIR)

    exe_path = os.path.join(_DIR, "dist", "Dictation.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\nBuild complete: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        return exe_path
    else:
        print("Build failed - exe not found.", file=sys.stderr)
        sys.exit(1)


def main():
    if "--standalone" in sys.argv:
        build_standalone()
    else:
        build_engine()


if __name__ == "__main__":
    main()
