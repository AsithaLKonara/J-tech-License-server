"""
L4 Non-Functional Test Suite Fixtures

Provides global fixtures for dialog mocking and common setup.
"""

import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox


@pytest.fixture(autouse=True)
def mock_all_dialogs():
    """Automatically mock all dialogs for all tests"""
    with patch('PySide6.QtWidgets.QMessageBox.question') as mock_question, \
         patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning, \
         patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical, \
         patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
         patch('PySide6.QtWidgets.QDialog.exec') as mock_dialog_exec:
        
        # Default responses
        mock_question.return_value = QMessageBox.Yes
        mock_warning.return_value = QMessageBox.Ok
        mock_critical.return_value = QMessageBox.Ok
        mock_info.return_value = QMessageBox.Ok
        mock_dialog_exec.return_value = QDialog.Accepted
        
        yield {
            'question': mock_question,
            'warning': mock_warning,
            'critical': mock_critical,
            'info': mock_info,
            'dialog_exec': mock_dialog_exec
        }

