#!/usr/bin/env python3
"""
Run all Design Tools Tab tests programmatically.

This script runs all tests without the GUI and outputs results to console and file.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QTest

from ui.main_window import UploadBridgeMainWindow
from tests.gui.test_runner import TestRunner
from tests.gui.test_types import TestResult, TestStatus
from tests.gui.report_generator import ReportGenerator


class ConsoleTestRunner(QObject):
    """Test runner that outputs to console."""
    
    def __init__(self):
        super().__init__()
        self.results: Dict[str, List[TestResult]] = defaultdict(list)
        self.current_category = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def on_test_started(self, category: str, feature: str):
        """Handle test started."""
        if self.current_category != category:
            self.current_category = category
            print(f"\n{'='*70}")
            print(f"Testing: {category}")
            print(f"{'='*70}")
        print(f"  → {feature}...", end=" ", flush=True)
        
    def on_test_completed(self, category: str, feature: str, status: str, message: str, error: str = None):
        """Handle test completed."""
        test_status = TestStatus.PASS if status == "Pass" else TestStatus.FAIL if status == "Fail" else TestStatus.IN_PROGRESS
        
        result = TestResult(
            category=category,
            feature=feature,
            status=test_status,
            message=message,
            error=error
        )
        self.results[category].append(result)
        self.total_tests += 1
        
        if status == "Pass":
            self.passed_tests += 1
            print("✓ PASS")
        else:
            self.failed_tests += 1
            print("✗ FAIL")
            if error:
                print(f"    Error: {error[:200]}")
                
    def on_category_completed(self, category: str, passed: int, total: int):
        """Handle category completed."""
        print(f"\n  {category}: {passed}/{total} passed")
        
    def on_log_message(self, message: str):
        """Handle log message."""
        if message.startswith("ERROR") or message.startswith("WARNING"):
            print(f"  {message}")
        # Don't print all log messages to keep output clean
        
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ({self.passed_tests*100//self.total_tests if self.total_tests > 0 else 0}%)")
        print(f"Failed: {self.failed_tests} ({self.failed_tests*100//self.total_tests if self.total_tests > 0 else 0}%)")
        print("\n" + "="*70)
        print("BY CATEGORY:")
        print("="*70)
        
        for category, results in sorted(self.results.items()):
            passed = sum(1 for r in results if r.status == TestStatus.PASS)
            total = len(results)
            status_icon = "✓" if passed == total else "✗"
            print(f"{status_icon} {category}: {passed}/{total} passed")
            
        # Print failed tests
        failed = []
        for category, results in self.results.items():
            for result in results:
                if result.status == TestStatus.FAIL:
                    failed.append((category, result))
        
        if failed:
            print("\n" + "="*70)
            print("FAILED TESTS:")
            print("="*70)
            for category, result in failed:
                print(f"  ✗ [{category}] {result.feature}")
                print(f"      {result.message}")
                if result.error:
                    print(f"      Error: {result.error[:200]}")


def main():
    """Main entry point."""
    print("="*70)
    print("Design Tools Tab - Automated Test Suite")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Design Tools Test Runner")
    
    # Create console test runner
    console_runner = ConsoleTestRunner()
    
    # Create test runner
    test_runner = TestRunner()
    
    # Create main window in main thread
    print("Creating Upload Bridge main window...")
    try:
        main_window = UploadBridgeMainWindow()
        main_window.show()
        QApplication.processEvents()
        
        # Initialize Design Tools tab
        print("Initializing Design Tools Tab...")
        if main_window.design_tab is None:
            main_window.initialize_tab('design_tools')
            QApplication.processEvents()
            
            # Wait for tab to initialize
            for _ in range(20):
                QTest.qWait(50)
                QApplication.processEvents()
                if main_window.design_tab is not None:
                    break
        
        if main_window.design_tab is None:
            print("ERROR: Failed to initialize Design Tools Tab")
            return 1
        
        # Set window in test runner
        test_runner.set_main_window(main_window)
        print("Main window and Design Tools Tab ready")
        print()
        
    except Exception as e:
        print(f"ERROR: Failed to create main window: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Connect signals
    test_runner.test_started.connect(console_runner.on_test_started)
    test_runner.test_completed.connect(console_runner.on_test_completed)
    test_runner.category_completed.connect(console_runner.on_category_completed)
    test_runner.log_message.connect(console_runner.on_log_message)
    
    # Run tests
    print("Starting test execution...")
    print()
    
    try:
        # Run tests synchronously (in main thread)
        test_runner.run_all_tests()
        
        # Process events to ensure all signals are handled
        QApplication.processEvents()
        
        # Wait a bit for any remaining signals
        for _ in range(10):
            QTest.qWait(100)
            QApplication.processEvents()
        
    except Exception as e:
        print(f"\nERROR during test execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    console_runner.print_summary()
    
    # Generate report
    print("\n" + "="*70)
    print("Generating test report...")
    print("="*70)
    
    report_generator = ReportGenerator()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # HTML report
    html_path = project_root / f"tests/gui/test_report_{timestamp}.html"
    try:
        report_generator.export_html(console_runner.results, str(html_path))
        print(f"✓ HTML report saved: {html_path}")
    except Exception as e:
        print(f"✗ Failed to generate HTML report: {str(e)}")
    
    # JSON report
    json_path = project_root / f"tests/gui/test_report_{timestamp}.json"
    try:
        report_generator.export_json(console_runner.results, str(json_path))
        print(f"✓ JSON report saved: {json_path}")
    except Exception as e:
        print(f"✗ Failed to generate JSON report: {str(e)}")
    
    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Return exit code based on test results
    return 0 if console_runner.failed_tests == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

