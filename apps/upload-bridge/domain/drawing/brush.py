"""
Brush System - Brush settings and configurations

Provides brush settings: size, shape, hardness, opacity.
"""

from dataclasses import dataclass
from typing import Tuple
from enum import Enum


class BrushShape(Enum):
    """Brush shapes"""
    SQUARE = "square"
    CIRCLE = "circle"


@dataclass
class BrushSettings:
    """Brush settings configuration"""
    size: int = 1  # Brush size (1-max)
    shape: BrushShape = BrushShape.SQUARE
    hardness: float = 1.0  # Edge hardness (0.0-1.0)
    opacity: float = 1.0  # Brush opacity (0.0-1.0)
    
    def __post_init__(self):
        """Validate settings"""
        self.size = max(1, self.size)
        self.hardness = max(0.0, min(1.0, self.hardness))
        self.opacity = max(0.0, min(1.0, self.opacity))


class Brush:
    """Brush tool with settings"""
    
    def __init__(self, settings: BrushSettings = None):
        """
        Initialize brush.
        
        Args:
            settings: Brush settings (creates default if None)
        """
        self.settings = settings or BrushSettings()
    
    def get_coverage(self, center_x: int, center_y: int, width: int, height: int) -> list[Tuple[int, int, float]]:
        """
        Get pixel coverage for brush stroke.
        
        Returns list of (x, y, opacity) tuples where opacity is based on
        brush position within the stroke area.
        
        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            width: Matrix width
            height: Matrix height
            
        Returns:
            List of (x, y, opacity) tuples
        """
        coverage = []
        size = self.settings.size
        half_size = size // 2
        
        for dy in range(-half_size, half_size + 1):
            for dx in range(-half_size, half_size + 1):
                x = center_x + dx
                y = center_y + dy
                
                if 0 <= x < width and 0 <= y < height:
                    # Calculate distance from center
                    if self.settings.shape == BrushShape.CIRCLE:
                        dist = (dx * dx + dy * dy) ** 0.5
                        max_dist = half_size + 0.5
                        if dist <= max_dist:
                            # Hardness affects falloff
                            normalized_dist = dist / max_dist
                            opacity = 1.0 - (normalized_dist * (1.0 - self.settings.hardness))
                            opacity = max(0.0, min(1.0, opacity))
                            coverage.append((x, y, opacity * self.settings.opacity))
                    else:
                        # Square brush
                        coverage.append((x, y, self.settings.opacity))
        
        return coverage

