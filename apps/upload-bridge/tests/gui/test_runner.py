"""
Test Runner - Executes automated tests on Design Tools Tab.

Launches Upload Bridge application and runs all test cases.
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, List
from PySide6.QtCore import QObject, Signal, QTimer, QEventLoop
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from ui.main_window import UploadBridgeMainWindow
from ui.tabs.design_tools_tab import DesignToolsTab
from tests.gui.test_cases import TestCases


class TestRunner(QObject):
    """Test execution engine."""
    
    # Signals
    test_started = Signal(str, str)  # category, feature
    test_completed = Signal(str, str, str, str, str)  # category, feature, status, message, error
    category_completed = Signal(str, int, int)  # category, passed, total
    all_tests_completed = Signal()
    log_message = Signal(str)
    progress_updated = Signal(int)
    finished = Signal()
    
    # Signal to request window creation in main thread
    create_window_requested = Signal()
    window_ready = Signal(object)  # Emits the main_window when ready
    
    def __init__(self):
        super().__init__()
        self.main_window: Optional[UploadBridgeMainWindow] = None
        self.design_tab: Optional[DesignToolsTab] = None
        self.test_cases: Optional[TestCases] = None
        self.stop_requested = False
        self.total_tests = 157  # Total number of tests
        self.completed_tests = 0
        self.test_cases_instance: Optional[TestCases] = None
        self._window_created = False
        
    def set_main_window(self, main_window: UploadBridgeMainWindow):
        """Set the main window (must be called from main thread)."""
        self.main_window = main_window
        self._window_created = True
        
    def run_all_tests(self):
        """Run all test categories."""
        try:
            # Wait for window to be created in main thread
            if not self._window_created:
                self.log_message.emit("Waiting for main window to be created...")
                # Wait up to 10 seconds for window creation
                max_wait = 10000
                waited = 0
                app = QApplication.instance()
                while not self._window_created and waited < max_wait and not self.stop_requested:
                    QTest.qWait(100)
                    waited += 100
                    if app:
                        app.processEvents()
                
                if not self._window_created:
                    self.log_message.emit("ERROR: Main window was not created in time")
                    self.finished.emit()
                    return
            
            if self.main_window is None:
                self.log_message.emit("ERROR: Main window is None")
                self.finished.emit()
                return
            
            self.log_message.emit("Main window ready")
            
            # Get QApplication (should already exist from main GUI)
            app = QApplication.instance()
            if app is None:
                self.log_message.emit("ERROR: QApplication not found. Please run from GUI.")
                self.finished.emit()
                return
            
            # Process events to keep GUI responsive
            app.processEvents()
            
            # Wait for window to be ready (with event processing)
            for _ in range(5):
                QTest.qWait(100)
                app.processEvents()
            
            self.log_message.emit("Initializing Design Tools Tab...")
            
            # Design Tools tab should already be initialized in main thread
            # Just verify it exists
            self.design_tab = self.main_window.design_tab
            
            if self.design_tab is None:
                self.log_message.emit("WARNING: Design Tools Tab not initialized, attempting to initialize...")
                # Last resort: try to initialize (this should not be needed)
                # But we'll try anyway with proper thread safety
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(
                    self.main_window,
                    "initialize_tab",
                    Qt.ConnectionType.QueuedConnection,
                    Qt.Q_ARG(str, "design_tools")
                )
                # Wait briefly
                max_wait = 3000
                waited = 0
                app = QApplication.instance()
                while self.main_window.design_tab is None and waited < max_wait and not self.stop_requested:
                    QTest.qWait(100)
                    waited += 100
                    if app:
                        app.processEvents()
                
                self.design_tab = self.main_window.design_tab
                
                if self.design_tab is None:
                    self.log_message.emit("ERROR: Failed to initialize Design Tools Tab")
                    self.finished.emit()
                    return
            
            self.log_message.emit("Design Tools Tab initialized successfully")
            self.log_message.emit("")
            
            # Initialize test cases with stop flag reference
            self.test_cases = TestCases(self.design_tab, self.log_message, lambda: self.stop_requested)
            self.test_cases_instance = self.test_cases
            
            # Run all test categories
            categories = [
                ("Header Toolbar", self._test_header_toolbar),
                ("Toolbox Tabs", self._test_toolbox_tabs),
                ("Drawing Tools", self._test_drawing_tools),
                ("Canvas Features", self._test_canvas_features),
                ("Timeline Features", self._test_timeline_features),
                ("Layer System", self._test_layer_system),
                ("Automation", self._test_automation),
                ("Effects", self._test_effects),
                ("Export/Import", self._test_export_import),
                ("Scratchpads", self._test_scratchpads),
                ("Keyboard Shortcuts", self._test_keyboard_shortcuts),
                ("Options and Parameters", self._test_options_parameters),
                ("Feature Flows", self._test_feature_flows),
            ]
            
            for category_name, test_method in categories:
                if self.stop_requested:
                    break
                
                # Process events between categories to keep GUI responsive
                app = QApplication.instance()
                if app:
                    app.processEvents()
                    
                self.log_message.emit(f"Running {category_name} tests...")
                test_method()
                
                # Process events after each category
                if app:
                    app.processEvents()
                
                if self.stop_requested:
                    break
            
            self.log_message.emit("")
            self.log_message.emit("All tests completed")
            self.all_tests_completed.emit()
            
        except KeyboardInterrupt:
            self.log_message.emit("Test execution interrupted by user")
            self.stop_requested = True
        except Exception as e:
            self.log_message.emit(f"ERROR: Test execution failed: {str(e)}")
            import traceback
            self.log_message.emit(traceback.format_exc())
        finally:
            # Cleanup
            try:
                if self.main_window:
                    self.log_message.emit("Cleaning up...")
                    # Don't close the window automatically - let user see results
                    # self.main_window.close()
            except Exception as e:
                self.log_message.emit(f"Warning: Cleanup error: {str(e)}")
            finally:
                self.finished.emit()
    
    def _test_header_toolbar(self):
        """Test header toolbar features."""
        self.test_cases.test_header_toolbar(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_toolbox_tabs(self):
        """Test toolbox tabs."""
        self.test_cases.test_toolbox_tabs(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_drawing_tools(self):
        """Test drawing tools."""
        self.test_cases.test_drawing_tools(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_canvas_features(self):
        """Test canvas features."""
        self.test_cases.test_canvas_features(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_timeline_features(self):
        """Test timeline features."""
        self.test_cases.test_timeline_features(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_layer_system(self):
        """Test layer system."""
        self.test_cases.test_layer_system(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_automation(self):
        """Test automation features."""
        self.test_cases.test_automation(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_effects(self):
        """Test effects features."""
        self.test_cases.test_effects(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_export_import(self):
        """Test export/import features."""
        self.test_cases.test_export_import(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_scratchpads(self):
        """Test scratchpad features."""
        self.test_cases.test_scratchpads(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_keyboard_shortcuts(self):
        """Test keyboard shortcuts."""
        self.test_cases.test_keyboard_shortcuts(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_options_parameters(self):
        """Test options and parameters."""
        self.test_cases.test_options_parameters(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _test_feature_flows(self):
        """Test feature flows."""
        self.test_cases.test_feature_flows(
            self.test_started,
            self.test_completed,
            self.category_completed
        )
        self._update_progress()
    
    def _update_progress(self):
        """Update progress based on completed tests."""
        # Calculate progress from test results
        if self.test_cases_instance:
            # Count completed tests from all categories
            total_completed = 0
            for category_results in self.test_cases_instance.test_results.values() if hasattr(self.test_cases_instance, 'test_results') else []:
                total_completed += len(category_results)
            
            progress = min(100, int((total_completed / self.total_tests) * 100))
            self.progress_updated.emit(progress)
        else:
            # Fallback: estimate based on categories completed
            self.completed_tests += 1
            progress = min(100, int((self.completed_tests / 13) * 100))  # 13 categories
            self.progress_updated.emit(progress)

