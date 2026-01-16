"""
Lazy Frame Loader - Load frames on-demand for large patterns
"""

import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from .pattern import Pattern, Frame

logger = logging.getLogger(__name__)


class LazyFrameLoader:
    """
    Lazy frame loader with LRU cache for on-demand frame loading.
    
    Features:
    - Load frames on-demand as user scrubs timeline
    - LRU cache with configurable size
    - Progress tracking
    - Memory-efficient for large patterns
    """
    
    def __init__(self, pattern: Pattern, cache_size: int = 50):
        """
        Initialize lazy frame loader.
        
        Args:
            pattern: Pattern to load frames from
            cache_size: Maximum number of frames to cache (LRU eviction)
        """
        self.pattern = pattern
        self.cache_size = cache_size
        self.frame_cache: OrderedDict[int, Frame] = OrderedDict()
        self.loaded_indices: set = set()
        self.total_frames = len(pattern.frames) if pattern else 0
        
        # Pre-load first frame
        if self.total_frames > 0:
            self.load_frame(0)
    
    def load_frame(self, frame_index: int) -> Optional[Frame]:
        """
        Load a frame (from cache or pattern).
        
        Args:
            frame_index: Index of frame to load
            
        Returns:
            Frame object or None if index out of range
        """
        if frame_index < 0 or frame_index >= self.total_frames:
            return None
        
        # Check cache first
        if frame_index in self.frame_cache:
            # Move to end (most recently used)
            frame = self.frame_cache.pop(frame_index)
            self.frame_cache[frame_index] = frame
            logger.debug(f"Cache HIT: Frame {frame_index}")
            return frame
        
        # Cache miss - load from pattern
        logger.debug(f"Cache MISS: Loading frame {frame_index}")
        
        if not self.pattern or frame_index >= len(self.pattern.frames):
            return None
        
        frame = self.pattern.frames[frame_index]
        
        # Create a copy for caching
        cached_frame = Frame(
            pixels=[tuple(p) for p in frame.pixels],
            duration_ms=frame.duration_ms
        )
        
        # Evict oldest if cache is full
        if len(self.frame_cache) >= self.cache_size:
            oldest_index = next(iter(self.frame_cache))
            del self.frame_cache[oldest_index]
            self.loaded_indices.discard(oldest_index)
            logger.debug(f"Cache eviction: Removed frame {oldest_index}")
        
        # Add to cache
        self.frame_cache[frame_index] = cached_frame
        self.loaded_indices.add(frame_index)
        
        return cached_frame
    
    def preload_frames(self, indices: List[int]):
        """
        Preload multiple frames.
        
        Args:
            indices: List of frame indices to preload
        """
        for idx in indices:
            if 0 <= idx < self.total_frames:
                self.load_frame(idx)
    
    def preload_range(self, start: int, end: int):
        """
        Preload a range of frames.
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive)
        """
        for idx in range(max(0, start), min(self.total_frames, end)):
            self.load_frame(idx)
    
    def get_frame(self, frame_index: int) -> Optional[Frame]:
        """
        Get frame (alias for load_frame for clarity).
        
        Args:
            frame_index: Index of frame
            
        Returns:
            Frame object or None
        """
        return self.load_frame(frame_index)
    
    def clear_cache(self):
        """Clear the frame cache."""
        self.frame_cache.clear()
        self.loaded_indices.clear()
        # Re-load first frame
        if self.total_frames > 0:
            self.load_frame(0)
        logger.info("Frame cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_frames': len(self.frame_cache),
            'cache_size': self.cache_size,
            'total_frames': self.total_frames,
            'cache_usage': len(self.frame_cache) / self.cache_size * 100 if self.cache_size > 0 else 0.0,
            'loaded_indices': sorted(self.loaded_indices),
        }
    
    def is_frame_loaded(self, frame_index: int) -> bool:
        """
        Check if frame is currently cached.
        
        Args:
            frame_index: Frame index to check
            
        Returns:
            True if frame is in cache
        """
        return frame_index in self.frame_cache

