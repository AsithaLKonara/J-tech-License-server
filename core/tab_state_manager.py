"""
Tab State Manager - Persist and restore tab configurations
"""

from PySide6.QtCore import QSettings
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TabStateManager:
    """
    Manages saving and loading of tab state configurations
    Uses QSettings for persistence across application sessions
    """
    
    def __init__(self, settings: QSettings = None):
        """
        Initialize tab state manager
        
        Args:
            settings: QSettings instance (optional, creates new if not provided)
        """
        self.settings = settings or QSettings("UploadBridge", "UploadBridge")
        self._state_prefix = "tab_state/"
    
    def save_tab_state(self, tab_name: str, state: Dict):
        """
        Save tab state to persistent storage
        
        Args:
            tab_name: Name of the tab (e.g., 'flash', 'design_tools')
            state: Dictionary containing tab state data
        """
        try:
            key = f"{self._state_prefix}{tab_name}"
            # Convert state dict to settings-compatible format
            self.settings.setValue(key, state)
            self.settings.sync()
            logger.debug(f"Saved state for tab '{tab_name}': {list(state.keys())}")
        except Exception as e:
            logger.error(f"Failed to save state for tab '{tab_name}': {e}", exc_info=True)
    
    def load_tab_state(self, tab_name: str) -> Optional[Dict]:
        """
        Load tab state from persistent storage
        
        Args:
            tab_name: Name of the tab
            
        Returns:
            Dictionary containing tab state, or None if not found
        """
        try:
            key = f"{self._state_prefix}{tab_name}"
            value = self.settings.value(key)
            if value and isinstance(value, dict):
                logger.debug(f"Loaded state for tab '{tab_name}': {list(value.keys())}")
                return value
            return None
        except Exception as e:
            logger.error(f"Failed to load state for tab '{tab_name}': {e}", exc_info=True)
            return None
    
    def clear_tab_state(self, tab_name: str):
        """
        Clear saved state for a tab
        
        Args:
            tab_name: Name of the tab
        """
        try:
            key = f"{self._state_prefix}{tab_name}"
            self.settings.remove(key)
            self.settings.sync()
            logger.debug(f"Cleared state for tab '{tab_name}'")
        except Exception as e:
            logger.error(f"Failed to clear state for tab '{tab_name}': {e}", exc_info=True)
    
    def clear_all_states(self):
        """Clear all saved tab states"""
        try:
            self.settings.beginGroup(self._state_prefix.rstrip('/'))
            self.settings.remove("")
            self.settings.endGroup()
            self.settings.sync()
            logger.debug("Cleared all tab states")
        except Exception as e:
            logger.error(f"Failed to clear all tab states: {e}", exc_info=True)

