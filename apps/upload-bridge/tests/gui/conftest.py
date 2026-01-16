"""
GUI Test Configuration - Dialog mocking for GUI tests

Provides dialog mocking to prevent QMessageBox from blocking GUI tests.
"""

import pytest
import os
import sys
from typing import Callable
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from core.pattern import Pattern, Frame, PatternMetadata

# Set offscreen platform to prevent GUI blocking during test collection
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure QApplication exists for GUI tests"""
    app = QApplication.instance()
    if app is None:
        # Use offscreen platform to prevent GUI windows
        if "QT_QPA_PLATFORM" not in os.environ:
            os.environ["QT_QPA_PLATFORM"] = "offscreen"
        app = QApplication(sys.argv if sys.argv else [])
    yield app


@pytest.fixture
def pattern_factory() -> Callable[[int, int, int], Pattern]:
    """Factory function to create test patterns."""
    def _make_pattern(frame_count: int = 3, width: int = 4, height: int = 1) -> Pattern:
        metadata = PatternMetadata(width=width, height=height)
        frames = []
        for idx in range(frame_count):
            pixels = [(idx * 10 + col, 0, 0) for col in range(width)]
            frames.append(Frame(pixels=pixels, duration_ms=50))
        return Pattern(name="Test Pattern", metadata=metadata, frames=frames)
    return _make_pattern


@pytest.fixture(autouse=True)
def mock_dialogs():
    """Auto-mock all dialogs to prevent blocking in GUI tests"""
    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning, \
         patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
         patch('PySide6.QtWidgets.QMessageBox.question') as mock_question, \
         patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical, \
         patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_open, \
         patch('PySide6.QtWidgets.QFileDialog.getSaveFileName') as mock_save, \
         patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input, \
         patch('PySide6.QtWidgets.QInputDialog.getItem') as mock_item:
        
        # Set default return values
        mock_open.return_value = ("", "")
        mock_save.return_value = ("", "")
        mock_input.return_value = ("", False)
        mock_item.return_value = ("", False)
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        yield {
            'warning': mock_warning,
            'information': mock_info,
            'question': mock_question,
            'critical': mock_critical,
            'open_file': mock_open,
            'save_file': mock_save,
            'input': mock_input,
            'item': mock_item,
        }

