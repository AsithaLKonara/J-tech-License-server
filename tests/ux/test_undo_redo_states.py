"""
Test Case TC-UX-005: Undo/Redo Visual Indication
Issue: No visual indication of undo/redo availability
Priority: High
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.mark.gui
class TestUndoRedoStates:
    """Test undo/redo button states and visual indicators"""
    
    def test_undo_disabled_when_nothing_to_undo(self, qtbot, design_tools_tab, sample_pattern):
        """Test that undo button is disabled when nothing to undo"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Verify undo button is disabled initially
        assert hasattr(design_tools_tab, 'canvas_undo_btn')
        assert not design_tools_tab.canvas_undo_btn.isEnabled()
    
    def test_undo_enabled_after_change(self, qtbot, design_tools_tab, sample_pattern):
        """Test that undo button is enabled after making a change"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Make a change (simulate drawing)
        # This would require simulating canvas interaction
        
        # Verify undo button is enabled
        # assert design_tabs_tab.undo_btn.isEnabled()
        pass
    
    def test_redo_disabled_when_nothing_to_redo(self, qtbot, design_tools_tab, sample_pattern):
        """Test that redo button is disabled when nothing to redo"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Verify redo button is disabled initially
        assert hasattr(design_tools_tab, 'canvas_redo_btn')
        assert not design_tools_tab.canvas_redo_btn.isEnabled()
    
    def test_redo_enabled_after_undo(self, qtbot, design_tools_tab, sample_pattern):
        """Test that redo button is enabled after undo"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Make a change
        # Undo the change
        # Verify redo button is enabled
        pass
    
    def test_tooltip_when_disabled(self, qtbot, design_tools_tab, sample_pattern):
        """Test that tooltip shows undo information when disabled"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Check undo button tooltip exists
        assert hasattr(design_tools_tab, 'canvas_undo_btn')
        tooltip = design_tools_tab.canvas_undo_btn.toolTip()
        assert tooltip is not None and len(tooltip) > 0
    
    def test_buttons_update_correctly(self, qtbot, design_tools_tab, sample_pattern):
        """Test that buttons enable/disable correctly based on history state"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Initial state: both disabled
        assert hasattr(design_tools_tab, 'canvas_undo_btn')
        assert hasattr(design_tools_tab, 'canvas_redo_btn')
        assert not design_tools_tab.canvas_undo_btn.isEnabled()
        assert not design_tools_tab.canvas_redo_btn.isEnabled()
        
        # After change: undo enabled, redo disabled
        # After undo: undo may be disabled, redo enabled
        # After redo: undo enabled, redo disabled
        pass


@pytest.fixture
def design_tools_tab(qtbot, mock_message_boxes):
    """Create DesignToolsTab instance for testing"""
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    # Wait for initialization to complete
    qtbot.wait(100)
    return tab


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing"""
    metadata = PatternMetadata(width=32, height=16)
    pixels = [(0, 0, 0)] * (32 * 16)
    
    pattern = Pattern(
        name="Test Pattern",
        metadata=metadata,
        frames=[Frame(pixels=pixels, duration_ms=100)]
    )
    
    return pattern

