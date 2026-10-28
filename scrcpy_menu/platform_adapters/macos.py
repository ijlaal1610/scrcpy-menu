"""macOS platform adapter: Homebrew paths and permissions guidance."""

import os
from typing import List
from .base import BasePlatformAdapter


class MacOSPlatformAdapter(BasePlatformAdapter):
    """Adapter for Apple macOS systems."""

    def get_platform_name(self) -> str:
        return "macOS"

    def get_camera_sinks(self) -> List[str]:
        return ["OBS Virtual Camera"]

    def supports_v4l2_loopback(self) -> bool:
        return False

    def get_search_paths(self) -> List[str]:
        return [
            "/opt/homebrew/bin",  # Apple Silicon Homebrew
            "/usr/local/bin",     # Intel Homebrew
            "/opt/local/bin",     # MacPorts
        ]
