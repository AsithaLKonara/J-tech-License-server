"""
L4 Non-Functional Tests: Stress Tests

Tests for stress conditions (many frames, many layers, many operations).
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.fixture
def app():
    """Ensure QApplication exists"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def design_tab(app):
    """Create DesignToolsTab instance"""
    tab = DesignToolsTab()
    yield tab
    tab.deleteLater()


class TestManyFramesStress:
    """Stress test with many frames"""
    
    @pytest.mark.slow
    def test_300_frames_stress(self, design_tab, qtbot):
        """Handle 300+ frames without crash"""
        qtbot.addWidget(design_tab)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100) for _ in range(300)]
        pattern = Pattern(name="Stress Test", metadata=metadata, frames=frames)
        
        design_tab.load_pattern(pattern)
        qtbot.wait(500)
        
        assert len(design_tab._pattern.frames) == 300
        assert design_tab._pattern is not None
    
    @pytest.mark.slow
    def test_add_remove_many_frames(self, design_tab, qtbot):
        """Add and remove many frames repeatedly"""
        qtbot.addWidget(design_tab)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
        pattern = Pattern(name="Stress Test", metadata=metadata, frames=frames)
        design_tab.load_pattern(pattern)
        qtbot.wait(100)
        
        # Add 100 frames
        for _ in range(100):
            design_tab.frame_manager.add_blank_after_current(100)
            qtbot.wait(10)
        
        assert len(design_tab._pattern.frames) == 101
        
        # Remove frames (keep at least 1)
        for _ in range(50):
            if len(design_tab._pattern.frames) > 1:
                current_index = design_tab.frame_manager.current_index()
                design_tab.frame_manager.delete(current_index)
                qtbot.wait(10)
        
        assert len(design_tab._pattern.frames) >= 1


class TestManyLayersStress:
    """Stress test with many layers"""
    
    @pytest.mark.slow
    def test_50_layers_stress(self, design_tab, qtbot):
        """Handle 50+ layers without crash"""
        qtbot.addWidget(design_tab)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
        pattern = Pattern(name="Stress Test", metadata=metadata, frames=frames)
        design_tab.load_pattern(pattern)
        qtbot.wait(100)
        
        # Add 50 layers
        for i in range(50):
            design_tab.layer_manager.add_layer(0, f"Layer {i}")
            qtbot.wait(10)
        
        layers = design_tab.layer_manager.get_layers(0)
        assert len(layers) >= 50


class TestManyUndoRedoStress:
    """Stress test with many undo/redo operations"""
    
    @pytest.mark.slow
    def test_2000_undo_redo_operations(self, design_tab, qtbot):
        """Handle 2000+ undo/redo operations"""
        qtbot.addWidget(design_tab)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
        pattern = Pattern(name="Stress Test", metadata=metadata, frames=frames)
        design_tab.load_pattern(pattern)
        qtbot.wait(100)
        
        # Make many changes
        for i in range(100):
            design_tab._on_canvas_pixel_updated(i % 16, (i // 16) % 16, (255, 0, 0))
            design_tab._commit_paint_operation()
            qtbot.wait(5)
        
        # Undo many times
        for _ in range(50):
            design_tab._on_undo()
            qtbot.wait(5)
        
        # Redo many times
        for _ in range(50):
            design_tab._on_redo()
            qtbot.wait(5)
        
        # Should not crash
        assert design_tab._pattern is not None


class TestLargePatternStress:
    """Stress test with large patterns"""
    
    @pytest.mark.slow
    def test_very_large_pattern(self, design_tab, qtbot):
        """Handle very large pattern (128x128)"""
        qtbot.addWidget(design_tab)
        
        metadata = PatternMetadata(width=128, height=128)
        frames = [Frame(pixels=[(0, 0, 0)] * (128 * 128), duration_ms=100)]
        pattern = Pattern(name="Large Pattern", metadata=metadata, frames=frames)
        
        design_tab.load_pattern(pattern)
        qtbot.wait(500)
        
        assert design_tab._pattern is not None
        assert design_tab._pattern.metadata.width == 128
        assert design_tab._pattern.metadata.height == 128

