"""
Flash-related domain events.

These events are published when firmware building and uploading operations occur.
"""

from core.events.base import DomainEvent
from core.pattern import Pattern
from typing import Optional
from pathlib import Path


class FirmwareBuildStartedEvent(DomainEvent):
    """Event published when firmware building starts."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        chip_id: str,
        source: Optional[str] = None
    ):
        """
        Initialize firmware build started event.
        
        Args:
            pattern: The pattern being built
            chip_id: Target chip identifier
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.chip_id = chip_id


class FirmwareBuildCompletedEvent(DomainEvent):
    """Event published when firmware building completes successfully."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        chip_id: str,
        firmware_path: str,
        duration_ms: float,
        source: Optional[str] = None
    ):
        """
        Initialize firmware build completed event.
        
        Args:
            pattern: The pattern that was built
            chip_id: Target chip identifier
            firmware_path: Path to built firmware
            duration_ms: Build duration in milliseconds
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.chip_id = chip_id
        self.firmware_path = firmware_path
        self.duration_ms = duration_ms


class FirmwareBuildFailedEvent(DomainEvent):
    """Event published when firmware building fails."""
    
    def __init__(
        self, 
        pattern: Pattern, 
        chip_id: str,
        error: Exception,
        source: Optional[str] = None
    ):
        """
        Initialize firmware build failed event.
        
        Args:
            pattern: The pattern that failed to build
            chip_id: Target chip identifier
            error: The exception that caused the failure
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.pattern = pattern
        self.chip_id = chip_id
        self.error = error
        self.error_message = str(error)


class FirmwareUploadStartedEvent(DomainEvent):
    """Event published when firmware uploading starts."""
    
    def __init__(
        self, 
        chip_id: str,
        firmware_path: str,
        port: Optional[str] = None,
        source: Optional[str] = None
    ):
        """
        Initialize firmware upload started event.
        
        Args:
            chip_id: Target chip identifier
            firmware_path: Path to firmware being uploaded
            port: Serial port
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.chip_id = chip_id
        self.firmware_path = firmware_path
        self.port = port


class FirmwareUploadCompletedEvent(DomainEvent):
    """Event published when firmware uploading completes successfully."""
    
    def __init__(
        self, 
        chip_id: str,
        firmware_path: str,
        port: Optional[str],
        success: bool,
        duration_ms: float,
        source: Optional[str] = None
    ):
        """
        Initialize firmware upload completed event.
        
        Args:
            chip_id: Target chip identifier
            firmware_path: Path to firmware that was uploaded
            port: Serial port
            success: Whether upload was successful
            duration_ms: Upload duration in milliseconds
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.chip_id = chip_id
        self.firmware_path = firmware_path
        self.port = port
        self.success = success
        self.duration_ms = duration_ms


class FirmwareUploadFailedEvent(DomainEvent):
    """Event published when firmware uploading fails."""
    
    def __init__(
        self, 
        chip_id: str,
        firmware_path: str,
        port: Optional[str],
        error: Exception,
        source: Optional[str] = None
    ):
        """
        Initialize firmware upload failed event.
        
        Args:
            chip_id: Target chip identifier
            firmware_path: Path to firmware that failed to upload
            port: Serial port
            error: The exception that caused the failure
            source: Optional source identifier
        """
        super().__init__(source=source)
        self.chip_id = chip_id
        self.firmware_path = firmware_path
        self.port = port
        self.error = error
        self.error_message = str(error)

