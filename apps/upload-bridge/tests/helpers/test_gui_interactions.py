"""
GUI Test Suite

Automated GUI interactions using QTest/qtbot.
"""

import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set offscreen platform to prevent GUI windows
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from tests.helpers.report_generator import TestResult, TestSuiteResult


class GUITestSuite:
    """Test suite for GUI interactions."""
    
    def __init__(self, app: Optional[QApplication] = None):
        """Initialize test suite."""
        self.app = app or QApplication.instance() or QApplication(sys.argv)
        self.test_results: List[TestResult] = []
    
    def log_test(self, name: str, passed: bool, error_message: Optional[str] = None, execution_time: float = 0.0, details: Optional[Dict[str, Any]] = None):
        """Log test result."""
        self.test_results.append(TestResult(
            name=name,
            suite="GUI Interactions",
            passed=passed,
            skipped=False,
            error_message=error_message,
            execution_time=execution_time,
            details=details or {}
        ))
    
    def test_application_startup(self) -> bool:
        """Test that application can start (QApplication exists)."""
        start_time = time.time()
        try:
            # Verify QApplication exists
            app = QApplication.instance()
            passed = app is not None
            execution_time = time.time() - start_time
            
            self.log_test(
                "Application Startup",
                passed,
                None if passed else "QApplication not available",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Application Startup", False, str(e), execution_time)
            return False
    
    def test_main_window_creation(self) -> bool:
        """Test main window can be created."""
        start_time = time.time()
        try:
            from ui.main_window import UploadBridgeMainWindow
            
            # Create main window
            main_window = UploadBridgeMainWindow()
            passed = main_window is not None
            
            # Cleanup
            main_window.close()
            del main_window
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "Main Window Creation",
                passed,
                None if passed else "Failed to create main window",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Main Window Creation", False, str(e), execution_time)
            return False
    
    def test_design_tools_tab_creation(self) -> bool:
        """Test design tools tab can be created."""
        start_time = time.time()
        try:
            from ui.tabs.design_tools_tab import DesignToolsTab
            
            # Create design tools tab
            design_tab = DesignToolsTab()
            passed = design_tab is not None
            
            # Cleanup
            design_tab.close()
            del design_tab
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "Design Tools Tab Creation",
                passed,
                None if passed else "Failed to create design tools tab",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Design Tools Tab Creation", False, str(e), execution_time)
            return False
    
    def test_license_dialog_creation(self) -> bool:
        """Test license activation dialog can be created."""
        start_time = time.time()
        try:
            from ui.license_activation_dialog import LicenseActivationDialog
            
            # Create license dialog
            license_dialog = LicenseActivationDialog()
            passed = license_dialog is not None
            
            # Cleanup
            license_dialog.close()
            del license_dialog
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "License Dialog Creation",
                passed,
                None if passed else "Failed to create license dialog",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("License Dialog Creation", False, str(e), execution_time)
            return False
    
    def test_widget_interactions(self) -> bool:
        """Test basic widget interactions."""
        start_time = time.time()
        try:
            from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout
            
            # Create a simple widget with a button
            widget = QWidget()
            layout = QVBoxLayout()
            button = QPushButton("Test Button")
            layout.addWidget(button)
            widget.setLayout(layout)
            widget.show()
            
            # Simulate button click
            QTest.mouseClick(button, Qt.LeftButton)
            
            passed = True  # If no exception, it works
            
            # Cleanup
            widget.close()
            del widget
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "Widget Interactions",
                passed,
                None,
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Widget Interactions", False, str(e), execution_time)
            return False
    
    def test_file_dialog_mocking(self) -> bool:
        """Test that file dialogs can be mocked."""
        start_time = time.time()
        try:
            # Mock QFileDialog.getOpenFileName
            with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName') as mock_dialog:
                mock_dialog.return_value = ("test_file.ledproj", "LED Project Files (*.ledproj)")
                
                # Call the mocked dialog
                result = QFileDialog.getOpenFileName(None, "Test", "", "*.ledproj")
                passed = result == ("test_file.ledproj", "LED Project Files (*.ledproj)")
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "File Dialog Mocking",
                passed,
                None if passed else "File dialog mocking failed",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("File Dialog Mocking", False, str(e), execution_time)
            return False
    
    def test_message_box_mocking(self) -> bool:
        """Test that message boxes can be mocked."""
        start_time = time.time()
        try:
            # Mock QMessageBox
            with patch('PySide6.QtWidgets.QMessageBox.question') as mock_box:
                mock_box.return_value = QMessageBox.Yes
                
                result = QMessageBox.question(None, "Test", "Test message")
                passed = result == QMessageBox.Yes
            
            execution_time = time.time() - start_time
            
            self.log_test(
                "Message Box Mocking",
                passed,
                None if passed else "Message box mocking failed",
                execution_time
            )
            
            return passed
        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Message Box Mocking", False, str(e), execution_time)
            return False
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all GUI tests."""
        print("\n" + "=" * 60)
        print("GUI Interactions Test Suite")
        print("=" * 60)
        
        test_methods = [
            self.test_application_startup,
            self.test_main_window_creation,
            self.test_design_tools_tab_creation,
            self.test_license_dialog_creation,
            self.test_widget_interactions,
            self.test_file_dialog_mocking,
            self.test_message_box_mocking,
        ]
        
        start_time = time.time()
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"ERROR in {test_method.__name__}: {e}")
        
        execution_time = time.time() - start_time
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.passed)
        failed = total - passed
        skipped = sum(1 for r in self.test_results if r.skipped)
        
        suite_result = TestSuiteResult(
            name="GUI Interactions",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            execution_time=execution_time,
            tests=self.test_results
        )
        
        print(f"\nGUI Interactions: {passed}/{total} passed ({execution_time:.2f}s)")
        
        return suite_result

