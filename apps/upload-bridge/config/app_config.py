"""
Application Configuration Management

This module provides functions for loading and saving application configuration.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_app_config() -> Dict[str, Any]:
    """Load application configuration from YAML file.
    
    Returns:
        Dict containing application configuration, or empty dict if file doesn't exist or error occurs.
    """
    config_path = Path(__file__).parent / "app_config.yaml"
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Error loading app config: %s", e)
        return {}


def save_app_config(config: Dict[str, Any]) -> bool:
    """Save application configuration to YAML file.
    
    Args:
        config: Dictionary containing configuration to save.
        
    Returns:
        True if save was successful, False otherwise.
    """
    config_path = Path(__file__).parent / "app_config.yaml"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error("Error saving app config: %s", e)
        return False

