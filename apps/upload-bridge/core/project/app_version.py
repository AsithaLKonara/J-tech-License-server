"""
Application Version Management

Provides utilities to get application version from various sources:
1. Executable metadata (if running from built executable)
2. setup.py (if running from source)
3. Environment variable (APP_VERSION)
4. Default fallback
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional


def get_version_from_setup_py() -> Optional[str]:
    """Extract version from setup.py file."""
    try:
        # Find setup.py relative to this file
        current_file = Path(__file__).resolve()
        app_dir = current_file.parent.parent.parent
        setup_py = app_dir / "setup.py"
        
        if not setup_py.exists():
            return None
        
        content = setup_py.read_text(encoding='utf-8')
        # Match: version="3.0.0" or version='3.0.0'
        match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def get_version_from_executable() -> Optional[str]:
    """Extract version from executable metadata (Windows)."""
    if sys.platform != 'win32':
        return None
    
    try:
        import win32api
        import win32con
        
        exe_path = sys.executable
        if not exe_path.endswith('.exe'):
            return None
        
        # Get file version info
        info = win32api.GetFileVersionInfo(exe_path, '\\')
        version = f"{info['FileVersionMS'] >> 16}.{(info['FileVersionMS'] & 0xFFFF)}.{info['FileVersionLS'] >> 16}.{info['FileVersionLS'] & 0xFFFF}"
        # Remove trailing .0 if present
        version = re.sub(r'\.0$', '', version)
        return version
    except ImportError:
        # pywin32 not available
        pass
    except Exception:
        pass
    return None


def get_version_from_environment() -> Optional[str]:
    """Get version from environment variable."""
    return os.getenv('APP_VERSION')


def get_app_version() -> str:
    """
    Get application version from various sources.
    
    Priority:
    1. Environment variable (APP_VERSION)
    2. Executable metadata (if running from built executable)
    3. setup.py (if running from source)
    4. Default fallback
    
    Returns:
        Version string (e.g., "3.0.0")
    """
    # Try environment variable first
    version = get_version_from_environment()
    if version:
        return version
    
    # Try executable metadata (Windows)
    version = get_version_from_executable()
    if version:
        return version
    
    # Try setup.py
    version = get_version_from_setup_py()
    if version:
        return version
    
    # Default fallback
    return "3.0.0"


# Module-level version for easy import
VERSION = get_app_version()
