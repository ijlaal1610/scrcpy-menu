"""ADB Device discovery, status monitoring, wireless pairing, and hardware queries."""

import os
import re
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple


def is_adb_available() -> bool:
    """Check if adb binary is located in PATH."""
    return shutil.which("adb") is not None


def get_connected_devices() -> List[Dict[str, str]]:
    """Parse 'adb devices -l' and return list of device descriptors."""
    if not is_adb_available():
        return []

    try:
        res = subprocess.run(
            ["adb", "devices", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        if res.returncode != 0:
            return []

        devices = []
        for line in res.stdout.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("List of devices"):
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                state = parts[1]
                info = {"serial": serial, "state": state}

                # Parse key:value metadata (e.g. model:Pixel_8 device:husky)
                for item in parts[2:]:
                    if ":" in item:
                        k, v = item.split(":", 1)
                        info[k] = v

                model = info.get("model", "")
                if model:
                    info["display_name"] = f"{model} [{serial}] ({state})"
                else:
                    info["display_name"] = f"Device [{serial}] ({state})"

                devices.append(info)

        return devices
    except Exception:
        return []


def connect_wireless(address: str) -> Tuple[bool, str]:
    """Connect to a device via adb connect <ip>:<port>."""
    if not address:
        return False, "Target IP:Port cannot be empty."

    if not re.match(r"^[0-9a-zA-Z\.\-_]+(:[0-9]+)?$", address):
        return False, "Invalid address format. Expected IP:PORT (e.g. 192.0.2.1:5555)."

    if ":" not in address:
        address += ":5555"

    try:
        res = subprocess.run(
            ["adb", "connect", address],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )
        out = (res.stdout + res.stderr).strip()
        if "connected to" in out.lower():
            return True, out
        return False, out
    except Exception as e:
        return False, f"Connection failed: {e}"


def pair_wireless(address: str, code: str) -> Tuple[bool, str]:
    """Pair a device using Android 11+ wireless debugging (adb pair <ip>:<port> <code>)."""
    if not address or not code:
        return False, "Both Address (IP:PORT) and 6-digit Pairing Code are required."

    address = address.strip()
    code = code.strip()

    if not re.match(r"^[0-9a-zA-Z\.\-_]+:[0-9]+$", address):
        return False, "Invalid address format. Expected IP:PORT with the specific pairing port shown on your phone."

    try:
        res = subprocess.run(
            ["adb", "pair", address, code],
            capture_output=True,
            text=True,
            timeout=15,
            check=False
        )
        out = (res.stdout + res.stderr).strip()
        if "successfully paired" in out.lower():
            return True, out
        return False, out
    except Exception as e:
        return False, f"Pairing failed: {e}"


def disconnect_wireless(address: Optional[str] = None) -> Tuple[bool, str]:
    """Disconnect one or all wireless adb targets."""
    cmd = ["adb", "disconnect"]
    if address:
        cmd.append(address)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
        return True, (res.stdout + res.stderr).strip()
    except Exception as e:
        return False, str(e)


def restart_adb_server() -> Tuple[bool, str]:
    """Kill and restart the local ADB server daemon."""
    try:
        subprocess.run(["adb", "kill-server"], capture_output=True, timeout=5, check=False)
        start_res = subprocess.run(["adb", "start-server"], capture_output=True, text=True, timeout=10, check=False)
        out = (start_res.stdout + start_res.stderr).strip() or "ADB server restarted."
        return True, out
    except Exception as e:
        return False, f"Could not restart ADB: {e}"


def install_apk(apk_path: str, device_serial: Optional[str] = None) -> Tuple[bool, str]:
    """Install an APK file onto the target device."""
    if not os.path.isfile(apk_path):
        return False, f"File not found: {apk_path}"

    cmd = ["adb"]
    if device_serial:
        cmd.extend(["-s", device_serial])
    cmd.extend(["install", "-r", apk_path])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        out = (res.stdout + res.stderr).strip()
        if "success" in out.lower():
            return True, f"Installed {os.path.basename(apk_path)} successfully."
        return False, out
    except Exception as e:
        return False, f"Install failed: {e}"


def push_file(file_path: str, destination: str = "/sdcard/Download/", device_serial: Optional[str] = None) -> Tuple[bool, str]:
    """Push a local file onto device storage."""
    if not os.path.exists(file_path):
        return False, f"Path not found: {file_path}"

    cmd = ["adb"]
    if device_serial:
        cmd.extend(["-s", device_serial])
    cmd.extend(["push", file_path, destination])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        out = (res.stdout + res.stderr).strip()
        return True, out or f"Pushed {os.path.basename(file_path)} to {destination}"
    except Exception as e:
        return False, f"Push failed: {e}"


def query_device_cameras(device_serial: Optional[str] = None) -> List[str]:
    """Execute 'scrcpy --list-cameras' to dynamically inspect device lenses."""
    cmd = ["scrcpy"]
    if device_serial:
        cmd.append(f"--serial={device_serial}")
    cmd.append("--list-cameras")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        cameras = []
        raw = res.stdout + res.stderr
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("--camera-id=") or "id=" in line or "camera" in line.lower():
                if any(x in line for x in ["back", "front", "id=", "wide", "fps"]):
                    cameras.append(line)
        return cameras
    except Exception:
        return []


def query_device_encoders(device_serial: Optional[str] = None) -> List[str]:
    """Execute 'scrcpy --list-encoders' to discover hardware video encoders."""
    cmd = ["scrcpy"]
    if device_serial:
        cmd.append(f"--serial={device_serial}")
    cmd.append("--list-encoders")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        encoders = []
        raw = res.stdout + res.stderr
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("--video-codec=") or "c2." in line or "omx." in line.lower():
                encoders.append(line)
        return encoders
    except Exception:
        return []


def query_installed_packages(device_serial: Optional[str] = None) -> List[str]:
    """Query third-party installed packages on the device via ADB."""
    cmd = ["adb"]
    if device_serial:
        cmd.extend(["-s", device_serial])
    cmd.extend(["shell", "pm", "list", "packages", "-3"])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        pkgs = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                pkg_name = line.replace("package:", "").strip()
                if pkg_name:
                    pkgs.append(pkg_name)
        return sorted(pkgs)
    except Exception:
        return []


def get_top_apps_by_display(device_serial: Optional[str] = None) -> Dict[int, str]:
    """
    Parse 'dumpsys activity activities' to identify the top active package on each display ID.
    Returns mapping {display_id: package_name}.
    """
    cmd = ["adb"]
    if device_serial:
        cmd.extend(["-s", device_serial])
    cmd.extend(["shell", "dumpsys", "activity", "activities"])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        out = res.stdout
        display_blocks = re.split(r"Display\s*#(\d+)", out)
        apps = {}
        for i in range(1, len(display_blocks), 2):
            d_id = int(display_blocks[i])
            block = display_blocks[i + 1]
            m = re.search(r"topResumedActivity=ActivityRecord\{[^\}]*\s+([a-zA-Z0-9_\.]+)/", block)
            if m:
                apps[d_id] = m.group(1)
        return apps
    except Exception:
        return {}


def force_stop_app(package_name: str, device_serial: Optional[str] = None) -> Tuple[bool, str]:
    """Force stop a package on the target device via 'adb shell am force-stop <package>'."""
    if not package_name:
        return False, "Package name cannot be empty."

    cmd = ["adb"]
    if device_serial:
        cmd.extend(["-s", device_serial])
    cmd.extend(["shell", "am", "force-stop", package_name])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
        if res.returncode == 0:
            return True, f"Force-stopped {package_name}"
        return False, res.stderr.strip() or f"Exit code {res.returncode}"
    except Exception as e:
        return False, str(e)
