"""
Matrix Detector - Automatically detects LED matrix size and shape
Provides intelligent matrix layout detection for pattern preview
"""

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .dimension_scorer import (
    COMMON_LAYOUTS,
    generate_layout_candidates,
    pick_best_layout,
)

logger = logging.getLogger(__name__)


@dataclass
class MatrixLayout:
    """LED matrix layout information"""
    width: int
    height: int
    total_leds: int
    layout_type: str  # "strip", "matrix", "ring", "custom"
    confidence: float  # 0.0 to 1.0
    suggested_arrangement: Optional[List[Tuple[int, int]]] = None  # (x, y) positions


class MatrixDetector:
    """
    Intelligent LED matrix layout detector
    
    Features:
    - Automatic width/height detection
    - Layout type classification
    - Confidence scoring
    - Common matrix size recognition
    - Custom layout support
    """
    
    # Common matrix sizes (legacy export)
    COMMON_MATRICES = list(COMMON_LAYOUTS)
    
    # Common strip lengths
    COMMON_STRIPS = [
        30, 60, 76, 100, 144, 150, 200, 300, 400, 500, 600, 800, 1000
    ]
    
    def __init__(self, max_cache_size: int = 100, enable_persistence: bool = True):
        """
        Initialize matrix detector with enhanced caching and optional persistence.
        
        Args:
            max_cache_size: Maximum number of cached entries (LRU eviction)
            enable_persistence: Enable disk-based cache persistence
        """
        # Enhanced cache: key -> (layout, access_count, last_access_time)
        self.layout_cache: OrderedDict[str, Tuple[MatrixLayout, int, float]] = OrderedDict()
        self.max_cache_size = max_cache_size
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }
        self.enable_persistence = enable_persistence
        self._cache_persistence = None
        
        # Load cache from disk if persistence enabled
        if enable_persistence:
            try:
                from .dimension_cache_persistence import DimensionCachePersistence
                self._cache_persistence = DimensionCachePersistence()
                loaded_cache = self._cache_persistence.load_cache()
                if loaded_cache:
                    self.layout_cache = loaded_cache
                    logger.info(f"Loaded {len(loaded_cache)} dimension cache entries from disk")
            except Exception as e:
                logger.warning(f"Failed to load dimension cache from disk: {e}")
    
    def _generate_cache_key(self, led_count: int, first_frame: Optional[List] = None) -> str:
        """
        Generate cache key from LED count and first frame hash.
        
        Args:
            led_count: Total number of LEDs
            first_frame: Optional first frame pixel data
            
        Returns:
            Cache key string
        """
        import time
        if first_frame and len(first_frame) == led_count:
            # Create hash from first frame pixels (sample first 100 pixels for speed)
            sample_size = min(100, len(first_frame))
            frame_hash = hashlib.md5(
                bytes([c for pixel in first_frame[:sample_size] for c in pixel])
            ).hexdigest()[:16]
            return f"{led_count}_{frame_hash}"
        return f"{led_count}_no_frame"
    
    def detect_layout(self, led_count: int, pattern_data: Optional[List] = None) -> MatrixLayout:
        """
        Detect the best matrix layout for given LED count with enhanced caching.
        
        Args:
            led_count: Total number of LEDs
            pattern_data: Optional pattern data for analysis
            
        Returns:
            MatrixLayout object with detected information
        """
        import time
        
        # Extract first frame if available
        first_frame = None
        if pattern_data:
            first_frame = pattern_data[0] if isinstance(pattern_data[0], list) else pattern_data
            if first_frame and len(first_frame) != led_count:
                first_frame = None
        
        # Generate cache key
        cache_key = self._generate_cache_key(led_count, first_frame)
        
        # Check cache
        if cache_key in self.layout_cache:
            layout, access_count, _ = self.layout_cache[cache_key]
            # Move to end (most recently used)
            self.layout_cache.move_to_end(cache_key)
            # Update access count and time
            self.layout_cache[cache_key] = (layout, access_count + 1, time.time())
            self.cache_stats['hits'] += 1
            logger.debug(f"Cache HIT for key {cache_key}: {layout.width}×{layout.height}")
            return layout
        
        # Cache miss - perform detection
        self.cache_stats['misses'] += 1
        logger.debug(f"Cache MISS for key {cache_key}, performing detection...")

        candidates = generate_layout_candidates(
            led_count,
            first_frame=first_frame,
            include_strips=True,
            limit=6,
        )

        if not candidates:
            fallback = MatrixLayout(
                width=led_count,
                height=1,
                total_leds=led_count,
                layout_type="strip",
                confidence=0.1,
            )
            self._cache_result(cache_key, fallback)
            return fallback

        width, height, confidence = candidates[0]
        layout_type = "matrix" if height > 1 else "strip"

        # Boost strip confidence for known lengths
        if layout_type == "strip" and led_count in self.COMMON_STRIPS:
            confidence = max(confidence, 0.7)

        layout = MatrixLayout(
            width=width,
            height=height,
            total_leds=led_count,
            layout_type=layout_type,
            confidence=confidence,
        )

        self._cache_result(cache_key, layout)
        return layout
    
    def _cache_result(self, cache_key: str, layout: MatrixLayout):
        """
        Cache detection result with LRU eviction and optional persistence.
        
        Args:
            cache_key: Cache key string
            layout: MatrixLayout to cache
        """
        import time
        
        # Evict oldest entry if cache is full
        if len(self.layout_cache) >= self.max_cache_size:
            oldest_key = next(iter(self.layout_cache))
            del self.layout_cache[oldest_key]
            self.cache_stats['evictions'] += 1
            logger.debug(f"Cache eviction: removed key {oldest_key}")
        
        # Add new entry
        self.layout_cache[cache_key] = (layout, 1, time.time())
        logger.debug(f"Cached result for key {cache_key}: {layout.width}×{layout.height}")
        
        # Save to disk periodically (every 10 new entries)
        if self.enable_persistence and self._cache_persistence and len(self.layout_cache) % 10 == 0:
            try:
                self._cache_persistence.save_cache(self.layout_cache)
            except Exception as e:
                logger.warning(f"Failed to save dimension cache: {e}")
    
    def clear_cache(self):
        """Clear the detection cache (memory and disk)."""
        self.layout_cache.clear()
        self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        
        # Clear disk cache if persistence enabled
        if self.enable_persistence and self._cache_persistence:
            try:
                self._cache_persistence.clear_cache()
            except Exception as e:
                logger.warning(f"Failed to clear dimension cache from disk: {e}")
        
        logger.info("Dimension detection cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            'size': len(self.layout_cache),
            'max_size': self.max_cache_size,
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': hit_rate,
            'total_requests': total_requests,
        }
    
    def invalidate_cache_for_pattern(self, led_count: int, first_frame_hash: Optional[str] = None):
        """
        Invalidate cache entries for a specific pattern.
        
        Args:
            led_count: LED count of pattern
            first_frame_hash: Optional hash of first frame (if None, invalidates all for LED count)
        """
        keys_to_remove = []
        if first_frame_hash:
            cache_key = f"{led_count}_{first_frame_hash[:16]}"
            if cache_key in self.layout_cache:
                keys_to_remove.append(cache_key)
        else:
            # Remove all entries for this LED count
            keys_to_remove = [k for k in self.layout_cache.keys() if k.startswith(f"{led_count}_")]
        
        for key in keys_to_remove:
            del self.layout_cache[key]
            logger.debug(f"Invalidated cache entry: {key}")
        
        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for LED count {led_count}")
    
    @classmethod
    def generate_candidate_layouts(
        cls,
        led_count: int,
        first_frame: Optional[Iterable[Tuple[int, int, int]]] = None,
        include_strips: bool = False,
        limit: int = 8
    ) -> List[Tuple[int, int, float]]:
        """
        Enumerate plausible (width, height) pairs with confidence scores.
        Shared by parsers so everyone ranks layouts consistently.
        """
        return generate_layout_candidates(
            led_count,
            first_frame=first_frame,
            include_strips=include_strips,
            limit=limit,
        )

    @classmethod
    def pick_best_dimensions(
        cls,
        led_count: int,
        first_frame: Optional[Iterable[Tuple[int, int, int]]] = None,
        include_strips: bool = False
    ) -> Optional[Tuple[int, int, float]]:
        """Convenience method returning the top-scoring candidate dimensions."""
        return pick_best_layout(
            led_count,
            first_frame=first_frame,
            include_strips=include_strips,
        )
    
    def get_suggested_arrangement(self, layout: MatrixLayout) -> List[Tuple[int, int]]:
        """
        Get suggested LED arrangement for the layout
        
        Args:
            layout: MatrixLayout object
            
        Returns:
            List of (x, y) positions for each LED
        """
        if layout.suggested_arrangement:
            return layout.suggested_arrangement
        
        arrangement = []
        
        if layout.layout_type == "strip":
            # Linear strip arrangement
            for i in range(layout.total_leds):
                arrangement.append((i, 0))
        
        elif layout.layout_type == "matrix":
            # Matrix arrangement
            for y in range(layout.height):
                for x in range(layout.width):
                    arrangement.append((x, y))
        
        else:
            # Default to linear arrangement
            for i in range(layout.total_leds):
                arrangement.append((i, 0))
        
        return arrangement
    
    def get_layout_info(self, layout: MatrixLayout) -> str:
        """
        Get human-readable layout information
        
        Args:
            layout: MatrixLayout object
            
        Returns:
            Formatted string with layout information
        """
        info = f"Layout: {layout.width}×{layout.height} {layout.layout_type}"
        info += f" (confidence: {layout.confidence:.1%})"
        
        if layout.layout_type == "matrix":
            info += f"\nMatrix size: {layout.width}×{layout.height}"
        elif layout.layout_type == "strip":
            info += f"\nStrip length: {layout.width} LEDs"
        
        return info
    
    def validate_layout(self, layout: MatrixLayout) -> Tuple[bool, List[str]]:
        """
        Validate a matrix layout
        
        Args:
            layout: MatrixLayout object to validate
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check dimensions
        if layout.width <= 0 or layout.height <= 0:
            warnings.append("Invalid dimensions")
            return False, warnings
        
        # Check total LEDs
        if layout.width * layout.height != layout.total_leds:
            warnings.append(f"Dimension mismatch: {layout.width}×{layout.height} ≠ {layout.total_leds}")
            return False, warnings
        
        # Check for very large matrices
        if layout.width > 100 or layout.height > 100:
            warnings.append(f"Very large matrix ({layout.width}×{layout.height}) may cause performance issues")
        
        # Check for unusual aspect ratios
        aspect_ratio = layout.width / layout.height
        if aspect_ratio > 10 or aspect_ratio < 0.1:
            warnings.append(f"Unusual aspect ratio ({aspect_ratio:.2f})")
        
        return True, warnings
    
    def get_optimization_suggestions(self, layout: MatrixLayout) -> List[str]:
        """
        Get optimization suggestions for the layout
        
        Args:
            layout: MatrixLayout object
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Size-based suggestions
        if layout.total_leds > 1000:
            suggestions.append("Consider reducing LED count for better performance")
        elif layout.total_leds > 500:
            suggestions.append("Large LED count may require optimization")
        
        # Matrix-specific suggestions
        if layout.layout_type == "matrix":
            if layout.width > 50 or layout.height > 50:
                suggestions.append("Large matrix size may cause memory issues")
            elif layout.width > 20 or layout.height > 20:
                suggestions.append("Moderate matrix size - monitor performance")
        
        # Strip-specific suggestions
        elif layout.layout_type == "strip":
            if layout.width > 500:
                suggestions.append("Long strip may require segmentation")
            elif layout.width > 200:
                suggestions.append("Long strip - consider power requirements")
        
        # Confidence-based suggestions
        if layout.confidence < 0.5:
            suggestions.append("Low confidence detection - verify layout manually")
        elif layout.confidence < 0.7:
            suggestions.append("Medium confidence detection - consider manual verification")
        
        return suggestions


# Shared detector instance for convenience function (enables caching across calls)
_shared_detector: Optional[MatrixDetector] = None

def get_shared_detector() -> MatrixDetector:
    """Get or create shared MatrixDetector instance for caching."""
    global _shared_detector
    if _shared_detector is None:
        _shared_detector = MatrixDetector()
    return _shared_detector

def detect_matrix_layout(led_count: int, pattern_data: Optional[List] = None) -> MatrixLayout:
    """
    Convenience function to detect matrix layout with caching.
    
    Uses a shared detector instance to enable caching across calls.
    
    Args:
        led_count: Total number of LEDs
        pattern_data: Optional pattern data for analysis
        
    Returns:
        MatrixLayout object
    """
    detector = get_shared_detector()
    return detector.detect_layout(led_count, pattern_data)


def get_matrix_info_string(led_count: int) -> str:
    """
    Get formatted matrix information string
    
    Args:
        led_count: Total number of LEDs
        
    Returns:
        Formatted information string
    """
    layout = detect_matrix_layout(led_count)
    detector = MatrixDetector()
    
    info = detector.get_layout_info(layout)
    
    # Add validation info
    is_valid, warnings = detector.validate_layout(layout)
    if not is_valid:
        info += f"\nValidation: FAILED ({', '.join(warnings)})"
    elif warnings:
        info += f"\nWarnings: {', '.join(warnings)}"
    else:
        info += "\nValidation: PASSED"
    
    # Add optimization suggestions
    suggestions = detector.get_optimization_suggestions(layout)
    if suggestions:
        info += f"\nSuggestions: {', '.join(suggestions)}"
    
    return info

