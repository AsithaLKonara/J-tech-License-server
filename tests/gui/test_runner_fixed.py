"""
Test Runner - Fixed version with better timeout handling and non-blocking operations.

This version includes:
- Better timeout handling
- More frequent event processing
- Graceful degradation if initialization fails
- Option to skip full application launch
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, List
from PySide6.QtCore import QObject, Signal, QTimer, QEventLoop, QThread
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from ui.main_window import UploadBridgeMainWindow
from ui.tabs.design_tools_tab import DesignToolsTab
from tests.gui.test_cases import TestCases


class TestRunnerFixed(QObject):
    """Test execution engine with improved timeout handling."""
    
    # Signals
    test_started = Signal(str, str)  # category, feature
    test_completed = Signal(str, str, str, str, str)  # category, feature, status, message, error
    category_completed = Signal(str, int, int)  # category, passed, total
    all_tests_completed = Signal()
    log_message = Signal(str)
    progress_updated = Signal(int)
    finished = Signal()
    
    def __init__(self, skip_app_launch: bool = False, timeout: int = 10000):
        super().__init__()
        self.main_window: Optional[UploadBridgeMainWindow] = None
        self.design_tab: Optional[DesignToolsTab] = None
        self.test_cases: Optional[TestCases] = None
        self.stop_requested = False
        self.total_tests = 157
        self.completed_tests = 0
        self.test_cases_instance: Optional[TestCases] = None
        self.skip_app_launch = skip_app_launch
        self.timeout_ms = timeout
        
    def run_all_tests(self):
        """Run all test categories with improved timeout handling."""
        try:
            app = QApplication.instance()
            if app is None:
                self.log_message.emit("ERROR: QApplication not found. Please run from GUI.")
                self.finished.emit()
                return
            
            if not self.skip_app_launch:
                self.log_message.emit("Launching Upload Bridge application...")
                app.processEvents()
                
                # Launch main window with timeout
                try:
                    self.main_window = UploadBridgeMainWindow()
                    self.main_window.show()
                    app.processEvents()
                    
                    # Wait for window with timeout and frequent event processing
                    start_time = time.time()
                    max_wait = 3.0  # 3 seconds max for window to show
                    
                    while not self.main_window.isVisible() and (time.time() - start_time) < max_wait:
                        QTest.qWait(50)  # Shorter waits
                        app.processEvents()
                        if self.stop_requested:
                            break
                    
                    if not self.main_window.isVisible():
                        self.log_message.emit("WARNING: Window did not become visible in time")
                    
                except Exception as e:
                    self.log_message.emit(f"ERROR: Failed to launch main window: {str(e)}")
                    self.finished.emit()
                    return
                
                # Initialize design tools tab with better timeout handling
                self.log_message.emit("Initializing Design Tools Tab...")
                app.processEvents()
                
                if self.main_window.design_tab is None:
                    try:
                        self.main_window.initialize_tab('design_tools')
                    except Exception as e:
                        self.log_message.emit(f"WARNING: Tab initialization error: {str(e)}")
                
                # Wait for initialization with timeout
                start_time = time.time()
                max_wait = 5.0  # 5 seconds max
                check_interval = 0.1  # Check every 100ms
                
                while self.main_window.design_tab is None and (time.time() - start_time) < max_wait:
                    QTest.qWait(int(check_interval * 1000))
                    app.processEvents()
                    if self.stop_requested:
                        break
                
                self.design_tab = self.main_window.design_tab
                
                if self.design_tab is None:
                    self.log_message.emit("ERROR: Failed to initialize Design Tools Tab within timeout")
                    self.log_message.emit("This may be due to initialization blocking. Try running with --skip-app-launch")
                    self.finished.emit()
                    return
            else:
                # Skip app launch - try to get existing instance
                self.log_message.emit("Skipping application launch - looking for existing instance...")
                app.processEvents()
                
                # Try to find existing design tools tab
                for widget in app.allWidgets():
                    if isinstance(widget, DesignToolsTab):
                        self.design_tab = widget
                        self.log_message.emit("Found existing Design Tools Tab instance")
                        break
                
                if self.design_tab is None:
                    self.log_message.emit("ERROR: No existing Design Tools Tab found")
                    self.log_message.emit("Please launch the application first, or run without --skip-app-launch")
                    self.finished.emit()
                    return
            
            self.log_message.emit("Design Tools Tab initialized successfully")
            self.log_message.emit("")
            app.processEvents()
            
            # Initialize test cases
            self.test_cases = TestCases(self.design_tab, self.log_message, lambda: self.stop_requested)
            self.test_cases_instance = self.test_cases
            
            # Run test categories with frequent event processing
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
                
                # Process events before each category
                app.processEvents()
                
                self.log_message.emit(f"Running {category_name} tests...")
                app.processEvents()
                
                try:
                    test_method()
                except Exception as e:
                    self.log_message.emit(f"ERROR in {category_name}: {str(e)}")
                    import traceback
                    self.log_message.emit(traceback.format_exc())
                
                # Process events after each category
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
            self.finished.emit()
    
    def _test_header_toolbar(self):
        """Test header toolbar features."""
        if self.test_cases:
            self.test_cases.test_header_toolbar(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_toolbox_tabs(self):
        """Test toolbox tabs."""
        if self.test_cases:
            self.test_cases.test_toolbox_tabs(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_drawing_tools(self):
        """Test drawing tools."""
        if self.test_cases:
            self.test_cases.test_drawing_tools(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_canvas_features(self):
        """Test canvas features."""
        if self.test_cases:
            self.test_cases.test_canvas_features(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_timeline_features(self):
        """Test timeline features."""
        if self.test_cases:
            self.test_cases.test_timeline_features(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_layer_system(self):
        """Test layer system."""
        if self.test_cases:
            self.test_cases.test_layer_system(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_automation(self):
        """Test automation features."""
        if self.test_cases:
            self.test_cases.test_automation(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_effects(self):
        """Test effects features."""
        if self.test_cases:
            self.test_cases.test_effects(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_export_import(self):
        """Test export/import features."""
        if self.test_cases:
            self.test_cases.test_export_import(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_scratchpads(self):
        """Test scratchpad features."""
        if self.test_cases:
            self.test_cases.test_scratchpads(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_keyboard_shortcuts(self):
        """Test keyboard shortcuts."""
        if self.test_cases:
            self.test_cases.test_keyboard_shortcuts(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_options_parameters(self):
        """Test options and parameters."""
        if self.test_cases:
            self.test_cases.test_options_parameters(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _test_feature_flows(self):
        """Test feature flows."""
        if self.test_cases:
            self.test_cases.test_feature_flows(
                self.test_started,
                self.test_completed,
                self.category_completed
            )
            self._update_progress()
    
    def _update_progress(self):
        """Update progress based on completed tests."""
        if self.test_cases_instance:
            total_completed = 0
            if hasattr(self.test_cases_instance, 'test_results'):
                for category_results in self.test_cases_instance.test_results.values():
                    total_completed += len(category_results)
            
            progress = min(100, int((total_completed / self.total_tests) * 100))
            self.progress_updated.emit(progress)
        else:
            self.completed_tests += 1
            progress = min(100, int((self.completed_tests / 13) * 100))
            self.progress_updated.emit(progress)

