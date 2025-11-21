"""
Dimension Detection Cache Persistence
Persists dimension detection cache to disk for faster re-loading
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)


class DimensionCachePersistence:
    """
    Manages persistence of dimension detection cache to disk.
    
    Features:
    - Save cache to JSON file
    - Load cache on startup
    - Automatic cache invalidation
    - Version control for cache format
    """
    
    CACHE_VERSION = 1
    CACHE_FILENAME = "dimension_cache.json"
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize cache persistence.
        
        Args:
            cache_dir: Directory to store cache file (default: user config dir)
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Use user config directory
            from PySide6.QtCore import QStandardPaths
            config_path = QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)
            self.cache_dir = Path(config_path) / "UploadBridge"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / self.CACHE_FILENAME
    
    def save_cache(self, cache_data: Dict[str, Tuple[Any, int, float]]) -> bool:
        """
        Save cache to disk.
        
        Args:
            cache_data: Cache dictionary from MatrixDetector
            
        Returns:
            True if saved successfully
        """
        try:
            # Convert cache to serializable format
            serializable_cache = {}
            for key, (layout, access_count, last_access) in cache_data.items():
                serializable_cache[key] = {
                    'width': layout.width,
                    'height': layout.height,
                    'total_leds': layout.total_leds,
                    'layout_type': layout.layout_type,
                    'confidence': layout.confidence,
                    'access_count': access_count,
                    'last_access': last_access
                }
            
            cache_obj = {
                'version': self.CACHE_VERSION,
                'cache': serializable_cache
            }
            
            # Write to file atomically
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_obj, f, indent=2)
            
            # Atomic rename
            temp_file.replace(self.cache_file)
            
            logger.info(f"Saved dimension cache to {self.cache_file} ({len(serializable_cache)} entries)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save dimension cache: {e}")
            return False
    
    def load_cache(self) -> Optional[Dict[str, Tuple[Any, int, float]]]:
        """
        Load cache from disk.
        
        Returns:
            Cache dictionary or None if load failed
        """
        if not self.cache_file.exists():
            logger.debug("Dimension cache file does not exist")
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_obj = json.load(f)
            
            # Check version
            version = cache_obj.get('version', 0)
            if version != self.CACHE_VERSION:
                logger.warning(f"Cache version mismatch ({version} vs {self.CACHE_VERSION}), ignoring cache")
                return None
            
            # Reconstruct cache
            from .matrix_detector import MatrixLayout
            cache_data = OrderedDict()
            
            for key, entry in cache_obj.get('cache', {}).items():
                layout = MatrixLayout(
                    width=entry['width'],
                    height=entry['height'],
                    total_leds=entry['total_leds'],
                    layout_type=entry['layout_type'],
                    confidence=entry['confidence']
                )
                cache_data[key] = (
                    layout,
                    entry.get('access_count', 1),
                    entry.get('last_access', 0.0)
                )
            
            logger.info(f"Loaded dimension cache from {self.cache_file} ({len(cache_data)} entries)")
            return cache_data
            
        except Exception as e:
            logger.error(f"Failed to load dimension cache: {e}")
            return None
    
    def clear_cache(self) -> bool:
        """
        Clear cache file from disk.
        
        Returns:
            True if cleared successfully
        """
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Cleared dimension cache file")
            return True
        except Exception as e:
            logger.error(f"Failed to clear dimension cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached data.
        
        Returns:
            Dictionary with cache information
        """
        info = {
            'cache_file': str(self.cache_file),
            'exists': self.cache_file.exists(),
            'size_bytes': 0,
            'entry_count': 0
        }
        
        if self.cache_file.exists():
            try:
                info['size_bytes'] = self.cache_file.stat().st_size
                
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_obj = json.load(f)
                    info['entry_count'] = len(cache_obj.get('cache', {}))
                    info['version'] = cache_obj.get('version', 0)
            except Exception:
                pass
        
        return info

