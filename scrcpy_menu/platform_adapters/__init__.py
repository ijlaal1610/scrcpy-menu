"""Platform adapter factory."""

import sys
from .base import BasePlatformAdapter
from .linux import LinuxPlatformAdapter
from .windows import WindowsPlatformAdapter
from .macos import MacOSPlatformAdapter


def get_platform_adapter() -> BasePlatformAdapter:
    """Instantiate and return the appropriate adapter for current operating system."""
    if sys.platform == "win32":
        return WindowsPlatformAdapter()
    elif sys.platform == "darwin":
        return MacOSPlatformAdapter()
    else:
        return LinuxPlatformAdapter()
