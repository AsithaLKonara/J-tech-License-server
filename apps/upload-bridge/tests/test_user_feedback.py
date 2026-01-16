"""
Tests for user feedback utilities.
"""

import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget, QApplication
import sys

# Initialize QApplication if not already done
if not QApplication.instance():
    app = QApplication(sys.argv)

from ui.utils.user_feedback import UserFeedback


class TestUserFeedback(unittest.TestCase):
    """Test user feedback utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parent = QWidget()
    
    def test_format_file_error_file_not_found(self):
        """Test formatting FileNotFoundError."""
        error = FileNotFoundError("No such file or directory: 'test.bin'")
        user_msg, details = UserFeedback.format_file_error("test.bin", error)
        
        self.assertIn("File not found", user_msg)
        self.assertIn("test.bin", user_msg)
        self.assertIn("Error Type: FileNotFoundError", details)
    
    def test_format_file_error_permission(self):
        """Test formatting PermissionError."""
        error = PermissionError("Permission denied: 'test.bin'")
        user_msg, details = UserFeedback.format_file_error("test.bin", error)
        
        self.assertIn("Permission denied", user_msg)
        self.assertIn("test.bin", user_msg)
    
    def test_format_validation_error(self):
        """Test formatting validation errors."""
        msg = UserFeedback.format_validation_error(
            "LED count",
            0,
            "positive integer",
            "0"
        )
        
        self.assertIn("LED count", msg)
        self.assertIn("Expected: positive integer", msg)
        self.assertIn("Got: 0", msg)
    
    def test_format_pattern_error(self):
        """Test formatting pattern errors."""
        error = ValueError("Invalid frame count")
        user_msg, details = UserFeedback.format_pattern_error("test_pattern", error)
        
        self.assertIn("Pattern error", user_msg)
        self.assertIn("test_pattern", user_msg)
        self.assertIn("Error Type: ValueError", details)
    
    @patch('ui.utils.user_feedback.QMessageBox')
    def test_show_error(self, mock_msgbox):
        """Test showing error dialog."""
        UserFeedback.show_error(
            self.parent,
            "Test Error",
            "Test message",
            "Test details"
        )
        
        mock_msgbox.assert_called_once()
        instance = mock_msgbox.return_value
        instance.setIcon.assert_called_once()
        instance.setText.assert_called_once_with("Test message")
        instance.setDetailedText.assert_called_once_with("Test details")
        instance.exec.assert_called_once()
    
    @patch('ui.utils.user_feedback.QMessageBox')
    def test_show_question(self, mock_msgbox):
        """Test showing question dialog."""
        mock_msgbox.return_value.exec.return_value = QWidget().Yes
        
        result = UserFeedback.show_question(
            self.parent,
            "Test Question",
            "Test message"
        )
        
        mock_msgbox.question.assert_called_once()
        # Note: Actual return value depends on user interaction in real usage


if __name__ == '__main__':
    unittest.main()

