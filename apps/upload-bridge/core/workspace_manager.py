"""
Workspace Manager - Multi-pattern workspace management
"""

from PySide6.QtCore import QObject, Signal
from core.pattern import Pattern
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class WorkspaceManager(QObject):
    """
    Manages multiple patterns in a workspace
    Allows switching between different patterns
    """
    
    # Signals
    pattern_added = Signal(str)  # pattern_name
    pattern_removed = Signal(str)  # pattern_name
    active_pattern_changed = Signal(str)  # pattern_name
    pattern_renamed = Signal(str, str)  # old_name, new_name
    
    def __init__(self):
        """Initialize workspace manager"""
        super().__init__()
        # Store patterns: {name: Pattern}
        self._patterns: Dict[str, Pattern] = {}
        self._active_pattern_name: Optional[str] = None
        self._name_counter = 1  # For generating unique names
    
    def add_pattern(self, pattern: Pattern, name: Optional[str] = None) -> str:
        """
        Add pattern to workspace
        
        Args:
            pattern: Pattern to add
            name: Optional name for the pattern (auto-generated if not provided)
            
        Returns:
            Name of the added pattern
        """
        if name is None:
            # Generate unique name
            base_name = pattern.name if pattern.name else "Pattern"
            name = base_name
            counter = 1
            while name in self._patterns:
                name = f"{base_name} {counter}"
                counter += 1
        
        # Ensure name is unique
        original_name = name
        counter = 1
        while name in self._patterns:
            name = f"{original_name} {counter}"
            counter += 1
        
        self._patterns[name] = pattern
        self.pattern_added.emit(name)
        
        # Set as active if it's the first pattern
        if self._active_pattern_name is None:
            self.set_active_pattern(name)
        
        logger.info(f"Added pattern to workspace: {name}")
        return name
    
    def remove_pattern(self, name: str) -> bool:
        """
        Remove pattern from workspace
        
        Args:
            name: Name of pattern to remove
            
        Returns:
            True if removed, False if not found
        """
        if name not in self._patterns:
            return False
        
        del self._patterns[name]
        
        # If it was active, switch to another pattern or None
        if self._active_pattern_name == name:
            if self._patterns:
                # Switch to first available pattern
                self._active_pattern_name = next(iter(self._patterns))
                self.active_pattern_changed.emit(self._active_pattern_name)
            else:
                self._active_pattern_name = None
                self.active_pattern_changed.emit("")
        
        self.pattern_removed.emit(name)
        logger.info(f"Removed pattern from workspace: {name}")
        return True
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """Get pattern by name"""
        return self._patterns.get(name)
    
    def list_patterns(self) -> List[str]:
        """List all pattern names in workspace"""
        return list(self._patterns.keys())
    
    def set_active_pattern(self, name: str) -> bool:
        """
        Set active pattern
        
        Args:
            name: Name of pattern to make active
            
        Returns:
            True if set, False if pattern not found
        """
        if name not in self._patterns:
            return False
        
        if self._active_pattern_name != name:
            self._active_pattern_name = name
            self.active_pattern_changed.emit(name)
            logger.info(f"Active pattern changed to: {name}")
        
        return True
    
    def get_active_pattern(self) -> Optional[Pattern]:
        """Get current active pattern"""
        if self._active_pattern_name:
            return self._patterns.get(self._active_pattern_name)
        return None
    
    def get_active_pattern_name(self) -> Optional[str]:
        """Get name of current active pattern"""
        return self._active_pattern_name
    
    def rename_pattern(self, old_name: str, new_name: str) -> bool:
        """
        Rename a pattern
        
        Args:
            old_name: Current name
            new_name: New name
            
        Returns:
            True if renamed, False if old_name not found or new_name already exists
        """
        if old_name not in self._patterns:
            return False
        
        if new_name in self._patterns and new_name != old_name:
            return False  # New name already exists
        
        pattern = self._patterns.pop(old_name)
        self._patterns[new_name] = pattern
        
        # Update active pattern name if it was renamed
        if self._active_pattern_name == old_name:
            self._active_pattern_name = new_name
        
        self.pattern_renamed.emit(old_name, new_name)
        logger.info(f"Renamed pattern: {old_name} -> {new_name}")
        return True
    
    def duplicate_pattern(self, name: str, new_name: Optional[str] = None) -> Optional[str]:
        """
        Duplicate a pattern
        
        Args:
            name: Name of pattern to duplicate
            new_name: Optional name for duplicate (auto-generated if not provided)
            
        Returns:
            Name of duplicated pattern, or None if original not found
        """
        if name not in self._patterns:
            return None
        
        pattern = self._patterns[name]
        
        # Create copy
        try:
            if hasattr(pattern, 'to_dict'):
                pattern_dict = pattern.to_dict()
                new_pattern = Pattern.from_dict(pattern_dict)
            else:
                import copy
                new_pattern = copy.deepcopy(pattern)
        except Exception as e:
            logger.error(f"Failed to duplicate pattern: {e}", exc_info=True)
            return None
        
        # Generate name if not provided
        if new_name is None:
            base_name = f"{name} Copy"
            new_name = base_name
            counter = 1
            while new_name in self._patterns:
                new_name = f"{base_name} {counter}"
                counter += 1
        
        return self.add_pattern(new_pattern, new_name)
    
    def clear(self):
        """Clear all patterns from workspace"""
        self._patterns.clear()
        self._active_pattern_name = None
        self.active_pattern_changed.emit("")
        logger.info("Workspace cleared")
    
    def count(self) -> int:
        """Get number of patterns in workspace"""
        return len(self._patterns)

