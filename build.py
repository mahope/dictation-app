"""
Build dictation.exe — a standalone Windows executable.

Usage:
    python build.py

Output:
    dist/Dictation.exe
"""

import subprocess
import sys
import os

_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # Generate icon if it doesn't exist
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
        print("\nTo use:")
        print("  1. Copy Dictation.exe wherever you like")
        print("  2. Double-click to run!")
        print("  3. Enter your OpenAI API key in the Settings window")
    else:
        print("Build failed - exe not found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
