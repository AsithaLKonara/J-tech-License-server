#!/usr/bin/env python3
"""
Comprehensive Design Tools Tab Feature Verification Script

Verifies all documented features, tools, flows, and options against actual code implementation.
"""

import os
import sys
import inspect
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

@dataclass
class VerificationResult:
    """Stores verification result for a single check."""
    category: str
    feature: str
    status: str  # "PASS", "FAIL", "PARTIAL", "NOT_FOUND"
    message: str = ""
    details: str = ""
    code_location: str = ""

@dataclass
class VerificationReport:
    """Complete verification report."""
    results: List[VerificationResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=lambda: {"PASS": 0, "FAIL": 0, "PARTIAL": 0, "NOT_FOUND": 0})
    
    def add_result(self, result: VerificationResult):
        """Add a verification result."""
        self.results.append(result)
        self.summary[result.status] = self.summary.get(result.status, 0) + 1

class DesignToolsVerifier:
    """Verifies Design Tools Tab features against code."""
    
    def __init__(self):
        self.report = VerificationReport()
        self.design_tools_tab = None
        self.design_tools_tab_class = None
        self.canvas_class = None
        self.timeline_class = None
        self._load_modules()
    
    def _load_modules(self):
        """Load required modules for verification."""
        try:
            # Use importlib to properly import modules
            import importlib
            
            # Import DesignToolsTab
            design_tools_module = importlib.import_module("ui.tabs.design_tools_tab")
            self.design_tools_tab_class = design_tools_module.DesignToolsTab
            
            # Import MatrixDesignCanvas
            canvas_module = importlib.import_module("ui.widgets.matrix_design_canvas")
            self.canvas_class = canvas_module.MatrixDesignCanvas
            self.drawing_mode_enum = canvas_module.DrawingMode
            self.pixel_shape_enum = canvas_module.PixelShape
            self.geometry_overlay_enum = canvas_module.GeometryOverlay
            
            # Import TimelineWidget
            timeline_module = importlib.import_module("ui.widgets.timeline_widget")
            self.timeline_class = timeline_module.TimelineWidget
            
            print(f"{GREEN}✓ Modules loaded successfully{RESET}\n")
        except Exception as e:
            print(f"{YELLOW}⚠ Warning: Failed to load modules via import: {e}{RESET}")
            print(f"{YELLOW}  Will use source code analysis instead{RESET}\n")
            # Fallback: use source code analysis
            self._load_modules_from_source()
    
    def _load_modules_from_source(self):
        """Fallback: Load class information from source files."""
        import ast
        
        # Create mock classes for source analysis
        class MockClass:
            def __init__(self, name):
                self.__name__ = name
        
        # Read design_tools_tab.py
        design_tools_file = project_root / "ui" / "tabs" / "design_tools_tab.py"
        with open(design_tools_file, 'r', encoding='utf-8') as f:
            design_tools_source = f.read()
        
        # Parse and find DesignToolsTab class
        design_tools_tree = ast.parse(design_tools_source)
        for node in ast.walk(design_tools_tree):
            if isinstance(node, ast.ClassDef) and node.name == "DesignToolsTab":
                self.design_tools_tab_class = MockClass("DesignToolsTab")
                # Store methods
                self.design_tools_tab_class._methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
                break
        
        # Read matrix_design_canvas.py
        canvas_file = project_root / "ui" / "widgets" / "matrix_design_canvas.py"
        with open(canvas_file, 'r', encoding='utf-8') as f:
            canvas_source = f.read()
        
        # Parse and find MatrixDesignCanvas class and enums
        canvas_tree = ast.parse(canvas_source)
        for node in ast.walk(canvas_tree):
            if isinstance(node, ast.ClassDef) and node.name == "MatrixDesignCanvas":
                self.canvas_class = MockClass("MatrixDesignCanvas")
                self.canvas_class._methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
            elif isinstance(node, ast.ClassDef) and node.name == "DrawingMode":
                self.drawing_mode_enum = MockClass("DrawingMode")
                # Extract enum values
                self.drawing_mode_enum._values = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                self.drawing_mode_enum._values.append(target.id)
            elif isinstance(node, ast.ClassDef) and node.name == "PixelShape":
                self.pixel_shape_enum = MockClass("PixelShape")
                self.pixel_shape_enum._values = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                self.pixel_shape_enum._values.append(target.id)
            elif isinstance(node, ast.ClassDef) and node.name == "GeometryOverlay":
                self.geometry_overlay_enum = MockClass("GeometryOverlay")
                self.geometry_overlay_enum._values = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                self.geometry_overlay_enum._values.append(target.id)
        
        # Read timeline_widget.py
        timeline_file = project_root / "ui" / "widgets" / "timeline_widget.py"
        with open(timeline_file, 'r', encoding='utf-8') as f:
            timeline_source = f.read()
        
        timeline_tree = ast.parse(timeline_source)
        for node in ast.walk(timeline_tree):
            if isinstance(node, ast.ClassDef) and node.name == "TimelineWidget":
                self.timeline_class = MockClass("TimelineWidget")
                self.timeline_class._methods = {n.name for n in node.body if isinstance(n, ast.FunctionDef)}
                # Extract signals
                self.timeline_class._signals = []
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and "Signal" in str(item.value):
                                self.timeline_class._signals.append(target.id)
                break
    
    def verify_method_exists(self, obj, method_name: str, category: str, feature: str) -> bool:
        """Verify a method exists on an object."""
        # Check if it's a mock class with _methods attribute
        if hasattr(obj, '_methods'):
            exists = method_name in obj._methods
        else:
            exists = hasattr(obj, method_name) and callable(getattr(obj, method_name, None))
        
        status = "PASS" if exists else "NOT_FOUND"
        location = f"{obj.__name__}.{method_name}" if hasattr(obj, '__name__') else str(type(obj))
        
        self.report.add_result(VerificationResult(
            category=category,
            feature=feature,
            status=status,
            message=f"Method {'exists' if exists else 'not found'}: {method_name}",
            code_location=location
        ))
        return exists
    
    def verify_attribute_exists(self, obj, attr_name: str, category: str, feature: str) -> bool:
        """Verify an attribute exists on an object."""
        # Check if it's a mock class with _signals attribute
        if hasattr(obj, '_signals'):
            exists = attr_name in obj._signals
        else:
            exists = hasattr(obj, attr_name)
        
        status = "PASS" if exists else "NOT_FOUND"
        location = f"{obj.__name__}.{attr_name}" if hasattr(obj, '__name__') else str(type(obj))
        
        self.report.add_result(VerificationResult(
            category=category,
            feature=feature,
            status=status,
            message=f"Attribute {'exists' if exists else 'not found'}: {attr_name}",
            code_location=location
        ))
        return exists
    
    def verify_enum_value(self, enum_class, value_name: str, category: str, feature: str) -> bool:
        """Verify an enum value exists."""
        # Check if it's a mock class with _values attribute
        if hasattr(enum_class, '_values'):
            exists = value_name in enum_class._values
            if exists:
                self.report.add_result(VerificationResult(
                    category=category,
                    feature=feature,
                    status="PASS",
                    message=f"Enum value exists: {value_name}",
                    code_location=f"{enum_class.__name__}.{value_name}"
                ))
                return True
            else:
                self.report.add_result(VerificationResult(
                    category=category,
                    feature=feature,
                    status="NOT_FOUND",
                    message=f"Enum value not found: {value_name}",
                    code_location=f"{enum_class.__name__}"
                ))
                return False
        else:
            try:
                value = getattr(enum_class, value_name)
                self.report.add_result(VerificationResult(
                    category=category,
                    feature=feature,
                    status="PASS",
                    message=f"Enum value exists: {value_name} = {value.value}",
                    code_location=f"{enum_class.__name__}.{value_name}"
                ))
                return True
            except AttributeError:
                self.report.add_result(VerificationResult(
                    category=category,
                    feature=feature,
                    status="NOT_FOUND",
                    message=f"Enum value not found: {value_name}",
                    code_location=f"{enum_class.__name__}"
                ))
                return False
    
    def verify_header_toolbar(self):
        """Verify header toolbar buttons and methods."""
        print(f"{BLUE}Verifying Header Toolbar...{RESET}")
        
        # Expected buttons and their methods
        header_buttons = {
            "New": "_on_new_pattern_clicked",
            "Templates": "_on_templates_clicked",
            "AI Generate": "_on_ai_generate_clicked",
            "Create Animation": "_on_create_animation_clicked",
            "Version History": "_on_version_history_clicked",
            "Save": "_on_header_save_clicked",
            "Settings": "_on_header_settings_clicked",
        }
        
        for button_name, method_name in header_buttons.items():
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Header Toolbar",
                f"{button_name} Button"
            )
        
        # Verify header toolbar creation method
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_header_toolbar",
            "Header Toolbar",
            "Header Toolbar Creation"
        )
        
        print(f"  {GREEN}✓ Header toolbar verification complete{RESET}\n")
    
    def verify_toolbox_tabs(self):
        """Verify all 8 toolbox tabs."""
        print(f"{BLUE}Verifying Toolbox Tabs...{RESET}")
        
        expected_tabs = [
            ("Brushes", "_create_brushes_tab"),
            ("LED Colors", "_create_led_colors_tab"),
            ("Pixel Mapping", "_create_pixel_mapping_tab"),
            ("Scratchpads", "_create_scratchpad_tab"),
            ("Layers", "_create_layers_tab"),
            ("Effects", "_create_effects_tab"),
            ("Automation", "_create_automation_tab"),
            ("Export", "_create_export_tab"),
        ]
        
        for tab_name, method_name in expected_tabs:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Toolbox Tabs",
                f"{tab_name} Tab"
            )
        
        # Verify toolbox column creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_toolbox_column",
            "Toolbox Tabs",
            "Toolbox Column Creation"
        )
        
        print(f"  {GREEN}✓ Toolbox tabs verification complete{RESET}\n")
    
    def verify_drawing_tools(self):
        """Verify all drawing tools."""
        print(f"{BLUE}Verifying Drawing Tools...{RESET}")
        
        # Verify DrawingMode enum values
        expected_modes = [
            "PIXEL", "RECTANGLE", "CIRCLE", "LINE", 
            "RANDOM", "GRADIENT", "BUCKET_FILL", "EYEDROPPER"
        ]
        
        for mode_name in expected_modes:
            self.verify_enum_value(
                self.drawing_mode_enum,
                mode_name,
                "Drawing Tools",
                f"{mode_name} Tool"
            )
        
        # Verify tool selection method
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_tool_selected",
            "Drawing Tools",
            "Tool Selection Handler"
        )
        
        # Verify drawing tools group creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_drawing_tools_group",
            "Drawing Tools",
            "Drawing Tools Group"
        )
        
        # Verify canvas drawing mode methods
        canvas_methods = [
            "set_drawing_mode",
            "set_brush_size",
            "set_shape_filled",
            "set_current_color",
        ]
        
        for method_name in canvas_methods:
            self.verify_method_exists(
                self.canvas_class,
                method_name,
                "Drawing Tools",
                f"Canvas {method_name}"
            )
        
        # Verify brush size options
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_brush_size_changed",
            "Drawing Tools",
            "Brush Size Control"
        )
        
        # Verify shape filled option
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_shape_filled_changed",
            "Drawing Tools",
            "Shape Filled Option"
        )
        
        # Verify bucket fill tolerance
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_bucket_fill_tolerance_changed",
            "Drawing Tools",
            "Bucket Fill Tolerance"
        )
        
        print(f"  {GREEN}✓ Drawing tools verification complete{RESET}\n")
    
    def verify_canvas_features(self):
        """Verify canvas features."""
        print(f"{BLUE}Verifying Canvas Features...{RESET}")
        
        # Verify canvas signals
        canvas_signals = [
            "pixel_updated",
            "hover_changed",
            "painting_finished",
            "color_picked",
        ]
        
        for signal_name in canvas_signals:
            self.verify_attribute_exists(
                self.canvas_class,
                signal_name,
                "Canvas Features",
                f"Canvas Signal: {signal_name}"
            )
        
        # Verify canvas methods
        canvas_methods = [
            "set_matrix_size",
            "set_frame_pixels",
            "to_pixels",
            "set_current_color",
            "set_erase_color",
            "set_drawing_mode",
            "set_brush_size",
            "set_shape_filled",
        ]
        
        for method_name in canvas_methods:
            self.verify_method_exists(
                self.canvas_class,
                method_name,
                "Canvas Features",
                f"Canvas Method: {method_name}"
            )
        
        # Verify PixelShape enum
        pixel_shapes = ["SQUARE", "ROUND", "ROUNDED"]
        for shape_name in pixel_shapes:
            self.verify_enum_value(
                self.pixel_shape_enum,
                shape_name,
                "Canvas Features",
                f"Pixel Shape: {shape_name}"
            )
        
        # Verify GeometryOverlay enum
        overlays = ["MATRIX", "CIRCLE", "RING", "RADIAL"]
        for overlay_name in overlays:
            self.verify_enum_value(
                self.geometry_overlay_enum,
                overlay_name,
                "Canvas Features",
                f"Geometry Overlay: {overlay_name}"
            )
        
        # Verify canvas panel creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_canvas_panel",
            "Canvas Features",
            "Canvas Panel Creation"
        )
        
        # Verify view controls
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_view_controls_group",
            "Canvas Features",
            "View Controls Group"
        )
        
        print(f"  {GREEN}✓ Canvas features verification complete{RESET}\n")
    
    def verify_timeline_features(self):
        """Verify timeline features."""
        print(f"{BLUE}Verifying Timeline Features...{RESET}")
        
        # Verify timeline signals
        timeline_signals = [
            "frameSelected",
            "framesSelected",
            "playheadDragged",
            "contextMenuRequested",
            "overlayActivated",
            "layerTrackSelected",
            "frameMoved",
            "frameDurationChanged",
            "layerMoved",
            "layerVisibilityToggled",
        ]
        
        for signal_name in timeline_signals:
            self.verify_attribute_exists(
                self.timeline_class,
                signal_name,
                "Timeline Features",
                f"Timeline Signal: {signal_name}"
            )
        
        # Verify timeline dock creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_timeline_dock",
            "Timeline Features",
            "Timeline Dock Creation"
        )
        
        # Verify frame operations
        frame_operations = [
            "_on_add_frame",
            "_on_duplicate_frame",
            "_on_delete_frame",
            "_on_frame_selected",
            "_on_frames_selected",
        ]
        
        for method_name in frame_operations:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Timeline Features",
                f"Frame Operation: {method_name}"
            )
        
        # Verify playback controls
        playback_methods = [
            "_on_transport_play",
            "_on_transport_pause",
            "_on_transport_stop",
            "_step_frame",
        ]
        
        for method_name in playback_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Timeline Features",
                f"Playback Control: {method_name}"
            )
        
        # Verify duration control
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_duration_changed",
            "Timeline Features",
            "Frame Duration Control"
        )
        
        # Verify timeline zoom
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_on_timeline_zoom_changed",
            "Timeline Features",
            "Timeline Zoom Control"
        )
        
        print(f"  {GREEN}✓ Timeline features verification complete{RESET}\n")
    
    def verify_layer_system(self):
        """Verify layer system."""
        print(f"{BLUE}Verifying Layer System...{RESET}")
        
        # Verify layer manager import
        try:
            from domain.layers import LayerManager, Layer
            self.report.add_result(VerificationResult(
                category="Layer System",
                feature="LayerManager Import",
                status="PASS",
                message="LayerManager class imported successfully",
                code_location="domain.layers.LayerManager"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Layer System",
                feature="LayerManager Import",
                status="FAIL",
                message=f"Failed to import LayerManager: {e}",
                code_location="domain.layers"
            ))
        
        # Verify layer panel widget
        try:
            from ui.widgets.layer_panel import LayerPanelWidget
            self.report.add_result(VerificationResult(
                category="Layer System",
                feature="LayerPanelWidget Import",
                status="PASS",
                message="LayerPanelWidget class imported successfully",
                code_location="ui.widgets.layer_panel.LayerPanelWidget"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Layer System",
                feature="LayerPanelWidget Import",
                status="FAIL",
                message=f"Failed to import LayerPanelWidget: {e}",
                code_location="ui.widgets.layer_panel"
            ))
        
        # Verify layer-related methods
        layer_methods = [
            "_on_active_layer_changed",
            "_on_solo_mode_changed",
            "_on_timeline_layer_visibility_toggled",
            "_on_timeline_layer_selected",
        ]
        
        for method_name in layer_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Layer System",
                f"Layer Method: {method_name}"
            )
        
        # Verify layer panel creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_layers_tab",
            "Layer System",
            "Layers Tab Creation"
        )
        
        print(f"  {GREEN}✓ Layer system verification complete{RESET}\n")
    
    def verify_automation(self):
        """Verify automation features."""
        print(f"{BLUE}Verifying Automation Features...{RESET}")
        
        # Verify AutomationQueueManager
        try:
            from domain.automation.queue import AutomationQueueManager
            self.report.add_result(VerificationResult(
                category="Automation",
                feature="AutomationQueueManager Import",
                status="PASS",
                message="AutomationQueueManager class imported successfully",
                code_location="domain.automation.queue.AutomationQueueManager"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Automation",
                feature="AutomationQueueManager Import",
                status="FAIL",
                message=f"Failed to import AutomationQueueManager: {e}",
                code_location="domain.automation.queue"
            ))
        
        # Verify automation tab creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_automation_tab",
            "Automation",
            "Automation Tab Creation"
        )
        
        # Verify legacy automation panel
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_legacy_automation_panel",
            "Automation",
            "Canvas Automation Panel"
        )
        
        # Verify LMS automation panel
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_lms_automation_panel",
            "Automation",
            "LMS Automation Panel"
        )
        
        # Verify LMS builder tab
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_lms_builder_tab",
            "Automation",
            "LMS Instruction Builder"
        )
        
        # Verify LMS queue tab
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_lms_queue_tab",
            "Automation",
            "LMS Queue Tab"
        )
        
        # Verify LMS export tab
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_lms_export_tab",
            "Automation",
            "LMS Export Tab"
        )
        
        # Verify automation action groups
        automation_groups = [
            "_create_automation_actions_group",
            "_create_apply_effect_group",
            "_create_action_queue_group",
            "_create_action_inspector_group",
            "_create_processing_group",
            "_create_presets_group",
        ]
        
        for method_name in automation_groups:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Automation",
                f"Automation Group: {method_name}"
            )
        
        # Verify LMS methods
        lms_methods = [
            "_on_lms_add_instruction",
            "_on_lms_remove_instruction",
            "_on_lms_duplicate_instruction",
            "_on_lms_move_instruction",
            "_on_lms_preview_sequence",
            "_on_lms_apply_preview",
            "_on_lms_exit_preview",
            "_on_lms_import_leds",
            "_on_lms_export_leds",
        ]
        
        for method_name in lms_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Automation",
                f"LMS Method: {method_name}"
            )
        
        print(f"  {GREEN}✓ Automation features verification complete{RESET}\n")
    
    def verify_effects(self):
        """Verify effects features."""
        print(f"{BLUE}Verifying Effects Features...{RESET}")
        
        # Verify EffectLibrary
        try:
            from domain.effects import EffectLibrary, EffectDefinition
            self.report.add_result(VerificationResult(
                category="Effects",
                feature="EffectLibrary Import",
                status="PASS",
                message="EffectLibrary class imported successfully",
                code_location="domain.effects.EffectLibrary"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Effects",
                feature="EffectLibrary Import",
                status="FAIL",
                message=f"Failed to import EffectLibrary: {e}",
                code_location="domain.effects"
            ))
        
        # Verify EffectsLibraryWidget
        try:
            from ui.widgets.effects_library_widget import EffectsLibraryWidget
            self.report.add_result(VerificationResult(
                category="Effects",
                feature="EffectsLibraryWidget Import",
                status="PASS",
                message="EffectsLibraryWidget class imported successfully",
                code_location="ui.widgets.effects_library_widget.EffectsLibraryWidget"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Effects",
                feature="EffectsLibraryWidget Import",
                status="FAIL",
                message=f"Failed to import EffectsLibraryWidget: {e}",
                code_location="ui.widgets.effects_library_widget"
            ))
        
        # Verify effects tab creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_effects_tab",
            "Effects",
            "Effects Tab Creation"
        )
        
        # Verify effects methods
        effects_methods = [
            "_on_effect_selection_changed",
            "_on_effect_preview_requested",
            "_on_effect_apply_requested",
            "_on_effects_refresh_requested",
            "_refresh_effects_library",
        ]
        
        for method_name in effects_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Effects",
                f"Effect Method: {method_name}"
            )
        
        print(f"  {GREEN}✓ Effects features verification complete{RESET}\n")
    
    def verify_export_import(self):
        """Verify export/import features."""
        print(f"{BLUE}Verifying Export/Import Features...{RESET}")
        
        # Verify export methods
        export_methods = [
            "_on_open_export_dialog",
            "_emit_pattern",
            "_on_export_frame_as_image",
            "_on_export_animation_as_gif",
            "_on_export_code_template",
            "_on_optimize_pattern",
        ]
        
        for method_name in export_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Export/Import",
                f"Export Method: {method_name}"
            )
        
        # Verify import methods
        import_methods = [
            "_on_import_image",
        ]
        
        for method_name in import_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Export/Import",
                f"Import Method: {method_name}"
            )
        
        # Verify export groups
        export_groups = [
            "_create_pattern_export_group",
            "_create_code_template_group",
            "_create_import_group",
            "_create_matrix_configuration_group",
            "_create_export_summary_group",
        ]
        
        for method_name in export_groups:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Export/Import",
                f"Export Group: {method_name}"
            )
        
        # Verify ImageImporter
        try:
            from core.image_importer import ImageImporter
            self.report.add_result(VerificationResult(
                category="Export/Import",
                feature="ImageImporter Import",
                status="PASS",
                message="ImageImporter class imported successfully",
                code_location="core.image_importer.ImageImporter"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Export/Import",
                feature="ImageImporter Import",
                status="FAIL",
                message=f"Failed to import ImageImporter: {e}",
                code_location="core.image_importer"
            ))
        
        # Verify ImageExporter
        try:
            from core.image_exporter import ImageExporter
            self.report.add_result(VerificationResult(
                category="Export/Import",
                feature="ImageExporter Import",
                status="PASS",
                message="ImageExporter class imported successfully",
                code_location="core.image_exporter.ImageExporter"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Export/Import",
                feature="ImageExporter Import",
                status="FAIL",
                message=f"Failed to import ImageExporter: {e}",
                code_location="core.image_exporter"
            ))
        
        print(f"  {GREEN}✓ Export/Import features verification complete{RESET}\n")
    
    def verify_scratchpads(self):
        """Verify scratchpad features."""
        print(f"{BLUE}Verifying Scratchpads Features...{RESET}")
        
        # Verify scratchpad tab creation
        self.verify_method_exists(
            self.design_tools_tab_class,
            "_create_scratchpad_tab",
            "Scratchpads",
            "Scratchpads Tab Creation"
        )
        
        # Verify scratchpad methods
        scratchpad_methods = [
            "_copy_to_scratchpad",
            "_paste_from_scratchpad",
            "_clear_scratchpad_slot",
            "_refresh_scratchpad_status",
        ]
        
        for method_name in scratchpad_methods:
            self.verify_method_exists(
                self.design_tools_tab_class,
                method_name,
                "Scratchpads",
                f"Scratchpad Method: {method_name}"
            )
        
        # Verify ScratchpadManager
        try:
            from domain.scratchpads import ScratchpadManager
            self.report.add_result(VerificationResult(
                category="Scratchpads",
                feature="ScratchpadManager Import",
                status="PASS",
                message="ScratchpadManager class imported successfully",
                code_location="domain.scratchpads.ScratchpadManager"
            ))
        except ImportError as e:
            self.report.add_result(VerificationResult(
                category="Scratchpads",
                feature="ScratchpadManager Import",
                status="FAIL",
                message=f"Failed to import ScratchpadManager: {e}",
                code_location="domain.scratchpads"
            ))
        
        print(f"  {GREEN}✓ Scratchpads features verification complete{RESET}\n")
    
    def verify_keyboard_shortcuts(self):
        """Verify keyboard shortcuts."""
        print(f"{BLUE}Verifying Keyboard Shortcuts...{RESET}")
        
        # Verify keyPressEvent method
        self.verify_method_exists(
            self.design_tools_tab_class,
            "keyPressEvent",
            "Keyboard Shortcuts",
            "KeyPressEvent Handler"
        )
        
        # Read keyPressEvent implementation to check shortcuts
        try:
            source_file = project_root / "ui" / "tabs" / "design_tools_tab.py"
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for documented shortcuts
            shortcuts_to_check = {
                "Ctrl+Z": "Ctrl+Z" in content or "Qt.Key_Z" in content,
                "Ctrl+Y": "Ctrl+Y" in content or "Qt.Key_Y" in content,
                "Ctrl+D": "Ctrl+D" in content or "Qt.Key_D" in content,
                "Ctrl+R": "Ctrl+R" in content or "Qt.Key_R" in content,
                "Space": "Qt.Key_Space" in content or "Key_Space" in content,
                "Delete": "Qt.Key_Delete" in content or "Key_Delete" in content,
                "Ctrl+0": "Ctrl+0" in content or "Qt.Key_0" in content,
                "Ctrl+1": "Ctrl+1" in content or "Qt.Key_1" in content,
            }
            
            for shortcut, found in shortcuts_to_check.items():
                status = "PASS" if found else "PARTIAL"
                self.report.add_result(VerificationResult(
                    category="Keyboard Shortcuts",
                    feature=f"Shortcut: {shortcut}",
                    status=status,
                    message=f"Shortcut {'found' if found else 'not found'} in keyPressEvent",
                    code_location="DesignToolsTab.keyPressEvent"
                ))
        except Exception as e:
            self.report.add_result(VerificationResult(
                category="Keyboard Shortcuts",
                feature="Shortcut Verification",
                status="FAIL",
                message=f"Failed to read source file: {e}",
                code_location="design_tools_tab.py"
            ))
        
        print(f"  {GREEN}✓ Keyboard shortcuts verification complete{RESET}\n")
    
    def verify_options_parameters(self):
        """Verify options and parameters."""
        print(f"{BLUE}Verifying Options and Parameters...{RESET}")
        
        # Check for specific option controls in code
        source_file = project_root / "ui" / "tabs" / "design_tools_tab.py"
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for documented options
            options_to_check = {
                "Brush Size": "brush_size_spin" in content or "setRange(1, 8)" in content,
                "Shape Filled": "shape_filled_checkbox" in content,
                "Bucket Fill Tolerance": "bucket_fill_tolerance_spin" in content or "setRange(0, 255)" in content,
                "Frame Duration": "duration_spin" in content or "setRange(1, 2000)" in content,
                "Timeline Zoom": "timeline_zoom_slider" in content or "setRange(25, 400)" in content,
                "Autosave Interval": "autosave_interval_spin" in content or "setRange(1, 60)" in content,
            }
            
            for option_name, found in options_to_check.items():
                status = "PASS" if found else "PARTIAL"
                self.report.add_result(VerificationResult(
                    category="Options and Parameters",
                    feature=option_name,
                    status=status,
                    message=f"Option control {'found' if found else 'not found'} in code",
                    code_location="DesignToolsTab"
                ))
        except Exception as e:
            self.report.add_result(VerificationResult(
                category="Options and Parameters",
                feature="Option Verification",
                status="FAIL",
                message=f"Failed to read source file: {e}",
                code_location="design_tools_tab.py"
            ))
        
        print(f"  {GREEN}✓ Options and parameters verification complete{RESET}\n")
    
    def verify_flows(self):
        """Verify documented flows."""
        print(f"{BLUE}Verifying Feature Flows...{RESET}")
        
        # Verify flow methods exist
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
            all_found = True
            missing = []
            for method_name in methods:
                # Use verify_method_exists to check
                if hasattr(self.design_tools_tab_class, '_methods'):
                    # Mock class
                    found = method_name in self.design_tools_tab_class._methods
                else:
                    found = hasattr(self.design_tools_tab_class, method_name)
                
                if not found:
                    all_found = False
                    missing.append(method_name)
            
            status = "PASS" if all_found else "PARTIAL"
            message = "All flow methods exist" if all_found else f"Missing methods: {', '.join(missing)}"
            
            self.report.add_result(VerificationResult(
                category="Feature Flows",
                feature=flow_name,
                status=status,
                message=message,
                code_location="DesignToolsTab"
            ))
        
        print(f"  {GREEN}✓ Feature flows verification complete{RESET}\n")
    
    def verify_all(self):
        """Run all verification checks."""
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Design Tools Tab - Comprehensive Feature Verification{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        self.verify_header_toolbar()
        self.verify_toolbox_tabs()
        self.verify_drawing_tools()
        self.verify_canvas_features()
        self.verify_timeline_features()
        self.verify_layer_system()
        self.verify_automation()
        self.verify_effects()
        self.verify_export_import()
        self.verify_scratchpads()
        self.verify_keyboard_shortcuts()
        self.verify_options_parameters()
        self.verify_flows()
        
        return self.report
    
    def generate_report(self) -> str:
        """Generate markdown report."""
        report_lines = []
        report_lines.append("# Design Tools Tab - Feature Verification Report")
        report_lines.append("")
        report_lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Verifier**: Automated Verification Script")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        
        # Summary
        total = sum(self.report.summary.values())
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Checks**: {total}")
        report_lines.append(f"- **Passed**: {self.report.summary.get('PASS', 0)} ({self.report.summary.get('PASS', 0)*100//total if total > 0 else 0}%)")
        report_lines.append(f"- **Failed**: {self.report.summary.get('FAIL', 0)}")
        report_lines.append(f"- **Partial**: {self.report.summary.get('PARTIAL', 0)}")
        report_lines.append(f"- **Not Found**: {self.report.summary.get('NOT_FOUND', 0)}")
        report_lines.append("")
        
        # Group by category
        categories = {}
        for result in self.report.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in sorted(categories.items()):
            report_lines.append(f"## {category}")
            report_lines.append("")
            
            passed = sum(1 for r in results if r.status == "PASS")
            failed = sum(1 for r in results if r.status == "FAIL")
            partial = sum(1 for r in results if r.status == "PARTIAL")
            not_found = sum(1 for r in results if r.status == "NOT_FOUND")
            
            report_lines.append(f"**Status**: {passed}/{len(results)} passed, {failed} failed, {partial} partial, {not_found} not found")
            report_lines.append("")
            report_lines.append("| Feature | Status | Message | Code Location |")
            report_lines.append("|---------|--------|---------|---------------|")
            
            for result in sorted(results, key=lambda x: x.feature):
                status_icon = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "PARTIAL": "⚠️",
                    "NOT_FOUND": "🔍"
                }.get(result.status, "❓")
                
                report_lines.append(
                    f"| {result.feature} | {status_icon} {result.status} | {result.message} | `{result.code_location}` |"
                )
            
            report_lines.append("")
        
        return "\n".join(report_lines)

def main():
    """Main verification function."""
    verifier = DesignToolsVerifier()
    report = verifier.verify_all()
    
    # Generate and save report
    report_md = verifier.generate_report()
    report_file = project_root / "docs" / "DESIGN_TOOLS_VERIFICATION_REPORT.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    # Print summary
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Verification Complete{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    total = sum(report.summary.values())
    print(f"Total Checks: {total}")
    print(f"{GREEN}Passed: {report.summary.get('PASS', 0)}{RESET} ({report.summary.get('PASS', 0)*100//total if total > 0 else 0}%)")
    print(f"{RED}Failed: {report.summary.get('FAIL', 0)}{RESET}")
    print(f"{YELLOW}Partial: {report.summary.get('PARTIAL', 0)}{RESET}")
    print(f"{BLUE}Not Found: {report.summary.get('NOT_FOUND', 0)}{RESET}")
    print(f"\nReport saved to: {report_file}\n")
    
    return 0 if report.summary.get('FAIL', 0) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

