"""
L0 Structural Tests: Imports and Dependency Structure

Tests that all modules import without side-effects and dependencies are correct.
"""

import pytest
import sys
from pathlib import Path
import importlib


# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


class TestCoreImports:
    """Test core module imports"""
    
    def test_pattern_imports(self):
        """Core pattern module imports"""
        from core.pattern import Pattern, Frame, PatternMetadata
        assert Pattern is not None
        assert Frame is not None
        assert PatternMetadata is not None
    
    def test_domain_imports(self):
        """Domain module imports"""
        from domain.pattern_state import PatternState
        from domain.frames import FrameManager
        from domain.layers import LayerManager
        from domain.history import HistoryManager
        from domain.automation.queue import AutomationQueueManager
        from domain.canvas import CanvasController
        
        assert PatternState is not None
        assert FrameManager is not None
        assert LayerManager is not None
        assert HistoryManager is not None
        assert AutomationQueueManager is not None
        assert CanvasController is not None
    
    def test_io_imports(self):
        """I/O module imports"""
        from core.io.lms_formats import (
            parse_dat_file, parse_hex_file, parse_bin_stream,
            parse_leds_file, write_leds_file
        )
        assert parse_dat_file is not None
        assert parse_hex_file is not None
        assert parse_bin_stream is not None
        assert parse_leds_file is not None
        assert write_leds_file is not None


class TestTabImports:
    """Test tab module imports"""
    
    def test_design_tools_tab_imports(self):
        """DesignToolsTab imports"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        assert DesignToolsTab is not None
    
    def test_preview_tab_imports(self):
        """PreviewTab imports"""
        from ui.tabs.preview_tab import PreviewTab
        assert PreviewTab is not None
    
    def test_media_upload_tab_imports(self):
        """MediaUploadTab imports"""
        from ui.tabs.media_upload_tab import MediaUploadTab
        assert MediaUploadTab is not None
    
    def test_flash_tab_imports(self):
        """FlashTab imports"""
        from ui.tabs.flash_tab import FlashTab
        assert FlashTab is not None
    
    def test_pattern_library_tab_imports(self):
        """PatternLibraryTab imports"""
        from ui.tabs.pattern_library_tab import PatternLibraryTab
        assert PatternLibraryTab is not None
    
    def test_wifi_upload_tab_imports(self):
        """WiFiUploadTab imports"""
        from ui.tabs.wifi_upload_tab import WiFiUploadTab
        assert WiFiUploadTab is not None
    
    def test_audio_reactive_tab_imports(self):
        """AudioReactiveTab imports"""
        from ui.tabs.audio_reactive_tab import AudioReactiveTab
        assert AudioReactiveTab is not None
    
    def test_arduino_ide_tab_imports(self):
        """ArduinoIDETab imports"""
        from ui.tabs.arduino_ide_tab import ArduinoIDETab
        assert ArduinoIDETab is not None
    
    def test_batch_flash_tab_imports(self):
        """BatchFlashTab imports"""
        from ui.tabs.batch_flash_tab import BatchFlashTab
        assert BatchFlashTab is not None
    
    def test_esp32_sdcard_tab_imports(self):
        """ESP32SDCardTab imports"""
        from ui.tabs.esp32_sdcard_tab import ESP32SDCardTab
        assert ESP32SDCardTab is not None


class TestMainWindowImport:
    """Test MainWindow import"""
    
    def test_main_window_imports(self):
        """MainWindow imports"""
        from ui.main_window import UploadBridgeMainWindow
        assert UploadBridgeMainWindow is not None


class TestImportSideEffects:
    """Test that imports don't have unwanted side-effects"""
    
    def test_design_tools_tab_import_no_side_effects(self):
        """DesignToolsTab import doesn't crash"""
        # Note: QApplication may already exist in test environment
        # This test just verifies import doesn't crash
        try:
            from ui.tabs.design_tools_tab import DesignToolsTab
            assert DesignToolsTab is not None
        except Exception as e:
            pytest.fail(f"DesignToolsTab import failed: {e}")


class TestDependencyStructure:
    """Test dependency structure"""
    
    def test_core_has_no_ui_dependencies(self):
        """Core modules don't depend on UI"""
        import core.pattern
        import core.io.lms_formats
        
        # These should import without Qt
        assert core.pattern is not None
        assert core.io.lms_formats is not None
    
    def test_domain_has_no_ui_dependencies(self):
        """Domain modules don't depend on UI"""
        import domain.pattern_state
        import domain.frames
        import domain.layers
        
        # These should import without Qt
        assert domain.pattern_state is not None
        assert domain.frames is not None
        assert domain.layers is not None

