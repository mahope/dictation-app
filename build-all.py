"""
Build the complete Dictation app (Tauri + Python sidecar).

Steps:
  1. PyInstaller → dictation-engine.exe
  2. Copy to dictation-app/src-tauri/binaries/
  3. npm run tauri build → Dictation.exe

Usage:
    python build-all.py
"""

import os
import platform
import shutil
import subprocess
import sys

_DIR = os.path.dirname(os.path.abspath(__file__))
_TAURI_DIR = os.path.join(_DIR, "dictation-app")
_TAURI_SRC = os.path.join(_TAURI_DIR, "src-tauri")
_BINARIES_DIR = os.path.join(_TAURI_SRC, "binaries")


def step(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def main():
    # Step 1: Build Python sidecar
    step("Step 1/3: Building dictation-engine.exe")
    subprocess.check_call([sys.executable, "build.py"], cwd=_DIR)

    engine_src = os.path.join(_DIR, "dist", "dictation-engine.exe")
    if not os.path.exists(engine_src):
        print("ERROR: dictation-engine.exe not found", file=sys.stderr)
        sys.exit(1)

    # Step 2: Copy to Tauri binaries dir with target triple suffix
    step("Step 2/3: Copying sidecar to Tauri binaries")
    os.makedirs(_BINARIES_DIR, exist_ok=True)

    # Tauri expects the binary name with target triple
    target_triple = "x86_64-pc-windows-msvc"
    dest_name = f"dictation-engine-{target_triple}.exe"
    dest_path = os.path.join(_BINARIES_DIR, dest_name)

    shutil.copy2(engine_src, dest_path)
    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    print(f"Copied: {dest_path} ({size_mb:.1f} MB)")

    # Step 3: Build Tauri app
    step("Step 3/3: Building Tauri app (npm run tauri build)")

    # Ensure npm dependencies are installed
    subprocess.check_call(["npm", "install"], cwd=_TAURI_DIR, shell=True)
    subprocess.check_call(
        ["npm", "run", "tauri", "build"],
        cwd=_TAURI_DIR,
        shell=True,
    )

    # Check for output
    bundle_dir = os.path.join(_TAURI_SRC, "target", "release", "bundle")
    nsis_dir = os.path.join(bundle_dir, "nsis")
    msi_dir = os.path.join(bundle_dir, "msi")

    print(f"\n{'='*60}")
    print("  Build complete!")
    print(f"{'='*60}")

    for d in [nsis_dir, msi_dir]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                fp = os.path.join(d, f)
                if os.path.isfile(fp):
                    size_mb = os.path.getsize(fp) / (1024 * 1024)
                    print(f"  {fp} ({size_mb:.1f} MB)")

    exe_path = os.path.join(_TAURI_SRC, "target", "release", "dictation-app.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"  Portable: {exe_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
