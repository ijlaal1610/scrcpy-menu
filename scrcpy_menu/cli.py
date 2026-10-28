"""Terminal CLI Quick Menu for scrcpy-menu with zero third-party dependencies."""

import re
import sys
import shutil
import subprocess
from typing import List, Optional

from .core.config import load_config, save_config
from .core.device import get_connected_devices, is_adb_available, connect_wireless
from .core.desktop_mode import (
    DESKTOP_MODE_FLAGS,
    get_desktop_mode_status,
    set_desktop_mode,
    restore_desktop_mode_defaults,
    detect_desktop_mode_support,
)
from .core.capabilities import get_scrcpy_version_info, generate_system_diagnostics
from .platform_adapters import get_platform_adapter

# Strict Input Validators
_RE_RES = re.compile(r"^\d{3,5}x\d{3,5}$")
_RE_DPI = re.compile(r"^\d{2,4}$")
_RE_PKG = re.compile(r"^[a-zA-Z0-9_\.]+$")
_RE_BITRATE = re.compile(r"^\d{1,3}[kKmMgG]?$")
_RE_FPS = re.compile(r"^\d{1,3}$")


def validate_resolution(val: str) -> bool:
    return bool(_RE_RES.match(val.strip())) if val else False


def validate_dpi(val: str) -> bool:
    return bool(_RE_DPI.match(val.strip())) if val else False


def validate_package_name(val: str) -> bool:
    return bool(_RE_PKG.match(val.strip())) if val else False


def validate_bitrate(val: str) -> bool:
    return bool(_RE_BITRATE.match(val.strip())) if val else False


def validate_fps(val: str) -> bool:
    return bool(_RE_FPS.match(val.strip())) if val else False


SHORTCUTS_LIST = [
    ("MOD + f", "Toggle fullscreen"),
    ("MOD + Left / Right", "Rotate display (90 degrees left / right)"),
    ("MOD + g", "Resize window to 1:1 pixel mapping"),
    ("MOD + w", "Resize window to remove black borders"),
    ("MOD + h", "Home button (Android)"),
    ("MOD + b / Backspace", "Back button (Android)"),
    ("MOD + s", "App Switcher (Recents)"),
    ("MOD + m", "Menu button"),
    ("MOD + p", "Power button (turn screen on / off)"),
    ("MOD + o", "Turn device physical screen off (keep mirroring)"),
    ("MOD + Shift + o", "Turn device physical screen on"),
    ("MOD + r", "Rotate device screen"),
    ("MOD + n", "Expand notification panel"),
    ("MOD + Shift + n", "Collapse notification panel"),
    ("MOD + c", "Copy device clipboard to computer"),
    ("MOD + v", "Paste computer clipboard to device"),
    ("MOD + Shift + v", "Paste computer clipboard as raw key events"),
    ("MOD + k", "Toggle physical keyboard simulation (UHID)"),
    ("MOD + i", "Toggle mouse capture / pointer lock"),
    ("MOD + Up / Down", "Volume Up / Volume Down"),
]


def print_shortcuts_table():
    print("\n" + "=" * 65)
    print("      ⌨️  SCRCPY KEYBOARD & MOUSE SHORTCUTS REFERENCE")
    print("=" * 65)
    print("  Note: 'MOD' is Left-Alt (default) or Left-Super (Windows key)")
    print("-" * 65)
    print(f"  {'Shortcut':<24} {'Action'}")
    print("-" * 65)
    for sc, desc in SHORTCUTS_LIST:
        print(f"  {sc:<24} {desc}")
    print("=" * 65 + "\n")


def select_target_device() -> Optional[str]:
    """List devices and prompt user to choose if multiple exist."""
    devices = get_connected_devices()
    if not devices:
        return None
    if len(devices) == 1:
        return devices[0]["serial"]

    print("\nMultiple devices connected:")
    for idx, d in enumerate(devices, 1):
        print(f"  [{idx}] {d.get('display_name', d['serial'])}")

    try:
        choice = input(f"Select device [1-{len(devices)}] (Default 1): ").strip()
        idx = int(choice) if choice.isdigit() else 1
        if 1 <= idx <= len(devices):
            return devices[idx - 1]["serial"]
    except Exception:
        pass
    return devices[0]["serial"]


def cli_custom_virtual_display() -> List[str]:
    """Interactive builder for a custom virtual display command with strict validation."""
    print("\n── Custom Virtual Display Builder ──")

    # Resolution
    print("\nSelect Resolution:")
    print("  1) 1920x1080 (FHD)")
    print("  2) 2560x1440 (2K)")
    print("  3) 1280x720  (HD)")
    print("  4) 1024x768  (4:3)")
    print("  5) Default   (Phone native)")
    print("  6) Custom WxH")
    r = input("Choice [1]: ").strip() or "1"
    res_map = {"1": "1920x1080", "2": "2560x1440", "3": "1280x720", "4": "1024x768", "5": "", "6": ""}
    if r == "6":
        res = input("Enter WxH (e.g. 1920x1080): ").strip()
        if not validate_resolution(res):
            print(f"[!] Invalid resolution format '{res}'. Defaulting to 1920x1080.")
            res = "1920x1080"
    else:
        res = res_map.get(r, "1920x1080")

    # DPI
    print("\nSelect Density (DPI):")
    print("  1) Default")
    print("  2) 420 (Phone standard)")
    print("  3) 320 (Large text)")
    print("  4) 240 (Compact / Tablet)")
    print("  5) 180 (Desktop / UI dense)")
    d = input("Choice [1]: ").strip() or "1"
    dpi_map = {"1": "", "2": "420", "3": "320", "4": "240", "5": "180"}
    dpi = dpi_map.get(d, "")
    if dpi and not validate_dpi(dpi):
        print(f"[!] Invalid DPI value '{dpi}'. Using default.")
        dpi = ""

    # Build new-display arg
    parts = ["scrcpy"]
    if res and dpi:
        parts.append(f"--new-display={res}/{dpi}")
    elif res:
        parts.append(f"--new-display={res}")
    else:
        parts.append("--new-display")

    # Flex display
    flex = input("\nUse flex-display (resize virtual display with window)? [Y/n]: ").strip().lower()
    if flex != "n":
        parts.append("--flex-display")

    # Start app
    app = input("Start an app? Enter package name or press Enter to skip: ").strip()
    if app:
        if not validate_package_name(app):
            print(f"[!] Rejected unsafe package name format: '{app}'. Skipping app start.")
        else:
            force = input("  Force-stop app first? [y/N]: ").strip().lower()
            prefix = "+" if force == "y" else ""
            parts.append(f"--start-app={prefix}{app}")

    # Keep active
    keep = input("Keep display active in background? [Y/n]: ").strip().lower()
    if keep != "n":
        parts.append("--keep-active")

    # Destroy content
    destroy = input("Destroy content when display closed? [y/N]: ").strip().lower()
    if destroy != "y":
        parts.append("--no-vd-destroy-content")

    # Audio
    audio = input("Capture audio on PC? [Y/n]: ").strip().lower()
    if audio != "n":
        parts.append("--audio-source=output")
    else:
        parts.append("--no-audio")

    # Bitrate
    br = input("Bitrate (e.g. 8M, 16M) [16M]: ").strip() or "16M"
    if not validate_bitrate(br):
        print(f"[!] Invalid bitrate '{br}'. Defaulting to 16M.")
        br = "16M"
    parts.append(f"--video-bit-rate={br}")

    # Max FPS
    fps = input("Max FPS (0=unlimited) [60]: ").strip() or "60"
    if not validate_fps(fps):
        print(f"[!] Invalid FPS '{fps}'. Defaulting to 60.")
        fps = "60"
    if fps != "0":
        parts.append(f"--max-fps={fps}")

    return parts


def cli_toggle_desktop_mode(device_serial: Optional[str] = None):
    """View and toggle Android desktop mode settings safely via ADB."""
    print("\n── Android Desktop Mode Settings (via ADB) ──")
    statuses = get_desktop_mode_status(device_serial)
    all_enabled = True
    for flag, desc, val in statuses:
        enabled = (val == "1")
        if not enabled:
            all_enabled = False
        icon = "[ON] " if enabled else "[OFF]"
        print(f" {icon} {desc}")

    print(f"\nOverall Status: {'✅ FULLY ENABLED' if all_enabled else '⚠️  PARTIAL / DISABLED'}")

    try:
        action = input("\nOptions: [1] Enable all flags  [2] Restore OEM defaults  [Enter] Keep unchanged: ").strip()
    except (EOFError, KeyboardInterrupt):
        action = ""

    if action == "1":
        succ, msg = set_desktop_mode(True, device_serial)
        print(f"\n✔ {msg}")
    elif action == "2":
        succ, msg = restore_desktop_mode_defaults(device_serial)
        print(f"\n✔ {msg}")
    else:
        print("No changes made.")


def run_cli_menu():
    """Main terminal loop."""
    print("=" * 60)
    print("       🚀 Scrcpy Control Center - Terminal Menu")
    print("=" * 60)

    devices = get_connected_devices()
    target_serial = None
    if not devices:
        print("⚠️  No ADB devices connected.")
        print("   Connect a phone via USB with USB debugging enabled,")
        print("   or pair wirelessly via 'adb connect <ip>:5555'")
    else:
        if len(devices) == 1:
            target_serial = devices[0]["serial"]
            print(f"✔ Active device: {devices[0].get('display_name', target_serial)}")
        else:
            print(f"✔ Found {len(devices)} connected devices.")
            target_serial = select_target_device()

    adapter = get_platform_adapter()
    default_sink = adapter.get_camera_sinks()[0] if adapter.get_camera_sinks() else "/dev/video2"

    print("\nSelect Configuration:")
    print(" ── Camera Modes ──")
    print(f"  1) 📷 Camera 1080p @ 30fps + Anti-Lag ({default_sink})")
    print(f"  2) 📷 Camera 1080p @ 60fps + Anti-Lag ({default_sink})")
    print(f"  3) 📷 Camera 1080p @ 30fps Standard ({default_sink})")
    print(f"  4) 📷 Camera 1080p @ 60fps Standard ({default_sink})")
    print(" ── Screen Mirror Modes ──")
    print("  5) 📱 Screen Mirror -> 120 FPS Native")
    print("  6) 📱 Screen Mirror -> 60 FPS Standard")
    print(f"  7) 📱 Screen Mirror -> Output to Webcam ({default_sink})")
    print(" ── Virtual Display Modes ──")
    print("  8) 🖥️  Virtual Display — 1080p Flex + Audio (Blank)")
    print("  9) 🖥️  Virtual Display — 1080p Flex + Chrome")
    print(" 10) 🖥️  Virtual Display — Desktop Mode (1080p, 180 DPI, Flex)")
    print(" 11) 🖥️  Virtual Display — Custom (interactive builder)")
    print(" ── Settings & Diagnostics ──")
    print(" 12) ⚙️  Toggle Android Desktop Mode via ADB (Enable / Restore Defaults)")
    print(" 13) ⌨️  View Keyboard & Mouse Shortcuts Reference")
    print(" 14) 🔍 View System Diagnostics Report")
    print("  0) Exit")

    try:
        choice = input("\nEnter choice [0-14]: ").strip()
    except (EOFError, KeyboardInterrupt):
        choice = "0"

    cmd: Optional[List[str]] = None

    if choice == "1":
        cmd = ["scrcpy", "--video-source=camera", "--camera-size=1920x1080", "--camera-fps=30", "--video-bit-rate=8M", "--v4l2-buffer=0", "--no-audio", f"--v4l2-sink={default_sink}"]
    elif choice == "2":
        cmd = ["scrcpy", "--video-source=camera", "--camera-size=1920x1080", "--camera-fps=60", "--video-bit-rate=8M", "--v4l2-buffer=0", "--no-audio", f"--v4l2-sink={default_sink}"]
    elif choice == "3":
        cmd = ["scrcpy", "--video-source=camera", "--camera-size=1920x1080", "--camera-fps=30", f"--v4l2-sink={default_sink}"]
    elif choice == "4":
        cmd = ["scrcpy", "--video-source=camera", "--camera-size=1920x1080", "--camera-fps=60", f"--v4l2-sink={default_sink}"]
    elif choice == "5":
        cmd = ["scrcpy", "--max-fps=120", "--stay-awake", "--audio-source=output"]
    elif choice == "6":
        cmd = ["scrcpy", "--max-fps=60", "--stay-awake", "--audio-source=output"]
    elif choice == "7":
        cmd = ["scrcpy", "--max-fps=60", f"--v4l2-sink={default_sink}", "--audio-source=output"]
    elif choice == "8":
        cmd = ["scrcpy", "--new-display=1920x1080", "--flex-display", "--keep-active", "--no-vd-destroy-content", "--audio-source=output", "--video-bit-rate=8M", "--max-fps=60"]
    elif choice == "9":
        cmd = ["scrcpy", "--new-display=1920x1080", "--flex-display", "--keep-active", "--no-vd-destroy-content", "--audio-source=output", "--video-bit-rate=8M", "--max-fps=60", "--start-app=com.android.chrome"]
    elif choice == "10":
        print("\n⚙️ Enabling Android Desktop Mode flags via ADB...")
        succ, msg = set_desktop_mode(True, target_serial)
        if not succ:
            print(f"⚠️ Warning: Could not fully enable desktop mode flags: {msg}")
        else:
            print(f"✔ {msg}")
        cmd = ["scrcpy", "--new-display=1920x1080/180", "--flex-display", "--keep-active", "--no-vd-destroy-content", "--audio-source=output", "--video-bit-rate=16M", "--max-fps=60"]
    elif choice == "11":
        cmd = cli_custom_virtual_display()
    elif choice == "12":
        cli_toggle_desktop_mode(target_serial)
        return
    elif choice == "13":
        print_shortcuts_table()
        return
    elif choice == "14":
        print("\n" + generate_system_diagnostics(target_serial))
        return
    elif choice in ("0", ""):
        print("Exiting.")
        sys.exit(0)
    else:
        print("Invalid choice.")
        return

    if cmd:
        # If specific device selected, target it
        if target_serial and "-s" not in cmd and "--serial" not in cmd:
            cmd.insert(1, f"--serial={target_serial}")

        print(f"\nExecuting: {' '.join(cmd)}\n")
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\nProcess interrupted by user.")
        except Exception as e:
            print(f"\n[!] Execution error: {e}", file=sys.stderr)
