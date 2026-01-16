"""
Chip Database Management

This module provides functions for loading the chip database.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_chip_database() -> Dict[str, Any]:
    """Load chip database from YAML file.
    
    Returns:
        Dict containing chip database, or empty dict if file doesn't exist or error occurs.
    """
    config_path = Path(__file__).parent / "chip_database.yaml"
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error("Error loading chip database: %s", e)
        return {}

