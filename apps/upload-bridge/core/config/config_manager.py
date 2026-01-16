"""
Configuration Manager - Centralized configuration management.

Provides environment-based configuration with validation and secrets management.
"""

import os
import json
import yaml
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from core.config.environment import Environment, get_environment

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration manager.
    
    Features:
    - Environment-based configuration
    - Configuration validation
    - Secrets management
    - Hot-reload support (optional)
    - Type-safe access
    """
    
    _instance: Optional['ConfigManager'] = None
    
    def __init__(self):
        """Initialize configuration manager."""
        if ConfigManager._instance is not None:
            raise RuntimeError("ConfigManager is a singleton. Use get_config() instead.")
        
        self.environment = get_environment()
        self._config: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}
        self._config_file: Optional[Path] = None
        ConfigManager._instance = self
        self._load_config()
    
    @classmethod
    def instance(cls) -> 'ConfigManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load configuration from environment and files."""
        # Load from environment variables
        self._load_from_environment()
        
        # Determine the base directory of the application
        # Assumes config_manager.py is in <app_root>/core/config/
        app_root = Path(__file__).resolve().parents[2] # Go up 2 levels from core/config/config_manager.py
        
        # Try to load from YAML config first (preferred)
        yaml_config_path = app_root / "config" / "app_config.yaml"
        logger.debug(f"ConfigManager: Looking for config file at: {yaml_config_path.absolute()}")
        if yaml_config_path.exists():
            logger.debug(f"ConfigManager: Found config file at: {yaml_config_path.absolute()}")
            self._load_from_file(yaml_config_path)
            self._config_file = yaml_config_path
        else:
            logger.debug(f"ConfigManager: Config file NOT found at: {yaml_config_path.absolute()}")
            # Fallback to JSON config if YAML doesn't exist
            config_file = Path("config") / f"{self.environment.value}.json"
            if config_file.exists():
                self._load_from_file(config_file)
                self._config_file = config_file
        
        # Load defaults
        self._load_defaults()
        
        # Validate configuration
        self._validate_config()
        logger.debug(f"Final config after _load_config: {self._config}")
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # Application settings
        self._config['app_name'] = os.getenv('APP_NAME', 'Upload Bridge')
        self._config['app_version'] = os.getenv('APP_VERSION', '3.0.0')
        self._config['debug'] = os.getenv('DEBUG', 'False').lower() == 'true'
        logger.debug(f"Config after loading from environment: {self._config}")
        
        # Logging settings
        self._config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
        self._config['log_to_file'] = os.getenv('LOG_TO_FILE', 'True').lower() == 'true'
        self._config['log_to_console'] = os.getenv('LOG_TO_CONSOLE', 'True').lower() == 'true'
        self._config['log_json'] = os.getenv('LOG_JSON', 'False').lower() == 'true'
        self._config['log_dir'] = os.getenv('LOG_DIR', 'logs')
        
        # Performance settings
        self._config['max_pattern_size'] = int(os.getenv('MAX_PATTERN_SIZE', '1000000'))
        self._config['cache_size'] = int(os.getenv('CACHE_SIZE', '100'))
        
        # Feature flags
        self._config['enable_analytics'] = os.getenv('ENABLE_ANALYTICS', 'False').lower() == 'true'
        self._config['enable_telemetry'] = os.getenv('ENABLE_TELEMETRY', 'False').lower() == 'true'
    
    def _load_from_file(self, config_file: Path) -> None:
        """Load configuration from YAML or JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                # Check file extension to determine format
                if config_file.suffix in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f) or {}
                    logger.debug(f"Config from YAML file (raw): {file_config}")
                    if "auth_server_url" in file_config:
                        logger.debug(f"DEBUG (YAML raw): auth_server_url found: {file_config['auth_server_url']}")
                    else:
                        logger.debug(f"DEBUG (YAML raw): auth_server_url NOT found in raw file_config")
                    # Flatten YAML structure if needed (YAML may have nested structure)
                    # For app_config.yaml, we expect a flat structure that matches our config keys
                    if isinstance(file_config, dict):
                        # Handle nested YAML structure - flatten common sections
                        flattened = {}
                        for key, value in file_config.items():
                            if isinstance(value, dict):
                                # Flatten nested dicts with dot notation or prefix
                                for subkey, subvalue in value.items():
                                    flattened[f"{key}_{subkey}"] = subvalue
                            else:
                                flattened[key] = value
                        file_config = flattened
                        logger.debug(f"Config from YAML file (flattened): {file_config}")
                    if "auth_server_url" in file_config:
                        logger.debug(f"DEBUG (YAML flattened): auth_server_url found: {file_config['auth_server_url']}")
                    else:
                        logger.debug(f"DEBUG (YAML flattened): auth_server_url NOT found in flattened file_config")
                else:
                    # Assume JSON format
                    file_config = json.load(f)
                self._config.update(file_config)
            logger.info(f"Loaded configuration from {config_file}")
            logger.debug(f"Config after loading from file {config_file}: {self._config}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        defaults = {
            'app_name': 'Upload Bridge',
            'app_version': '3.0.0',
            'debug': False,
            'log_level': 'INFO',
            'log_to_file': True,
            'log_to_console': True,
            'log_json': False,
            'log_dir': 'logs',
            'max_pattern_size': 1000000,
            'cache_size': 100,
            'enable_analytics': False,
            'enable_telemetry': False,
        }
        
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config.get('log_level') not in valid_log_levels:
            logger.warning(f"Invalid log level: {self._config.get('log_level')}, using INFO")
            self._config['log_level'] = 'INFO'
        
        # Validate numeric values
        if self._config.get('max_pattern_size', 0) < 0:
            logger.warning("max_pattern_size must be positive, using default")
            self._config['max_pattern_size'] = 1000000
        
        if self._config.get('cache_size', 0) < 0:
            logger.warning("cache_size must be positive, using default")
            self._config['cache_size'] = 100
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        logger.debug(f"Configuration updated: {key} = {value}")
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value (from environment or secrets file).
        
        Args:
            key: Secret key
            default: Default value if key not found
        
        Returns:
            Secret value
        """
        # First check environment
        env_key = key.upper().replace('.', '_')
        value = os.getenv(env_key)
        if value:
            return value
        
        # Check loaded secrets
        if key in self._secrets:
            return self._secrets[key]
        
        return default
    
    def set_secret(self, key: str, value: str) -> None:
        """
        Set secret value (in memory only, not persisted).
        
        Args:
            key: Secret key
            value: Secret value
        """
        self._secrets[key] = value
        logger.debug(f"Secret updated: {key}")
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._config.clear()
        self._secrets.clear()
        self._load_config()
        logger.info("Configuration reloaded")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration (excluding secrets).
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()
    
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        
        Returns:
            True if production
        """
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """
        Check if running in development environment.
        
        Returns:
            True if development
        """
        return self.environment == Environment.DEVELOPMENT


def get_config() -> ConfigManager:
    """
    Get the configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    return ConfigManager.instance()

