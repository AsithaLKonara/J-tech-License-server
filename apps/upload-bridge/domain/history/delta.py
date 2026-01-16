"""
State Delta Compression - Store only changes instead of full snapshots

Provides delta compression for history management to optimize memory usage.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from core.pattern import Pattern, Frame


@dataclass
class StateDelta:
    """
    Represents changes between two pattern states.
    
    Stores only the differences to save memory.
    """
    frame_index: int
    changed_pixels: List[tuple[int, int, tuple[int, int, int]]]  # (x, y, color)
    duration_changed: bool = False
    duration_ms: Optional[int] = None
    metadata_changed: bool = False
    metadata_fields: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert delta to dictionary"""
        return {
            "frame_index": self.frame_index,
            "changed_pixels": self.changed_pixels,
            "duration_changed": self.duration_changed,
            "duration_ms": self.duration_ms,
            "metadata_changed": self.metadata_changed,
            "metadata_fields": self.metadata_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateDelta':
        """Create delta from dictionary"""
        return cls(
            frame_index=data["frame_index"],
            changed_pixels=data.get("changed_pixels", []),
            duration_changed=data.get("duration_changed", False),
            duration_ms=data.get("duration_ms"),
            metadata_changed=data.get("metadata_changed", False),
            metadata_fields=data.get("metadata_fields"),
        )


def compute_delta(
    before: Pattern,
    after: Pattern,
    frame_index: int
) -> Optional[StateDelta]:
    """
    Compute delta between two pattern states.
    
    Args:
        before: Pattern state before change
        after: Pattern state after change
        frame_index: Frame index that changed
        
    Returns:
        StateDelta if changes detected, None otherwise
    """
    if frame_index >= len(before.frames) or frame_index >= len(after.frames):
        return None
    
    before_frame = before.frames[frame_index]
    after_frame = after.frames[frame_index]
    
    # Find changed pixels
    changed_pixels = []
    if len(before_frame.pixels) == len(after_frame.pixels):
        width = after.metadata.width
        height = after.metadata.height
        
        for i, (before_pixel, after_pixel) in enumerate(zip(before_frame.pixels, after_frame.pixels)):
            if before_pixel != after_pixel:
                x = i % width
                y = i // width
                changed_pixels.append((x, y, after_pixel))
    
    # Check duration change
    duration_changed = before_frame.duration_ms != after_frame.duration_ms
    duration_ms = after_frame.duration_ms if duration_changed else None
    
    # Check metadata changes (simplified - full implementation would track specific fields)
    metadata_changed = False
    metadata_fields = None
    
    if changed_pixels or duration_changed or metadata_changed:
        return StateDelta(
            frame_index=frame_index,
            changed_pixels=changed_pixels,
            duration_changed=duration_changed,
            duration_ms=duration_ms,
            metadata_changed=metadata_changed,
            metadata_fields=metadata_fields,
        )
    
    return None


def apply_delta(pattern: Pattern, delta: StateDelta) -> Pattern:
    """
    Apply delta to pattern state.
    
    Args:
        pattern: Pattern to apply delta to
        delta: StateDelta to apply
        
    Returns:
        New Pattern with delta applied
    """
    from copy import deepcopy
    
    # Create copy
    new_pattern = deepcopy(pattern)
    
    # Apply frame changes
    if delta.frame_index < len(new_pattern.frames):
        frame = new_pattern.frames[delta.frame_index]
        
        # Apply pixel changes
        width = new_pattern.metadata.width
        for x, y, color in delta.changed_pixels:
            idx = y * width + x
            if idx < len(frame.pixels):
                frame.pixels[idx] = color
        
        # Apply duration change
        if delta.duration_changed and delta.duration_ms is not None:
            frame.duration_ms = delta.duration_ms
    
    # Apply metadata changes
    if delta.metadata_changed and delta.metadata_fields:
        for key, value in delta.metadata_fields.items():
            if hasattr(new_pattern.metadata, key):
                setattr(new_pattern.metadata, key, value)
    
    return new_pattern

