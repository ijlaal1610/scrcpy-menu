"""Abstract base adapter for platform-specific capabilities."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BasePlatformAdapter(ABC):
    """Base class for platform integrations (Linux, Windows, macOS)."""

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return human-readable platform name."""
        pass

    @abstractmethod
    def get_camera_sinks(self) -> List[str]:
        """Return list of available virtual camera sink devices/targets."""
        pass

    @abstractmethod
    def supports_v4l2_loopback(self) -> bool:
        """Check if Linux V4L2 virtual camera loopback is available."""
        pass

    @abstractmethod
    def get_search_paths(self) -> List[str]:
        """Return platform-specific search paths for scrcpy and adb binaries."""
        pass
