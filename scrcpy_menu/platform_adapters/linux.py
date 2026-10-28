"""Linux platform adapter: V4L2 virtual camera detection and device node discovery."""

import os
from typing import List
from .base import BasePlatformAdapter


class LinuxPlatformAdapter(BasePlatformAdapter):
    """Adapter for Linux systems."""

    def get_platform_name(self) -> str:
        return "Linux"

    def get_camera_sinks(self) -> List[str]:
        """Scan /dev for available V4L2 video devices."""
        sinks = []
        if os.path.exists("/dev"):
            for entry in sorted(os.listdir("/dev")):
                if entry.startswith("video") and entry[5:].isdigit():
                    sinks.append(f"/dev/{entry}")
        if not sinks:
            sinks = ["/dev/video2", "/dev/video0"]
        return sinks

    def supports_v4l2_loopback(self) -> bool:
        """Check if v4l2loopback kernel module is loaded."""
        try:
            with open("/proc/modules", "r") as f:
                content = f.read()
                return "v4l2loopback" in content
        except Exception:
            return os.path.exists("/dev/video2")

    def get_search_paths(self) -> List[str]:
        return [
            "/usr/bin",
            "/usr/local/bin",
            os.path.expanduser("~/.local/bin"),
            "/snap/bin",
        ]
