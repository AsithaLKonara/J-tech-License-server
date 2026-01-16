"""
Pattern Operations Component.

Handles pattern-level operations like create, load, save, duplicate.
Extracted from DesignToolsTab to improve maintainability.
"""

from typing import Optional
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QWidget

from core.pattern import Pattern
from core.services.pattern_service import PatternService
from core.repositories.pattern_repository import PatternRepository


class PatternOperationsComponent(QObject):
    """
    Component for pattern-level operations.
    
    This component handles:
    - Pattern creation
    - Pattern loading
    - Pattern saving
    - Pattern duplication
    - Pattern validation
    """
    
    # Signals
    pattern_created = Signal(Pattern)
    pattern_loaded = Signal(Pattern)
    pattern_saved = Signal(Pattern, str)  # pattern, file_path
    pattern_duplicated = Signal(Pattern, Pattern)  # original, duplicate
    pattern_validation_failed = Signal(str)  # error message
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the pattern operations component.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.pattern_service = PatternService()
        self.repository = PatternRepository.instance()
    
    def create_pattern(
        self,
        name: str = "New Design",
        width: int = 72,
        height: int = 1
    ) -> Optional[Pattern]:
        """
        Create a new blank pattern.
        
        Args:
            name: Pattern name
            width: Matrix width
            height: Matrix height
        
        Returns:
            Created pattern or None if creation failed
        """
        try:
            pattern = self.pattern_service.create_blank_pattern(
                name=name,
                width=width,
                height=height
            )
            self.pattern_created.emit(pattern)
            return pattern
        except Exception as e:
            self.pattern_validation_failed.emit(f"Failed to create pattern: {str(e)}")
            return None
    
    def load_pattern(self, file_path: str) -> Optional[Pattern]:
        """
        Load a pattern from a file.
        
        Args:
            file_path: Path to pattern file
        
        Returns:
            Loaded pattern or None if loading failed
        """
        try:
            pattern, format_name = self.pattern_service.load_pattern(file_path)
            self.pattern_loaded.emit(pattern)
            return pattern
        except Exception as e:
            self.pattern_validation_failed.emit(f"Failed to load pattern: {str(e)}")
            return None
    
    def save_pattern(self, pattern: Pattern, file_path: str) -> bool:
        """
        Save a pattern to a file.
        
        Args:
            pattern: Pattern to save
            file_path: Path where to save
        
        Returns:
            True if save succeeded, False otherwise
        """
        try:
            # Validate pattern first
            is_valid, error = self.pattern_service.validate_pattern(pattern)
            if not is_valid:
                self.pattern_validation_failed.emit(error or "Pattern validation failed")
                return False
            
            self.pattern_service.save_pattern(pattern, file_path)
            self.pattern_saved.emit(pattern, file_path)
            return True
        except Exception as e:
            self.pattern_validation_failed.emit(f"Failed to save pattern: {str(e)}")
            return False
    
    def duplicate_pattern(self, pattern: Pattern, new_name: Optional[str] = None) -> Optional[Pattern]:
        """
        Duplicate a pattern.
        
        Args:
            pattern: Pattern to duplicate
            new_name: Optional name for duplicate
        
        Returns:
            Duplicated pattern or None if duplication failed
        """
        try:
            duplicated = self.pattern_service.duplicate_pattern(pattern, new_name)
            self.pattern_duplicated.emit(pattern, duplicated)
            return duplicated
        except Exception as e:
            self.pattern_validation_failed.emit(f"Failed to duplicate pattern: {str(e)}")
            return None
    
    def validate_pattern(self, pattern: Pattern) -> tuple[bool, Optional[str]]:
        """
        Validate a pattern.
        
        Args:
            pattern: Pattern to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.pattern_service.validate_pattern(pattern)
    
    def get_current_pattern(self) -> Optional[Pattern]:
        """
        Get the current pattern from repository.
        
        Returns:
            Current pattern or None
        """
        return self.repository.get_current_pattern()
    
    def is_dirty(self) -> bool:
        """
        Check if current pattern has unsaved changes.
        
        Returns:
            True if pattern is dirty
        """
        return self.repository.is_dirty()
    
    def set_dirty(self, dirty: bool = True) -> None:
        """
        Mark current pattern as dirty.
        
        Args:
            dirty: True to mark as dirty
        """
        self.repository.set_dirty(dirty)

