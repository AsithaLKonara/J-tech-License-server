"""
Animation Migration - Convert old LayerAnimation to new LayerAction system.

This module handles migration from the old LayerAnimation architecture
to the new per-layer LayerAction automation system.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from domain.layer_animation import LayerAnimation, AnimationType
from domain.automation.layer_action import LayerAction


def migrate_layer_animation_to_actions(
    animation: LayerAnimation,
    total_frames: int
) -> List[LayerAction]:
    """
    Convert a LayerAnimation object to a list of LayerAction objects.
    
    Args:
        animation: LayerAnimation object to migrate
        total_frames: Total number of frames in the pattern
        
    Returns:
        List of LayerAction objects representing the animation
    """
    if not animation or animation.animation_type == AnimationType.NONE:
        return []
    
    actions: List[LayerAction] = []
    
    # Determine frame range
    start_frame = animation.start_frame
    end_frame = animation.end_frame if animation.end_frame is not None else total_frames - 1
    end_frame = min(end_frame, total_frames - 1)
    
    if start_frame > end_frame or start_frame < 0:
        return []
    
    # Convert based on animation type
    if animation.animation_type == AnimationType.SCROLL:
        # Extract scroll direction from keyframes
        direction = "right"  # default
        if animation.keyframes:
            # Check for offset_x or offset_y in keyframes
            first_kf = animation.keyframes[0]
            last_kf = animation.keyframes[-1]
            
            if hasattr(first_kf, 'offset_x') and hasattr(last_kf, 'offset_x'):
                if last_kf.offset_x > first_kf.offset_x:
                    direction = "right"
                elif last_kf.offset_x < first_kf.offset_x:
                    direction = "left"
            elif hasattr(first_kf, 'offset_y') and hasattr(last_kf, 'offset_y'):
                if last_kf.offset_y > first_kf.offset_y:
                    direction = "down"
                elif last_kf.offset_y < first_kf.offset_y:
                    direction = "up"
        
        # Create scroll action
        action = LayerAction(
            type="scroll",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "direction": direction,
                "speed": animation.speed,
                "loop": animation.loop,
            },
            finalized=False,
            name=f"Scroll {direction}"
        )
        actions.append(action)
    
    elif animation.animation_type == AnimationType.ROTATE:
        # Extract rotation from keyframes
        rotation_amount = 90  # default
        if animation.keyframes:
            first_kf = animation.keyframes[0]
            last_kf = animation.keyframes[-1]
            if hasattr(first_kf, 'rotation') and hasattr(last_kf, 'rotation'):
                rotation_amount = int(last_kf.rotation - first_kf.rotation)
        
        action = LayerAction(
            type="rotate",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "degrees": rotation_amount,
                "speed": animation.speed,
                "loop": animation.loop,
            },
            finalized=False,
            name=f"Rotate {rotation_amount}°"
        )
        actions.append(action)
    
    elif animation.animation_type == AnimationType.FADE:
        # Fade animations are handled via opacity keyframes
        # For now, we'll create a simple fade action
        fade_in = True
        if animation.keyframes:
            first_kf = animation.keyframes[0]
            last_kf = animation.keyframes[-1]
            if hasattr(first_kf, 'opacity') and hasattr(last_kf, 'opacity'):
                fade_in = first_kf.opacity < last_kf.opacity
        
        action = LayerAction(
            type="fade",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "fade_in": fade_in,
                "speed": animation.speed,
            },
            finalized=False,
            name="Fade In" if fade_in else "Fade Out"
        )
        actions.append(action)
    
    elif animation.animation_type == AnimationType.PULSE:
        # Pulse animation - create a repeating fade action
        min_opacity = 0.5
        max_opacity = 1.0
        if animation.keyframes:
            opacities = [kf.opacity for kf in animation.keyframes if hasattr(kf, 'opacity') and kf.opacity is not None]
            if opacities:
                min_opacity = min(opacities)
                max_opacity = max(opacities)
        
        action = LayerAction(
            type="pulse",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "min_opacity": min_opacity,
                "max_opacity": max_opacity,
                "speed": animation.speed,
                "loop": animation.loop,
            },
            finalized=False,
            name="Pulse"
        )
        actions.append(action)
    
    elif animation.animation_type == AnimationType.SCALE:
        # Scale animation
        scale_start = 1.0
        scale_end = 1.0
        if animation.keyframes:
            first_kf = animation.keyframes[0]
            last_kf = animation.keyframes[-1]
            if hasattr(first_kf, 'scale') and hasattr(last_kf, 'scale'):
                scale_start = first_kf.scale
                scale_end = last_kf.scale
        
        action = LayerAction(
            type="scale",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "scale_start": scale_start,
                "scale_end": scale_end,
                "speed": animation.speed,
                "loop": animation.loop,
            },
            finalized=False,
            name="Scale"
        )
        actions.append(action)
    
    elif animation.animation_type == AnimationType.CUSTOM:
        # Custom animations - try to preserve as much as possible
        action = LayerAction(
            type="custom",
            start_frame=start_frame,
            end_frame=end_frame,
            params={
                "speed": animation.speed,
                "direction": animation.direction,
                "loop": animation.loop,
                "keyframes": [
                    {
                        "frame_index": kf.frame_index,
                        "opacity": getattr(kf, 'opacity', None),
                        "offset_x": getattr(kf, 'offset_x', None),
                        "offset_y": getattr(kf, 'offset_y', None),
                        "rotation": getattr(kf, 'rotation', None),
                        "scale": getattr(kf, 'scale', None),
                    }
                    for kf in animation.keyframes
                ]
            },
            finalized=False,
            name="Custom Animation"
        )
        actions.append(action)
    
    return actions


def migrate_animation_manager_to_layer_automation(
    animation_manager,
    layer_manager,
    total_frames: int
) -> None:
    """
    Migrate all animations from LayerAnimationManager to layer automation.
    
    Args:
        animation_manager: LayerAnimationManager instance with old animations
        layer_manager: LayerManager instance to migrate to
        total_frames: Total number of frames in the pattern
    """
    if not hasattr(animation_manager, '_animations'):
        return
    
    for layer_index, animation in animation_manager._animations.items():
        if animation and animation.animation_type != AnimationType.NONE:
            # Convert animation to actions
            actions = migrate_layer_animation_to_actions(animation, total_frames)
            
            # Add actions to layer
            if actions and 0 <= layer_index < len(layer_manager._layer_tracks):
                track = layer_manager._layer_tracks[layer_index]
                for action in actions:
                    track.add_automation(action)
    
    # Clear old animations (optional - keep for backward compat if needed)
    # animation_manager._animations.clear()
