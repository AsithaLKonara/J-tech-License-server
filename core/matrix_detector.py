"""
Matrix Detector - Automatically detects LED matrix size and shape
Provides intelligent matrix layout detection for pattern preview
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .dimension_scorer import (
    COMMON_LAYOUTS,
    generate_layout_candidates,
    pick_best_layout,
)


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
    
    def __init__(self):
        self.layout_cache: Dict[int, MatrixLayout] = {}
    
    def detect_layout(self, led_count: int, pattern_data: Optional[List] = None) -> MatrixLayout:
        """
        Detect the best matrix layout for given LED count
        
        Args:
            led_count: Total number of LEDs
            pattern_data: Optional pattern data for analysis
            
        Returns:
            MatrixLayout object with detected information
        """
        if led_count in self.layout_cache:
            return self.layout_cache[led_count]
        
        first_frame = None
        if pattern_data:
            first_frame = pattern_data[0] if isinstance(pattern_data[0], list) else pattern_data
            if first_frame and len(first_frame) != led_count:
                first_frame = None

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
            self.layout_cache[led_count] = fallback
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

        self.layout_cache[led_count] = layout
        return layout
    
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


def detect_matrix_layout(led_count: int, pattern_data: Optional[List] = None) -> MatrixLayout:
    """
    Convenience function to detect matrix layout
    
    Args:
        led_count: Total number of LEDs
        pattern_data: Optional pattern data for analysis
        
    Returns:
        MatrixLayout object
    """
    detector = MatrixDetector()
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

