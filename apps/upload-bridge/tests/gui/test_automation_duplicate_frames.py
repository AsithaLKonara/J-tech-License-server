"""
GUI Automated Test for Automation Duplicate Frame Detection

This test script simulates clicking the "Apply Actions" button and verifies:
- Frame count before/after automation
- No duplicate frames are created
- Correct number of frames are generated
- Frame uniqueness validation
- Comprehensive logging of all interactions
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import logging

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QProgressBar, QTextEdit, QLabel, QGroupBox, 
    QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtGui import QColor, QFont

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Import core modules
from core.pattern import Pattern, Frame, PatternMetadata
from domain.actions import DesignAction
# UI modules will be imported in setup_test_environment to avoid Qt initialization issues


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation_duplicate_frames_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestResult:
    """Test result container"""
    def __init__(self, name: str, status: str, message: str = "", details: dict = None):
        self.name = name
        self.status = status  # "PASS", "FAIL", "ERROR", "SKIP"
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class AutomationDuplicateFramesTest(QMainWindow):
    """GUI test application for automation duplicate frame detection"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Automation Duplicate Frames Test")
        self.setGeometry(100, 100, 1200, 800)
        
        self.main_window: Optional[UploadBridgeMainWindow] = None
        self.design_tab: Optional[DesignToolsTab] = None
        self.test_results: List[TestResult] = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Automation Duplicate Frames Test")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Test")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.start_button.clicked.connect(self.run_tests)
        
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Results tree
        results_group = QGroupBox("Test Results")
        results_layout = QVBoxLayout()
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Test", "Status", "Message", "Timestamp"])
        self.results_tree.setColumnWidth(0, 300)
        self.results_tree.setColumnWidth(1, 100)
        self.results_tree.setColumnWidth(2, 400)
        results_layout.addWidget(self.results_tree)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group, 1)
        
        # Log output
        log_group = QGroupBox("Test Log")
        log_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.log_output)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message to both the UI and logger"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        logger.info(message)
        self.log_output.append(log_message)
        QApplication.processEvents()
        
    def add_result(self, result: TestResult):
        """Add a test result to the tree"""
        self.test_results.append(result)
        
        item = QTreeWidgetItem(self.results_tree)
        item.setText(0, result.name)
        item.setText(1, result.status)
        item.setText(2, result.message)
        item.setText(3, result.timestamp.strftime("%H:%M:%S"))
        
        # Color code by status
        if result.status == "PASS":
            item.setForeground(1, QColor(0, 150, 0))
        elif result.status == "FAIL":
            item.setForeground(1, QColor(200, 0, 0))
        elif result.status == "ERROR":
            item.setForeground(1, QColor(200, 100, 0))
        
        self.results_tree.scrollToItem(item)
        QApplication.processEvents()
        
    def _frames_are_identical(self, frame1: Frame, frame2: Frame) -> bool:
        """Check if two frames have identical pixel content"""
        if len(frame1.pixels) != len(frame2.pixels):
            return False
        for p1, p2 in zip(frame1.pixels, frame2.pixels):
            if isinstance(p1, (list, tuple)) and isinstance(p2, (list, tuple)):
                if len(p1) >= 3 and len(p2) >= 3:
                    if p1[0] != p2[0] or p1[1] != p2[1] or p1[2] != p2[2]:
                        return False
                else:
                    return False
            else:
                return False
        return True
        
    def check_duplicate_frames(self, frames: List[Frame]) -> List[Tuple[int, int]]:
        """Check for duplicate frames and return list of (index1, index2) pairs"""
        duplicates = []
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                if self._frames_are_identical(frames[i], frames[j]):
                    duplicates.append((i, j))
        return duplicates
        
    def setup_test_environment(self) -> bool:
        """Set up the test environment (create main window and design tab)"""
        try:
            # Import here to ensure Qt is initialized
            try:
                from ui import UploadBridgeMainWindow  # This is EditorController exported from ui/__init__.py
                from ui.tabs.design_tools_tab import DesignToolsTab
            except ImportError as e:
                # Try alternative import path
                try:
                    self.log(f"First import failed: {str(e)}, trying factory import...", "INFO")
                    from ui.factory import EditorController
                    UploadBridgeMainWindow = EditorController
                    from ui.tabs.design_tools_tab import DesignToolsTab
                    self.log("Successfully imported from factory", "INFO")
                except ImportError as e2:
                    self.log(f"ERROR: Failed to import UI modules", "ERROR")
                    self.log(f"  First error: {str(e)}", "ERROR")
                    self.log(f"  Second error: {str(e2)}", "ERROR")
                    self.log(f"  Python path: {sys.path[:5]}", "ERROR")
                    self.log(f"  Current working directory: {os.getcwd()}", "ERROR")
                    self.log(f"  Project root: {project_root}", "ERROR")
                    self.log(f"  Project root exists: {project_root.exists()}", "ERROR")
                    import traceback
                    self.log(traceback.format_exc(), "ERROR")
                    return False
                
            self.log("Creating main window...")
            self.main_window = UploadBridgeMainWindow()
            self.main_window.show()
            QApplication.processEvents()
            QTest.qWait(500)
            
            self.log("Initializing Design Tools Tab...")
            if self.main_window.design_tab is None:
                self.main_window.initialize_tab('design_tools')
                QApplication.processEvents()
                QTest.qWait(500)
                
                # Wait for tab to initialize
                for _ in range(20):
                    QTest.qWait(50)
                    QApplication.processEvents()
                    if self.main_window.design_tab is not None:
                        break
                        
            self.design_tab = self.main_window.design_tab
            
            if self.design_tab is None:
                self.log("ERROR: Failed to initialize Design Tools Tab", "ERROR")
                return False
                
            self.log("Design Tools Tab initialized successfully")
            
            # Create a test pattern if none exists
            if self.design_tab._pattern is None:
                self.log("Creating test pattern...")
                metadata = PatternMetadata(width=8, height=8)
                blank_frame = Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)
                pattern = Pattern(
                    name="Test Pattern",
                    metadata=metadata,
                    frames=[blank_frame]
                )
                self.design_tab._pattern = pattern
                self.design_tab._current_frame_index = 0
                self.log("Test pattern created (8x8, 1 frame)")
            
            return True
            
        except Exception as e:
            self.log(f"ERROR: Failed to set up test environment: {str(e)}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return False
            
    def test_scenario_1_new_pattern(self):
        """Test 1: Generate frames on a new pattern with no existing frames"""
        self.log("=" * 60)
        self.log("Test 1: New Pattern - Generate Frames from Scratch")
        self.log("=" * 60)
        
        try:
            # Create new pattern with single frame
            metadata = PatternMetadata(width=8, height=8)
            blank_frame = Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100)  # Red frame
            pattern = Pattern(
                name="Test Pattern 1",
                metadata=metadata,
                frames=[blank_frame]
            )
            self.design_tab._pattern = pattern
            self.design_tab._current_frame_index = 0
            
            initial_frame_count = len(pattern.frames)
            self.log(f"Initial frame count: {initial_frame_count}")
            
            # Add scroll action
            scroll_action = DesignAction(
                name="Scroll Right",
                action_type="scroll",
                params={
                    "direction": "Right",
                    "repeat": 1,
                    "gap_ms": 0
                }
            )
            self.design_tab.automation_manager.set_actions([scroll_action])
            self.log("Added scroll action (Right, repeat=1)")
            
            # Click "Apply Actions" button
            self.log("Clicking 'Apply Actions' button...")
            if hasattr(self.design_tab, 'apply_actions_btn'):
                self.design_tab.apply_actions_btn.click()
            else:
                # Try to find the button
                for child in self.design_tab.findChildren(QPushButton):
                    if "apply" in child.text().lower() and "action" in child.text().lower():
                        child.click()
                        break
            QApplication.processEvents()
            QTest.qWait(1000)  # Wait for frame generation
            
            final_frame_count = len(self.design_tab._pattern.frames)
            self.log(f"Final frame count: {final_frame_count}")
            
            # Check for duplicates
            duplicates = self.check_duplicate_frames(self.design_tab._pattern.frames)
            
            # Verify results
            passed = True
            message_parts = []
            
            if final_frame_count <= initial_frame_count:
                passed = False
                message_parts.append(f"Expected more frames, got {final_frame_count}")
            else:
                message_parts.append(f"Frame count increased from {initial_frame_count} to {final_frame_count}")
                
            if len(duplicates) > 0:
                passed = False
                message_parts.append(f"Found {len(duplicates)} duplicate frame pairs: {duplicates}")
            else:
                message_parts.append("No duplicate frames detected")
                
            status = "PASS" if passed else "FAIL"
            message = " | ".join(message_parts)
            
            result = TestResult(
                name="Test 1: New Pattern",
                status=status,
                message=message,
                details={
                    "initial_frames": initial_frame_count,
                    "final_frames": final_frame_count,
                    "frames_added": final_frame_count - initial_frame_count,
                    "duplicates": len(duplicates),
                    "duplicate_pairs": duplicates
                }
            )
            self.add_result(result)
            
            if passed:
                self.log(f"✓ Test 1 PASSED: {message}")
            else:
                self.log(f"✗ Test 1 FAILED: {message}", "ERROR")
                
            return passed
            
        except Exception as e:
            self.log(f"ERROR in Test 1: {str(e)}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            result = TestResult(
                name="Test 1: New Pattern",
                status="ERROR",
                message=f"Exception: {str(e)}"
            )
            self.add_result(result)
            return False
            
    def test_scenario_2_existing_frames(self):
        """Test 2: Generate frames when frames already exist"""
        self.log("=" * 60)
        self.log("Test 2: Existing Frames - Append New Frames")
        self.log("=" * 60)
        
        try:
            # Create pattern with multiple existing frames
            metadata = PatternMetadata(width=8, height=8)
            frames = []
            for i in range(3):
                pixels = [(i * 50 % 255, (i * 100) % 255, (i * 150) % 255)] * 64
                frames.append(Frame(pixels=pixels, duration_ms=100))
                
            pattern = Pattern(
                name="Test Pattern 2",
                metadata=metadata,
                frames=frames
            )
            self.design_tab._pattern = pattern
            self.design_tab._current_frame_index = 0
            
            initial_frame_count = len(pattern.frames)
            self.log(f"Initial frame count: {initial_frame_count}")
            
            # Add rotate action
            rotate_action = DesignAction(
                name="Rotate 90° Clockwise",
                action_type="rotate",
                params={
                    "mode": "90° Clockwise",
                    "repeat": 1,
                    "gap_ms": 0
                }
            )
            self.design_tab.automation_manager.set_actions([rotate_action])
            self.log("Added rotate action (90° Clockwise, repeat=1)")
            
            # Click "Apply Actions" button
            self.log("Clicking 'Apply Actions' button...")
            if hasattr(self.design_tab, 'apply_actions_btn'):
                self.design_tab.apply_actions_btn.click()
            else:
                for child in self.design_tab.findChildren(QPushButton):
                    if "apply" in child.text().lower() and "action" in child.text().lower():
                        child.click()
                        break
            QApplication.processEvents()
            QTest.qWait(1000)
            
            final_frame_count = len(self.design_tab._pattern.frames)
            self.log(f"Final frame count: {final_frame_count}")
            
            # Check for duplicates
            duplicates = self.check_duplicate_frames(self.design_tab._pattern.frames)
            
            # Verify results
            passed = True
            message_parts = []
            
            if final_frame_count <= initial_frame_count:
                passed = False
                message_parts.append(f"Expected more frames, got {final_frame_count}")
            else:
                message_parts.append(f"Frames appended: {initial_frame_count} → {final_frame_count}")
                
            if len(duplicates) > 0:
                passed = False
                message_parts.append(f"Found {len(duplicates)} duplicate pairs: {duplicates}")
            else:
                message_parts.append("No duplicates detected")
                
            # Verify existing frames are still there
            if final_frame_count < initial_frame_count:
                passed = False
                message_parts.append("Existing frames were removed (should append only)")
                
            status = "PASS" if passed else "FAIL"
            message = " | ".join(message_parts)
            
            result = TestResult(
                name="Test 2: Existing Frames",
                status=status,
                message=message,
                details={
                    "initial_frames": initial_frame_count,
                    "final_frames": final_frame_count,
                    "frames_added": final_frame_count - initial_frame_count,
                    "duplicates": len(duplicates),
                    "duplicate_pairs": duplicates
                }
            )
            self.add_result(result)
            
            if passed:
                self.log(f"✓ Test 2 PASSED: {message}")
            else:
                self.log(f"✗ Test 2 FAILED: {message}", "ERROR")
                
            return passed
            
        except Exception as e:
            self.log(f"ERROR in Test 2: {str(e)}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            result = TestResult(
                name="Test 2: Existing Frames",
                status="ERROR",
                message=f"Exception: {str(e)}"
            )
            self.add_result(result)
            return False
            
    def test_scenario_3_multiple_actions(self):
        """Test 3: Generate frames with multiple actions"""
        self.log("=" * 60)
        self.log("Test 3: Multiple Actions")
        self.log("=" * 60)
        
        try:
            # Create new pattern
            metadata = PatternMetadata(width=8, height=8)
            blank_frame = Frame(pixels=[(0, 255, 0)] * 64, duration_ms=100)  # Green frame
            pattern = Pattern(
                name="Test Pattern 3",
                metadata=metadata,
                frames=[blank_frame]
            )
            self.design_tab._pattern = pattern
            self.design_tab._current_frame_index = 0
            
            initial_frame_count = len(pattern.frames)
            self.log(f"Initial frame count: {initial_frame_count}")
            
            # Add multiple actions
            scroll_action = DesignAction(
                name="Scroll Right",
                action_type="scroll",
                params={"direction": "Right", "repeat": 1, "gap_ms": 0}
            )
            wipe_action = DesignAction(
                name="Wipe Left to Right",
                action_type="wipe",
                params={"mode": "Left to Right", "repeat": 1, "gap_ms": 0}
            )
            
            self.design_tab.automation_manager.set_actions([scroll_action, wipe_action])
            self.log("Added scroll + wipe actions")
            
            # Click "Apply Actions" button
            self.log("Clicking 'Apply Actions' button...")
            if hasattr(self.design_tab, 'apply_actions_btn'):
                self.design_tab.apply_actions_btn.click()
            else:
                for child in self.design_tab.findChildren(QPushButton):
                    if "apply" in child.text().lower() and "action" in child.text().lower():
                        child.click()
                        break
            QApplication.processEvents()
            QTest.qWait(1500)
            
            final_frame_count = len(self.design_tab._pattern.frames)
            self.log(f"Final frame count: {final_frame_count}")
            
            # Check for duplicates
            duplicates = self.check_duplicate_frames(self.design_tab._pattern.frames)
            
            # Verify results
            passed = True
            message_parts = []
            
            if final_frame_count <= initial_frame_count:
                passed = False
                message_parts.append(f"Expected more frames, got {final_frame_count}")
            else:
                message_parts.append(f"Generated {final_frame_count - initial_frame_count} new frames")
                
            if len(duplicates) > 0:
                passed = False
                message_parts.append(f"Found {len(duplicates)} duplicate pairs")
            else:
                message_parts.append("No duplicates detected")
                
            status = "PASS" if passed else "FAIL"
            message = " | ".join(message_parts)
            
            result = TestResult(
                name="Test 3: Multiple Actions",
                status=status,
                message=message,
                details={
                    "initial_frames": initial_frame_count,
                    "final_frames": final_frame_count,
                    "frames_added": final_frame_count - initial_frame_count,
                    "duplicates": len(duplicates),
                    "duplicate_pairs": duplicates
                }
            )
            self.add_result(result)
            
            if passed:
                self.log(f"✓ Test 3 PASSED: {message}")
            else:
                self.log(f"✗ Test 3 FAILED: {message}", "ERROR")
                
            return passed
            
        except Exception as e:
            self.log(f"ERROR in Test 3: {str(e)}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            result = TestResult(
                name="Test 3: Multiple Actions",
                status="ERROR",
                message=f"Exception: {str(e)}"
            )
            self.add_result(result)
            return False
            
    def run_tests(self):
        """Run all test scenarios"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.test_results.clear()
        self.results_tree.clear()
        self.log_output.clear()
        
        self.log("=" * 60)
        self.log("Starting Automation Duplicate Frames Test Suite")
        self.log("=" * 60)
        self.log("")
        
        # Setup
        self.progress_bar.setValue(10)
        if not self.setup_test_environment():
            self.log("Failed to set up test environment. Aborting.", "ERROR")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return
            
        # Run tests
        results = []
        tests = [
            ("Test 1: New Pattern", self.test_scenario_1_new_pattern),
            ("Test 2: Existing Frames", self.test_scenario_2_existing_frames),
            ("Test 3: Multiple Actions", self.test_scenario_3_multiple_actions),
        ]
        
        total_tests = len(tests)
        for i, (test_name, test_func) in enumerate(tests):
            self.progress_bar.setValue(20 + int((i / total_tests) * 70))
            try:
                result = test_func()
                results.append((test_name, result))
                QTest.qWait(500)  # Brief pause between tests
            except Exception as e:
                self.log(f"ERROR running {test_name}: {str(e)}", "ERROR")
                results.append((test_name, False))
                
        # Summary
        self.progress_bar.setValue(100)
        self.log("")
        self.log("=" * 60)
        self.log("Test Suite Summary")
        self.log("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        failed = total_tests - passed
        
        self.log(f"Total tests: {total_tests}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log("")
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            self.log(f"{test_name}: {status}")
            
        if failed == 0:
            self.log("")
            self.log("✓ All tests passed!")
        else:
            self.log("")
            self.log(f"✗ {failed} test(s) failed")
            
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)


def main():
    """Main entry point"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    window = AutomationDuplicateFramesTest()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()