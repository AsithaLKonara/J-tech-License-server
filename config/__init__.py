"""
Configuration Management for Upload Bridge
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def load_chip_database() -> Dict[str, Any]:
    """Load chip database from YAML file"""
    config_path = Path(__file__).parent / "chip_database.yaml"
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Error loading chip database: %s", e)
        return {}

def load_app_config() -> Dict[str, Any]:
    """Load application configuration from YAML file"""
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
    """Save application configuration to YAML file"""
    config_path = Path(__file__).parent / "app_config.yaml"
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False)
        return True
    except Exception as e:
        logger.error("Error saving app config: %s", e)
        return False

