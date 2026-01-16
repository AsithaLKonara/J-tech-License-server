#!/usr/bin/env python3
"""
Fully Automated GUI Test Runner

Runs the complete GUI test suite 100% automatically with full monitoring.
Handles "not responding" issues and provides detailed logging.

Usage:
    python tests/gui/run_gui_tests_automated.py
"""

import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLabel, QProgressBar
from PySide6.QtCore import QTimer, QThread, Signal, QObject, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest

from tests.gui.test_runner_fixed import TestRunnerFixed
from tests.gui.report_generator import ReportGenerator
from tests.gui.test_types import TestResult, TestStatus


class AutomatedTestMonitor(QObject):
    """Monitors test execution and handles automation."""
    
    test_started = Signal(str, str)
    test_completed = Signal(str, str, str, str, str)
    category_completed = Signal(str, int, int)
    all_tests_completed = Signal()
    log_message = Signal(str)
    progress_updated = Signal(int)
    
    def __init__(self):
        super().__init__()
        self.test_runner: Optional[TestRunnerFixed] = None
        self.test_thread: Optional[QThread] = None
        self.results = {}
        self.logs = []
        self.start_time = None
        self.completed = False
        self.error_occurred = False
        
    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
        self.log_message.emit(log_entry)
    
    def start_automated_tests(self):
        """Start tests automatically."""
        self.start_time = time.time()
        self.log("=" * 70)
        self.log("Starting Fully Automated GUI Test Suite")
        self.log("=" * 70)
        self.log("")
        
        # Create test runner with timeout protection
        self.log("Creating test runner...")
        self.test_runner = TestRunnerFixed(skip_app_launch=False, timeout=15000)
        
        # Connect signals
        self.test_runner.test_started.connect(self.on_test_started)
        self.test_runner.test_completed.connect(self.on_test_completed)
        self.test_runner.category_completed.connect(self.on_category_completed)
        self.test_runner.all_tests_completed.connect(self.on_all_tests_completed)
        self.test_runner.log_message.connect(self.log)
        self.test_runner.progress_updated.connect(self.on_progress_updated)
        self.test_runner.finished.connect(self.on_finished)
        
        # Create thread for test execution
        self.test_thread = QThread()
        self.test_runner.moveToThread(self.test_thread)
        
        # Start monitoring timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_execution)
        self.monitor_timer.start(1000)  # Check every second
        
        # Start test execution
        self.test_thread.started.connect(self.test_runner.run_all_tests)
        self.log("Starting test thread...")
        self.test_thread.start()
        
        # Set up timeout protection
        QTimer.singleShot(60000, self.check_timeout)  # 60 second overall timeout
    
    def monitor_execution(self):
        """Monitor test execution for responsiveness."""
        app = QApplication.instance()
        if app:
            app.processEvents()
        
        # Check if thread is still running
        if self.test_thread and not self.test_thread.isRunning() and not self.completed:
            if not self.error_occurred:
                self.log("WARNING: Test thread finished unexpectedly")
                self.error_occurred = True
    
    def check_timeout(self):
        """Check if tests are taking too long."""
        if not self.completed:
            elapsed = time.time() - self.start_time if self.start_time else 0
            if elapsed > 60:
                self.log(f"WARNING: Tests running for {elapsed:.1f} seconds")
                self.log("This may indicate a hang. Monitoring continues...")
    
    def on_test_started(self, category: str, feature: str):
        """Handle test started."""
        self.test_started.emit(category, feature)
    
    def on_test_completed(self, category: str, feature: str, status: str, message: str, error: Optional[str] = None):
        """Handle test completed."""
        if category not in self.results:
            self.results[category] = []
        
        result = TestResult(
            category=category,
            feature=feature,
            status=TestStatus.PASS if status == "Pass" else TestStatus.FAIL,
            message=message,
            error=error
        )
        self.results[category].append(result)
        
        self.test_completed.emit(category, feature, status, message, error)
    
    def on_category_completed(self, category: str, passed: int, total: int):
        """Handle category completed."""
        self.category_completed.emit(category, passed, total)
    
    def on_progress_updated(self, progress: int):
        """Handle progress update."""
        self.progress_updated.emit(progress)
    
    def on_all_tests_completed(self):
        """Handle all tests completed."""
        self.completed = True
        if self.monitor_timer:
            self.monitor_timer.stop()
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.log("")
        self.log("=" * 70)
        self.log("All Tests Completed")
        self.log("=" * 70)
        self.log(f"Total time: {elapsed:.2f} seconds")
        self.log("")
        
        # Generate summary
        self.generate_summary()
        
        self.all_tests_completed.emit()
    
    def on_finished(self):
        """Handle test runner finished."""
        if self.test_thread:
            self.test_thread.quit()
            self.test_thread.wait(5000)  # Wait up to 5 seconds
    
    def generate_summary(self):
        """Generate test summary."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        self.log("Test Summary:")
        self.log("-" * 70)
        
        for category, results in self.results.items():
            passed = sum(1 for r in results if r.status == TestStatus.PASS)
            failed = sum(1 for r in results if r.status == TestStatus.FAIL)
            total = len(results)
            
            total_tests += total
            total_passed += passed
            total_failed += failed
            
            status = "✅" if failed == 0 else "❌"
            self.log(f"{status} {category}: {passed}/{total} passed")
        
        self.log("-" * 70)
        self.log(f"Total: {total_passed}/{total_tests} passed")
        if total_failed > 0:
            self.log(f"Failed: {total_failed}")
        self.log("")
    
    def generate_report(self, output_file: Optional[Path] = None):
        """Generate test report."""
        if output_file is None:
            output_file = project_root / "docs" / "GUI_TEST_RESULTS_AUTOMATED.md"
        
        report_generator = ReportGenerator()
        
        # Convert results to report format
        all_results = []
        for category, results in self.results.items():
            all_results.extend(results)
        
        report = report_generator.generate_html_report(all_results)
        
        # Also save as markdown
        with open(output_file, 'w') as f:
            f.write(f"# Automated GUI Test Results\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Summary\n\n")
            
            total_tests = sum(len(r) for r in self.results.values())
            total_passed = sum(sum(1 for t in r if t.status == TestStatus.PASS) for r in self.results.values())
            total_failed = total_tests - total_passed
            
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Passed**: {total_passed}\n")
            f.write(f"- **Failed**: {total_failed}\n\n")
            
            f.write(f"## Detailed Results\n\n")
            for category, results in self.results.items():
                f.write(f"### {category}\n\n")
                for result in results:
                    status = "✅ PASS" if result.status == TestStatus.PASS else "❌ FAIL"
                    f.write(f"- {status}: {result.feature}\n")
                    if result.message:
                        f.write(f"  - {result.message}\n")
                    if result.error:
                        f.write(f"  - Error: {result.error}\n")
                f.write("\n")
            
            f.write(f"## Log Output\n\n")
            f.write("```\n")
            for log_entry in self.logs:
                f.write(f"{log_entry}\n")
            f.write("```\n")
        
        self.log(f"Report saved to: {output_file}")


class AutomatedTestGUI(QWidget):
    """Minimal GUI for automated test execution."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automated GUI Test Suite - Running...")
        self.setGeometry(100, 100, 800, 600)
        self.monitor = AutomatedTestMonitor()
        self.setup_ui()
        self.connect_signals()
        
        # Auto-start tests after a short delay
        QTimer.singleShot(500, self.start_tests)
    
    def setup_ui(self):
        """Set up minimal UI."""
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        layout.addWidget(self.log_output)
    
    def connect_signals(self):
        """Connect monitor signals."""
        self.monitor.log_message.connect(self.log)
        self.monitor.progress_updated.connect(self.update_progress)
        self.monitor.all_tests_completed.connect(self.on_tests_completed)
    
    def log(self, message: str):
        """Add log message."""
        self.log_output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress(self, value: int):
        """Update progress bar."""
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Running tests... {value}%")
    
    def start_tests(self):
        """Start automated tests."""
        self.status_label.setText("Starting automated tests...")
        self.monitor.start_automated_tests()
    
    def on_tests_completed(self):
        """Handle tests completed."""
        self.status_label.setText("Tests completed! Generating report...")
        self.setWindowTitle("Automated GUI Test Suite - Complete")
        
        # Generate report
        self.monitor.generate_report()
        
        self.status_label.setText("✅ All tests completed! Check docs/GUI_TEST_RESULTS_AUTOMATED.md")
        
        # Auto-close after 5 seconds
        QTimer.singleShot(5000, self.close)


def main():
    """Main entry point."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
    
    # Create and show automated test GUI
    window = AutomatedTestGUI()
    window.show()
    
    # Process events to keep GUI responsive
    event_timer = QTimer()
    event_timer.timeout.connect(lambda: app.processEvents())
    event_timer.start(50)  # Process events every 50ms
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

