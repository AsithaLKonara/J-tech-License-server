"""
Frame Management Component.

Handles frame-level operations like add, delete, duplicate, move.
Extracted from DesignToolsTab to improve maintainability.
"""

from typing import Optional
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from core.pattern import Pattern, Frame
from domain.pattern_state import PatternState
from domain.frames import FrameManager


class FrameManagementComponent(QObject):
    """
    Component for frame management operations.
    
    This component handles:
    - Frame addition
    - Frame deletion
    - Frame duplication
    - Frame reordering
    - Frame selection
    - Frame duration management
    """
    
    # Signals
    frame_added = Signal(int)  # frame_index
    frame_deleted = Signal(int)  # deleted_index
    frame_duplicated = Signal(int, int)  # original_index, duplicate_index
    frame_moved = Signal(int, int)  # from_index, to_index
    frame_selected = Signal(int)  # frame_index
    frame_duration_changed = Signal(int, int, int)  # frame_index, old_duration, new_duration
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the frame management component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.pattern_state: Optional[PatternState] = None
        self.frame_manager: Optional[FrameManager] = None
    
    def set_pattern(self, pattern: Pattern) -> None:
        """
        Set the pattern for frame management.
        
        Args:
            pattern: Pattern to manage
        """
        self.pattern_state = PatternState(pattern)
        self.frame_manager = FrameManager(self.pattern_state)
        
        # Connect frame manager signals
        self.frame_manager.frame_index_changed.connect(self._on_frame_index_changed)
        self.frame_manager.frame_duration_changed.connect(self._on_frame_duration_changed)
    
    def add_frame(self, after_index: Optional[int] = None, duration_ms: int = 50) -> Optional[int]:
        """
        Add a new blank frame.
        
        Args:
            after_index: Index to add after (None = add at end)
            duration_ms: Frame duration in milliseconds
        
        Returns:
            Index of added frame or None if failed
        """
        if not self.frame_manager:
            return None
        
        try:
            if after_index is None:
                after_index = self.frame_manager.current_index()
            
            new_index = self.frame_manager.add_blank_after_current(duration_ms)
            self.frame_added.emit(new_index)
            return new_index
        except Exception:
            return None
    
    def delete_frame(self, frame_index: Optional[int] = None) -> bool:
        """
        Delete a frame.
        
        Args:
            frame_index: Index of frame to delete (None = current)
        
        Returns:
            True if deletion succeeded
        """
        if not self.frame_manager:
            return False
        
        try:
            if frame_index is not None:
                self.frame_manager.select(frame_index)
            
            deleted_index = self.frame_manager.current_index()
            self.frame_manager.delete()
            self.frame_deleted.emit(deleted_index)
            return True
        except Exception:
            return False
    
    def duplicate_frame(self, frame_index: Optional[int] = None) -> Optional[int]:
        """
        Duplicate a frame.
        
        Args:
            frame_index: Index of frame to duplicate (None = current)
        
        Returns:
            Index of duplicated frame or None if failed
        """
        if not self.frame_manager:
            return None
        
        try:
            if frame_index is not None:
                self.frame_manager.select(frame_index)
            
            original_index = self.frame_manager.current_index()
            duplicate_index = self.frame_manager.duplicate()
            self.frame_duplicated.emit(original_index, duplicate_index)
            return duplicate_index
        except Exception:
            return None
    
    def move_frame(self, from_index: int, to_index: int) -> bool:
        """
        Move a frame to a new position.
        
        Args:
            from_index: Current index of frame
            to_index: Target index
        
        Returns:
            True if move succeeded
        """
        if not self.frame_manager:
            return False
        
        try:
            self.frame_manager.select(from_index)
            self.frame_manager.move(from_index, to_index)
            self.frame_moved.emit(from_index, to_index)
            return True
        except Exception:
            return False
    
    def select_frame(self, frame_index: int) -> bool:
        """
        Select a frame.
        
        Args:
            frame_index: Index of frame to select
        
        Returns:
            True if selection succeeded
        """
        if not self.frame_manager:
            return False
        
        try:
            self.frame_manager.select(frame_index)
            return True
        except Exception:
            return False
    
    def set_frame_duration(self, frame_index: int, duration_ms: int) -> bool:
        """
        Set frame duration.
        
        Args:
            frame_index: Index of frame
            duration_ms: New duration in milliseconds
        
        Returns:
            True if update succeeded
        """
        if not self.frame_manager:
            return False
        
        try:
            old_duration = self.frame_manager.frame(frame_index).duration_ms
            self.frame_manager.set_duration(frame_index, duration_ms)
            self.frame_duration_changed.emit(frame_index, old_duration, duration_ms)
            return True
        except Exception:
            return False
    
    def get_current_frame_index(self) -> Optional[int]:
        """
        Get current frame index.
        
        Returns:
            Current frame index or None
        """
        if not self.frame_manager:
            return None
        return self.frame_manager.current_index()
    
    def get_frame_count(self) -> int:
        """
        Get total frame count.
        
        Returns:
            Number of frames
        """
        if not self.pattern_state:
            return 0
        return self.pattern_state.frame_count()
    
    def _on_frame_index_changed(self, index: int) -> None:
        """Handle frame index change from frame manager."""
        self.frame_selected.emit(index)
    
    def _on_frame_duration_changed(self, index: int, duration: int) -> None:
        """Handle frame duration change from frame manager."""
        # Duration change already handled by set_frame_duration
        pass

