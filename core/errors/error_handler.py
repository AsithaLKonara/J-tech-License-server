"""
Error Handler - Centralized error handling.

Provides a centralized way to handle errors consistently across the application,
with logging, user notification, and error recovery capabilities.
"""

import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler:
    """
    Centralized error handler.
    
    Provides consistent error handling, logging, and user notification
    across the application.
    """
    
    # Singleton instance
    _instance: Optional['ErrorHandler'] = None
    
    def __init__(self):
        """Initialize the error handler."""
        if ErrorHandler._instance is not None:
            raise RuntimeError("ErrorHandler is a singleton. Use ErrorHandler.instance() instead.")
        
        self._error_handlers: Dict[type, Callable] = {}
        self._user_notification_callback: Optional[Callable] = None
        ErrorHandler._instance = self
    
    @classmethod
    def instance(cls) -> 'ErrorHandler':
        """
        Get the singleton instance of ErrorHandler.
        
        Returns:
            ErrorHandler: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_handler(self, exception_type: type, handler: Callable[[Exception], None]) -> None:
        """
        Register a custom handler for a specific exception type.
        
        Args:
            exception_type: The exception type to handle
            handler: Callback function to handle the exception
        """
        self._error_handlers[exception_type] = handler
        logger.debug(f"Registered error handler for {exception_type.__name__}")
    
    def set_user_notification_callback(self, callback: Callable[[str, ErrorSeverity], None]) -> None:
        """
        Set callback for user notifications.
        
        Args:
            callback: Function that takes (message, severity) and shows to user
        """
        self._user_notification_callback = callback
    
    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        show_to_user: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Handle an error.
        
        Args:
            error: The exception to handle
            severity: Error severity level
            show_to_user: Whether to show error to user
            context: Optional additional context information
        """
        error_type = type(error)
        
        # Log the error
        log_message = f"Error: {error_type.__name__}: {str(error)}"
        if context:
            log_message += f" | Context: {context}"
        
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, exc_info=True)
        elif severity == ErrorSeverity.ERROR:
            logger.error(log_message, exc_info=True)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Check for custom handler
        if error_type in self._error_handlers:
            try:
                self._error_handlers[error_type](error)
                return
            except Exception as e:
                logger.error(f"Error in custom handler for {error_type.__name__}: {e}", exc_info=True)
        
        # Default handling: show to user if requested
        if show_to_user and self._user_notification_callback:
            try:
                user_message = self._format_user_message(error, context)
                self._user_notification_callback(user_message, severity)
            except Exception as e:
                logger.error(f"Error showing user notification: {e}", exc_info=True)
    
    def _format_user_message(self, error: Exception, context: Optional[Dict[str, Any]]) -> str:
        """
        Format error message for user display.
        
        Args:
            error: The exception
            context: Optional context information
        
        Returns:
            Formatted user-friendly message
        """
        # Use error message if available
        message = str(error)
        
        # Add context if available
        if context:
            context_parts = []
            if 'file_path' in context:
                context_parts.append(f"File: {context['file_path']}")
            if 'chip_id' in context:
                context_parts.append(f"Chip: {context['chip_id']}")
            if 'port' in context:
                context_parts.append(f"Port: {context['port']}")
            
            if context_parts:
                message += f"\n\n{', '.join(context_parts)}"
        
        return message
    
    def handle_pattern_error(self, error: Exception, file_path: Optional[str] = None) -> None:
        """
        Handle pattern-related errors.
        
        Args:
            error: The exception
            file_path: Optional file path
        """
        context = {'file_path': file_path} if file_path else None
        self.handle_error(error, ErrorSeverity.ERROR, context=context)
    
    def handle_export_error(self, error: Exception, format: Optional[str] = None) -> None:
        """
        Handle export-related errors.
        
        Args:
            error: The exception
            format: Optional export format
        """
        context = {'format': format} if format else None
        self.handle_error(error, ErrorSeverity.ERROR, context=context)
    
    def handle_flash_error(self, error: Exception, chip_id: Optional[str] = None, port: Optional[str] = None) -> None:
        """
        Handle flash-related errors.
        
        Args:
            error: The exception
            chip_id: Optional chip ID
            port: Optional serial port
        """
        context = {}
        if chip_id:
            context['chip_id'] = chip_id
        if port:
            context['port'] = port
        self.handle_error(error, ErrorSeverity.ERROR, context=context if context else None)


def get_error_handler() -> ErrorHandler:
    """
    Get the singleton error handler instance.
    
    Returns:
        ErrorHandler: The singleton error handler
    """
    return ErrorHandler.instance()

