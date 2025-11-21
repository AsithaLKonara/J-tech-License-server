"""
Comprehensive Test Configuration - Dialog mocking and common fixtures

Provides dialog mocking to prevent QMessageBox from blocking comprehensive tests.
"""

import pytest
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QMessageBox


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure QApplication exists for comprehensive tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def mock_dialogs():
    """Auto-mock all dialogs to prevent blocking in comprehensive tests"""
    with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warning, \
         patch('PySide6.QtWidgets.QMessageBox.information') as mock_info, \
         patch('PySide6.QtWidgets.QMessageBox.question') as mock_question, \
         patch('PySide6.QtWidgets.QMessageBox.critical') as mock_critical, \
         patch('PySide6.QtWidgets.QDialog.exec') as mock_dialog_exec, \
         patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_open, \
         patch('PySide6.QtWidgets.QFileDialog.getSaveFileName') as mock_save, \
         patch('PySide6.QtWidgets.QInputDialog.getText') as mock_input, \
         patch('PySide6.QtWidgets.QInputDialog.getInt') as mock_int, \
         patch('PySide6.QtWidgets.QInputDialog.getItem') as mock_item:
        
        # Set default return values
        from PySide6.QtWidgets import QDialog
        mock_open.return_value = ("", "")
        mock_save.return_value = ("", "")
        mock_input.return_value = ("", False)
        mock_int.return_value = (0, False)
        mock_item.return_value = ("", False)
        mock_question.return_value = QMessageBox.StandardButton.Yes
        mock_dialog_exec.return_value = QDialog.DialogCode.Accepted
        
        yield {
            'warning': mock_warning,
            'information': mock_info,
            'question': mock_question,
            'critical': mock_critical,
            'dialog_exec': mock_dialog_exec,
            'open_file': mock_open,
            'save_file': mock_save,
            'input': mock_input,
            'int': mock_int,
            'item': mock_item,
        }
