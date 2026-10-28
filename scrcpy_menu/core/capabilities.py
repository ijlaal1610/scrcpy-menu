"""Scrcpy version detection, capability negotiation, and diagnostic report generator."""

import os
import re
import sys
import shutil
import platform
import subprocess
from typing import Dict, Any, Optional


def get_scrcpy_version_info() -> Dict[str, Any]:
    """Inspect installed scrcpy binary and extract version numbers and features."""
    info: Dict[str, Any] = {
        "installed": False,
        "path": shutil.which("scrcpy") or "",
        "version_str": "Not installed",
        "major": 0,
        "minor": 0,
        "patch": 0,
        "has_new_display": False,
        "has_flex_display": False,
        "has_start_app": False,
        "has_camera_source": False,
        "has_v4l2_sink": (sys.platform.startswith("linux")),
        "raw_output": "",
    }

    if not info["path"]:
        return info

    try:
        res = subprocess.run(
            ["scrcpy", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        info["raw_output"] = res.stdout.strip()
        info["installed"] = (res.returncode == 0)

        # e.g. "scrcpy 3.1 <https://github.com/Genymobile/scrcpy>"
        m = re.search(r"scrcpy\s+v?([0-9]+)\.([0-9]+)(?:\.([0-9]+))?", res.stdout)
        if m:
            info["major"] = int(m.group(1))
            info["minor"] = int(m.group(2))
            info["patch"] = int(m.group(3)) if m.group(3) else 0
            info["version_str"] = f"{info['major']}.{info['minor']}.{info['patch']}"

            # Feature capabilities based on version
            # --new-display introduced in v2.2
            info["has_new_display"] = (info["major"] > 2) or (info["major"] == 2 and info["minor"] >= 2)
            # --start-app and camera source introduced in v2.0
            info["has_start_app"] = (info["major"] >= 2)
            info["has_camera_source"] = (info["major"] >= 2)

            # Test help text for --flex-display
            try:
                help_res = subprocess.run(
                    ["scrcpy", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                info["has_flex_display"] = ("--flex-display" in help_res.stdout or "--flex-display" in help_res.stderr)
            except Exception:
                info["has_flex_display"] = (info["major"] >= 3)
    except Exception as e:
        info["raw_output"] = f"Error querying scrcpy: {e}"

    return info


def generate_system_diagnostics(target_device: Optional[str] = None) -> str:
    """Generate a clean, copyable Markdown diagnostic summary of host and device state."""
    scrcpy_info = get_scrcpy_version_info()
    lines = [
        "# Scrcpy Control Center - Diagnostics Report",
        f"- **Date / Time**: {platform.uname().system} {platform.python_version()}",
        f"- **Platform**: {sys.platform} ({platform.platform()})",
        f"- **Desktop Session**: {os.environ.get('XDG_SESSION_TYPE', 'unknown')}",
        "",
        "## Scrcpy Capability Matrix",
        f"- **Scrcpy Binary**: `{scrcpy_info['path'] or 'NOT FOUND'}`",
        f"- **Scrcpy Version**: `{scrcpy_info['version_str']}`",
        f"- **Virtual Display (--new-display)**: {'✅ Supported' if scrcpy_info['has_new_display'] else '❌ Requires scrcpy >= 2.2'}",
        f"- **Flex Display (--flex-display)**: {'✅ Supported' if scrcpy_info['has_flex_display'] else '⚠️ Not supported in this version'}",
        f"- **App Launch (--start-app)**: {'✅ Supported' if scrcpy_info['has_start_app'] else '❌ Unsupported'}",
        f"- **Camera Source (--video-source=camera)**: {'✅ Supported' if scrcpy_info['has_camera_source'] else '❌ Unsupported'}",
        f"- **V4L2 Virtual Webcam**: {'✅ Supported (Linux)' if scrcpy_info['has_v4l2_sink'] else 'ℹ️ N/A (Non-Linux platform)'}",
        "",
        "## ADB & Device Status",
    ]

    adb_path = shutil.which("adb")
    lines.append(f"- **ADB Binary**: `{adb_path or 'NOT FOUND'}`")
    if adb_path:
        try:
            v_res = subprocess.run(["adb", "version"], capture_output=True, text=True, check=False)
            lines.append(f"- **ADB Version**: `{v_res.stdout.splitlines()[0] if v_res.stdout else 'unknown'}`")
        except Exception:
            pass

        try:
            dev_res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, check=False)
            lines.append("\n**Connected Devices**:")
            lines.append("```")
            lines.append(dev_res.stdout.strip() or "No devices detected.")
            lines.append("```")
        except Exception as e:
            lines.append(f"- Error listing devices: {e}")

    if sys.platform.startswith("linux"):
        lines.append("")
        lines.append("## Linux V4L2 Video Nodes")
        v4l2_nodes = [f"/dev/{f}" for f in sorted(os.listdir("/dev")) if f.startswith("video")] if os.path.exists("/dev") else []
        lines.append(f"- Available nodes: `{', '.join(v4l2_nodes) if v4l2_nodes else 'None found'}`")

    return "\n".join(lines)
