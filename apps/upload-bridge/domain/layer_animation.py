"""
Layer Animation System - Enable independent animations per layer.

This module provides animation capabilities for layer tracks, allowing
different layers to animate independently with different properties,
speeds, and effects.
"""

from __future__ import annotations
from typing import Optional, Dict, List, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from domain.layers import LayerTrack

Color = Tuple[int, int, int]


class AnimationType(Enum):
    """Types of layer animations."""
    NONE = "none"
    SCROLL = "scroll"  # Scroll layer content
    FADE = "fade"  # Fade in/out
    PULSE = "pulse"  # Pulse opacity
    ROTATE = "rotate"  # Rotate layer content
    SCALE = "scale"  # Scale layer content
    CUSTOM = "custom"  # Custom animation function


@dataclass
class AnimationKeyframe:
    """Keyframe for layer animation properties."""
    frame_index: int
    opacity: Optional[float] = None
    visible: Optional[bool] = None
    offset_x: float = 0.0  # Horizontal offset for scroll/position
    offset_y: float = 0.0  # Vertical offset for scroll/position
    rotation: float = 0.0  # Rotation angle in degrees
    scale: float = 1.0  # Scale factor


@dataclass
class LayerAnimation:
    """
    Animation configuration for a layer track.
    
    Each layer can have independent animation properties that change
    over time, allowing for complex multi-layer animations.
    """
    animation_type: AnimationType = AnimationType.NONE
    speed: float = 1.0  # Animation speed multiplier
    direction: str = "forward"  # "forward", "backward", "pingpong"
    loop: bool = True  # Whether animation loops
    keyframes: List[AnimationKeyframe] = field(default_factory=list)
    start_frame: int = 0  # Animation start frame
    end_frame: Optional[int] = None  # Animation end frame (None = end of pattern)
    
    def get_property_at_frame(
        self,
        frame_index: int,
        total_frames: int,
        property_name: str
    ) -> Optional[float]:
        """
        Get animated property value at a specific frame.
        
        Args:
            frame_index: Current frame index (absolute pattern frame number)
            total_frames: Total number of frames in pattern
            property_name: Property to get ("opacity", "offset_x", "offset_y", "rotation", "scale")
            
        Returns:
            Property value or None if not animated
            
        Note:
            Keyframe frame_index values are normalized (0 = start of animation, 100 = end of animation),
            not absolute pattern frame numbers. Interpolation is based on the animation's frame range
            (start_frame to end_frame), which is then mapped to normalized keyframe indices.
        """
        if not self.keyframes:
            return None
        
        # Normalize frame index based on animation range
        anim_start = self.start_frame
        anim_end = self.end_frame if self.end_frame is not None else total_frames - 1
        
        if frame_index < anim_start or frame_index > anim_end:
            return None
        
        # Find surrounding keyframes
        # Convert absolute frame to local frame within animation range
        local_frame = frame_index - anim_start
        anim_length = anim_end - anim_start + 1
        
        if anim_length <= 0:
            return None
        
        # Apply speed (in animation frame space: 0 to anim_length-1)
        speed_frame = int(local_frame * self.speed)
        if self.loop:
            speed_frame = speed_frame % anim_length
        else:
            # Clamp for non-looping animations (prevent exceeding animation range)
            speed_frame = min(speed_frame, anim_length - 1)
            speed_frame = max(0, speed_frame)  # Also ensure non-negative
        
        # Map to normalized keyframe range (0-100)
        # Keyframes use normalized indices: 0 = start, 100 = end of animation
        normalized_speed_frame = int((speed_frame / anim_length) * 100) if anim_length > 0 else 0
        normalized_speed_frame = max(0, min(100, normalized_speed_frame))  # Clamp to 0-100
        
        # Find surrounding keyframes (keyframes use normalized indices 0-100)
        before_keyframe = None
        after_keyframe = None
        
        for kf in self.keyframes:
            # Keyframe.frame_index is normalized (0-100), compare with normalized_speed_frame
            if kf.frame_index <= normalized_speed_frame:
                before_keyframe = kf
            if kf.frame_index >= normalized_speed_frame and after_keyframe is None:
                after_keyframe = kf
        
        # If no keyframes found, return None
        if before_keyframe is None and after_keyframe is None:
            return None
        
        # If exact match, return keyframe value
        if before_keyframe and before_keyframe.frame_index == normalized_speed_frame:
            return getattr(before_keyframe, property_name, None)
        
        if after_keyframe and after_keyframe.frame_index == normalized_speed_frame:
            return getattr(after_keyframe, property_name, None)
        
        # Interpolate between keyframes (using normalized indices 0-100)
        if before_keyframe and after_keyframe:
            t = (normalized_speed_frame - before_keyframe.frame_index) / (
                after_keyframe.frame_index - before_keyframe.frame_index
            ) if after_keyframe.frame_index != before_keyframe.frame_index else 0.0
            
            before_val = getattr(before_keyframe, property_name, None)
            after_val = getattr(after_keyframe, property_name, None)
            
            if before_val is not None and after_val is not None:
                # Linear interpolation
                return before_val + (after_val - before_val) * t
            elif before_val is not None:
                return before_val
            elif after_val is not None:
                return after_val
        
        # Return single keyframe value
        if before_keyframe:
            return getattr(before_keyframe, property_name, None)
        if after_keyframe:
            return getattr(after_keyframe, property_name, None)
        
        return None


class LayerAnimationManager:
    """
    Manages animations for layer tracks.
    
    Each layer track can have independent animation properties,
    allowing for complex multi-layer animations.
    
    Note: Currently supports one animation per layer track. Setting a new
    animation replaces any existing animation for that layer.
    """
    
    def __init__(self):
        # Store animations per layer track: {layer_track_id: LayerAnimation}
        self._animations: Dict[str, LayerAnimation] = {}
    
    def set_animation(
        self,
        layer_track_id: str,
        animation: LayerAnimation
    ) -> None:
        """Set animation for a layer track by its unique ID."""
        self._animations[str(layer_track_id)] = animation
    
    def get_animation(self, layer_track_id: str) -> Optional[LayerAnimation]:
        """Get animation for a layer track by its unique ID."""
        return self._animations.get(str(layer_track_id))
    
    def remove_animation(self, layer_track_id: str) -> None:
        """Remove animation from a layer track by its unique ID."""
        tid = str(layer_track_id)
        if tid in self._animations:
            del self._animations[tid]
    
    def apply_animation_to_frame(
        self,
        layer_track: LayerTrack,
        layer_track_index: int,
        frame_index: int,
        total_frames: int
    ) -> None:
        """
        Apply animation properties to a layer track at a specific frame.
        
        This modifies the layer track's frame data based on animation keyframes.
        """
        animation = self.get_animation(layer_track_index)
        if not animation or animation.animation_type == AnimationType.NONE:
            return
        
        # Get animated properties
        opacity = animation.get_property_at_frame(frame_index, total_frames, "opacity")
        visible = animation.get_property_at_frame(frame_index, total_frames, "visible")
        
        # Apply to layer frame
        layer_frame = layer_track.get_frame(frame_index)
        if layer_frame:
            if opacity is not None:
                layer_frame.opacity = opacity
            if visible is not None:
                layer_frame.visible = visible
        
        # Apply animation type-specific transformations
        if animation.animation_type == AnimationType.SCROLL:
            # Scroll animation would transform pixel positions
            # This is a placeholder - actual implementation would need pixel transformation
            pass
        elif animation.animation_type == AnimationType.FADE:
            # Fade is handled via opacity keyframes
            pass
        elif animation.animation_type == AnimationType.PULSE:
            # Pulse is handled via opacity keyframes with sine wave
            pass


# Animation presets for common use cases
def create_scroll_animation(
    direction: str = "right",
    speed: float = 1.0,
    start_frame: int = 0,
    end_frame: Optional[int] = None
) -> LayerAnimation:
    """
    Create a scroll animation preset.
    
    Args:
        direction: "right", "left", "up", "down"
        speed: Animation speed multiplier
        start_frame: Frame where animation starts (absolute pattern frame number)
        end_frame: Frame where animation ends (None = end of pattern, absolute frame number)
    
    Returns:
        LayerAnimation configured for scrolling
        
    Note:
        Keyframes use normalized frame_index values (0 = start of animation, 100 = end of animation),
        not absolute pattern frame numbers. The animation system maps the actual frame range
        (start_frame to end_frame) to this normalized 0-100 space for interpolation.
    """
    keyframes = []
    
    # Create keyframes for scroll animation
    # Keyframe frame_index values are normalized: 0 = start, 100 = end of animation
    # These are NOT absolute pattern frame numbers
    if direction.lower() in ["right", "left"]:
        # Horizontal scroll
        offset_start = 0.0
        offset_end = 1.0 if direction.lower() == "right" else -1.0
        keyframes = [
            AnimationKeyframe(frame_index=0, offset_x=offset_start),
            AnimationKeyframe(frame_index=100, offset_x=offset_end),
        ]
    elif direction.lower() in ["up", "down"]:
        # Vertical scroll
        offset_start = 0.0
        offset_end = 1.0 if direction.lower() == "down" else -1.0
        keyframes = [
            AnimationKeyframe(frame_index=0, offset_y=offset_start),
            AnimationKeyframe(frame_index=100, offset_y=offset_end),
        ]
    
    return LayerAnimation(
        animation_type=AnimationType.SCROLL,
        speed=speed,
        direction="forward",
        loop=True,
        keyframes=keyframes,
        start_frame=start_frame,
        end_frame=end_frame
    )


def create_fade_animation(
    fade_in: bool = True,
    duration_frames: int = 10,
    start_frame: int = 0
) -> LayerAnimation:
    """
    Create a fade in/out animation preset.
    
    Note: Keyframes use normalized indices (0 = start, 100 = end), not absolute
    frame numbers. The duration_frames parameter determines the animation length
    in actual pattern frames, but keyframes are normalized to 0-100.
    """
    if fade_in:
        keyframes = [
            AnimationKeyframe(frame_index=0, opacity=0.0),   # Normalized: start
            AnimationKeyframe(frame_index=100, opacity=1.0), # Normalized: end
        ]
    else:
        keyframes = [
            AnimationKeyframe(frame_index=0, opacity=1.0),   # Normalized: start
            AnimationKeyframe(frame_index=100, opacity=0.0), # Normalized: end
        ]
    
    return LayerAnimation(
        animation_type=AnimationType.FADE,
        keyframes=keyframes,
        start_frame=start_frame,
        end_frame=start_frame + duration_frames
    )


def create_pulse_animation(
    min_opacity: float = 0.5,
    max_opacity: float = 1.0,
    period_frames: int = 20,
    start_frame: int = 0,
    end_frame: Optional[int] = None
) -> LayerAnimation:
    """
    Create a pulse animation preset.
    
    Note: Keyframes use normalized indices (0 = start, 50 = middle, 100 = end),
    not absolute frame numbers. The period_frames parameter determines the
    pulse period in actual pattern frames, but keyframes are normalized to 0-100.
    """
    keyframes = [
        AnimationKeyframe(frame_index=0, opacity=min_opacity),    # Normalized: start
        AnimationKeyframe(frame_index=50, opacity=max_opacity),     # Normalized: middle
        AnimationKeyframe(frame_index=100, opacity=min_opacity),   # Normalized: end
    ]
    
    return LayerAnimation(
        animation_type=AnimationType.PULSE,
        loop=True,
        keyframes=keyframes,
        start_frame=start_frame,
        end_frame=end_frame
    )
