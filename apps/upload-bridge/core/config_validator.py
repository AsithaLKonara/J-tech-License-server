"""
Configuration validation utilities.

Validates application configuration at startup and provides
clear error messages if required values are missing.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfigValue:
    """Represents a configuration value to validate"""
    name: str
    required: bool = False
    default: Optional[Any] = None
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    env_var: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class ConfigValidator:
    """Validates application configuration"""
    
    # Define expected configuration values
    REQUIRED_CONFIGS = {
        'device_polling_interval': ConfigValue(
            name='device_polling_interval',
            required=False,
            default=5,
            validator=lambda x: isinstance(x, (int, float)) and x > 0,
            description='Device polling interval in seconds',
            suggestions=['Must be > 0', 'Typical values: 1-10 seconds']
        ),
        'upload_timeout': ConfigValue(
            name='upload_timeout',
            required=False,
            default=30,
            validator=lambda x: isinstance(x, (int, float)) and x > 0,
            description='Upload timeout in seconds',
            suggestions=['Must be > 0', 'Typical values: 10-300 seconds']
        ),
        'max_retry_attempts': ConfigValue(
            name='max_retry_attempts',
            required=False,
            default=3,
            validator=lambda x: isinstance(x, int) and x > 0,
            description='Maximum number of retry attempts',
            suggestions=['Must be > 0', 'Typical values: 2-5']
        ),
        'max_concurrent_uploads': ConfigValue(
            name='max_concurrent_uploads',
            required=False,
            default=3,
            validator=lambda x: isinstance(x, int) and x > 0,
            description='Maximum concurrent uploads',
            suggestions=['Must be > 0', 'Typical values: 1-5']
        ),
        'log_level': ConfigValue(
            name='log_level',
            required=False,
            default='INFO',
            validator=lambda x: x in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'),
            description='Logging level',
            env_var='UPLOADBRIDGE_LOG_LEVEL',
            suggestions=['Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL']
        ),
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize validator.
        
        Args:
            config: Configuration dictionary to validate
        """
        self.config = config or {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate the configuration.
        
        Returns:
            Tuple of (is_valid, merged_config)
        """
        merged_config = {}
        self.errors.clear()
        self.warnings.clear()
        
        for config_key, config_def in self.REQUIRED_CONFIGS.items():
            # Try to get value from config
            value = self.config.get(config_key)
            
            # If not in config, try environment variable
            if value is None and config_def.env_var:
                value = os.getenv(config_def.env_var)
            
            # If not found, use default or raise error
            if value is None:
                if config_def.required:
                    self.errors.append(
                        f"Missing required config: {config_key}\n"
                        f"  Description: {config_def.description}\n"
                        f"  {chr(10).join(config_def.suggestions)}"
                    )
                    continue
                else:
                    value = config_def.default
                    if value is not None:
                        self.warnings.append(
                            f"Using default for {config_key}: {value}"
                        )
            
            # Validate the value
            if config_def.validator and not config_def.validator(value):
                self.errors.append(
                    f"Invalid value for {config_key}: {value}\n"
                    f"  Description: {config_def.description}\n"
                    f"  {chr(10).join(config_def.suggestions)}"
                )
                continue
            
            merged_config[config_key] = value
        
        # Log warnings
        for warning in self.warnings:
            logger.warning(warning)
        
        # Log errors
        for error in self.errors:
            logger.error(error)
        
        is_valid = len(self.errors) == 0
        return is_valid, merged_config
    
    def validate_file_path(self, key: str, path_str: str, must_exist: bool = False) -> bool:
        """
        Validate a file path configuration.
        
        Args:
            key: Configuration key
            path_str: Path string to validate
            must_exist: Whether file must exist
        
        Returns:
            True if valid
        """
        try:
            path = Path(path_str).expanduser()
            
            if must_exist and not path.exists():
                self.errors.append(
                    f"File does not exist: {key} = {path_str}\n"
                    f"  Full path: {path.absolute()}"
                )
                return False
            
            # Check if parent directory exists
            if not path.parent.exists():
                self.warnings.append(
                    f"Parent directory does not exist: {key}\n"
                    f"  Will create: {path.parent.absolute()}"
                )
            
            return True
        
        except Exception as e:
            self.errors.append(f"Invalid file path for {key}: {e}")
            return False
    
    def validate_port(self, key: str, port: Any) -> bool:
        """
        Validate a port number.
        
        Args:
            key: Configuration key
            port: Port number to validate
        
        Returns:
            True if valid
        """
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                self.errors.append(
                    f"Port out of range for {key}: {port}\n"
                    f"  Valid range: 1-65535"
                )
                return False
            return True
        
        except (ValueError, TypeError):
            self.errors.append(f"Invalid port for {key}: {port} (must be integer)")
            return False
    
    def get_error_message(self) -> str:
        """
        Get formatted error message.
        
        Returns:
            Error message string
        """
        if not self.errors:
            return ""
        
        message = "Configuration validation failed:\n\n"
        for i, error in enumerate(self.errors, 1):
            message += f"{i}. {error}\n\n"
        
        return message.strip()


class ConfigurationManager:
    """Manages application configuration with validation"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        Load and validate configuration.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            True if configuration is valid
        """
        validator = ConfigValidator(config_dict)
        is_valid, validated_config = validator.validate()
        
        if not is_valid:
            logger.error(validator.get_error_message())
            return False
        
        self._config = validated_config
        logger.info("Configuration validated successfully")
        return True
    
    def load_from_file(self, config_path: Path) -> bool:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            True if loaded successfully
        """
        try:
            import json
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            return self.load_config(config_dict)
        
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return False
        
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False
    
    def load_from_env(self) -> bool:
        """
        Load configuration from environment variables.
        
        Returns:
            True if loaded successfully
        """
        config_dict = {}
        
        # Map environment variables to config keys
        env_mappings = {
            'UPLOADBRIDGE_LOG_LEVEL': 'log_level',
            'UPLOADBRIDGE_UPLOAD_TIMEOUT': 'upload_timeout',
            'UPLOADBRIDGE_POLLING_INTERVAL': 'device_polling_interval',
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                config_dict[config_key] = value
        
        if config_dict:
            return self.load_config(config_dict)
        
        logger.debug("No configuration environment variables found")
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()


def get_config_manager() -> ConfigurationManager:
    """Get the configuration manager instance"""
    return ConfigurationManager()
