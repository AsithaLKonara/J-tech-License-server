"""
Error Handling - Centralized error handling system.

This module provides a centralized error handling system with custom exceptions
and error handlers for consistent error management across the application.
"""

from core.errors.exceptions import (
    PatternError,
    PatternLoadError,
    PatternSaveError,
    PatternValidationError,
    ExportError,
    ExportValidationError,
    FlashError,
    FlashBuildError,
    FlashUploadError,
    ServiceError
)
from core.errors.error_handler import ErrorHandler, get_error_handler, ErrorSeverity

__all__ = [
    'PatternError',
    'PatternLoadError',
    'PatternSaveError',
    'PatternValidationError',
    'ExportError',
    'ExportValidationError',
    'FlashError',
    'FlashBuildError',
    'FlashUploadError',
    'ServiceError',
    'ErrorHandler',
    'get_error_handler',
    'ErrorSeverity',
]

