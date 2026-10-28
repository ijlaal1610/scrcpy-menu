#!/usr/bin/env python3
"""
Fast standalone packaging script for scrcpy-menu using PyInstaller.
Builds a single-file executable bundling only QtCore, QtGui, and QtWidgets
while excluding unnecessary multi-hundred-megabyte modules (QtWebEngine, Qt3D, QtQml).
"""

import sys
import shutil
import subprocess
from pathlib import Path

# Ensure stdout and stderr handle utf-8 safely across Windows code pages
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def build():
    print("=" * 60)
    print(" [*] Building Scrcpy Control Center Standalone Executable")
    print("=" * 60)

    repo_dir = Path(__file__).resolve().parent
    entry_script = repo_dir / "scrcpy-menu"

    # Modules to explicitly exclude to keep build fast and binary compact
    excluded_modules = [
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtPdf",
        "PySide6.QtPdfWidgets",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtQuickWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.QtDesigner",
        "PySide6.QtHelp",
        "PySide6.QtTest",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtPositioning",
        "PySide6.QtBluetooth",
        "PySide6.QtNfc",
        "PySide6.QtSpatialAudio",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
    ]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=scrcpy-control-center",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--noupx",
        f"--paths={repo_dir}",
        "--hidden-import=scrcpy_menu",
        "--hidden-import=scrcpy_menu.core",
        "--hidden-import=scrcpy_menu.platform_adapters",
        "--hidden-import=scrcpy_menu.ui",
        "--hidden-import=scrcpy_menu.cli",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
    ]

    for mod in excluded_modules:
        cmd.append(f"--exclude-module={mod}")

    cmd.append(str(entry_script))

    print(f"Executing PyInstaller (excluding unused QtWebEngine/3D/Qml)...")
    res = subprocess.run(cmd, cwd=repo_dir)
    if res.returncode == 0:
        dist_dir = repo_dir / "dist"
        print("\n" + "=" * 60)
        print(" [+] BUILD SUCCESSFUL!")
        print(f" Executable generated in: {dist_dir}")
        for item in dist_dir.glob("scrcpy-control-center*"):
            print(f"  -> {item.name} ({item.stat().st_size / (1024*1024):.1f} MB)")
        print("=" * 60)
    else:
        print(f"\n[!] Build failed with exit code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)


if __name__ == "__main__":
    build()
