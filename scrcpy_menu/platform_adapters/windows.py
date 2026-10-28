"""Windows platform adapter: DirectShow detection and standard scrcpy paths."""

import os
from typing import List
from .base import BasePlatformAdapter


class WindowsPlatformAdapter(BasePlatformAdapter):
    """Adapter for Microsoft Windows systems."""

    def get_platform_name(self) -> str:
        return "Windows"

    def get_camera_sinks(self) -> List[str]:
        """Windows virtual camera sinks (e.g. OBS Virtual Camera / Unity Cam)."""
        # On Windows scrcpy does not use /dev/videoN; it uses direct rendering or external virtual cam drivers
        return ["OBS Virtual Camera", "Unity Video Capture"]

    def supports_v4l2_loopback(self) -> bool:
        # V4L2 is a Linux kernel subsystem; not applicable on native Windows
        return False

    def get_search_paths(self) -> List[str]:
        paths = []
        # Standard scoop / chocolatey / manual install locations
        user_profile = os.environ.get("USERPROFILE", "")
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        local_app_data = os.environ.get("LOCALAPPDATA", "")

        if user_profile:
            paths.append(os.path.join(user_profile, "scoop", "apps", "scrcpy", "current"))
            paths.append(os.path.join(user_profile, "scrcpy"))
        if local_app_data:
            paths.append(os.path.join(local_app_data, "Programs", "scrcpy"))
        paths.append(os.path.join(program_files, "scrcpy"))
        return paths
