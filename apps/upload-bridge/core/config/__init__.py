"""
Configuration Management - Centralized configuration for enterprise applications.

Provides environment-based configuration with validation and secrets management.
"""

from core.config.config_manager import ConfigManager, get_config
from core.config.environment import Environment, get_environment

__all__ = [
    'ConfigManager',
    'get_config',
    'Environment',
    'get_environment',
]

