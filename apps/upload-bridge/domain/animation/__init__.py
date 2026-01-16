"""
Animation System - Keyframe-based animation with tweening and curves.
"""

from .keyframe import Keyframe, KeyframeType
from .animation_curve import AnimationCurve, CurveType
from .keyframe_animation import KeyframeAnimation
from .tween import Tween, TweenType, interpolate

__all__ = [
    "Keyframe",
    "KeyframeType",
    "AnimationCurve",
    "CurveType",
    "KeyframeAnimation",
    "Tween",
    "TweenType",
    "interpolate",
]

