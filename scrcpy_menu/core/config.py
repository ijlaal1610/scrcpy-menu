"""Cross-platform configuration manager for scrcpy-menu with atomic persistence."""

import os
import sys
import json
import tempfile
from pathlib import Path

DEFAULT_CONFIG = {
    # Mirror mode
    "mirror_fps": "120",
    "mirror_bitrate": "8M",
    "mirror_stay_awake": True,
    "mirror_audio": True,
    "mirror_turn_screen_off": False,
    "mirror_fullscreen": False,
    "mirror_hid_keyboard": False,
    "mirror_hid_mouse": False,
    "mirror_otg": False,
    "mirror_record": False,

    # Virtual display mode
    "vd_resolution": "1920x1080",
    "vd_dpi": "180",
    "vd_flex": True,
    "vd_keep_active": True,
    "vd_destroy_content": False,
    "vd_audio": True,
    "vd_bitrate": "16M",
    "vd_fps": "60",
    "vd_app": "",
    "vd_force_desktop_mode": False,
    "vd_hid_keyboard": False,
    "vd_hid_mouse": False,
    "vd_record": False,

    # Camera mode
    "camera_size": "1920x1080",
    "camera_fps": "30",
    "camera_bitrate": "8M",
    "camera_anti_lag": True,
    "camera_facing": "back",
    "camera_id": "",
    "camera_sink": "/dev/video2",

    # UI preferences
    "selected_device": "",
    "record_dir": "",
    "last_tab": 0,
    "theme": "dark",
}


def get_config_dir() -> Path:
    """Return platform-appropriate configuration directory."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "scrcpy-menu"
        return Path.home() / ".scrcpy-menu"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "scrcpy-menu"
    else:
        # Linux / BSD (XDG standard)
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "scrcpy-menu"
        return Path.home() / ".config" / "scrcpy-menu"


def get_config_path() -> Path:
    """Return full path to configuration JSON file."""
    return get_config_dir() / "config.json"


def load_config() -> dict:
    """Load configuration dictionary, merging with defaults."""
    cfg = DEFAULT_CONFIG.copy()
    path = get_config_path()
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception as e:
            print(f"[!] Warning: Could not read config file ({e}). Using defaults.", file=sys.stderr)
    return cfg


def save_config(cfg: dict) -> bool:
    """Atomically save configuration to disk with restrictive file permissions."""
    cfg_dir = get_config_dir()
    try:
        cfg_dir.mkdir(parents=True, exist_ok=True)
        # Apply restrictive permissions to config directory on POSIX
        if sys.platform != "win32":
            try:
                os.chmod(cfg_dir, 0o700)
            except Exception:
                pass

        target_file = get_config_path()
        with tempfile.NamedTemporaryFile("w", dir=str(cfg_dir), delete=False, encoding="utf-8") as tf:
            json.dump(cfg, tf, indent=2)
            temp_name = tf.name

        if sys.platform != "win32":
            try:
                os.chmod(temp_name, 0o600)
            except Exception:
                pass

        os.replace(temp_name, target_file)
        return True
    except Exception as e:
        print(f"[!] Error: Failed to save config to {get_config_path()}: {e}", file=sys.stderr)
        return False
