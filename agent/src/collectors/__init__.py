"""
System information collectors for different platforms
"""
import platform

from .base import BaseCollector


def get_collector():
    """Factory function to get the appropriate collector for the current platform."""
    system = platform.system().lower()

    if system == 'windows':
        from .windows import WindowsCollector
        return WindowsCollector()
    elif system == 'darwin':
        from .macos import MacOSCollector
        return MacOSCollector()
    elif system == 'linux':
        from .linux import LinuxCollector
        return LinuxCollector()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


__all__ = ['get_collector', 'BaseCollector']
