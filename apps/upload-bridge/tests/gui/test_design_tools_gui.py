#!/usr/bin/env python3
"""
Design Tools Tab - Automated Test GUI Application

Launches Upload Bridge application and automatically tests all Design Tools Tab features.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QProgressBar,
    QTextEdit, QLabel, QSplitter, QGroupBox, QMessageBox,
    QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QBrush, QFont

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

try:
    from tests.gui.test_runner_fixed import TestRunnerFixed as TestRunner
except ImportError:
    from tests.gui.test_runner import TestRunner
from tests.gui.report_generator import ReportGenerator
from tests.gui.test_types import TestResult, TestStatus


class TestDesignToolsGUI(QMainWindow):
    """Main test GUI application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Design Tools Tab - Automated Test Suite")
        self.setGeometry(100, 100, 1400, 900)
        
        self.test_results: Dict[str, List[TestResult]] = {}
        self.test_runner: Optional[TestRunner] = None
        self.test_thread: Optional[QThread] = None
        self.test_main_window = None  # Reference to test window
        self.report_generator = ReportGenerator()
        
        self._setup_ui()
        self._setup_connections()
        
    def _setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Design Tools Tab - Automated Test Suite")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)
        
        # Summary panel
        summary_group = QGroupBox("Test Summary")
        summary_layout = QHBoxLayout()
        
        self.summary_label = QLabel("Ready to start tests")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        summary_layout.addWidget(self.summary_label)
        summary_layout.addWidget(self.progress_bar, 1)
        
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Tests")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.start_button.clicked.connect(self.start_tests)
        
        self.stop_button = QPushButton("Stop Tests")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        self.stop_button.clicked.connect(self.stop_tests)
        
        self.export_button = QPushButton("Export Report")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_report)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Splitter for results and log
        splitter = QSplitter(Qt.Horizontal)
        
        # Test results tree
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout()
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Test", "Status", "Message"])
        self.results_tree.setColumnWidth(0, 400)
        self.results_tree.setColumnWidth(1, 120)
        self.results_tree.setColumnWidth(2, 300)
        self.results_tree.setAlternatingRowColors(True)
        
        results_layout.addWidget(self.results_tree)
        results_group.setLayout(results_layout)
        
        # Log output
        log_group = QGroupBox("Test Log")
        log_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        
        log_layout.addWidget(self.log_output)
        log_group.setLayout(log_layout)
        
        splitter.addWidget(results_group)
        splitter.addWidget(log_group)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter, 1)
        
    def _setup_connections(self):
        """Set up signal connections."""
        pass  # Will be connected when test runner is created
        
    def _initialize_test_tree(self):
        """Initialize the test results tree with all test categories."""
        self.results_tree.clear()
        self.test_results.clear()
        
        categories = [
            ("Header Toolbar", 8),
            ("Toolbox Tabs", 9),
            ("Drawing Tools", 17),
            ("Canvas Features", 21),
            ("Timeline Features", 22),
            ("Layer System", 7),
            ("Automation", 22),
            ("Effects", 8),
            ("Export/Import", 14),
            ("Scratchpads", 6),
            ("Keyboard Shortcuts", 9),
            ("Options and Parameters", 6),
            ("Feature Flows", 8),
        ]
        
        for category, count in categories:
            category_item = QTreeWidgetItem(self.results_tree)
            category_item.setText(0, category)
            category_item.setText(1, "Pending")
            category_item.setText(2, f"{count} tests")
            category_item.setExpanded(True)
            
            # Set pending color
            category_item.setForeground(1, QBrush(QColor(128, 128, 128)))
            
            self.test_results[category] = []
            
    def start_tests(self):
        """Start the test execution."""
        self.log("=" * 70)
        self.log("Starting Design Tools Tab Test Suite")
        self.log("=" * 70)
        self.log(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("")
        
        self._initialize_test_tree()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Create test runner in a separate thread with timeout protection
        self.test_thread = QThread()
        try:
            # Try to use fixed version with better timeout handling
            self.test_runner = TestRunner(timeout=10000)  # 10 second timeout
        except TypeError:
            # Fallback to original if fixed version doesn't support timeout
            self.test_runner = TestRunner()
        self.test_runner.moveToThread(self.test_thread)
        
        # IMPORTANT: Create main window in MAIN THREAD before starting worker thread
        # Qt widgets MUST be created in the main thread to avoid crashes
        self.log("Creating Upload Bridge main window in main thread...")
        try:
            from ui.main_window import UploadBridgeMainWindow
            self.test_main_window = UploadBridgeMainWindow()
            self.test_main_window.show()
            QApplication.processEvents()
            
            # Initialize the Design Tools tab in the main thread
            self.log("Initializing Design Tools Tab...")
            if self.test_main_window.design_tab is None:
                self.test_main_window.initialize_tab('design_tools')
                QApplication.processEvents()
                
                # Wait a bit for tab to initialize
                from PySide6.QtTest import QTest
                for _ in range(10):
                    QTest.qWait(50)
                    QApplication.processEvents()
                    if self.test_main_window.design_tab is not None:
                        break
            
            if self.test_main_window.design_tab is None:
                self.log("WARNING: Design Tools Tab not initialized, but continuing...")
            
            # Set the window in the test runner
            self.test_runner.set_main_window(self.test_main_window)
            self.log("Main window and Design Tools Tab ready")
        except Exception as e:
            self.log(f"ERROR: Failed to create main window: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return
        
        # Connect signals
        self.test_thread.started.connect(self.test_runner.run_all_tests)
        self.test_runner.test_started.connect(self.on_test_started)
        self.test_runner.test_completed.connect(self.on_test_completed)
        self.test_runner.category_completed.connect(self.on_category_completed)
        self.test_runner.all_tests_completed.connect(self.on_all_tests_completed)
        self.test_runner.log_message.connect(self.log)
        self.test_runner.progress_updated.connect(self.update_progress)
        self.test_runner.finished.connect(self.test_thread.quit)
        self.test_runner.finished.connect(self.test_runner.deleteLater)
        self.test_thread.finished.connect(self.test_thread.deleteLater)
        
        # Use a timer to periodically process events and keep GUI responsive
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self._process_events)
        self.event_timer.start(50)  # Process events every 50ms for better responsiveness
        
        # Add timeout protection - if tests don't start within 30 seconds, show warning
        self.start_timeout_timer = QTimer()
        self.start_timeout_timer.setSingleShot(True)
        self.start_timeout_timer.timeout.connect(self._check_test_start_timeout)
        self.start_timeout_timer.start(30000)  # 30 seconds
        
        # Track if tests have actually started
        self.tests_started = False
        
        # Start thread
        self.test_thread.start()
    
    def _check_test_start_timeout(self):
        """Check if tests have started, warn if they haven't."""
        if not self.tests_started:
            self.log("WARNING: Tests appear to be hanging during initialization")
            self.log("This may be due to:")
            self.log("  1. Main window taking too long to initialize")
            self.log("  2. Design Tools Tab initialization blocking")
            self.log("  3. Network or file system operations blocking")
            self.log("")
            self.log("You can:")
            self.log("  - Click 'Stop Tests' to cancel")
            self.log("  - Check the main Upload Bridge window for errors")
            self.log("  - Try running the application manually first")
    
    def on_test_started(self, category: str, feature: str):
        """Handle test started signal."""
        self.tests_started = True  # Mark that tests have started
        if hasattr(self, 'start_timeout_timer'):
            self.start_timeout_timer.stop()  # Cancel timeout since tests started
        self.log(f"[{category}] Starting: {feature}")
    
    def _process_events(self):
        """Process Qt events to keep GUI responsive."""
        QApplication.processEvents()
        
    def stop_tests(self):
        """Stop the test execution."""
        if self.test_runner:
            self.test_runner.stop_requested = True
            self.log("Test execution stopped by user")
            # Stop the event timer
            if hasattr(self, 'event_timer'):
                self.event_timer.stop()
            self.on_all_tests_completed()
            
        
    def on_test_completed(self, category: str, feature: str, status: str, message: str, error: Optional[str] = None):
        """Handle test completed signal."""
        # Find or create test item
        category_item = None
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            if item.text(0) == category:
                category_item = item
                break
        
        if category_item:
            # Check if test item already exists
            test_item = None
            for i in range(category_item.childCount()):
                child = category_item.child(i)
                if child.text(0) == feature:
                    test_item = child
                    break
            
            if not test_item:
                test_item = QTreeWidgetItem(category_item)
                test_item.setText(0, feature)
            
            test_item.setText(1, status)
            test_item.setText(2, message)
            
            # Set color based on status
            if status == "Pass":
                test_item.setForeground(1, QBrush(QColor(0, 150, 0)))
                self.log(f"[{category}] ✓ PASS: {feature}")
            elif status == "Fail":
                test_item.setForeground(1, QBrush(QColor(200, 0, 0)))
                self.log(f"[{category}] ✗ FAIL: {feature}")
                if error:
                    self.log(f"  Error: {error}")
            elif status == "In Progress":
                test_item.setForeground(1, QBrush(QColor(255, 165, 0)))
            else:
                test_item.setForeground(1, QBrush(QColor(128, 128, 128)))
            
            # Store result
            test_result = TestResult(
                category=category,
                feature=feature,
                status=TestStatus.PASS if status == "Pass" else TestStatus.FAIL if status == "Fail" else TestStatus.IN_PROGRESS,
                message=message,
                error=error
            )
            self.test_results[category].append(test_result)
            
    def on_category_completed(self, category: str, passed: int, total: int):
        """Handle category completed signal."""
        # Update category item
        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            if item.text(0) == category:
                status_text = f"{passed}/{total} passed"
                item.setText(1, status_text)
                
                if passed == total:
                    item.setForeground(1, QBrush(QColor(0, 150, 0)))
                elif passed > 0:
                    item.setForeground(1, QBrush(QColor(255, 165, 0)))
                else:
                    item.setForeground(1, QBrush(QColor(200, 0, 0)))
                
                break
        
        self.log(f"[{category}] Completed: {passed}/{total} tests passed")
        self.log("")
        
    def on_all_tests_completed(self):
        """Handle all tests completed signal."""
        # Stop the event timer
        if hasattr(self, 'event_timer'):
            self.event_timer.stop()
        
        self.log("=" * 70)
        self.log("Test Suite Completed")
        self.log("=" * 70)
        
        # Calculate summary
        total_tests = 0
        total_passed = 0
        
        for category, results in self.test_results.items():
            total_tests += len(results)
            total_passed += sum(1 for r in results if r.status == TestStatus.PASS)
        
        self.summary_label.setText(
            f"Tests Completed: {total_passed}/{total_tests} passed "
            f"({total_passed*100//total_tests if total_tests > 0 else 0}%)"
        )
        self.progress_bar.setValue(100)
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(True)
        
        self.log(f"Total: {total_tests} tests, {total_passed} passed, {total_tests - total_passed} failed")
        self.log(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Process events one more time to ensure UI updates
        QApplication.processEvents()
        
    def update_progress(self, value: int):
        """Update progress bar."""
        self.progress_bar.setValue(value)
        
    def log(self, message: str):
        """Add message to log output."""
        self.log_output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def export_report(self):
        """Export test report."""
        if not self.test_results:
            QMessageBox.warning(self, "No Results", "No test results to export. Please run tests first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Test Report",
            f"design_tools_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            "HTML Files (*.html);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.json'):
                    self.report_generator.export_json(self.test_results, file_path)
                else:
                    self.report_generator.export_html(self.test_results, file_path)
                
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Failed to export report:\n{str(e)}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = TestDesignToolsGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

