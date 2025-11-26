"""
Frame-related domain events.

These events are published when frame-related operations occur.
"""

from core.events.base import DomainEvent
from core.pattern import Frame, Pattern
from typing import Optional


class FrameAddedEvent(DomainEvent):
    """Event published when a frame is added to a pattern."""
    
    def __init__(self, pattern: Pattern, frame: Frame, frame_index: int, source: Optional[str] = None):
        """
        Initialize frame added event.
        
        Args:
            pattern: The pattern containing the frame
            frame: The added frame
            frame_index: Index where the frame was added
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.frame = frame
        self.frame_index = frame_index


class FrameDeletedEvent(DomainEvent):
    """Event published when a frame is deleted from a pattern."""
    
    def __init__(self, pattern: Pattern, frame_index: int, deleted_frame: Frame, source: Optional[str] = None):
        """
        Initialize frame deleted event.
        
        Args:
            pattern: The pattern from which the frame was deleted
            frame_index: Index where the frame was deleted
            deleted_frame: The deleted frame
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.frame_index = frame_index
        self.deleted_frame = deleted_frame


class FrameDuplicatedEvent(DomainEvent):
    """Event published when a frame is duplicated."""
    
    def __init__(self, pattern: Pattern, original_index: int, duplicate_index: int, source: Optional[str] = None):
        """
        Initialize frame duplicated event.
        
        Args:
            pattern: The pattern containing the frames
            original_index: Index of the original frame
            duplicate_index: Index of the duplicated frame
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.original_index = original_index
        self.duplicate_index = duplicate_index


class FrameMovedEvent(DomainEvent):
    """Event published when a frame is moved/reordered."""
    
    def __init__(self, pattern: Pattern, from_index: int, to_index: int, source: Optional[str] = None):
        """
        Initialize frame moved event.
        
        Args:
            pattern: The pattern containing the frame
            from_index: Original index of the frame
            to_index: New index of the frame
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.from_index = from_index
        self.to_index = to_index


class FrameSelectedEvent(DomainEvent):
    """Event published when a frame is selected."""
    
    def __init__(self, pattern: Pattern, frame_index: int, source: Optional[str] = None):
        """
        Initialize frame selected event.
        
        Args:
            pattern: The pattern containing the frame
            frame_index: Index of the selected frame
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.frame_index = frame_index


class FrameDurationChangedEvent(DomainEvent):
    """Event published when a frame's duration is changed."""
    
    def __init__(self, pattern: Pattern, frame_index: int, old_duration: int, new_duration: int, source: Optional[str] = None):
        """
        Initialize frame duration changed event.
        
        Args:
            pattern: The pattern containing the frame
            frame_index: Index of the frame
            old_duration: Previous duration in milliseconds
            new_duration: New duration in milliseconds
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.frame_index = frame_index
        self.old_duration = old_duration
        self.new_duration = new_duration

