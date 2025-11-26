"""
Keyframe - Represents a keyframe in an animation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from enum import Enum

RGB = Tuple[int, int, int]


class KeyframeType(Enum):
    """Type of keyframe."""
    POSITION = "position"
    COLOR = "color"
    SCALE = "scale"
    ROTATION = "rotation"
    OPACITY = "opacity"
    CUSTOM = "custom"


@dataclass
class Keyframe:
    """
    A keyframe in an animation timeline.
    
    Keyframes define specific values at specific times, and the animation
    system interpolates between keyframes to create smooth motion.
    """
    frame_index: int  # Frame number (0-based)
    keyframe_type: KeyframeType
    value: Any  # Value at this keyframe (type depends on keyframe_type)
    curve_type: str = "linear"  # Interpolation curve: linear, ease_in, ease_out, ease_in_out, bezier
    tension: float = 0.0  # Tension for bezier curves (-1.0 to 1.0)
    metadata: Dict[str, Any] = None  # Additional metadata
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize keyframe to dictionary."""
        return {
            "frame_index": self.frame_index,
            "keyframe_type": self.keyframe_type.value,
            "value": self.value,
            "curve_type": self.curve_type,
            "tension": self.tension,
            "metadata": self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Keyframe":
        """Deserialize keyframe from dictionary."""
        return Keyframe(
            frame_index=data["frame_index"],
            keyframe_type=KeyframeType(data["keyframe_type"]),
            value=data["value"],
            curve_type=data.get("curve_type", "linear"),
            tension=data.get("tension", 0.0),
            metadata=data.get("metadata", {})
        )

