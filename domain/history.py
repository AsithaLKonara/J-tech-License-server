"""
History Manager - Undo/Redo system for pattern editing.

This module provides a command pattern-based history system for tracking
and reverting changes to frames and patterns.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from copy import deepcopy
from core.pattern import Frame

RGB = Tuple[int, int, int]


class HistoryCommand:
    """Base class for history commands."""
    
    def __init__(self, description: str = ""):
        self.description = description
    
    def execute(self) -> None:
        """Execute the command."""
        raise NotImplementedError
    
    def undo(self) -> None:
        """Undo the command."""
        raise NotImplementedError


class FrameStateCommand(HistoryCommand):
    """Command for frame state changes (pixel painting, etc.)."""
    
    def __init__(self, frame_index: int, old_pixels: List[RGB], new_pixels: List[RGB], description: str = "Edit frame"):
        super().__init__(description)
        self.frame_index = frame_index
        self.old_pixels = deepcopy(old_pixels)
        self.new_pixels = deepcopy(new_pixels)
    
    def execute(self) -> List[RGB]:
        """Return the new state."""
        return deepcopy(self.new_pixels)
    
    def undo(self) -> List[RGB]:
        """Return the old state."""
        return deepcopy(self.old_pixels)


class HistoryManager:
    """
    Manages undo/redo history for pattern editing.
    
    Features:
    - Per-frame history tracking
    - Maximum history depth (default 50)
    - Command pattern for actions
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize history manager.
        
        Args:
            max_history: Maximum number of commands to keep in history
        """
        self.max_history = max_history
        self._history: List[List[HistoryCommand]] = []  # Per-frame history stacks
        self._redo_stacks: List[List[HistoryCommand]] = []  # Per-frame redo stacks
        self._current_frame_index = 0
    
    def set_frame_count(self, count: int):
        """Initialize history stacks for given number of frames."""
        while len(self._history) < count:
            self._history.append([])
            self._redo_stacks.append([])
        # Trim excess
        while len(self._history) > count:
            self._history.pop()
            self._redo_stacks.pop()
    
    def set_current_frame(self, frame_index: int):
        """Set the currently active frame."""
        self._current_frame_index = frame_index
    
    def push_command(self, command: HistoryCommand, frame_index: Optional[int] = None):
        """
        Push a command onto the history stack.
        
        Args:
            command: Command to push
            frame_index: Frame index (uses current frame if None)
        """
        if frame_index is None:
            frame_index = self._current_frame_index
        
        # Ensure we have stacks for this frame
        while len(self._history) <= frame_index:
            self._history.append([])
            self._redo_stacks.append([])
        
        # Add command to history
        self._history[frame_index].append(command)
        
        # Clear redo stack when new command is added
        self._redo_stacks[frame_index] = []
        
        # Trim history if too long
        if len(self._history[frame_index]) > self.max_history:
            self._history[frame_index].pop(0)
    
    def can_undo(self, frame_index: Optional[int] = None) -> bool:
        """Check if undo is possible."""
        if frame_index is None:
            frame_index = self._current_frame_index
        if frame_index >= len(self._history):
            return False
        return len(self._history[frame_index]) > 0
    
    def can_redo(self, frame_index: Optional[int] = None) -> bool:
        """Check if redo is possible."""
        if frame_index is None:
            frame_index = self._current_frame_index
        if frame_index >= len(self._redo_stacks):
            return False
        return len(self._redo_stacks[frame_index]) > 0
    
    def undo(self, frame_index: Optional[int] = None) -> Optional[HistoryCommand]:
        """
        Undo the last command.
        
        Returns:
            The command that was undone, or None if nothing to undo
        """
        if frame_index is None:
            frame_index = self._current_frame_index
        
        if not self.can_undo(frame_index):
            return None
        
        command = self._history[frame_index].pop()
        self._redo_stacks[frame_index].append(command)
        return command
    
    def redo(self, frame_index: Optional[int] = None) -> Optional[HistoryCommand]:
        """
        Redo the last undone command.
        
        Returns:
            The command that was redone, or None if nothing to redo
        """
        if frame_index is None:
            frame_index = self._current_frame_index
        
        if not self.can_redo(frame_index):
            return None
        
        command = self._redo_stacks[frame_index].pop()
        self._history[frame_index].append(command)
        return command
    
    def clear(self, frame_index: Optional[int] = None):
        """Clear history for a frame or all frames."""
        if frame_index is None:
            self._history = []
            self._redo_stacks = []
        else:
            if frame_index < len(self._history):
                self._history[frame_index] = []
            if frame_index < len(self._redo_stacks):
                self._redo_stacks[frame_index] = []
    
    def get_history_count(self, frame_index: Optional[int] = None) -> int:
        """Get number of commands in history for a frame."""
        if frame_index is None:
            frame_index = self._current_frame_index
        if frame_index >= len(self._history):
            return 0
        return len(self._history[frame_index])
    
    def get_redo_count(self, frame_index: Optional[int] = None) -> int:
        """Get number of commands in redo stack for a frame."""
        if frame_index is None:
            frame_index = self._current_frame_index
        if frame_index >= len(self._redo_stacks):
            return 0
        return len(self._redo_stacks[frame_index])

