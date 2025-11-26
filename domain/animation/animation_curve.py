"""
Animation Curves - Easing functions for smooth animations.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Callable


class CurveType(Enum):
    """Animation curve types."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    BOUNCE = "bounce"
    ELASTIC = "elastic"


class AnimationCurve:
    """Animation curve/easing function."""
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation."""
        return t
    
    @staticmethod
    def ease_in(t: float) -> float:
        """Ease in (slow start)."""
        return t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        """Ease out (slow end)."""
        return t * (2 - t)
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Ease in and out."""
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease in."""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease out."""
        return t * (2 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease in and out."""
        if t < 0.5:
            return 2 * t * t
        return -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease in."""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease out."""
        return (t - 1) * (t - 1) * (t - 1) + 1
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease in and out."""
        if t < 0.5:
            return 4 * t * t * t
        return (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
    
    @staticmethod
    def bounce(t: float) -> float:
        """Bounce easing."""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375
    
    @staticmethod
    def elastic(t: float) -> float:
        """Elastic easing."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        p = 0.3
        s = p / 4
        return math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
    
    @classmethod
    def get_curve_function(cls, curve_type: str) -> Callable[[float], float]:
        """Get curve function by name."""
        curve_map = {
            CurveType.LINEAR.value: cls.linear,
            CurveType.EASE_IN.value: cls.ease_in,
            CurveType.EASE_OUT.value: cls.ease_out,
            CurveType.EASE_IN_OUT.value: cls.ease_in_out,
            CurveType.EASE_IN_QUAD.value: cls.ease_in_quad,
            CurveType.EASE_OUT_QUAD.value: cls.ease_out_quad,
            CurveType.EASE_IN_OUT_QUAD.value: cls.ease_in_out_quad,
            CurveType.EASE_IN_CUBIC.value: cls.ease_in_cubic,
            CurveType.EASE_OUT_CUBIC.value: cls.ease_out_cubic,
            CurveType.EASE_IN_OUT_CUBIC.value: cls.ease_in_out_cubic,
            CurveType.BOUNCE.value: cls.bounce,
            CurveType.ELASTIC.value: cls.elastic,
        }
        return curve_map.get(curve_type, cls.linear)
    
    @classmethod
    def apply_curve(cls, t: float, curve_type: str) -> float:
        """Apply curve to normalized time (0.0 to 1.0)."""
        curve_func = cls.get_curve_function(curve_type)
        return curve_func(max(0.0, min(1.0, t)))

