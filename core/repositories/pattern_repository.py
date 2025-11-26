"""
Pattern Repository - Single source of truth for pattern state management.

This repository provides centralized access to the current pattern,
ensuring consistency across all components.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from core.pattern import Pattern


class PatternRepository(QObject):
    """
    Repository for managing the current pattern state.
    
    This is the single source of truth for the active pattern in the application.
    All components should access the pattern through this repository to ensure
    consistency and avoid state duplication.
    
    Usage:
        # Get current pattern
        pattern = PatternRepository.get_current_pattern()
        
        # Set current pattern
        PatternRepository.set_current_pattern(new_pattern)
        
        # Subscribe to changes
        PatternRepository.instance().pattern_changed.connect(callback)
    """
    
    # Signal emitted when pattern changes
    pattern_changed = Signal(Pattern)
    pattern_cleared = Signal()
    
    # Singleton instance
    _instance: Optional['PatternRepository'] = None
    _current_pattern: Optional[Pattern] = None
    _current_file: Optional[str] = None
    _is_dirty: bool = False
    
    def __init__(self):
        """Initialize the repository (private - use instance() instead)."""
        super().__init__()
        if PatternRepository._instance is not None:
            raise RuntimeError("PatternRepository is a singleton. Use PatternRepository.instance() instead.")
        PatternRepository._instance = self
    
    @classmethod
    def instance(cls) -> 'PatternRepository':
        """
        Get the singleton instance of PatternRepository.
        
        Returns:
            PatternRepository: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_current_pattern(cls) -> Optional[Pattern]:
        """
        Get the current pattern.
        
        Returns:
            Optional[Pattern]: The current pattern, or None if no pattern is loaded
        """
        return cls._current_pattern
    
    @classmethod
    def set_current_pattern(cls, pattern: Pattern, file_path: Optional[str] = None) -> None:
        """
        Set the current pattern.
        
        This will emit the pattern_changed signal to notify all observers.
        
        Args:
            pattern: The pattern to set as current
            file_path: Optional file path associated with the pattern
        """
        if not isinstance(pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(pattern).__name__}")
        
        old_pattern = cls._current_pattern
        cls._current_pattern = pattern
        cls._current_file = file_path
        cls._is_dirty = False
        
        # Emit signal if instance exists
        instance = cls._instance
        if instance:
            instance.pattern_changed.emit(pattern)
    
    @classmethod
    def clear_pattern(cls) -> None:
        """
        Clear the current pattern.
        
        This will emit the pattern_cleared signal to notify all observers.
        """
        cls._current_pattern = None
        cls._current_file = None
        cls._is_dirty = False
        
        # Emit signal if instance exists
        instance = cls._instance
        if instance:
            instance.pattern_cleared.emit()
    
    @classmethod
    def get_current_file(cls) -> Optional[str]:
        """
        Get the file path associated with the current pattern.
        
        Returns:
            Optional[str]: The file path, or None if no file is associated
        """
        return cls._current_file
    
    @classmethod
    def set_current_file(cls, file_path: Optional[str]) -> None:
        """
        Set the file path associated with the current pattern.
        
        Args:
            file_path: The file path to associate with the current pattern
        """
        cls._current_file = file_path
    
    @classmethod
    def is_dirty(cls) -> bool:
        """
        Check if the current pattern has unsaved changes.
        
        Returns:
            bool: True if the pattern has unsaved changes, False otherwise
        """
        return cls._is_dirty
    
    @classmethod
    def set_dirty(cls, dirty: bool = True) -> None:
        """
        Mark the current pattern as dirty (has unsaved changes).
        
        Args:
            dirty: True to mark as dirty, False to mark as clean
        """
        cls._is_dirty = dirty
    
    @classmethod
    def has_pattern(cls) -> bool:
        """
        Check if a pattern is currently loaded.
        
        Returns:
            bool: True if a pattern is loaded, False otherwise
        """
        return cls._current_pattern is not None

