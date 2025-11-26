"""
Keyframe Animation - Animation system using keyframes and tweening.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field

from core.pattern import Pattern, Frame
from .keyframe import Keyframe, KeyframeType
from .animation_curve import AnimationCurve
from .tween import Tween, TweenType, interpolate_rgb

RGB = Tuple[int, int, int]


@dataclass
class MotionPath:
    """Defines a motion path for animated objects."""
    keyframes: List[Tuple[int, int]]  # List of (frame_index, x, y) positions
    loop: bool = False
    closed: bool = False  # If True, path loops back to start
    
    def get_position_at_frame(self, frame_index: int, total_frames: int) -> Optional[Tuple[int, int]]:
        """Get position at specific frame index."""
        if not self.keyframes:
            return None
        
        if self.loop:
            frame_index = frame_index % total_frames
        
        # Find surrounding keyframes
        for i, (kf_frame, x, y) in enumerate(self.keyframes):
            if kf_frame >= frame_index:
                if i == 0:
                    return (x, y)
                # Interpolate between previous and current
                prev_frame, prev_x, prev_y = self.keyframes[i - 1]
                if kf_frame == prev_frame:
                    return (x, y)
                t = (frame_index - prev_frame) / (kf_frame - prev_frame)
                interp_x = int(prev_x + (x - prev_x) * t)
                interp_y = int(prev_y + (y - prev_y) * t)
                return (interp_x, interp_y)
        
        # Return last keyframe
        _, x, y = self.keyframes[-1]
        return (x, y)


@dataclass
class KeyframeAnimation:
    """
    Keyframe-based animation system.
    
    Manages keyframes for various properties (position, color, scale, etc.)
    and generates interpolated frames between keyframes.
    """
    keyframes: List[Keyframe] = field(default_factory=list)
    motion_paths: Dict[str, MotionPath] = field(default_factory=dict)
    default_curve: str = "linear"
    
    def add_keyframe(self, keyframe: Keyframe) -> None:
        """Add a keyframe to the animation."""
        self.keyframes.append(keyframe)
        self.keyframes.sort(key=lambda kf: kf.frame_index)
    
    def remove_keyframe(self, frame_index: int, keyframe_type: KeyframeType) -> bool:
        """Remove a keyframe at the given frame index and type."""
        original_count = len(self.keyframes)
        self.keyframes = [
            kf for kf in self.keyframes
            if not (kf.frame_index == frame_index and kf.keyframe_type == keyframe_type)
        ]
        return len(self.keyframes) < original_count
    
    def get_keyframes(self, keyframe_type: KeyframeType) -> List[Keyframe]:
        """Get all keyframes of a specific type."""
        return [kf for kf in self.keyframes if kf.keyframe_type == keyframe_type]
    
    def get_keyframe_at(self, frame_index: int, keyframe_type: KeyframeType) -> Optional[Keyframe]:
        """Get keyframe at specific frame index and type."""
        for kf in self.keyframes:
            if kf.frame_index == frame_index and kf.keyframe_type == keyframe_type:
                return kf
        return None
    
    def get_value_at_frame(
        self,
        frame_index: int,
        keyframe_type: KeyframeType,
        default_value: Any = None
    ) -> Any:
        """
        Get interpolated value at a specific frame index.
        
        Args:
            frame_index: Frame index to get value for
            keyframe_type: Type of keyframe
            default_value: Default value if no keyframes exist
        
        Returns:
            Interpolated value
        """
        type_keyframes = self.get_keyframes(keyframe_type)
        if not type_keyframes:
            return default_value
        
        # Find surrounding keyframes
        prev_kf = None
        next_kf = None
        
        for kf in type_keyframes:
            if kf.frame_index <= frame_index:
                prev_kf = kf
            if kf.frame_index >= frame_index and next_kf is None:
                next_kf = kf
        
        # Exact match
        if prev_kf and prev_kf.frame_index == frame_index:
            return prev_kf.value
        
        # Before first keyframe
        if prev_kf is None:
            return type_keyframes[0].value
        
        # After last keyframe
        if next_kf is None:
            return type_keyframes[-1].value
        
        # Interpolate between keyframes
        if prev_kf.frame_index == next_kf.frame_index:
            return prev_kf.value
        
        # Calculate interpolation factor
        frame_range = next_kf.frame_index - prev_kf.frame_index
        t = (frame_index - prev_kf.frame_index) / frame_range if frame_range > 0 else 0.0
        
        # Apply curve
        curve_type = prev_kf.curve_type or self.default_curve
        t_curved = AnimationCurve.apply_curve(t, curve_type)
        
        # Interpolate value
        if keyframe_type == KeyframeType.COLOR:
            return interpolate_rgb(prev_kf.value, next_kf.value, t_curved)
        elif isinstance(prev_kf.value, (int, float)) and isinstance(next_kf.value, (int, float)):
            return prev_kf.value + (next_kf.value - prev_kf.value) * t_curved
        elif isinstance(prev_kf.value, tuple) and isinstance(next_kf.value, tuple):
            if len(prev_kf.value) == len(next_kf.value):
                return tuple(
                    prev_kf.value[i] + (next_kf.value[i] - prev_kf.value[i]) * t_curved
                    for i in range(len(prev_kf.value))
                )
        
        # Default: return previous value
        return prev_kf.value
    
    def generate_frames(
        self,
        base_pattern: Pattern,
        start_frame: int = 0,
        end_frame: Optional[int] = None
    ) -> List[Frame]:
        """
        Generate interpolated frames from keyframes.
        
        Args:
            base_pattern: Base pattern to animate
            start_frame: Starting frame index
            end_frame: Ending frame index (None = use pattern frame count)
        
        Returns:
            List of generated frames
        """
        if end_frame is None:
            end_frame = base_pattern.frame_count
        
        generated_frames: List[Frame] = []
        
        for frame_idx in range(start_frame, end_frame):
            base_frame = base_pattern.frames[frame_idx % len(base_pattern.frames)]
            
            # Get animated values
            color_override = self.get_value_at_frame(frame_idx, KeyframeType.COLOR)
            position = self.get_value_at_frame(frame_idx, KeyframeType.POSITION)
            
            # Create new frame with modifications
            new_pixels = list(base_frame.pixels)
            
            # Apply color override if specified
            if color_override:
                new_pixels = [color_override] * len(new_pixels)
            
            # Apply position/motion path if specified
            # (This would require more complex pixel manipulation)
            
            generated_frames.append(Frame(
                pixels=new_pixels,
                duration_ms=base_frame.duration_ms
            ))
        
        return generated_frames
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize animation to dictionary."""
        return {
            "keyframes": [kf.to_dict() for kf in self.keyframes],
            "motion_paths": {
                name: {
                    "keyframes": path.keyframes,
                    "loop": path.loop,
                    "closed": path.closed
                }
                for name, path in self.motion_paths.items()
            },
            "default_curve": self.default_curve
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "KeyframeAnimation":
        """Deserialize animation from dictionary."""
        animation = KeyframeAnimation(
            default_curve=data.get("default_curve", "linear")
        )
        
        for kf_data in data.get("keyframes", []):
            animation.add_keyframe(Keyframe.from_dict(kf_data))
        
        for name, path_data in data.get("motion_paths", {}).items():
            animation.motion_paths[name] = MotionPath(
                keyframes=path_data["keyframes"],
                loop=path_data.get("loop", False),
                closed=path_data.get("closed", False)
            )
        
        return animation

