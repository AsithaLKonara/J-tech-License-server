"""
Gradient Engine - Multi-stop gradient interpolation for LED matrices.

Supports:
- Linear gradients (horizontal, vertical, diagonal)
- Radial gradients (circular, from center point)
- Multi-stop gradients (2-10 color stops)
- Color interpolation with various easing functions
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum
import math


RGB = Tuple[int, int, int]


class GradientType(Enum):
    """Gradient rendering types."""
    LINEAR = "linear"
    RADIAL = "radial"


class EasingFunction(Enum):
    """Easing functions for gradient interpolation."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


@dataclass
class GradientStop:
    """
    A single color stop in a gradient.
    
    Attributes:
        position: Position along gradient (0.0 = start, 1.0 = end)
        color: RGB color at this stop
    """
    position: float
    color: RGB
    
    def __post_init__(self):
        """Validate stop parameters."""
        if not (0.0 <= self.position <= 1.0):
            raise ValueError(f"Position must be 0.0-1.0, got {self.position}")
        r, g, b = self.color
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            raise ValueError(f"Invalid RGB color: {self.color}")


@dataclass
class Gradient:
    """
    Multi-stop gradient definition.
    
    Attributes:
        type: Gradient type (linear or radial)
        stops: List of color stops (must have at least 2)
        easing: Easing function for interpolation
    """
    type: GradientType = GradientType.LINEAR
    stops: List[GradientStop] = field(default_factory=list)
    easing: EasingFunction = EasingFunction.LINEAR
    
    def __post_init__(self):
        """Validate and sort stops."""
        if len(self.stops) < 2:
            raise ValueError("Gradient must have at least 2 stops")
        # Sort stops by position
        self.stops = sorted(self.stops, key=lambda s: s.position)
    
    def add_stop(self, position: float, color: RGB) -> None:
        """Add a new color stop and re-sort."""
        self.stops.append(GradientStop(position, color))
        self.stops = sorted(self.stops, key=lambda s: s.position)
    
    def remove_stop(self, index: int) -> bool:
        """Remove a stop by index. Returns False if would leave <2 stops."""
        if len(self.stops) <= 2:
            return False
        if 0 <= index < len(self.stops):
            del self.stops[index]
            return True
        return False
    
    def get_color_at(self, t: float) -> RGB:
        """
        Get interpolated color at position t (0.0-1.0).
        
        Args:
            t: Position along gradient (0.0-1.0)
            
        Returns:
            Interpolated RGB color
        """
        # Clamp t to valid range
        t = max(0.0, min(1.0, t))
        
        # Apply easing function
        t = self._apply_easing(t)
        
        # Find surrounding stops
        left_stop = self.stops[0]
        right_stop = self.stops[-1]
        
        for i in range(len(self.stops) - 1):
            if self.stops[i].position <= t <= self.stops[i + 1].position:
                left_stop = self.stops[i]
                right_stop = self.stops[i + 1]
                break
        
        # Calculate local t between the two stops
        if right_stop.position == left_stop.position:
            local_t = 0.0
        else:
            local_t = (t - left_stop.position) / (right_stop.position - left_stop.position)
        
        # Interpolate RGB values
        r = int(left_stop.color[0] * (1 - local_t) + right_stop.color[0] * local_t)
        g = int(left_stop.color[1] * (1 - local_t) + right_stop.color[1] * local_t)
        b = int(left_stop.color[2] * (1 - local_t) + right_stop.color[2] * local_t)
        
        return (r, g, b)
    
    def _apply_easing(self, t: float) -> float:
        """Apply easing function to t."""
        if self.easing == EasingFunction.LINEAR:
            return t
        elif self.easing == EasingFunction.EASE_IN:
            return t * t
        elif self.easing == EasingFunction.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif self.easing == EasingFunction.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        return t


class GradientRenderer:
    """
    Renders gradients to pixel grids.
    
    Handles both linear and radial gradient rendering with multi-stop support.
    """
    
    @staticmethod
    def render_linear(
        gradient: Gradient,
        width: int,
        height: int,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float
    ) -> List[List[RGB]]:
        """
        Render a linear gradient to a 2D pixel grid.
        
        Args:
            gradient: Gradient definition
            width: Grid width
            height: Grid height
            start_x: Gradient start X coordinate
            start_y: Gradient start Y coordinate
            end_x: Gradient end X coordinate
            end_y: Gradient end Y coordinate
            
        Returns:
            2D grid of RGB colors
        """
        grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        # Calculate gradient vector
        dx = end_x - start_x
        dy = end_y - start_y
        length_sq = dx * dx + dy * dy
        
        if length_sq == 0:
            # Degenerate case: start == end, fill with start color
            color = gradient.stops[0].color
            for y in range(height):
                for x in range(width):
                    grid[y][x] = color
            return grid
        
        # For each pixel, project onto gradient line
        for y in range(height):
            for x in range(width):
                # Vector from start to pixel
                px = x - start_x
                py = y - start_y
                
                # Project onto gradient vector
                dot = px * dx + py * dy
                t = dot / length_sq
                
                # Get color at this position
                color = gradient.get_color_at(t)
                grid[y][x] = color
        
        return grid
    
    @staticmethod
    def render_radial(
        gradient: Gradient,
        width: int,
        height: int,
        center_x: float,
        center_y: float,
        radius: float
    ) -> List[List[RGB]]:
        """
        Render a radial gradient to a 2D pixel grid.
        
        Args:
            gradient: Gradient definition
            width: Grid width
            height: Grid height
            center_x: Gradient center X coordinate
            center_y: Gradient center Y coordinate
            radius: Gradient radius
            
        Returns:
            2D grid of RGB colors
        """
        grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        
        if radius <= 0:
            # Degenerate case: fill with start color
            color = gradient.stops[0].color
            for y in range(height):
                for x in range(width):
                    grid[y][x] = color
            return grid
        
        # For each pixel, calculate distance from center
        for y in range(height):
            for x in range(width):
                # Distance from center
                dx = x - center_x
                dy = y - center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Normalize to 0.0-1.0
                t = min(distance / radius, 1.0)
                
                # Get color at this position
                color = gradient.get_color_at(t)
                grid[y][x] = color
        
        return grid


# Preset gradients for common use cases
PRESET_GRADIENTS = {
    "rainbow": Gradient(
        type=GradientType.LINEAR,
        stops=[
            GradientStop(0.0, (255, 0, 0)),      # Red
            GradientStop(0.17, (255, 127, 0)),   # Orange
            GradientStop(0.33, (255, 255, 0)),   # Yellow
            GradientStop(0.5, (0, 255, 0)),      # Green
            GradientStop(0.67, (0, 0, 255)),     # Blue
            GradientStop(0.83, (75, 0, 130)),    # Indigo
            GradientStop(1.0, (148, 0, 211)),    # Violet
        ]
    ),
    "fire": Gradient(
        type=GradientType.RADIAL,
        stops=[
            GradientStop(0.0, (255, 255, 255)),  # White (hot center)
            GradientStop(0.3, (255, 255, 0)),    # Yellow
            GradientStop(0.6, (255, 127, 0)),    # Orange
            GradientStop(0.85, (255, 0, 0)),     # Red
            GradientStop(1.0, (128, 0, 0)),      # Dark red
        ]
    ),
    "ice": Gradient(
        type=GradientType.LINEAR,
        stops=[
            GradientStop(0.0, (255, 255, 255)),  # White
            GradientStop(0.5, (173, 216, 230)),  # Light blue
            GradientStop(1.0, (0, 0, 139)),      # Dark blue
        ]
    ),
    "sunset": Gradient(
        type=GradientType.LINEAR,
        stops=[
            GradientStop(0.0, (255, 94, 77)),    # Coral
            GradientStop(0.5, (255, 165, 0)),    # Orange
            GradientStop(1.0, (255, 215, 0)),    # Gold
        ]
    ),
    "ocean": Gradient(
        type=GradientType.LINEAR,
        stops=[
            GradientStop(0.0, (0, 105, 148)),    # Deep blue
            GradientStop(0.5, (0, 191, 255)),    # Sky blue
            GradientStop(1.0, (127, 255, 212)),  # Aqua
        ]
    ),
}


def create_simple_gradient(color_start: RGB, color_end: RGB, gradient_type: GradientType = GradientType.LINEAR) -> Gradient:
    """
    Create a simple 2-stop gradient.
    
    Args:
        color_start: Starting color
        color_end: Ending color
        gradient_type: Linear or radial
        
    Returns:
        Gradient with 2 stops
    """
    return Gradient(
        type=gradient_type,
        stops=[
            GradientStop(0.0, color_start),
            GradientStop(1.0, color_end),
        ]
    )
