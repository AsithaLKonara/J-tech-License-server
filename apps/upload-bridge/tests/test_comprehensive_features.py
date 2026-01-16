#!/usr/bin/env python3
"""Comprehensive feature testing for all tabs"""
import sys
import traceback
sys.path.insert(0, '.')

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import inspect

errors = []
warnings = []

def log_error(tab_name, feature, error):
    error_msg = f"{tab_name} - {feature}: {type(error).__name__}: {str(error)}"
    errors.append(error_msg)
    print(f"✗ {error_msg}")

def log_warning(tab_name, feature, warning):
    warning_msg = f"{tab_name} - {feature}: {warning}"
    warnings.append(warning_msg)
    print(f"⚠ {warning_msg}")

def test_method_call(tab, tab_name, method_name, *args, **kwargs):
    """Safely test calling a method"""
    if not hasattr(tab, method_name):
        return False
    try:
        method = getattr(tab, method_name)
        sig = inspect.signature(method)
        # Check if method can be called with provided args
        required = [p for p, param in sig.parameters.items() 
                   if param.default == inspect.Parameter.empty and p != 'self']
        if len(required) <= len(args):
            method(*args, **kwargs)
            return True
    except Exception as e:
        log_error(tab_name, method_name, e)
        return False
    return False

def test_design_tools_features(tab):
    """Test Design Tools Tab specific features"""
    print("\n=== Design Tools Tab Features ===")
    
    # Test toolbox tab switching
    if hasattr(tab, 'toolbox_tabs'):
        try:
            for i in range(tab.toolbox_tabs.count()):
                tab.toolbox_tabs.setCurrentIndex(i)
                print(f"  ✓ Switched to toolbox tab {i}")
        except Exception as e:
            log_error("DesignToolsTab", "toolbox tab switching", e)
    
    # Test timeline operations
    if hasattr(tab, 'timeline') and hasattr(tab, '_pattern') and tab._pattern:
        try:
            frame_count = len(tab._pattern.frames) if tab._pattern.frames else 0
            if frame_count > 0:
                tab.timeline.set_playhead(0)
                print(f"  ✓ Set timeline playhead to frame 0")
        except Exception as e:
            log_error("DesignToolsTab", "timeline operations", e)
    
    # Test canvas operations
    if hasattr(tab, 'canvas'):
        try:
            tab.canvas.set_matrix_size(16, 16)
            print(f"  ✓ Set canvas size to 16x16")
        except Exception as e:
            log_error("DesignToolsTab", "canvas operations", e)

def test_all_features():
    """Test all features comprehensively"""
    print("=" * 70)
    print("COMPREHENSIVE FEATURE TESTING")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    # Import all tabs
    from ui.tabs.media_upload_tab import MediaUploadTab
    from ui.tabs.design_tools_tab import DesignToolsTab
    from ui.tabs.preview_tab import PreviewTab
    from ui.tabs.flash_tab import FlashTab
    from ui.tabs.batch_flash_tab import BatchFlashTab
    from ui.tabs.pattern_library_tab import PatternLibraryTab
    from ui.tabs.audio_reactive_tab import AudioReactiveTab
    from ui.tabs.wifi_upload_tab import WiFiUploadTab
    from ui.tabs.arduino_ide_tab import ArduinoIDETab
    from ui.tabs.esp32_sdcard_tab import ESP32SDCardTab
    
    tabs = {
        "MediaUploadTab": MediaUploadTab(),
        "DesignToolsTab": DesignToolsTab(),
        "PreviewTab": PreviewTab(),
        "FlashTab": FlashTab(),
        "BatchFlashTab": BatchFlashTab(),
        "PatternLibraryTab": PatternLibraryTab(),
        "AudioReactiveTab": AudioReactiveTab(),
        "WiFiUploadTab": WiFiUploadTab(),
        "ArduinoIDETab": ArduinoIDETab(),
        "ESP32SDCardTab": ESP32SDCardTab(),
    }
    
    print(f"\n✓ Initialized {len(tabs)} tabs")
    
    # Test Design Tools Tab features
    if "DesignToolsTab" in tabs:
        test_design_tools_features(tabs["DesignToolsTab"])
    
    # Test common methods on all tabs
    print("\n=== Testing Common Methods ===")
    common_methods = [
        ("show", []),
        ("hide", []),
        ("setEnabled", [True]),
        ("update", []),
    ]
    
    for tab_name, tab in tabs.items():
        for method_name, args in common_methods:
            test_method_call(tab, tab_name, method_name, *args)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tabs Tested: {len(tabs)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    
    if errors:
        print("\n--- ERRORS ---")
        for i, error in enumerate(errors[:20], 1):  # Show first 20
            print(f"{i}. {error}")
        if len(errors) > 20:
            print(f"... and {len(errors) - 20} more errors")
    
    if warnings:
        print("\n--- WARNINGS ---")
        for i, warning in enumerate(warnings[:10], 1):  # Show first 10
            print(f"{i}. {warning}")
        if len(warnings) > 10:
            print(f"... and {len(warnings) - 10} more warnings")
    
    if not errors:
        print("\n✓ All feature tests passed!")
    else:
        print(f"\n✗ {len(errors)} error(s) found")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = test_all_features()
    sys.exit(0 if success else 1)

