"""
Feature Flags System - Server-Issued Feature Control
Allows server to control which features are enabled for users
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureFlags:
    """
    Manages server-issued feature flags with local caching.
    """
    
    CACHE_FILE = Path.home() / ".upload_bridge" / "feature_flags.json"
    CACHE_TTL = 3600  # 1 hour cache
    
    def __init__(self, server_url: str = "http://localhost:3000", auth_manager=None):
        self.server_url = server_url
        self.auth_manager = auth_manager
        self._flags_cache = {}
        self._cache_timestamp = 0
    
    def is_enabled(self, feature: str, user_token: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for the current user.
        
        Args:
            feature: Feature name to check
            user_token: Optional session/entitlement token
        
        Returns:
            True if feature is enabled, False otherwise
        """
        # Load flags if cache expired
        if self._is_cache_expired():
            self._refresh_flags(user_token)
        
        # Check cached flags
        return self._flags_cache.get(feature, False)
    
    def get_all_flags(self, user_token: Optional[str] = None) -> Dict[str, bool]:
        """
        Get all feature flags for current user.
        
        Args:
            user_token: Optional session/entitlement token
        
        Returns:
            Dictionary of feature flags
        """
        if self._is_cache_expired():
            self._refresh_flags(user_token)
        
        return self._flags_cache.copy()
    
    def _is_cache_expired(self) -> bool:
        """Check if cache has expired"""
        return (time.time() - self._cache_timestamp) > self.CACHE_TTL
    
    def _refresh_flags(self, user_token: Optional[str] = None):
        """Refresh feature flags from server"""
        try:
            # Try to get token from auth manager if not provided
            if not user_token and self.auth_manager:
                if hasattr(self.auth_manager, 'session_token') and self.auth_manager.session_token:
                    user_token = self.auth_manager.session_token
            
            headers = {}
            if user_token:
                headers['Authorization'] = f'Bearer {user_token}'
            
            response = requests.post(
                f"{self.server_url}/api/v2/features/check",
                json={'features': list(self._flags_cache.keys()) if self._flags_cache else []},
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self._flags_cache = data.get('flags', {})
                self._cache_timestamp = time.time()
                self._save_cache()
            else:
                # Use cached flags if server unavailable
                self._load_cache()
                
        except Exception as e:
            logger.warning("Failed to refresh feature flags: %s", e)
            # Use cached flags on error
            self._load_cache()
    
    def _save_cache(self):
        """Save flags cache to disk"""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                'flags': self._flags_cache,
                'timestamp': self._cache_timestamp
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error("Failed to save feature flags cache: %s", e)
    
    def _load_cache(self):
        """Load flags cache from disk"""
        try:
            if self.CACHE_FILE.exists():
                with open(self.CACHE_FILE, 'r') as f:
                    cache_data = json.load(f)
                    self._flags_cache = cache_data.get('flags', {})
                    self._cache_timestamp = cache_data.get('timestamp', 0)
        except Exception as e:
            logger.error("Failed to load feature flags cache: %s", e)
            self._flags_cache = {}
            self._cache_timestamp = 0
    
    def clear_cache(self):
        """Clear feature flags cache"""
        self._flags_cache = {}
        self._cache_timestamp = 0
        if self.CACHE_FILE.exists():
            self.CACHE_FILE.unlink()


# Global feature flags instance
_feature_flags_instance = None


def get_feature_flags(server_url: str = "http://localhost:3000", auth_manager=None) -> FeatureFlags:
    """Get or create global feature flags instance"""
    global _feature_flags_instance
    if _feature_flags_instance is None:
        _feature_flags_instance = FeatureFlags(server_url, auth_manager)
    return _feature_flags_instance


def is_feature_enabled(feature: str, server_url: str = "http://localhost:3000", auth_manager=None) -> bool:
    """Convenience function to check if a feature is enabled"""
    flags = get_feature_flags(server_url, auth_manager)
    user_token = None
    if auth_manager and hasattr(auth_manager, 'session_token'):
        user_token = auth_manager.session_token
    return flags.is_enabled(feature, user_token)
