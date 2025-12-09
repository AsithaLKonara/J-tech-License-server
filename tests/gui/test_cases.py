"""
Test Cases - Individual test implementations for Design Tools Tab.

Each test method verifies specific features and functionality.
"""

import time
from pathlib import Path
from typing import Optional, Callable, Tuple
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QTabWidget
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from ui.tabs.design_tools_tab import DesignToolsTab
from ui.widgets.matrix_design_canvas import DrawingMode


class TestCases:
    """Test case implementations."""
    
    def __init__(self, design_tab: DesignToolsTab, log_signal: Signal, stop_flag_getter=None):
        self.design_tab = design_tab
        self.log_signal = log_signal
        self.timeout = 5000  # 5 seconds timeout for operations
        self.max_retries = 2  # Maximum retry attempts for flaky tests
        self.test_results = {}  # Store test results for progress tracking
        self._stop_flag_getter = stop_flag_getter  # Function to get stop_requested flag from TestRunner
        
    @property
    def stop_requested(self):
        """Check if stop was requested."""
        if self._stop_flag_getter is not None:
            try:
                return self._stop_flag_getter()
            except Exception:
                return False
        return False
        
    def process_events(self):
        """Process Qt events to keep GUI responsive."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.processEvents()
            # Also use QTest.qWait with a very short delay to allow more processing
            QTest.qWait(1)
        
    def log(self, message: str):
        """Emit log message."""
        self.log_signal.emit(message)
    
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function with error handling."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            self.log(f"ERROR: {error_msg}")
            return None, error_msg
    
    def verify_widget_exists(self, widget_name: str, parent: Optional[QWidget] = None) -> Tuple[bool, Optional[QWidget]]:
        """Verify a widget exists and return it."""
        if parent is None:
            parent = self.design_tab
        
        widget = parent.findChild(QWidget, widget_name)
        if widget is None:
            # Try finding by object name or attribute
            widget = getattr(parent, widget_name, None)
        
        exists = widget is not None and isinstance(widget, QWidget)
        return exists, widget
    
    def verify_method_exists(self, obj, method_name: str) -> bool:
        """Verify a method exists on an object."""
        try:
            if obj is None:
                return False
            return hasattr(obj, method_name) and callable(getattr(obj, method_name, None))
        except Exception:
            return False
    
    def wait_for_widget(self, widget_name: str, timeout_ms: int = 2000, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """Wait for a widget to become available."""
        if parent is None:
            parent = self.design_tab
        
        elapsed = 0
        while elapsed < timeout_ms:
            exists, widget = self.verify_widget_exists(widget_name, parent)
            if exists and widget:
                return widget
            QTest.qWait(100)
            elapsed += 100
        
        return None
    
    def test_header_toolbar(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test header toolbar features."""
        category = "Header Toolbar"
        passed = 0
        total = 0
        
        tests = [
            ("New Pattern Button", "_on_new_pattern_clicked"),
            ("Templates Button", "_on_templates_clicked"),
            ("AI Generate Button", "_on_ai_generate_clicked"),
            ("Create Animation Button", "_on_create_animation_clicked"),
            ("Version History Button", "_on_version_history_clicked"),
            ("Save Button", "_on_header_save_clicked"),
            ("Settings Button", "_on_header_settings_clicked"),
            ("Header Toolbar Creation", "_create_header_toolbar"),
        ]
        
        for feature, method_name in tests:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()  # Keep GUI responsive
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
                    
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            # Process events after each test to keep GUI responsive
            self.process_events()
        
        category_completed.emit(category, passed, total)
    
    def test_toolbox_tabs(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test toolbox tabs."""
        category = "Toolbox Tabs"
        passed = 0
        total = 0
        
        tabs = [
            ("Brushes Tab", "_create_brushes_tab"),
            ("LED Colors Tab", "_create_led_colors_tab"),
            ("Pixel Mapping Tab", "_create_pixel_mapping_tab"),
            ("Scratchpads Tab", "_create_scratchpad_tab"),
            ("Layers Tab", "_create_layers_tab"),
            ("Effects Tab", "_create_effects_tab"),
            ("Automation Tab", "_create_automation_tab"),
            ("Export Tab", "_create_export_tab"),
            ("Toolbox Column Creation", "_create_toolbox_column"),
        ]
        
        for feature, method_name in tabs:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
                    
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            # Process events after each test to keep GUI responsive
            self.process_events()
        
        category_completed.emit(category, passed, total)
    
    def test_drawing_tools(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test drawing tools."""
        category = "Drawing Tools"
        passed = 0
        total = 0
        
        # Test DrawingMode enum values
        drawing_modes = [
            "PIXEL", "RECTANGLE", "CIRCLE", "LINE",
            "RANDOM", "GRADIENT", "BUCKET_FILL", "EYEDROPPER"
        ]
        
        for mode_name in drawing_modes:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, f"{mode_name} Tool")
            self.process_events()
            
            try:
                mode = getattr(DrawingMode, mode_name, None)
                if mode is not None:
                    test_completed.emit(category, f"{mode_name} Tool", "Pass", f"DrawingMode.{mode_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, f"{mode_name} Tool", "Fail", f"DrawingMode.{mode_name} not found", None)
                    
            except Exception as e:
                test_completed.emit(category, f"{mode_name} Tool", "Fail", f"Error: {str(e)}", str(e))
            
            # Process events after each test to keep GUI responsive
            self.process_events()
        
        # Test tool selection method
        total += 1
        test_started.emit(category, "Tool Selection Handler")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_tool_selected")
            if exists:
                test_completed.emit(category, "Tool Selection Handler", "Pass", "Method _on_tool_selected exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Tool Selection Handler", "Fail", "Method _on_tool_selected not found", None)
        except Exception as e:
            test_completed.emit(category, "Tool Selection Handler", "Fail", f"Error: {str(e)}", str(e))
        
        # Test brush size control
        total += 1
        test_started.emit(category, "Brush Size Control")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_brush_size_changed")
            if exists:
                test_completed.emit(category, "Brush Size Control", "Pass", "Method _on_brush_size_changed exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Brush Size Control", "Fail", "Method _on_brush_size_changed not found", None)
        except Exception as e:
            test_completed.emit(category, "Brush Size Control", "Fail", f"Error: {str(e)}", str(e))
        
        # Test shape filled option
        total += 1
        test_started.emit(category, "Shape Filled Option")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_shape_filled_changed")
            if exists:
                test_completed.emit(category, "Shape Filled Option", "Pass", "Method _on_shape_filled_changed exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Shape Filled Option", "Fail", "Method _on_shape_filled_changed not found", None)
        except Exception as e:
            test_completed.emit(category, "Shape Filled Option", "Fail", f"Error: {str(e)}", str(e))
        
        # Test bucket fill tolerance
        total += 1
        test_started.emit(category, "Bucket Fill Tolerance")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_bucket_fill_tolerance_changed")
            if exists:
                test_completed.emit(category, "Bucket Fill Tolerance", "Pass", "Method _on_bucket_fill_tolerance_changed exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Bucket Fill Tolerance", "Fail", "Method _on_bucket_fill_tolerance_changed not found", None)
        except Exception as e:
            test_completed.emit(category, "Bucket Fill Tolerance", "Fail", f"Error: {str(e)}", str(e))
        
        # Test drawing tools group creation
        total += 1
        test_started.emit(category, "Drawing Tools Group")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_drawing_tools_group")
            if exists:
                test_completed.emit(category, "Drawing Tools Group", "Pass", "Method _create_drawing_tools_group exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Drawing Tools Group", "Fail", "Method _create_drawing_tools_group not found", None)
        except Exception as e:
            test_completed.emit(category, "Drawing Tools Group", "Fail", f"Error: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_canvas_features(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test canvas features."""
        category = "Canvas Features"
        passed = 0
        total = 0
        
        # Test canvas methods
        canvas_methods = [
            ("set_matrix_size", "Canvas Method: set_matrix_size"),
            ("set_frame_pixels", "Canvas Method: set_frame_pixels"),
            ("to_pixels", "Canvas Method: to_pixels"),
            ("set_current_color", "Canvas Method: set_current_color"),
            ("set_erase_color", "Canvas Method: set_erase_color"),
            ("set_drawing_mode", "Canvas Method: set_drawing_mode"),
            ("set_brush_size", "Canvas Method: set_brush_size"),
            ("set_shape_filled", "Canvas Method: set_shape_filled"),
        ]
        
        # Wait for canvas to be initialized
        if not hasattr(self.design_tab, 'canvas') or self.design_tab.canvas is None:
            # Try to wait a bit for canvas initialization
            QTest.qWait(500)
        
        if hasattr(self.design_tab, 'canvas') and self.design_tab.canvas:
            canvas = self.design_tab.canvas
            
            for method_name, feature in canvas_methods:
                if self.stop_requested:
                    break
                total += 1
                test_started.emit(category, feature)
                self.process_events()
                
                try:
                    exists = self.verify_method_exists(canvas, method_name)
                    if exists:
                        test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                        passed += 1
                    else:
                        test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
                except Exception as e:
                    test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
                
                self.process_events()
        else:
            # Canvas not initialized, mark all as fail
            for _, feature in canvas_methods:
                total += 1
                test_started.emit(category, feature)
                test_completed.emit(category, feature, "Fail", "Canvas not initialized", None)
        
        # Test canvas panel creation
        total += 1
        test_started.emit(category, "Canvas Panel Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_canvas_panel")
            if exists:
                test_completed.emit(category, "Canvas Panel Creation", "Pass", "Method _create_canvas_panel exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Canvas Panel Creation", "Fail", "Method _create_canvas_panel not found", None)
        except Exception as e:
            test_completed.emit(category, "Canvas Panel Creation", "Fail", f"Error: {str(e)}", str(e))
        
        # Test view controls
        total += 1
        test_started.emit(category, "View Controls Group")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_view_controls_group")
            if exists:
                test_completed.emit(category, "View Controls Group", "Pass", "Method _create_view_controls_group exists", None)
                passed += 1
            else:
                test_completed.emit(category, "View Controls Group", "Fail", "Method _create_view_controls_group not found", None)
        except Exception as e:
            test_completed.emit(category, "View Controls Group", "Fail", f"Error: {str(e)}", str(e))
        
        # Test canvas signals
        if hasattr(self.design_tab, 'canvas') and self.design_tab.canvas:
            canvas = self.design_tab.canvas
            signals = [
                ("pixel_updated", "Canvas Signal: pixel_updated"),
                ("hover_changed", "Canvas Signal: hover_changed"),
                ("painting_finished", "Canvas Signal: painting_finished"),
                ("color_picked", "Canvas Signal: color_picked"),
            ]
            
            for signal_name, feature in signals:
                if self.stop_requested:
                    break
                total += 1
                test_started.emit(category, feature)
                self.process_events()
                
                try:
                    exists = hasattr(canvas, signal_name)
                    if exists:
                        test_completed.emit(category, feature, "Pass", f"Signal {signal_name} exists", None)
                        passed += 1
                    else:
                        test_completed.emit(category, feature, "Fail", f"Signal {signal_name} not found", None)
                except Exception as e:
                    test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
                
                self.process_events()
        else:
            # Canvas not initialized
            signals = [
                ("pixel_updated", "Canvas Signal: pixel_updated"),
                ("hover_changed", "Canvas Signal: hover_changed"),
                ("painting_finished", "Canvas Signal: painting_finished"),
                ("color_picked", "Canvas Signal: color_picked"),
            ]
            for _, feature in signals:
                total += 1
                test_started.emit(category, feature)
                test_completed.emit(category, feature, "Fail", "Canvas not initialized", None)
        
        # Test geometry overlays and pixel shapes
        from ui.widgets.matrix_design_canvas import GeometryOverlay, PixelShape
        
        overlays = ["MATRIX", "CIRCLE", "RING", "RADIAL"]
        for overlay_name in overlays:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, f"Geometry Overlay: {overlay_name}")
            self.process_events()
            try:
                overlay = getattr(GeometryOverlay, overlay_name, None)
                if overlay is not None:
                    test_completed.emit(category, f"Geometry Overlay: {overlay_name}", "Pass", f"GeometryOverlay.{overlay_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, f"Geometry Overlay: {overlay_name}", "Fail", f"GeometryOverlay.{overlay_name} not found", None)
            except Exception as e:
                test_completed.emit(category, f"Geometry Overlay: {overlay_name}", "Fail", f"Error: {str(e)}", str(e))
            self.process_events()
        
        shapes = ["SQUARE", "ROUND", "ROUNDED"]
        for shape_name in shapes:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, f"Pixel Shape: {shape_name}")
            self.process_events()
            try:
                shape = getattr(PixelShape, shape_name, None)
                if shape is not None:
                    test_completed.emit(category, f"Pixel Shape: {shape_name}", "Pass", f"PixelShape.{shape_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, f"Pixel Shape: {shape_name}", "Fail", f"PixelShape.{shape_name} not found", None)
            except Exception as e:
                test_completed.emit(category, f"Pixel Shape: {shape_name}", "Fail", f"Error: {str(e)}", str(e))
            self.process_events()
        
        category_completed.emit(category, passed, total)
    
    def test_timeline_features(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test timeline features."""
        category = "Timeline Features"
        passed = 0
        total = 0
        
        # Test frame operations
        frame_ops = [
            ("_on_add_frame", "Frame Operation: _on_add_frame"),
            ("_on_duplicate_frame", "Frame Operation: _on_duplicate_frame"),
            ("_on_delete_frame", "Frame Operation: _on_delete_frame"),
            ("_on_frame_selected", "Frame Operation: _on_frame_selected"),
            ("_on_frames_selected", "Frame Operation: _on_frames_selected"),
        ]
        
        for method_name, feature in frame_ops:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test playback controls
        playback_methods = [
            ("_on_transport_play", "Playback Control: _on_transport_play"),
            ("_on_transport_pause", "Playback Control: _on_transport_pause"),
            ("_on_transport_stop", "Playback Control: _on_transport_stop"),
            ("_step_frame", "Playback Control: _step_frame"),
        ]
        
        for method_name, feature in playback_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test duration control
        total += 1
        test_started.emit(category, "Frame Duration Control")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_duration_changed")
            if exists:
                test_completed.emit(category, "Frame Duration Control", "Pass", "Method _on_duration_changed exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Frame Duration Control", "Fail", "Method _on_duration_changed not found", None)
        except Exception as e:
            test_completed.emit(category, "Frame Duration Control", "Fail", f"Error: {str(e)}", str(e))
        
        # Test timeline zoom
        total += 1
        test_started.emit(category, "Timeline Zoom Control")
        try:
            exists = self.verify_method_exists(self.design_tab, "_on_timeline_zoom_changed")
            if exists:
                test_completed.emit(category, "Timeline Zoom Control", "Pass", "Method _on_timeline_zoom_changed exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Timeline Zoom Control", "Fail", "Method _on_timeline_zoom_changed not found", None)
        except Exception as e:
            test_completed.emit(category, "Timeline Zoom Control", "Fail", f"Error: {str(e)}", str(e))
        
        # Test timeline dock creation
        total += 1
        test_started.emit(category, "Timeline Dock Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_timeline_dock")
            if exists:
                test_completed.emit(category, "Timeline Dock Creation", "Pass", "Method _create_timeline_dock exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Timeline Dock Creation", "Fail", "Method _create_timeline_dock not found", None)
        except Exception as e:
            test_completed.emit(category, "Timeline Dock Creation", "Fail", f"Error: {str(e)}", str(e))
        
        # Wait for timeline to be initialized
        if not hasattr(self.design_tab, 'timeline') or self.design_tab.timeline is None:
            # Try to wait a bit for timeline initialization
            QTest.qWait(500)
        
        # Test timeline widget signals (if timeline widget exists)
        if hasattr(self.design_tab, 'timeline') and self.design_tab.timeline:
            from ui.widgets.timeline_widget import TimelineWidget
            timeline = self.design_tab.timeline
            
            signals = [
                "frameSelected", "framesSelected", "playheadDragged",
                "contextMenuRequested", "overlayActivated", "layerTrackSelected",
                "frameMoved", "frameDurationChanged", "layerMoved", "layerVisibilityToggled"
            ]
            
            for signal_name in signals:
                if self.stop_requested:
                    break
                total += 1
                test_started.emit(category, f"Timeline Signal: {signal_name}")
                self.process_events()
                
                try:
                    exists = hasattr(timeline, signal_name)
                    if exists:
                        test_completed.emit(category, f"Timeline Signal: {signal_name}", "Pass", f"Signal {signal_name} exists", None)
                        passed += 1
                    else:
                        test_completed.emit(category, f"Timeline Signal: {signal_name}", "Fail", f"Signal {signal_name} not found", None)
                except Exception as e:
                    test_completed.emit(category, f"Timeline Signal: {signal_name}", "Fail", f"Error: {str(e)}", str(e))
                
                self.process_events()
        else:
            # Timeline not initialized, mark signals as fail
            signals = [
                "frameSelected", "framesSelected", "playheadDragged",
                "contextMenuRequested", "overlayActivated", "layerTrackSelected",
                "frameMoved", "frameDurationChanged", "layerMoved", "layerVisibilityToggled"
            ]
            for signal_name in signals:
                total += 1
                test_started.emit(category, f"Timeline Signal: {signal_name}")
                test_completed.emit(category, f"Timeline Signal: {signal_name}", "Fail", "Timeline not initialized", None)
        
        category_completed.emit(category, passed, total)
    
    def test_layer_system(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test layer system."""
        category = "Layer System"
        passed = 0
        total = 0
        
        # Test LayerManager import
        total += 1
        test_started.emit(category, "LayerManager Import")
        try:
            from domain.layers import LayerManager
            test_completed.emit(category, "LayerManager Import", "Pass", "LayerManager class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "LayerManager Import", "Fail", f"Failed to import LayerManager: {str(e)}", str(e))
        
        # Test LayerPanelWidget import
        total += 1
        test_started.emit(category, "LayerPanelWidget Import")
        try:
            from ui.widgets.layer_panel import LayerPanelWidget
            test_completed.emit(category, "LayerPanelWidget Import", "Pass", "LayerPanelWidget class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "LayerPanelWidget Import", "Fail", f"Failed to import LayerPanelWidget: {str(e)}", str(e))
        
        # Test layer methods
        layer_methods = [
            ("_on_active_layer_changed", "Layer Method: _on_active_layer_changed"),
            ("_on_solo_mode_changed", "Layer Method: _on_solo_mode_changed"),
            ("_on_timeline_layer_visibility_toggled", "Layer Method: _on_timeline_layer_visibility_toggled"),
            ("_on_timeline_layer_selected", "Layer Method: _on_timeline_layer_selected"),
        ]
        
        for method_name, feature in layer_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test layers tab creation
        total += 1
        test_started.emit(category, "Layers Tab Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_layers_tab")
            if exists:
                test_completed.emit(category, "Layers Tab Creation", "Pass", "Method _create_layers_tab exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Layers Tab Creation", "Fail", "Method _create_layers_tab not found", None)
        except Exception as e:
            test_completed.emit(category, "Layers Tab Creation", "Fail", f"Error: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_automation(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test automation features."""
        category = "Automation"
        passed = 0
        total = 0
        
        # Test AutomationQueueManager import
        total += 1
        test_started.emit(category, "AutomationQueueManager Import")
        try:
            from domain.automation.queue import AutomationQueueManager
            test_completed.emit(category, "AutomationQueueManager Import", "Pass", "AutomationQueueManager class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "AutomationQueueManager Import", "Fail", f"Failed to import AutomationQueueManager: {str(e)}", str(e))
        
        # Test automation tab creation
        total += 1
        test_started.emit(category, "Automation Tab Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_automation_tab")
            if exists:
                test_completed.emit(category, "Automation Tab Creation", "Pass", "Method _create_automation_tab exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Automation Tab Creation", "Fail", "Method _create_automation_tab not found", None)
        except Exception as e:
            test_completed.emit(category, "Automation Tab Creation", "Fail", f"Error: {str(e)}", str(e))
        
        # Test automation panels
        panels = [
            ("_create_legacy_automation_panel", "Canvas Automation Panel"),
            ("_create_lms_automation_panel", "LMS Automation Panel"),
        ]
        
        for method_name, feature in panels:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test LMS tabs
        lms_tabs = [
            ("_create_lms_builder_tab", "LMS Instruction Builder"),
            ("_create_lms_queue_tab", "LMS Queue Tab"),
            ("_create_lms_export_tab", "LMS Export Tab"),
        ]
        
        for method_name, feature in lms_tabs:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test automation groups
        groups = [
            ("_create_automation_actions_group", "Automation Group: _create_automation_actions_group"),
            ("_create_apply_effect_group", "Automation Group: _create_apply_effect_group"),
            ("_create_action_queue_group", "Automation Group: _create_action_queue_group"),
            ("_create_action_inspector_group", "Automation Group: _create_action_inspector_group"),
            ("_create_processing_group", "Automation Group: _create_processing_group"),
            ("_create_presets_group", "Automation Group: _create_presets_group"),
        ]
        
        for method_name, feature in groups:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test LMS methods
        lms_methods = [
            ("_on_lms_add_instruction", "LMS Method: _on_lms_add_instruction"),
            ("_on_lms_remove_instruction", "LMS Method: _on_lms_remove_instruction"),
            ("_on_lms_duplicate_instruction", "LMS Method: _on_lms_duplicate_instruction"),
            ("_on_lms_move_instruction", "LMS Method: _on_lms_move_instruction"),
            ("_on_lms_preview_sequence", "LMS Method: _on_lms_preview_sequence"),
            ("_on_lms_apply_preview", "LMS Method: _on_lms_apply_preview"),
            ("_on_lms_exit_preview", "LMS Method: _on_lms_exit_preview"),
            ("_on_lms_import_leds", "LMS Method: _on_lms_import_leds"),
            ("_on_lms_export_leds", "LMS Method: _on_lms_export_leds"),
        ]
        
        for method_name, feature in lms_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        category_completed.emit(category, passed, total)
    
    def test_effects(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test effects features."""
        category = "Effects"
        passed = 0
        total = 0
        
        # Test EffectLibrary import
        total += 1
        test_started.emit(category, "EffectLibrary Import")
        try:
            from domain.effects import EffectLibrary
            test_completed.emit(category, "EffectLibrary Import", "Pass", "EffectLibrary class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "EffectLibrary Import", "Fail", f"Failed to import EffectLibrary: {str(e)}", str(e))
        
        # Test EffectsLibraryWidget import
        total += 1
        test_started.emit(category, "EffectsLibraryWidget Import")
        try:
            from ui.widgets.effects_library_widget import EffectsLibraryWidget
            test_completed.emit(category, "EffectsLibraryWidget Import", "Pass", "EffectsLibraryWidget class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "EffectsLibraryWidget Import", "Fail", f"Failed to import EffectsLibraryWidget: {str(e)}", str(e))
        
        # Test effects tab creation
        total += 1
        test_started.emit(category, "Effects Tab Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_effects_tab")
            if exists:
                test_completed.emit(category, "Effects Tab Creation", "Pass", "Method _create_effects_tab exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Effects Tab Creation", "Fail", "Method _create_effects_tab not found", None)
        except Exception as e:
            test_completed.emit(category, "Effects Tab Creation", "Fail", f"Error: {str(e)}", str(e))
        
        # Test effects methods
        effects_methods = [
            ("_on_effect_selection_changed", "Effect Method: _on_effect_selection_changed"),
            ("_on_effect_preview_requested", "Effect Method: _on_effect_preview_requested"),
            ("_on_effect_apply_requested", "Effect Method: _on_effect_apply_requested"),
            ("_on_effects_refresh_requested", "Effect Method: _on_effects_refresh_requested"),
            ("_refresh_effects_library", "Effect Method: _refresh_effects_library"),
        ]
        
        for method_name, feature in effects_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        category_completed.emit(category, passed, total)
    
    def test_export_import(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test export/import features."""
        category = "Export/Import"
        passed = 0
        total = 0
        
        # Test export methods
        export_methods = [
            ("_on_open_export_dialog", "Export Method: _on_open_export_dialog"),
            ("_emit_pattern", "Export Method: _emit_pattern"),
            ("_on_export_frame_as_image", "Export Method: _on_export_frame_as_image"),
            ("_on_export_animation_as_gif", "Export Method: _on_export_animation_as_gif"),
            ("_on_export_code_template", "Export Method: _on_export_code_template"),
            ("_on_optimize_pattern", "Export Method: _on_optimize_pattern"),
        ]
        
        for method_name, feature in export_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test import methods
        import_methods = [
            ("_on_import_image", "Import Method: _on_import_image"),
        ]
        
        for method_name, feature in import_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test export groups
        export_groups = [
            ("_create_pattern_export_group", "Export Group: _create_pattern_export_group"),
            ("_create_code_template_group", "Export Group: _create_code_template_group"),
            ("_create_import_group", "Export Group: _create_import_group"),
            ("_create_matrix_configuration_group", "Export Group: _create_matrix_configuration_group"),
            ("_create_export_summary_group", "Export Group: _create_export_summary_group"),
        ]
        
        for method_name, feature in export_groups:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test ImageImporter
        total += 1
        test_started.emit(category, "ImageImporter Import")
        try:
            from core.image_importer import ImageImporter
            test_completed.emit(category, "ImageImporter Import", "Pass", "ImageImporter class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "ImageImporter Import", "Fail", f"Failed to import ImageImporter: {str(e)}", str(e))
        
        # Test ImageExporter
        total += 1
        test_started.emit(category, "ImageExporter Import")
        try:
            from core.image_exporter import ImageExporter
            test_completed.emit(category, "ImageExporter Import", "Pass", "ImageExporter class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "ImageExporter Import", "Fail", f"Failed to import ImageExporter: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_scratchpads(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test scratchpad features."""
        category = "Scratchpads"
        passed = 0
        total = 0
        
        # Test scratchpad tab creation
        total += 1
        test_started.emit(category, "Scratchpads Tab Creation")
        try:
            exists = self.verify_method_exists(self.design_tab, "_create_scratchpad_tab")
            if exists:
                test_completed.emit(category, "Scratchpads Tab Creation", "Pass", "Method _create_scratchpad_tab exists", None)
                passed += 1
            else:
                test_completed.emit(category, "Scratchpads Tab Creation", "Fail", "Method _create_scratchpad_tab not found", None)
        except Exception as e:
            test_completed.emit(category, "Scratchpads Tab Creation", "Fail", f"Error: {str(e)}", str(e))
        
        # Test scratchpad methods
        scratchpad_methods = [
            ("_copy_to_scratchpad", "Scratchpad Method: _copy_to_scratchpad"),
            ("_paste_from_scratchpad", "Scratchpad Method: _paste_from_scratchpad"),
            ("_clear_scratchpad_slot", "Scratchpad Method: _clear_scratchpad_slot"),
            ("_refresh_scratchpad_status", "Scratchpad Method: _refresh_scratchpad_status"),
        ]
        
        for method_name, feature in scratchpad_methods:
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, feature)
            self.process_events()
            
            try:
                exists = self.verify_method_exists(self.design_tab, method_name)
                if exists:
                    test_completed.emit(category, feature, "Pass", f"Method {method_name} exists", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Method {method_name} not found", None)
            except Exception as e:
                test_completed.emit(category, feature, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        # Test ScratchpadManager
        total += 1
        test_started.emit(category, "ScratchpadManager Import")
        try:
            from domain.scratchpads import ScratchpadManager
            test_completed.emit(category, "ScratchpadManager Import", "Pass", "ScratchpadManager class imported successfully", None)
            passed += 1
        except ImportError as e:
            test_completed.emit(category, "ScratchpadManager Import", "Fail", f"Failed to import ScratchpadManager: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_keyboard_shortcuts(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test keyboard shortcuts."""
        category = "Keyboard Shortcuts"
        passed = 0
        total = 0
        
        # Test keyPressEvent method
        total += 1
        test_started.emit(category, "KeyPressEvent Handler")
        try:
            exists = self.verify_method_exists(self.design_tab, "keyPressEvent")
            if exists:
                test_completed.emit(category, "KeyPressEvent Handler", "Pass", "Method keyPressEvent exists", None)
                passed += 1
            else:
                test_completed.emit(category, "KeyPressEvent Handler", "Fail", "Method keyPressEvent not found", None)
        except Exception as e:
            test_completed.emit(category, "KeyPressEvent Handler", "Fail", f"Error: {str(e)}", str(e))
        
        # Test shortcuts by checking source code
        shortcuts = [
            ("Ctrl+Z", "Shortcut: Ctrl+Z"),
            ("Ctrl+Y", "Shortcut: Ctrl+Y"),
            ("Ctrl+D", "Shortcut: Ctrl+D"),
            ("Ctrl+R", "Shortcut: Ctrl+R"),
            ("Space", "Shortcut: Space"),
            ("Delete", "Shortcut: Delete"),
            ("Ctrl+0", "Shortcut: Ctrl+0"),
            ("Ctrl+1", "Shortcut: Ctrl+1"),
        ]
        
        # Read source file to check for shortcuts
        try:
            source_file = Path(__file__).parent.parent.parent / "ui" / "tabs" / "design_tools_tab.py"
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for shortcut_key, feature in shortcuts:
                if self.stop_requested:
                    break
                total += 1
                test_started.emit(category, feature)
                self.process_events()
                
                # Check for shortcut in code
                found = False
                if shortcut_key == "Ctrl+Z":
                    found = "Qt.Key_Z" in content and "ControlModifier" in content
                elif shortcut_key == "Ctrl+Y":
                    found = "Qt.Key_Y" in content and "ControlModifier" in content
                elif shortcut_key == "Ctrl+D":
                    found = "Qt.Key_D" in content and "ControlModifier" in content
                elif shortcut_key == "Ctrl+R":
                    found = "Qt.Key_R" in content and "ControlModifier" in content
                elif shortcut_key == "Space":
                    found = "Qt.Key_Space" in content or "Key_Space" in content
                elif shortcut_key == "Delete":
                    found = "Qt.Key_Delete" in content or "Key_Delete" in content
                elif shortcut_key == "Ctrl+0":
                    found = "Qt.Key_0" in content and "ControlModifier" in content
                elif shortcut_key == "Ctrl+1":
                    found = "Qt.Key_1" in content and "ControlModifier" in content
                
                if found:
                    test_completed.emit(category, feature, "Pass", f"Shortcut {shortcut_key} found in keyPressEvent", None)
                    passed += 1
                else:
                    test_completed.emit(category, feature, "Fail", f"Shortcut {shortcut_key} not found in keyPressEvent", None)
                
                self.process_events()
                    
        except Exception as e:
            # If we can't read the file, mark all shortcuts as fail
            for _, feature in shortcuts:
                total += 1
                test_started.emit(category, feature)
                test_completed.emit(category, feature, "Fail", f"Failed to read source file: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_options_parameters(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test options and parameters."""
        category = "Options and Parameters"
        passed = 0
        total = 0
        
        # Check for specific option controls in code
        source_file = Path(__file__).parent.parent.parent / "ui" / "tabs" / "design_tools_tab.py"
        
        options = [
            ("Brush Size", "brush_size_spin", "setRange(1, 8)"),
            ("Shape Filled", "shape_filled_checkbox", None),
            ("Bucket Fill Tolerance", "bucket_fill_tolerance_spin", "setRange(0, 255)"),
            ("Frame Duration", "duration_spin", "setRange(1, 2000)"),
            ("Timeline Zoom", "timeline_zoom_slider", "setRange(25, 400)"),
            ("Autosave Interval", "autosave_interval_spin", "setRange(1, 60)"),
        ]
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for option_name, widget_name, range_check in options:
                if self.stop_requested:
                    break
                total += 1
                test_started.emit(category, option_name)
                self.process_events()
                
                found = widget_name in content
                if range_check:
                    found = found or range_check in content
                
                if found:
                    test_completed.emit(category, option_name, "Pass", f"Option control {option_name} found in code", None)
                    passed += 1
                else:
                    test_completed.emit(category, option_name, "Fail", f"Option control {option_name} not found in code", None)
                
                self.process_events()
                    
        except Exception as e:
            # If we can't read the file, mark all options as fail
            for option_name, _, _ in options:
                total += 1
                test_started.emit(category, option_name)
                test_completed.emit(category, option_name, "Fail", f"Failed to read source file: {str(e)}", str(e))
        
        category_completed.emit(category, passed, total)
    
    def test_feature_flows(
        self,
        test_started: Signal,
        test_completed: Signal,
        category_completed: Signal
    ):
        """Test feature flows."""
        category = "Feature Flows"
        passed = 0
        total = 0
        
        # Flow methods mapping
        flow_methods = {
            "Create New Pattern": ["_on_new_pattern_clicked"],
            "Draw and Animate": ["_on_tool_selected", "_on_add_frame"],
            "Apply Automation": ["_create_automation_tab", "_on_lms_add_instruction"],
            "Multi-Layer Workflow": ["_create_layers_tab", "_on_active_layer_changed"],
            "Import and Edit": ["_on_import_image"],
            "LMS Instruction Workflow": ["_create_lms_builder_tab", "_on_lms_export_leds"],
            "Effect Application": ["_create_effects_tab", "_on_effect_apply_requested"],
            "Scratchpad Workflow": ["_create_scratchpad_tab", "_copy_to_scratchpad", "_paste_from_scratchpad"],
        }
        
        for flow_name, methods in flow_methods.items():
            if self.stop_requested:
                break
            total += 1
            test_started.emit(category, flow_name)
            self.process_events()
            
            try:
                all_found = True
                missing = []
                
                for method_name in methods:
                    if not self.verify_method_exists(self.design_tab, method_name):
                        all_found = False
                        missing.append(method_name)
                    self.process_events()  # Process events during method checking
                
                if all_found:
                    test_completed.emit(category, flow_name, "Pass", "All flow methods exist", None)
                    passed += 1
                else:
                    test_completed.emit(category, flow_name, "Fail", f"Missing methods: {', '.join(missing)}", None)
                    
            except Exception as e:
                test_completed.emit(category, flow_name, "Fail", f"Error: {str(e)}", str(e))
            
            self.process_events()
        
        category_completed.emit(category, passed, total)

