"""Android Desktop Mode configuration and OEM default rollback via ADB."""

import subprocess
from typing import List, Tuple, Dict, Optional

DESKTOP_MODE_FLAGS = [
    ("force_desktop_mode_on_external_displays", "Force desktop mode on external/virtual displays"),
    ("enable_freeform_support", "Enable freeform (resizable) windows"),
    ("force_resizable_activities", "Force all activities to be resizable"),
    ("allow_non_resizable_multi_window", "Allow non-resizable apps in multi-window"),
]

# Track initial states captured per device serial
_initial_state_cache: Dict[str, Dict[str, str]] = {}


def _build_adb_prefix(device_serial: Optional[str] = None) -> List[str]:
    """Return base adb command with optional device serial target."""
    if device_serial:
        return ["adb", "-s", device_serial]
    return ["adb"]


def capture_desktop_mode_backup(device_serial: Optional[str] = None) -> Dict[str, str]:
    """Read and cache initial values of all desktop mode flags for a device."""
    serial_key = device_serial or "default"
    if serial_key in _initial_state_cache:
        return _initial_state_cache[serial_key]

    backup = {}
    adb = _build_adb_prefix(device_serial)
    for flag, _desc in DESKTOP_MODE_FLAGS:
        try:
            res = subprocess.run(
                adb + ["shell", "settings", "get", "global", flag],
                capture_output=True,
                text=True,
                check=False
            )
            val = res.stdout.strip()
            backup[flag] = val
        except Exception:
            backup[flag] = "null"

    _initial_state_cache[serial_key] = backup
    return backup


def get_desktop_mode_status(device_serial: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """Return list of (flag, description, current_value) tuples."""
    results = []
    adb = _build_adb_prefix(device_serial)
    for flag, desc in DESKTOP_MODE_FLAGS:
        try:
            res = subprocess.run(
                adb + ["shell", "settings", "get", "global", flag],
                capture_output=True,
                text=True,
                check=False
            )
            val = res.stdout.strip()
            results.append((flag, desc, val))
        except Exception as e:
            results.append((flag, desc, f"error: {e}"))
    return results


def set_desktop_mode(enable: bool = True, device_serial: Optional[str] = None) -> Tuple[bool, str]:
    """
    Configure Android desktop mode flags.
    If enable=True: writes '1' to all flags after backing up initial states.
    If enable=False: delegates to restore_desktop_mode_defaults() to avoid leaving hardcoded 0 overrides.
    """
    if not enable:
        return restore_desktop_mode_defaults(device_serial)

    # Capture initial state for clean rollback later
    capture_desktop_mode_backup(device_serial)

    errors = []
    adb = _build_adb_prefix(device_serial)
    for flag, _desc in DESKTOP_MODE_FLAGS:
        try:
            res = subprocess.run(
                adb + ["shell", "settings", "put", "global", flag, "1"],
                capture_output=True,
                text=True,
                check=False
            )
            if res.returncode != 0:
                err = res.stderr.strip() or f"exit code {res.returncode}"
                errors.append(f"{flag}: {err}")
        except Exception as e:
            errors.append(f"{flag}: {e}")

    if errors:
        return False, "Errors: " + "; ".join(errors)
    return True, "Enabled all desktop mode flags. Note: Android UI reboot may be needed for full effect."


def restore_desktop_mode_defaults(device_serial: Optional[str] = None) -> Tuple[bool, str]:
    """
    Restore Android desktop mode settings to OEM baseline.
    Restores original values if previously set, or deletes overrides ('settings delete global <flag>')
    to let the Android OEM firmware use its default windowing behavior.
    """
    serial_key = device_serial or "default"
    backup = _initial_state_cache.get(serial_key, {})
    adb = _build_adb_prefix(device_serial)
    errors = []
    restored_count = 0

    for flag, _desc in DESKTOP_MODE_FLAGS:
        orig = backup.get(flag)
        try:
            if orig is not None and orig not in ("null", ""):
                # Restore to original recorded value
                res = subprocess.run(
                    adb + ["shell", "settings", "put", "global", flag, orig],
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                # Delete the setting override completely so OEM default takes effect
                res = subprocess.run(
                    adb + ["shell", "settings", "delete", "global", flag],
                    capture_output=True,
                    text=True,
                    check=False
                )

            if res.returncode == 0:
                restored_count += 1
            else:
                errors.append(f"{flag}: {res.stderr.strip()}")
        except Exception as e:
            errors.append(f"{flag}: {e}")

    if errors:
        return False, f"Restored {restored_count}/{len(DESKTOP_MODE_FLAGS)} flags with errors: " + "; ".join(errors)
    return True, f"Successfully restored OEM defaults for all {len(DESKTOP_MODE_FLAGS)} flags."


def detect_desktop_mode_support(device_serial: Optional[str] = None) -> Dict[str, str]:
    """
    Detect Android ROM capabilities and desktop mode support characteristics.
    Returns dictionary with brand, model, android_version, sdk, and compatibility analysis.
    """
    adb = _build_adb_prefix(device_serial)
    props = {}
    for key, prop in [
        ("brand", "ro.product.brand"),
        ("model", "ro.product.model"),
        ("sdk", "ro.build.version.sdk"),
        ("release", "ro.build.version.release"),
        ("dex", "ro.config.knox"),
        ("miui", "ro.miui.ui.version.name"),
    ]:
        try:
            r = subprocess.run(adb + ["shell", "getprop", prop], capture_output=True, text=True, check=False)
            props[key] = r.stdout.strip()
        except Exception:
            props[key] = ""

    brand = (props.get("brand") or "").lower()
    sdk_str = props.get("sdk") or "0"
    sdk = int(sdk_str) if sdk_str.isdigit() else 0

    # Capability rating
    if brand == "samsung":
        analysis = "Samsung device detected. DeX / Desktop mode is strongly supported natively."
    elif sdk >= 30: # Android 11+
        analysis = f"Android {props.get('release', '11+')} (SDK {sdk}). AOSP Freeform & Desktop windowing supported."
    elif sdk >= 29: # Android 10
        analysis = "Android 10 (SDK 29). Basic desktop mode flags supported; system UI may vary."
    else:
        analysis = f"Legacy Android SDK {sdk}. Desktop windowing may be unsupported or limited."

    props["analysis"] = analysis
    return props
