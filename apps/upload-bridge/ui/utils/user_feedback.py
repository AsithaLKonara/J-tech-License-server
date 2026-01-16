"""
User Feedback Utilities - Enhanced error messages and user notifications.

Provides consistent, user-friendly error messages and feedback throughout the application.
"""

from PySide6.QtWidgets import QMessageBox, QWidget
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class UserFeedback:
    """Centralized user feedback and error handling utilities."""
    
    @staticmethod
    def show_error(
        parent: Optional[QWidget],
        title: str,
        message: str,
        details: Optional[str] = None,
        log_error: bool = True
    ) -> None:
        """
        Show an error dialog with optional details.
        
        Args:
            parent: Parent widget for the dialog
            title: Error dialog title
            message: Main error message (user-friendly)
            details: Optional technical details (shown in expandable section)
            log_error: Whether to log the error
        """
        if log_error:
            logger.error(f"{title}: {message}")
            if details:
                logger.debug(f"Error details: {details}")
        
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        if details:
            msg.setDetailedText(details)
        
        msg.exec()
    
    @staticmethod
    def show_warning(
        parent: Optional[QWidget],
        title: str,
        message: str,
        details: Optional[str] = None
    ) -> None:
        """Show a warning dialog."""
        logger.warning(f"{title}: {message}")
        
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        if details:
            msg.setDetailedText(details)
        
        msg.exec()
    
    @staticmethod
    def show_info(
        parent: Optional[QWidget],
        title: str,
        message: str,
        details: Optional[str] = None
    ) -> None:
        """Show an information dialog."""
        logger.info(f"{title}: {message}")
        
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        if details:
            msg.setDetailedText(details)
        
        msg.exec()
    
    @staticmethod
    def show_question(
        parent: Optional[QWidget],
        title: str,
        message: str,
        default_yes: bool = False
    ) -> bool:
        """
        Show a question dialog.
        
        Returns:
            True if user clicked Yes, False otherwise
        """
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def format_file_error(file_path: str, error: Exception) -> Tuple[str, str]:
        """
        Format a file operation error into user-friendly message and details.
        
        Returns:
            Tuple of (user_message, technical_details)
        """
        import os
        
        file_name = os.path.basename(file_path)
        error_type = type(error).__name__
        error_msg = str(error)
        
        # User-friendly message
        if isinstance(error, FileNotFoundError):
            user_msg = f"File not found: {file_name}\n\nThe file may have been moved or deleted."
        elif isinstance(error, PermissionError):
            user_msg = f"Permission denied: {file_name}\n\nYou may not have permission to access this file."
        elif isinstance(error, IsADirectoryError):
            user_msg = f"Expected a file, but found a directory: {file_name}"
        elif isinstance(error, OSError):
            user_msg = f"File system error: {file_name}\n\n{error_msg}"
        else:
            user_msg = f"Error reading file: {file_name}\n\n{error_msg}"
        
        # Technical details
        details = f"Error Type: {error_type}\n"
        details += f"File Path: {file_path}\n"
        details += f"Error Message: {error_msg}"
        
        return user_msg, details
    
    @staticmethod
    def format_validation_error(
        field_name: str,
        value: any,
        expected: str,
        actual: Optional[str] = None
    ) -> str:
        """Format a validation error message."""
        if actual:
            return f"Invalid {field_name}: {actual}\n\nExpected: {expected}\nGot: {value}"
        return f"Invalid {field_name}: {value}\n\nExpected: {expected}"
    
    @staticmethod
    def format_pattern_error(pattern_name: str, error: Exception) -> Tuple[str, str]:
        """Format a pattern-related error."""
        error_type = type(error).__name__
        error_msg = str(error)
        
        user_msg = f"Pattern error: {pattern_name}\n\n{error_msg}"
        details = f"Error Type: {error_type}\nPattern: {pattern_name}\nDetails: {error_msg}"
        
        return user_msg, details

