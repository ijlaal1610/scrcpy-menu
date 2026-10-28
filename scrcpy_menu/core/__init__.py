"""Core services for scrcpy-menu."""

from .config import load_config, save_config, get_config_path
from .device import get_connected_devices, is_adb_available, connect_wireless, disconnect_wireless
from .desktop_mode import (
    DESKTOP_MODE_FLAGS,
    get_desktop_mode_status,
    set_desktop_mode,
    restore_desktop_mode_defaults,
    detect_desktop_mode_support,
)
from .capabilities import get_scrcpy_version_info, generate_system_diagnostics
from .process import ScrcpyProcessManager
