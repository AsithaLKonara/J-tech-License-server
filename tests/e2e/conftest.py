"""
Pytest configuration for E2E user flow tests
"""

import pytest
import os
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
import sys

# Set offscreen platform to prevent GUI blocking
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for GUI tests"""
    if not QApplication.instance():
        app = QApplication(sys.argv)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture(autouse=True)
def mock_message_boxes(monkeypatch):
    """Mock QMessageBox calls to prevent blocking during tests"""
    # Mock QMessageBox.warning
    mock_warning = MagicMock(return_value=QMessageBox.StandardButton.Ok)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.warning", mock_warning)
    
    # Mock QMessageBox.question
    mock_question = MagicMock(return_value=QMessageBox.StandardButton.Yes)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.question", mock_question)
    
    # Mock QMessageBox.critical
    mock_critical = MagicMock(return_value=QMessageBox.StandardButton.Ok)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.critical", mock_critical)
    
    # Mock QMessageBox.information
    mock_info = MagicMock(return_value=QMessageBox.StandardButton.Ok)
    monkeypatch.setattr("PySide6.QtWidgets.QMessageBox.information", mock_info)
    
    # Mock QFileDialog to prevent blocking
    mock_file_dialog = MagicMock(return_value=("", ""))  # Return empty (cancelled)
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getOpenFileName", mock_file_dialog)
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", mock_file_dialog)
    
    return {
        'warning': mock_warning,
        'question': mock_question,
        'critical': mock_critical,
        'information': mock_info,
        'file_dialog': mock_file_dialog
    }

