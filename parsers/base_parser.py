"""
Base Parser - Abstract interface for pattern file parsers
"""

from abc import ABC, abstractmethod
from typing import Optional
import sys
sys.path.insert(0, str(__file__ + "/../../.."))

from core.pattern import Pattern


class ParserBase(ABC):
    """
    Base class for all pattern file format parsers
    
    Each format (Standard, Raw RGB, Intel HEX, DAT, etc.) implements this interface
    """
    
    def __init__(self):
        self.pattern: Optional[Pattern] = None
        self.last_error: Optional[str] = None
    
    @abstractmethod
    def detect(self, data: bytes, filename: str = "",
               suggested_leds: Optional[int] = None,
               suggested_frames: Optional[int] = None) -> bool:
        """
        Detect if this parser can handle the data
        
        Args:
            data: Raw file bytes
            filename: Original filename (for extension checking)
            suggested_leds: User-provided LED count hint
            suggested_frames: User-provided frame count hint
        
        Returns:
            True if this parser can handle the format
        """
        pass
    
    @abstractmethod
    def parse(self, data: bytes,
              suggested_leds: Optional[int] = None,
              suggested_frames: Optional[int] = None) -> Pattern:
        """
        Parse data into Pattern object
        
        Args:
            data: Raw file bytes
            suggested_leds: User-provided LED count (for headerless formats)
            suggested_frames: User-provided frame count (for headerless formats)
        
        Returns:
            Pattern object
        
        Raises:
            ValueError: If parsing fails
        """
        pass
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get human-readable format name"""
        pass
    
    @abstractmethod
    def get_format_description(self) -> str:
        """Get detailed format description"""
        pass
    
    def get_confidence(self, data: bytes) -> float:
        """
        Get confidence score (0.0-1.0) that this is the correct format
        
        Args:
            data: Raw file bytes
        
        Returns:
            Confidence score (0.0 = definitely not, 1.0 = definitely yes)
        
        Note:
            Default implementation returns 0.5 if detect() returns True
            Override for more sophisticated scoring
        """
        return 0.5 if self.detect(data, "") else 0.0

