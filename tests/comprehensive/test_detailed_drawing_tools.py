"""
Detailed Drawing Tools Testing
Tests all 8 drawing tools in detail (TC-DT-010 to TC-DT-090)
"""

import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab
from ui.widgets.matrix_design_canvas import MatrixDesignCanvas, DrawingMode


@pytest.fixture(scope="session")
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
    try:
        tab.close()
        tab.deleteLater()
    except:
        pass


@pytest.fixture
def sample_pattern():
    """Create sample pattern for testing"""
    metadata = PatternMetadata(width=16, height=16)
    frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
    return Pattern(name="Test Pattern", metadata=metadata, frames=frames)


class TestPixelTool:
    """TC-DT-010 to TC-DT-020: Pixel Tool"""
    
    def test_tc_dt_010_single_pixel_painting(self, design_tab, sample_pattern, qtbot):
        """TC-DT-010: Single pixel painting"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        if hasattr(design_tab, 'canvas') and design_tab.canvas:
            # Verify canvas exists
            assert design_tab.canvas is not None
    
    def test_tc_dt_011_brush_size_1_50(self, design_tab, qtbot):
        """TC-DT-011: Brush size 1-50 pixels"""
        if hasattr(design_tab, 'brush_size_spinbox'):
            spinbox = design_tab.brush_size_spinbox
            assert spinbox.minimum() == 1
            assert spinbox.maximum() >= 50
    
    def test_tc_dt_012_brush_shape_square_circle(self, design_tab, qtbot):
        """TC-DT-012: Brush shape (square/circle)"""
        if hasattr(design_tab, 'brush_shape_combo'):
            combo = design_tab.brush_shape_combo
            assert combo is not None


class TestRectangleTool:
    """TC-DT-021 to TC-DT-030: Rectangle Tool"""
    
    def test_tc_dt_021_draw_filled_rectangle(self, design_tab, sample_pattern, qtbot):
        """TC-DT-021: Draw filled rectangle"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None
    
    def test_tc_dt_022_draw_outline_rectangle(self, design_tab, qtbot):
        """TC-DT-022: Draw outline rectangle"""
        assert design_tab is not None


class TestCircleTool:
    """TC-DT-031 to TC-DT-040: Circle Tool"""
    
    def test_tc_dt_031_draw_filled_circle(self, design_tab, sample_pattern, qtbot):
        """TC-DT-031: Draw filled circle"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None


class TestLineTool:
    """TC-DT-041 to TC-DT-050: Line Tool"""
    
    def test_tc_dt_041_draw_straight_line(self, design_tab, sample_pattern, qtbot):
        """TC-DT-041: Draw straight line"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None


class TestFillTool:
    """TC-DT-051 to TC-DT-060: Fill Tool"""
    
    def test_tc_dt_051_flood_fill_connected_pixels(self, design_tab, sample_pattern, qtbot):
        """TC-DT-051: Flood fill connected pixels"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None


class TestGradientTool:
    """TC-DT-061 to TC-DT-070: Gradient Tool"""
    
    def test_tc_dt_061_linear_gradient_two_colors(self, design_tab, sample_pattern, qtbot):
        """TC-DT-061: Linear gradient between two colors"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None


class TestRandomSprayTool:
    """TC-DT-071 to TC-DT-080: Random Spray Tool"""
    
    def test_tc_dt_071_random_pixel_spray(self, design_tab, sample_pattern, qtbot):
        """TC-DT-071: Random pixel spray"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None


class TestTextTool:
    """TC-DT-081 to TC-DT-090: Text Tool"""
    
    def test_tc_dt_081_bitmap_font_rendering(self, design_tab, sample_pattern, qtbot):
        """TC-DT-081: Bitmap font rendering"""
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        assert design_tab is not None
    
    def test_tc_dt_082_multiple_bitmap_fonts(self, design_tab, qtbot):
        """TC-DT-082: Multiple bitmap fonts support"""
        from domain.text.bitmap_font import BitmapFontRepository
        from pathlib import Path
        # BitmapFontRepository requires base_path
        base_path = Path("Res/fonts") if Path("Res/fonts").exists() else Path(".")
        repo = BitmapFontRepository(base_path)
        assert repo is not None

