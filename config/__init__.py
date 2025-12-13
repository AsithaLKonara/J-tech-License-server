"""
Configuration Management for Upload Bridge

This package provides configuration management functionality.
Import functions from submodules for cleaner organization:
- `from config.app_config import load_app_config, save_app_config`
- `from config.chip_database import load_chip_database`

Or use convenience imports (backward compatible):
- `from config import load_app_config, save_app_config, load_chip_database`
"""

# Re-export functions from submodules for backward compatibility
from .app_config import load_app_config, save_app_config
from .chip_database import load_chip_database

__all__ = ['load_app_config', 'save_app_config', 'load_chip_database']

