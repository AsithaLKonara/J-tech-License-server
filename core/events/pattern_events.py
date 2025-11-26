"""
Pattern-related domain events.

These events are published when pattern-related operations occur.
"""

from core.events.base import DomainEvent
from core.pattern import Pattern
from typing import Optional


class PatternCreatedEvent(DomainEvent):
    """Event published when a new pattern is created."""
    
    def __init__(self, pattern: Pattern, source: Optional[str] = None):
        """
        Initialize pattern created event.
        
        Args:
            pattern: The created pattern
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern


class PatternLoadedEvent(DomainEvent):
    """Event published when a pattern is loaded from a file."""
    
    def __init__(self, pattern: Pattern, file_path: str, source: Optional[str] = None):
        """
        Initialize pattern loaded event.
        
        Args:
            pattern: The loaded pattern
            file_path: Path to the file that was loaded
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.file_path = file_path


class PatternSavedEvent(DomainEvent):
    """Event published when a pattern is saved to a file."""
    
    def __init__(self, pattern: Pattern, file_path: str, source: Optional[str] = None):
        """
        Initialize pattern saved event.
        
        Args:
            pattern: The saved pattern
            file_path: Path where the pattern was saved
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.file_path = file_path


class PatternModifiedEvent(DomainEvent):
    """Event published when a pattern is modified."""
    
    def __init__(self, pattern: Pattern, modification_type: str, source: Optional[str] = None):
        """
        Initialize pattern modified event.
        
        Args:
            pattern: The modified pattern
            modification_type: Type of modification (e.g., 'frame_added', 'pixel_changed')
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.modification_type = modification_type


class PatternClearedEvent(DomainEvent):
    """Event published when the current pattern is cleared."""
    
    def __init__(self, source: Optional[str] = None):
        """
        Initialize pattern cleared event.
        
        Args:
            source: Optional source identifier
        """
        super().__init__(source=source)


class PatternDuplicatedEvent(DomainEvent):
    """Event published when a pattern is duplicated."""
    
    def __init__(self, original_pattern: Pattern, duplicated_pattern: Pattern, source: Optional[str] = None):
        """
        Initialize pattern duplicated event.
        
        Args:
            original_pattern: The original pattern
            duplicated_pattern: The duplicated pattern
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.original_pattern = original_pattern
        self.duplicated_pattern = duplicated_pattern

