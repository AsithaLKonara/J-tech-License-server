"""
Unit tests for ErrorHandler.

Tests the centralized error handling system.
"""

import pytest
from core.errors.error_handler import ErrorHandler, ErrorSeverity
from core.errors.exceptions import (
    PatternLoadError,
    PatternSaveError,
    ExportError,
    FlashError
)


@pytest.fixture
def clean_error_handler():
    """Reset error handler before each test."""
    ErrorHandler._instance = None
    yield
    ErrorHandler._instance = None


class TestErrorHandlerSingleton:
    """Test singleton behavior."""
    
    def test_singleton_instance(self, clean_error_handler):
        """Test that instance() returns the same singleton."""
        handler1 = ErrorHandler.instance()
        handler2 = ErrorHandler.instance()
        assert handler1 is handler2
    
    def test_direct_instantiation_raises_error(self, clean_error_handler):
        """Test that direct instantiation raises RuntimeError."""
        ErrorHandler.instance()  # Create instance first
        with pytest.raises(RuntimeError, match="singleton"):
            ErrorHandler()


class TestErrorHandlerHandleError:
    """Test error handling."""
    
    def test_handle_error_logs(self, clean_error_handler, caplog):
        """Test that errors are logged."""
        handler = ErrorHandler.instance()
        
        error = ValueError("Test error")
        handler.handle_error(error, ErrorSeverity.ERROR, show_to_user=False)
        
        assert "ValueError" in caplog.text
        assert "Test error" in caplog.text
    
    def test_handle_error_with_context(self, clean_error_handler, caplog):
        """Test handling error with context."""
        handler = ErrorHandler.instance()
        
        error = PatternLoadError("Failed to load", file_path="/path/to/file.bin")
        handler.handle_error(error, context={'file_path': '/path/to/file.bin'}, show_to_user=False)
        
        assert "file_path" in caplog.text or "File" in caplog.text
    
    def test_handle_error_custom_handler(self, clean_error_handler):
        """Test custom error handler."""
        handler = ErrorHandler.instance()
        handler_called = []
        
        def custom_handler(error: Exception):
            handler_called.append(error)
        
        handler.register_handler(PatternLoadError, custom_handler)
        
        error = PatternLoadError("Failed to load")
        handler.handle_error(error, show_to_user=False)
        
        assert len(handler_called) == 1
        assert handler_called[0] == error
    
    def test_handle_error_user_notification(self, clean_error_handler):
        """Test user notification callback."""
        handler = ErrorHandler.instance()
        notifications = []
        
        def notify(message: str, severity: ErrorSeverity):
            notifications.append((message, severity))
        
        handler.set_user_notification_callback(notify)
        
        error = ValueError("Test error")
        handler.handle_error(error, ErrorSeverity.ERROR, show_to_user=True)
        
        assert len(notifications) == 1
        assert "Test error" in notifications[0][0]
        assert notifications[0][1] == ErrorSeverity.ERROR


class TestErrorHandlerSpecializedMethods:
    """Test specialized error handling methods."""
    
    def test_handle_pattern_error(self, clean_error_handler, caplog):
        """Test handling pattern errors."""
        handler = ErrorHandler.instance()
        
        error = PatternLoadError("Failed to load", file_path="/path/to/file.bin")
        handler.handle_pattern_error(error, file_path="/path/to/file.bin")
        
        assert "PatternLoadError" in caplog.text or "Failed to load" in caplog.text
    
    def test_handle_export_error(self, clean_error_handler, caplog):
        """Test handling export errors."""
        handler = ErrorHandler.instance()
        
        error = ExportError("Export failed")
        handler.handle_export_error(error, format="bin")
        
        assert "ExportError" in caplog.text or "Export failed" in caplog.text
    
    def test_handle_flash_error(self, clean_error_handler, caplog):
        """Test handling flash errors."""
        handler = ErrorHandler.instance()
        
        error = FlashError("Flash failed")
        handler.handle_flash_error(error, chip_id="esp8266", port="COM3")
        
        assert "FlashError" in caplog.text or "Flash failed" in caplog.text

