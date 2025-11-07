"""
Matrix Detector - Automatically detects LED matrix size and shape
Provides intelligent matrix layout detection for pattern preview
"""

import math
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass


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
    
    # Common matrix sizes
    COMMON_MATRICES = [
        (8, 8),    # 64 LEDs
        (10, 10), # 100 LEDs
        (12, 12), # 144 LEDs
        (16, 16), # 256 LEDs
        (20, 20), # 400 LEDs
        (24, 24), # 576 LEDs
        (32, 32), # 1024 LEDs
    ]
    
    # Common strip lengths
    COMMON_STRIPS = [
        30, 60, 76, 100, 144, 150, 200, 300, 400, 500, 600, 800, 1000
    ]
    
    def __init__(self):
        self.layout_cache = {}
    
    def detect_layout(self, led_count: int, pattern_data: Optional[List] = None) -> MatrixLayout:
        """
        Detect the best matrix layout for given LED count
        
        Args:
            led_count: Total number of LEDs
            pattern_data: Optional pattern data for analysis
            
        Returns:
            MatrixLayout object with detected information
        """
        # Check cache first
        if led_count in self.layout_cache:
            return self.layout_cache[led_count]
        
        # Try different detection methods
        layouts = []
        
        # Method 1: Perfect square matrix
        square_layout = self._detect_square_matrix(led_count)
        if square_layout:
            layouts.append(square_layout)
        
        # Method 2: Common matrix sizes
        common_layout = self._detect_common_matrix(led_count)
        if common_layout:
            layouts.append(common_layout)
        
        # Method 3: Strip layout
        strip_layout = self._detect_strip_layout(led_count)
        if strip_layout:
            layouts.append(strip_layout)
        
        # Method 4: Custom matrix (non-square)
        custom_layout = self._detect_custom_matrix(led_count)
        if custom_layout:
            layouts.append(custom_layout)
        
        # Method 5: Pattern data analysis
        if pattern_data:
            data_layout = self._analyze_pattern_data(led_count, pattern_data)
            if data_layout:
                layouts.append(data_layout)
        
        # Select best layout
        if not layouts:
            # Fallback to strip layout
            best_layout = MatrixLayout(
                width=led_count,
                height=1,
                total_leds=led_count,
                layout_type="strip",
                confidence=0.1
            )
        else:
            # Choose layout with highest confidence
            best_layout = max(layouts, key=lambda x: x.confidence)
        
        # Cache result
        self.layout_cache[led_count] = best_layout
        
        return best_layout
    
    def _detect_square_matrix(self, led_count: int) -> Optional[MatrixLayout]:
        """Detect if LED count forms a perfect square matrix"""
        sqrt = int(math.sqrt(led_count))
        if sqrt * sqrt == led_count:
            return MatrixLayout(
                width=sqrt,
                height=sqrt,
                total_leds=led_count,
                layout_type="matrix",
                confidence=0.9
            )
        return None
    
    def _detect_common_matrix(self, led_count: int) -> Optional[MatrixLayout]:
        """Detect common matrix sizes"""
        for width, height in self.COMMON_MATRICES:
            if width * height == led_count:
                return MatrixLayout(
                    width=width,
                    height=height,
                    total_leds=led_count,
                    layout_type="matrix",
                    confidence=0.8
                )
        return None
    
    def _detect_strip_layout(self, led_count: int) -> Optional[MatrixLayout]:
        """Detect strip layout"""
        if led_count in self.COMMON_STRIPS:
            confidence = 0.7
        else:
            confidence = 0.5
        
        return MatrixLayout(
            width=led_count,
            height=1,
            total_leds=led_count,
            layout_type="strip",
            confidence=confidence
        )
    
    def _detect_custom_matrix(self, led_count: int) -> Optional[MatrixLayout]:
        """Detect custom (non-square) matrix layouts"""
        # Try different aspect ratios
        aspect_ratios = [
            (2, 1),   # 2:1
            (3, 1),   # 3:1
            (4, 1),   # 4:1
            (1, 2),   # 1:2
            (1, 3),   # 1:3
            (1, 4),   # 1:4
            (3, 2),   # 3:2
            (2, 3),   # 2:3
            (4, 3),   # 4:3
            (3, 4),   # 3:4
        ]
        
        for width_ratio, height_ratio in aspect_ratios:
            # Calculate dimensions
            total_ratio = width_ratio * height_ratio
            if led_count % total_ratio == 0:
                multiplier = led_count // total_ratio
                width = width_ratio * multiplier
                height = height_ratio * multiplier
                
                if width > 1 and height > 1:
                    return MatrixLayout(
                        width=width,
                        height=height,
                        total_leds=led_count,
                        layout_type="matrix",
                        confidence=0.6
                    )
        
        return None
    
    def _analyze_pattern_data(self, led_count: int, pattern_data: List) -> Optional[MatrixLayout]:
        """Analyze pattern data to detect layout"""
        if not pattern_data or len(pattern_data) == 0:
            return None
        
        # Analyze first frame
        first_frame = pattern_data[0] if isinstance(pattern_data[0], list) else pattern_data
        
        if len(first_frame) != led_count:
            return None
        
        # Look for spatial patterns in the data
        # This is a simplified analysis - could be enhanced with more sophisticated algorithms
        
        # Check if data suggests a matrix layout
        # (This is a placeholder for more sophisticated analysis)
        
        return None
    
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

