"""ADB Device discovery, status monitoring, and wireless connection helper."""

import re
import shutil
import subprocess
from typing import List, Dict, Optional, Tuple


def is_adb_available() -> bool:
    """Check if adb binary is located in PATH."""
    return shutil.which("adb") is not None


def get_connected_devices() -> List[Dict[str, str]]:
    """
    Parse 'adb devices -l' and return list of device descriptors.
    Example item:
    {
        "serial": "192.0.2.1:5555",
        "state": "device",
        "model": "PhoneModel",
        "product": "phone",
        "device": "phone",
        "display_name": "PhoneModel [192.0.2.1:5555] (device)"
    }
    """
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

    # Basic host:port validation
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
