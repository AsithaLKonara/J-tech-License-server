"""
L0 Structural Tests: Signal Definitions

Tests that all signals exist and have correct signatures.
"""

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app():
    """Ensure QApplication exists"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestDesignToolsTabSignals:
    """Test DesignToolsTab signal definitions"""
    
    def test_pattern_modified_signal_exists(self, app):
        """pattern_modified signal exists"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        assert hasattr(tab, 'pattern_modified')
        assert isinstance(tab.pattern_modified, Signal)
    
    def test_pattern_created_signal_exists(self, app):
        """pattern_created signal exists"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        assert hasattr(tab, 'pattern_created')
        assert isinstance(tab.pattern_created, Signal)
    
    def test_playback_state_changed_signal_exists(self, app):
        """playback_state_changed signal exists"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        assert hasattr(tab, 'playback_state_changed')
        assert isinstance(tab.playback_state_changed, Signal)
        
        tab.deleteLater()


class TestFrameManagerSignals:
    """Test FrameManager signal definitions"""
    
    def test_frame_index_changed_signal_exists(self, app):
        """frame_index_changed signal exists"""
        from domain.frames import FrameManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = FrameManager(state)
        
        assert hasattr(manager, 'frame_index_changed')
        assert isinstance(manager.frame_index_changed, Signal)
    
    def test_frames_changed_signal_exists(self, app):
        """frames_changed signal exists"""
        from domain.frames import FrameManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = FrameManager(state)
        
        assert hasattr(manager, 'frames_changed')
        assert isinstance(manager.frames_changed, Signal)
    
    def test_frame_duration_changed_signal_exists(self, app):
        """frame_duration_changed signal exists"""
        from domain.frames import FrameManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = FrameManager(state)
        
        assert hasattr(manager, 'frame_duration_changed')
        assert isinstance(manager.frame_duration_changed, Signal)


class TestLayerManagerSignals:
    """Test LayerManager signal definitions"""
    
    def test_layers_changed_signal_exists(self, app):
        """layers_changed signal exists"""
        from domain.layers import LayerManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = LayerManager(state)
        
        assert hasattr(manager, 'layers_changed')
        assert isinstance(manager.layers_changed, Signal)
    
    def test_layer_added_signal_exists(self, app):
        """layer_added signal exists"""
        from domain.layers import LayerManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = LayerManager(state)
        
        assert hasattr(manager, 'layer_added')
        assert isinstance(manager.layer_added, Signal)
    
    def test_frame_pixels_changed_signal_exists(self, app):
        """frame_pixels_changed signal exists"""
        from domain.layers import LayerManager
        from domain.pattern_state import PatternState
        from core.pattern import Pattern, PatternMetadata, Frame
        
        metadata = PatternMetadata(width=16, height=16)
        pattern = Pattern(name="Test", metadata=metadata, frames=[Frame(pixels=[(0,0,0)]*256, duration_ms=100)])
        state = PatternState(pattern)
        manager = LayerManager(state)
        
        assert hasattr(manager, 'frame_pixels_changed')
        assert isinstance(manager.frame_pixels_changed, Signal)


class TestAutomationQueueSignals:
    """Test AutomationQueueManager signal definitions"""
    
    def test_queue_changed_signal_exists(self, app):
        """queue_changed signal exists"""
        from domain.automation.queue import AutomationQueueManager
        
        manager = AutomationQueueManager()
        
        assert hasattr(manager, 'queue_changed')
        assert isinstance(manager.queue_changed, Signal)


class TestCanvasSignals:
    """Test Canvas widget signal definitions"""
    
    def test_pixel_updated_signal_exists(self, app):
        """pixel_updated signal exists on canvas"""
        from ui.tabs.design_tools_tab import DesignToolsTab
        tab = DesignToolsTab()
        
        if hasattr(tab, 'canvas') and tab.canvas:
            assert hasattr(tab.canvas, 'pixel_updated')
            assert isinstance(tab.canvas.pixel_updated, Signal)
        
        tab.deleteLater()


class TestMainWindowSignals:
    """Test MainWindow signal definitions (if any)"""
    
    def test_main_window_signals_exist(self, app):
        """MainWindow signals exist if defined"""
        from ui.main_window import UploadBridgeMainWindow
        window = UploadBridgeMainWindow()
        
        # Check for common signals
        # Implementation dependent
        
        window.close()
        window.deleteLater()

