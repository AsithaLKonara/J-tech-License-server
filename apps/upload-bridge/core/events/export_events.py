"""
Export-related domain events.

These events are published when export operations occur.
"""

from core.events.base import DomainEvent
from core.pattern import Pattern
from typing import Optional
from pathlib import Path


class ExportStartedEvent(DomainEvent):
    """Event published when an export operation starts."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        format: str, 
        output_path: str, 
        source: Optional[str] = None
    ):
        """
        Initialize export started event.
        
        Args:
            pattern: The pattern being exported
            format: Export format (bin, hex, etc.)
            output_path: Path where export will be saved
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.format = format
        self.output_path = output_path


class ExportCompletedEvent(DomainEvent):
    """Event published when an export operation completes successfully."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        format: str, 
        output_path: str,
        duration_ms: float,
        source: Optional[str] = None
    ):
        """
        Initialize export completed event.
        
        Args:
            pattern: The exported pattern
            format: Export format
            output_path: Path where export was saved
            duration_ms: Export duration in milliseconds
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.format = format
        self.output_path = output_path
        self.duration_ms = duration_ms


class ExportFailedEvent(DomainEvent):
    """Event published when an export operation fails."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        format: str, 
        output_path: str,
        error: Exception,
        source: Optional[str] = None
    ):
        """
        Initialize export failed event.
        
        Args:
            pattern: The pattern that failed to export
            format: Export format
            output_path: Path where export was attempted
            error: The exception that caused the failure
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.format = format
        self.output_path = output_path
        self.error = error
        self.error_message = str(error)

