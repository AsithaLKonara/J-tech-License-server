"""
Layer Action - Per-layer automation actions that are evaluated at render time.

Each layer can have multiple automation actions that are applied during rendering,
allowing for non-destructive, time-based animations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LayerAction:
    """
    Represents an automation action attached to a layer track.
    
    Actions are evaluated at render time based on the current frame index.
    Only actions within the start_frame/end_frame range are applied.
    
    IMPORTANT: Automation is stateless and frame-index driven. Actions are applied
    in order, and the order matters for combined transformations (e.g., rotate then
    scroll produces different results than scroll then rotate).
    
    Attributes:
        type: Action type (e.g., "scroll", "rotate", "mirror", "wipe", etc.)
        start_frame: Frame index where action starts (inclusive)
        end_frame: Frame index where action ends (inclusive)
        params: Action-specific parameters (e.g., {"direction": "right", "offset": 1})
        finalized: If True, action has been baked into frames and should be skipped
        name: Optional human-readable name for the action
        order: Order of execution (lower values applied first). Defaults to 0.
               Actions with same order are applied in list order.
    """
    type: str
    start_frame: int
    end_frame: Optional[int] = None
    params: Dict[str, Any] = None
    finalized: bool = False
    name: Optional[str] = None
    order: int = 0
    
    def __post_init__(self):
        """Validate action parameters."""
        if self.start_frame < 0:
            raise ValueError(f"start_frame must be >= 0, got {self.start_frame}")
        if self.end_frame is not None and self.end_frame < self.start_frame:
            raise ValueError(f"end_frame ({self.end_frame}) must be >= start_frame ({self.start_frame})")
        if self.params is None:
            self.params = {}
    
    @property
    def is_time_based(self) -> bool:
        """
        Check if this action type is time-based (progressive animation) or static.
        
        Time-based actions: scroll, rotate, wipe, reveal, bounce, radial, colour_cycle
        Static actions: mirror, flip, invert (same result every frame, no frame_index dependency)
        
        Returns:
            True if action produces different results based on frame_index/step, False otherwise
        """
        time_based_types = {
            "scroll", "rotate", "wipe", "reveal", "bounce", "radial", "colour_cycle"
        }
        return self.type.lower() in time_based_types
    
    def is_active_at_frame(self, frame_index: int) -> bool:
        """Check if this action should be applied at the given frame index."""
        if self.finalized:
            return False
        if frame_index < self.start_frame:
            return False
        if self.end_frame is not None and frame_index > self.end_frame:
            return False
        return True
    
    def get_step(self, frame_index: int) -> Optional[int]:
        """
        Get the step number for this action at the given frame.
        
        Returns the number of steps (frames) since the action started.
        Used for progressive transformations (e.g., scroll by 1 pixel per frame).
        Returns None if the action is not active at this frame.
        """
        if not self.is_active_at_frame(frame_index):
            return None
        return frame_index - self.start_frame


def get_action_step(action: LayerAction, frame_index: int) -> Optional[int]:
    """
    Get the local step number for an action at a given frame (LMS-style).
    
    This computes frame-relative step: frame_index - action.start_frame.
    Returns None if the action is not active at this frame.
    
    Args:
        action: LayerAction to compute step for
        frame_index: Current frame index
        
    Returns:
        Local step number (0-based) or None if action is not active
    """
    # Check if action is finalized (should be skipped)
    if action.finalized:
        return None
    
    if frame_index < action.start_frame:
        return None
    if action.end_frame is not None and frame_index > action.end_frame:
        return None
    return frame_index - action.start_frame

