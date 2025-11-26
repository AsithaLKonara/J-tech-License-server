"""
Tweening - Interpolation between values.
"""

from __future__ import annotations

from enum import Enum
from typing import Tuple, Any, List
import math

RGB = Tuple[int, int, int]


class TweenType(Enum):
    """Tweening interpolation types."""
    LINEAR = "linear"
    STEP = "step"  # No interpolation, use start value


def interpolate_rgb(start: RGB, end: RGB, t: float) -> RGB:
    """Interpolate between two RGB colors."""
    r = int(start[0] + (end[0] - start[0]) * t)
    g = int(start[1] + (end[1] - start[1]) * t)
    b = int(start[2] + (end[2] - start[2]) * t)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def interpolate_float(start: float, end: float, t: float) -> float:
    """Interpolate between two float values."""
    return start + (end - start) * t


def interpolate_int(start: int, end: int, t: float) -> int:
    """Interpolate between two integer values."""
    return int(start + (end - start) * t)


def interpolate_tuple(start: Tuple, end: Tuple, t: float) -> Tuple:
    """Interpolate between two tuples of same length."""
    if len(start) != len(end):
        raise ValueError("Tuples must have same length")
    
    if isinstance(start[0], (int, float)) and isinstance(end[0], (int, float)):
        if isinstance(start[0], int) and isinstance(end[0], int):
            return tuple(interpolate_int(s, e, t) for s, e in zip(start, end))
        else:
            return tuple(interpolate_float(float(s), float(e), t) for s, e in zip(start, end))
    
    return start  # Can't interpolate, return start


def interpolate(value_type: type, start: Any, end: Any, t: float) -> Any:
    """
    Generic interpolation function.
    
    Args:
        value_type: Type of value to interpolate
        start: Start value
        end: End value
        t: Interpolation factor (0.0 to 1.0)
    
    Returns:
        Interpolated value
    """
    t = max(0.0, min(1.0, t))
    
    if value_type == RGB or (isinstance(start, tuple) and len(start) == 3 and all(isinstance(x, int) for x in start)):
        return interpolate_rgb(start, end, t)
    elif value_type == float or isinstance(start, float):
        return interpolate_float(start, end, t)
    elif value_type == int or isinstance(start, int):
        return interpolate_int(start, end, t)
    elif isinstance(start, tuple):
        return interpolate_tuple(start, end, t)
    else:
        # Default: return start if t < 0.5, else end
        return start if t < 0.5 else end


class Tween:
    """Tweening helper class."""
    
    def __init__(self, tween_type: TweenType = TweenType.LINEAR):
        self.tween_type = tween_type
    
    def interpolate(self, start: Any, end: Any, t: float, value_type: type = None) -> Any:
        """
        Interpolate between start and end values.
        
        Args:
            start: Start value
            end: End value
            t: Interpolation factor (0.0 to 1.0)
            value_type: Optional type hint for interpolation
        
        Returns:
            Interpolated value
        """
        if self.tween_type == TweenType.STEP:
            return start if t < 1.0 else end
        
        if value_type:
            return interpolate(value_type, start, end, t)
        else:
            return interpolate(type(start), start, end, t)

