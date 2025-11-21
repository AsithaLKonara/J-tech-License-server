#!/usr/bin/env python3
"""Comprehensive test script for all tabs and features"""
import sys
import traceback
sys.path.insert(0, '.')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import time

# Track errors
errors = []
warnings = []

def log_error(tab_name, feature, error):
    """Log an error"""
    error_msg = f"{tab_name} - {feature}: {type(error).__name__}: {str(error)}"
    errors.append(error_msg)
    print(f"✗ ERROR: {error_msg}")
    traceback.print_exc()

def log_warning(tab_name, feature, warning):
    """Log a warning"""
    warning_msg = f"{tab_name} - {feature}: {warning}"
    warnings.append(warning_msg)
    print(f"⚠ WARNING: {warning_msg}")

def test_tab_import(tab_name, tab_class_name):
    """Test importing a tab"""
    try:
        module_name = f"ui.tabs.{tab_name}"
        module = __import__(module_name, fromlist=[tab_class_name])
        tab_class = getattr(module, tab_class_name)
        print(f"✓ {tab_class_name} imported successfully")
        return tab_class
    except Exception as e:
        log_error(tab_name, "import", e)
        return None

def test_tab_initialization(tab_name, tab_class, app):
    """Test initializing a tab"""
    if tab_class is None:
        return None
    try:
        # Some tabs don't accept parent parameter
        import inspect
        sig = inspect.signature(tab_class.__init__)
        if 'parent' in sig.parameters:
            tab = tab_class(parent=None)
        else:
            tab = tab_class()
        print(f"✓ {tab_class.__name__} initialized successfully")
        return tab
    except Exception as e:
        log_error(tab_name, "initialization", e)
        return None

def test_tab_methods(tab, tab_name, safe_methods):
    """Test calling methods on a tab"""
    for method_name in safe_methods:
        if hasattr(tab, method_name):
            try:
                method = getattr(tab, method_name)
                # Only call methods with no required parameters
                import inspect
                sig = inspect.signature(method)
                required_params = [p for p, param in sig.parameters.items() 
                                 if param.default == inspect.Parameter.empty and p != 'self']
                if not required_params:
                    method()
                    print(f"  ✓ {method_name}()")
            except Exception as e:
                log_error(tab_name, method_name, e)

def test_design_tools_tab(tab, app):
    """Test Design Tools Tab features"""
    print("\n=== Testing Design Tools Tab ===")
    
    # Test basic methods (safe to call)
    safe_methods = [
        "_update_status_labels",
        "_update_transport_controls",
        "_mark_clean",
    ]
    test_tab_methods(tab, "DesignToolsTab", safe_methods)
    
    # Test UI access
    ui_elements = [
        "header_bar", "canvas_panel", "toolbox_container", "timeline_dock",
        "canvas", "timeline", "toolbox_tabs", "layer_panel"
    ]
    
    for element in ui_elements:
        try:
            if hasattr(tab, element):
                getattr(tab, element)
                print(f"  ✓ {element} exists")
            else:
                log_warning("DesignToolsTab", element, "does not exist")
        except Exception as e:
            log_error("DesignToolsTab", f"access {element}", e)
    
    # Test toolbox tabs access
    if hasattr(tab, "toolbox_tabs"):
        try:
            count = tab.toolbox_tabs.count()
            print(f"  ✓ toolbox_tabs has {count} tabs")
            for i in range(count):
                try:
                    widget = tab.toolbox_tabs.widget(i)
                    tab_name = tab.toolbox_tabs.tabText(i)
                    print(f"    ✓ Tab {i}: {tab_name}")
                except Exception as e:
                    log_error("DesignToolsTab", f"access toolbox tab {i}", e)
        except Exception as e:
            log_error("DesignToolsTab", "access toolbox_tabs", e)

def test_preview_tab(tab, app):
    """Test Preview Tab features"""
    print("\n=== Testing Preview Tab ===")
    
    methods_to_test = [
        ("setup_ui", lambda: tab.setup_ui() if hasattr(tab, 'setup_ui') else None),
    ]
    
    for method_name, method_call in methods_to_test:
        try:
            result = method_call()
            if result is not None:
                print(f"  ✓ {method_name}()")
        except Exception as e:
            log_error("PreviewTab", method_name, e)

def test_all_tabs():
    """Test all tabs comprehensively"""
    print("=" * 60)
    print("COMPREHENSIVE TAB TESTING")
    print("=" * 60)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Tab definitions: (tab_name, class_name)
    tabs_to_test = [
        ("media_upload_tab", "MediaUploadTab"),
        ("design_tools_tab", "DesignToolsTab"),
        ("preview_tab", "PreviewTab"),
        ("flash_tab", "FlashTab"),
        ("batch_flash_tab", "BatchFlashTab"),
        ("pattern_library_tab", "PatternLibraryTab"),
        ("audio_reactive_tab", "AudioReactiveTab"),
        ("wifi_upload_tab", "WiFiUploadTab"),
        ("arduino_ide_tab", "ArduinoIDETab"),
        ("esp32_sdcard_tab", "ESP32SDCardTab"),
    ]
    
    initialized_tabs = {}
    imported_classes = {}
    
    # Test imports
    print("\n--- Testing Imports ---")
    for tab_name, tab_class_name in tabs_to_test:
        tab_class = test_tab_import(tab_name, tab_class_name)
        if tab_class:
            imported_classes[tab_name] = tab_class
    
    # Test initialization
    print("\n--- Testing Initialization ---")
    for tab_name, tab_class_name in tabs_to_test:
        if tab_name in imported_classes:
            tab = test_tab_initialization(tab_name, imported_classes[tab_name], app)
            if tab:
                initialized_tabs[tab_name] = tab
    
    # Test specific tab features
    print("\n--- Testing Tab Features ---")
    if "design_tools_tab" in initialized_tabs:
        test_design_tools_tab(initialized_tabs["design_tools_tab"], app)
    
    if "preview_tab" in initialized_tabs:
        test_preview_tab(initialized_tabs["preview_tab"], app)
    
    # Test all tabs for basic UI access
    print("\n--- Testing UI Element Access ---")
    for tab_name, tab in initialized_tabs.items():
        print(f"\n{tab_name}:")
        # Check for common UI elements
        common_elements = ["layout", "widget", "setObjectName"]
        for element in common_elements:
            try:
                if hasattr(tab, element):
                    print(f"  ✓ {element} exists")
            except Exception as e:
                log_error(tab_name, f"check {element}", e)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Errors: {len(errors)}")
    print(f"Total Warnings: {len(warnings)}")
    
    if errors:
        print("\n--- ERRORS FOUND ---")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")
    
    if warnings:
        print("\n--- WARNINGS ---")
        for i, warning in enumerate(warnings, 1):
            print(f"{i}. {warning}")
    
    if not errors:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {len(errors)} error(s) found")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_all_tabs()
    sys.exit(0 if success else 1)

