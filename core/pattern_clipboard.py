"""
Pattern Clipboard - Shared clipboard for patterns across tabs
"""

from PySide6.QtCore import QObject, Signal
from core.pattern import Pattern
import logging

logger = logging.getLogger(__name__)


class PatternClipboard(QObject):
    """
    Singleton pattern clipboard manager for copying/pasting patterns across tabs
    """
    
    # Signals
    clipboard_changed = Signal(bool)  # Emitted when clipboard content changes (True=has pattern, False=empty)
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(PatternClipboard, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize clipboard (only once due to singleton)"""
        if self._initialized:
            return
        
        super().__init__()
        self._pattern: Pattern = None
        self._initialized = True
    
    def copy_pattern(self, pattern: Pattern):
        """Copy pattern to clipboard"""
        try:
            # Create a deep copy of the pattern
            if hasattr(pattern, 'to_dict'):
                pattern_dict = pattern.to_dict()
                self._pattern = Pattern.from_dict(pattern_dict)
            else:
                # Fallback: store reference (not ideal but works)
                import copy
                self._pattern = copy.deepcopy(pattern)
            
            self.clipboard_changed.emit(True)
            logger.info(f"Pattern '{pattern.name}' copied to clipboard")
        except Exception as e:
            logger.error(f"Failed to copy pattern to clipboard: {e}", exc_info=True)
            self._pattern = None
            self.clipboard_changed.emit(False)
    
    def paste_pattern(self) -> Pattern:
        """Get pattern from clipboard"""
        if self._pattern:
            # Return a copy to prevent modifications to clipboard
            try:
                if hasattr(self._pattern, 'to_dict'):
                    pattern_dict = self._pattern.to_dict()
                    return Pattern.from_dict(pattern_dict)
                else:
                    import copy
                    return copy.deepcopy(self._pattern)
            except Exception as e:
                logger.error(f"Failed to paste pattern from clipboard: {e}", exc_info=True)
                return None
        return None
    
    def has_pattern(self) -> bool:
        """Check if clipboard has a pattern"""
        return self._pattern is not None
    
    def clear(self):
        """Clear clipboard"""
        self._pattern = None
        self.clipboard_changed.emit(False)
        logger.info("Clipboard cleared")

