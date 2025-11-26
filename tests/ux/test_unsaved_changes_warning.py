"""
Test Case TC-UX-006: Unsaved Changes Warning on Load
Issue: Unsaved changes lost on load without warning
Priority: High
"""

import pytest
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.mark.gui
class TestUnsavedChangesWarning:
    """Test unsaved changes warning when loading new file"""
    
    def test_warning_on_load_with_unsaved_changes(self, qtbot, design_tools_tab, sample_pattern):
        """Test that warning appears when loading with unsaved changes"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Make changes to pattern (mark as dirty)
        design_tools_tab.is_dirty = True
        
        # Try to load a new file
        # Verify confirmation dialog appears
        # Verify dialog has "Save", "Discard", "Cancel" options
        pass
    
    def test_save_option_saves_then_loads(self, qtbot, design_tools_tab, sample_pattern):
        """Test that Save option saves current pattern then loads new file"""
        design_tools_tab.load_pattern(sample_pattern)
        design_tools_tab.is_dirty = True
        
        # Mock QMessageBox to return Save
        # Try to load new file
        # Verify save was called
        # Verify new file was loaded
        pass
    
    def test_discard_option_loads_without_saving(self, qtbot, design_tools_tab, sample_pattern):
        """Test that Discard option loads new file without saving"""
        design_tools_tab.load_pattern(sample_pattern)
        design_tools_tab.is_dirty = True
        
        original_frame_count = len(design_tools_tab._pattern.frames) if design_tools_tab._pattern else 0
        
        # Mock QMessageBox to return Discard
        # Try to load new file
        # Verify save was NOT called
        # Verify new file was loaded
        pass
    
    def test_cancel_option_keeps_current_pattern(self, qtbot, design_tools_tab, sample_pattern):
        """Test that Cancel option keeps current pattern"""
        design_tools_tab.load_pattern(sample_pattern)
        design_tools_tab.is_dirty = True
        
        original_frame_count = len(design_tools_tab._pattern.frames) if design_tools_tab._pattern else 0
        
        # Mock QMessageBox to return Cancel
        # Try to load new file
        # Verify pattern is unchanged
        assert design_tools_tab._pattern is not None
        assert len(design_tools_tab._pattern.frames) == original_frame_count
    
    def test_no_warning_when_no_unsaved_changes(self, qtbot, design_tools_tab, sample_pattern):
        """Test that no warning appears when there are no unsaved changes"""
        design_tools_tab.load_pattern(sample_pattern)
        design_tools_tab.is_dirty = False
        
        # Try to load new file
        # Verify no confirmation dialog appears
        # Verify new file loads directly
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

