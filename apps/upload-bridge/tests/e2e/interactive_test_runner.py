"""
Interactive Test Runner - GUI Application for Running User Flow Tests

This creates a GUI application that allows you to:
- Select which tests to run
- See test progress in real-time
- View test results
- Re-run failed tests
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QTextEdit, QLabel, QCheckBox,
    QGroupBox, QProgressBar, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
import subprocess
import json
import re


class TestRunnerThread(QThread):
    """Thread for running tests without blocking UI"""
    test_output = Signal(str)
    test_finished = Signal(int, dict)  # exit_code, results
    
    def __init__(self, test_file, test_filter=None):
        super().__init__()
        self.test_file = test_file
        self.test_filter = test_filter
        self._stop = False
    
    def run(self):
        """Run pytest and emit output"""
        cmd = ["python", "-m", "pytest", str(self.test_file), "-v", "--tb=short"]
        
        if self.test_filter:
            cmd.extend(["-k", self.test_filter])
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_lines = []
        for line in process.stdout:
            if self._stop:
                process.terminate()
                break
            output_lines.append(line)
            self.test_output.emit(line)
        
        process.wait()
        
        # Parse results
        results = self._parse_results(output_lines)
        self.test_finished.emit(process.returncode, results)
    
    def stop(self):
        """Stop test execution"""
        self._stop = True
    
    def _parse_results(self, output_lines):
        """Parse test output to extract results"""
        results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "tests": []
        }
        
        output_text = "".join(output_lines)
        
        # Extract test results
        passed_match = re.search(r'(\d+)\s+passed', output_text)
        failed_match = re.search(r'(\d+)\s+failed', output_text)
        skipped_match = re.search(r'(\d+)\s+skipped', output_text)
        error_match = re.search(r'(\d+)\s+error', output_text)
        
        if passed_match:
            results["passed"] = int(passed_match.group(1))
        if failed_match:
            results["failed"] = int(failed_match.group(1))
        if skipped_match:
            results["skipped"] = int(skipped_match.group(1))
        if error_match:
            results["errors"] = int(error_match.group(1))
        
        # Extract individual test results
        test_pattern = r'(PASSED|FAILED|SKIPPED|ERROR)\s+([^\s]+)'
        for match in re.finditer(test_pattern, output_text):
            status = match.group(1).lower()
            test_name = match.group(2)
            results["tests"].append({
                "name": test_name,
                "status": status
            })
        
        return results


class InteractiveTestRunner(QMainWindow):
    """GUI application for running user flow tests"""
    
    def __init__(self):
        super().__init__()
        self.test_file = Path(__file__).parent / "test_user_flows_automated.py"
        self.test_runner = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        self.setWindowTitle("User Flow Test Runner")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Automated User Flow Test Runner")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Splitter for test list and output
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: Test selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        test_group = QGroupBox("Test Selection")
        test_layout = QVBoxLayout()
        
        self.test_list = QListWidget()
        self.test_list.setSelectionMode(QListWidget.MultiSelection)
        self._populate_test_list()
        test_layout.addWidget(self.test_list)
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.test_list.selectAll)
        test_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.test_list.clearSelection)
        test_layout.addWidget(select_none_btn)
        
        test_group.setLayout(test_layout)
        left_layout.addWidget(test_group)
        
        # Control buttons
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        
        self.run_btn = QPushButton("▶ Run Selected Tests")
        self.run_btn.clicked.connect(self.run_tests)
        self.run_btn.setStyleSheet("font-size: 14px; padding: 10px;")
        control_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("⏹ Stop Tests")
        self.stop_btn.clicked.connect(self.stop_tests)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        left_layout.addWidget(control_group)
        
        left_layout.addStretch()
        splitter.addWidget(left_panel)
        
        # Right panel: Output
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        output_group = QGroupBox("Test Output")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFontFamily("Courier")
        output_layout.addWidget(self.output_text)
        
        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self.output_text.clear)
        output_layout.addWidget(clear_btn)
        
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)
        
        # Results summary
        results_group = QGroupBox("Results Summary")
        results_layout = QVBoxLayout()
        
        self.results_label = QLabel("No tests run yet")
        results_layout.addWidget(self.results_label)
        
        results_group.setLayout(results_layout)
        right_layout.addWidget(results_group)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])
    
    def _populate_test_list(self):
        """Populate test list from test file"""
        if not self.test_file.exists():
            self.output_text.append(f"Error: Test file not found: {self.test_file}")
            return
        
        # Read test file and extract test classes and methods
        with open(self.test_file, 'r') as f:
            content = f.read()
        
        # Find test classes
        class_pattern = r'class\s+(TestUserFlow_\w+):'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            self.test_list.addItem(class_name)
        
        # Find individual test methods
        method_pattern = r'def\s+(test_\w+)'
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            # Find which class it belongs to (simplified)
            self.test_list.addItem(f"  └─ {method_name}")
    
    def run_tests(self):
        """Run selected tests"""
        selected_items = self.test_list.selectedItems()
        
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select tests to run")
            return
        
        # Build test filter
        test_names = [item.text().strip() for item in selected_items]
        # Remove indentation markers
        test_names = [name.replace("  └─ ", "") for name in test_names]
        test_filter = " or ".join(test_names)
        
        self.output_text.clear()
        self.output_text.append("=" * 70)
        self.output_text.append("Starting Test Execution")
        self.output_text.append("=" * 70)
        self.output_text.append()
        
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        
        # Start test runner thread
        self.test_runner = TestRunnerThread(self.test_file, test_filter)
        self.test_runner.test_output.connect(self.on_test_output)
        self.test_runner.test_finished.connect(self.on_tests_finished)
        self.test_runner.start()
    
    def stop_tests(self):
        """Stop running tests"""
        if self.test_runner and self.test_runner.isRunning():
            self.test_runner.stop()
            self.test_runner.wait()
            self.output_text.append("\n⚠️ Tests stopped by user")
            self.on_tests_finished(1, {})
    
    def on_test_output(self, line):
        """Handle test output"""
        self.output_text.append(line.rstrip())
        # Auto-scroll to bottom
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_tests_finished(self, exit_code, results):
        """Handle test completion"""
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # Update results summary
        if results:
            summary = f"""
Results Summary:
  ✅ Passed: {results.get('passed', 0)}
  ❌ Failed: {results.get('failed', 0)}
  ⏭️  Skipped: {results.get('skipped', 0)}
  ⚠️  Errors: {results.get('errors', 0)}
            """
            self.results_label.setText(summary.strip())
        else:
            self.results_label.setText("Tests completed")
        
        self.output_text.append("\n" + "=" * 70)
        if exit_code == 0:
            self.output_text.append("✅ All tests completed successfully!")
        else:
            self.output_text.append("❌ Some tests failed")
        self.output_text.append("=" * 70)


def main():
    app = QApplication(sys.argv)
    window = InteractiveTestRunner()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

