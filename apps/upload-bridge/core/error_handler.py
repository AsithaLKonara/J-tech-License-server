"""
Centralized Error Handler - Unified error handling and user-friendly messages.

This module provides centralized error handling with custom exceptions
and user-friendly error messages.
"""

from __future__ import annotations

import logging
import traceback
from typing import Optional, Dict, Any, Callable
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Application crash risk
    HIGH = "high"  # Feature broken
    MEDIUM = "medium"  # Feature degraded
    LOW = "low"  # Minor issue


class ErrorCategory(Enum):
    """Error categories."""
    FILE_IO = "file_io"
    PATTERN = "pattern"
    FIRMWARE = "firmware"
    DEVICE = "device"
    UI = "ui"
    VALIDATION = "validation"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Structured error information."""
    message: str
    user_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    exception: Optional[Exception] = None


# Custom Exception Classes

class UploadBridgeError(Exception):
    """Base exception for Upload Bridge errors."""
    
    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.user_message = user_message or message
        self.severity = severity
        self.category = category
        self.error_code = error_code
        self.details = details or {}


class FileIOError(UploadBridgeError):
    """File I/O related errors."""
    
    def __init__(self, message: str, filepath: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            user_message=f"File operation failed: {message}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.FILE_IO,
            **kwargs
        )
        self.filepath = filepath
        if filepath:
            self.details = self.details or {}
            self.details['filepath'] = filepath


class PatternError(UploadBridgeError):
    """Pattern-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message=f"Pattern error: {message}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.PATTERN,
            **kwargs
        )


class FirmwareError(UploadBridgeError):
    """Firmware build/upload errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message=f"Firmware error: {message}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.FIRMWARE,
            **kwargs
        )


class DeviceError(UploadBridgeError):
    """Device connection/communication errors."""
    
    def __init__(self, message: str, device_info: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            user_message=f"Device error: {message}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEVICE,
            **kwargs
        )
        self.device_info = device_info


class ValidationError(UploadBridgeError):
    """Validation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            user_message=f"Validation error: {message}",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            **kwargs
        )


class ErrorHandler:
    """
    Centralized error handler.
    
    Provides:
    - Exception to ErrorInfo conversion
    - User-friendly error messages
    - Error logging
    - Error callbacks
    """
    
    def __init__(self):
        self._error_callbacks: list[Callable[[ErrorInfo], None]] = []
        self._error_history: list[ErrorInfo] = []
        self._max_history = 100
    
    def register_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Register a callback for error events."""
        self._error_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Unregister an error callback."""
        if callback in self._error_callbacks:
            self._error_callbacks.remove(callback)
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """
        Handle an error and convert to ErrorInfo.
        
        Args:
            error: Exception to handle
            context: Additional context information
        
        Returns:
            ErrorInfo object
        """
        # If already an UploadBridgeError, extract info
        if isinstance(error, UploadBridgeError):
            error_info = ErrorInfo(
                message=str(error),
                user_message=error.user_message,
                severity=error.severity,
                category=error.category,
                error_code=error.error_code,
                details={**(error.details or {}), **(context or {})},
                exception=error
            )
        else:
            # Convert generic exception to ErrorInfo
            error_info = self._convert_exception(error, context)
        
        # Log error
        self._log_error(error_info)
        
        # Add to history
        self._add_to_history(error_info)
        
        # Notify callbacks
        self._notify_callbacks(error_info)
        
        return error_info
    
    def _convert_exception(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorInfo:
        """Convert a generic exception to ErrorInfo."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Map common exceptions to user-friendly messages
        user_messages = {
            FileNotFoundError: f"File not found: {error_message}",
            PermissionError: f"Permission denied: {error_message}",
            ValueError: f"Invalid value: {error_message}",
            KeyError: f"Missing key: {error_message}",
            IOError: f"I/O error: {error_message}",
            OSError: f"System error: {error_message}",
        }
        
        user_message = user_messages.get(type(error), f"Error: {error_message}")
        
        # Determine severity
        if isinstance(error, (FileNotFoundError, PermissionError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, KeyError)):
            severity = ErrorSeverity.MEDIUM
        else:
            severity = ErrorSeverity.MEDIUM
        
        # Determine category
        category = ErrorCategory.UNKNOWN
        if isinstance(error, (FileNotFoundError, PermissionError, IOError, OSError)):
            category = ErrorCategory.FILE_IO
        
        return ErrorInfo(
            message=error_message,
            user_message=user_message,
            severity=severity,
            category=category,
            details={
                "error_type": error_type,
                "traceback": traceback.format_exc(),
                **(context or {})
            },
            exception=error
        )
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error to logger."""
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
        }.get(error_info.severity, logging.ERROR)
        
        logger.log(
            log_level,
            f"[{error_info.category.value}] {error_info.message}",
            extra={"error_info": error_info}
        )
        
        if error_info.details and "traceback" in error_info.details:
            logger.debug(f"Traceback: {error_info.details['traceback']}")
    
    def _add_to_history(self, error_info: ErrorInfo) -> None:
        """Add error to history."""
        self._error_history.append(error_info)
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)
    
    def _notify_callbacks(self, error_info: ErrorInfo) -> None:
        """Notify registered callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def get_error_history(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: Optional[int] = None
    ) -> list[ErrorInfo]:
        """Get error history with optional filtering."""
        history = self._error_history
        
        if category:
            history = [e for e in history if e.category == category]
        
        if severity:
            history = [e for e in history if e.severity == severity]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def clear_history(self) -> None:
        """Clear error history."""
        self._error_history.clear()
    
    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly message for an error."""
        error_info = self.handle_error(error)
        return error_info.user_message


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _error_handler


def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
    """Convenience function to handle an error."""
    return _error_handler.handle_error(error, context)


def get_user_message(error: Exception) -> str:
    """Convenience function to get user-friendly error message."""
    return _error_handler.get_user_message(error)

