"""
Runtime utility to handle application paths for script and PyInstaller modes.
"""

import sys
from pathlib import Path

def get_app_root() -> Path:
    """Returns the application root directory."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def get_resource_path(relative_path: str) -> Path:
    """Returns the absolute path to a resource, relative to app root."""
    return get_app_root() / relative_path
