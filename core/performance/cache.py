"""
Frame Cache - LRU cache for pattern frames to improve performance.

This module provides frame caching to avoid recomputing frame data
and improve application responsiveness.
"""

from __future__ import annotations

import time
from typing import Optional, Dict, Tuple, Any
from collections import OrderedDict
from threading import Lock

from core.pattern import Frame, Pattern

RGB = Tuple[int, int, int]


class FrameCache:
    """
    LRU cache for pattern frames.
    
    Caches computed frame data to avoid expensive recomputation.
    Thread-safe implementation.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize frame cache.
        
        Args:
            max_size: Maximum number of frames to cache
        """
        self._max_size = max_size
        self._cache: OrderedDict[str, Tuple[Frame, float]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, pattern_id: str, frame_index: int, width: int, height: int) -> str:
        """Create cache key."""
        return f"{pattern_id}:{frame_index}:{width}x{height}"
    
    def get(
        self,
        pattern_id: str,
        frame_index: int,
        width: int,
        height: int
    ) -> Optional[Frame]:
        """
        Get frame from cache.
        
        Args:
            pattern_id: Unique pattern identifier
            frame_index: Frame index
            width: Pattern width
            height: Pattern height
        
        Returns:
            Cached frame or None if not in cache
        """
        key = self._make_key(pattern_id, frame_index, width, height)
        
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                frame, timestamp = self._cache.pop(key)
                self._cache[key] = (frame, timestamp)
                self._hits += 1
                return frame
            
            self._misses += 1
            return None
    
    def put(
        self,
        pattern_id: str,
        frame_index: int,
        width: int,
        height: int,
        frame: Frame
    ) -> None:
        """
        Put frame in cache.
        
        Args:
            pattern_id: Unique pattern identifier
            frame_index: Frame index
            width: Pattern width
            height: Pattern height
            frame: Frame to cache
        """
        key = self._make_key(pattern_id, frame_index, width, height)
        
        with self._lock:
            # Remove if exists
            if key in self._cache:
                self._cache.pop(key)
            
            # Add to end
            self._cache[key] = (frame, time.time())
            
            # Evict oldest if over limit
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
    
    def invalidate_pattern(self, pattern_id: str) -> None:
        """Invalidate all frames for a pattern."""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(f"{pattern_id}:")
            ]
            for key in keys_to_remove:
                self._cache.pop(key, None)
    
    def invalidate_frame(
        self,
        pattern_id: str,
        frame_index: int
    ) -> None:
        """Invalidate specific frame."""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(f"{pattern_id}:{frame_index}:")
            ]
            for key in keys_to_remove:
                self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_requests": total
            }
    
    def resize(self, new_max_size: int) -> None:
        """Resize cache, evicting oldest entries if needed."""
        with self._lock:
            self._max_size = new_max_size
            while len(self._cache) > new_max_size:
                self._cache.popitem(last=False)


# Global frame cache instance
_frame_cache: Optional[FrameCache] = None


def get_frame_cache() -> FrameCache:
    """Get global frame cache instance."""
    global _frame_cache
    if _frame_cache is None:
        _frame_cache = FrameCache()
    return _frame_cache


def clear_frame_cache() -> None:
    """Clear global frame cache."""
    global _frame_cache
    if _frame_cache:
        _frame_cache.clear()

