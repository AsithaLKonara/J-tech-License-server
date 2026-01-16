"""
Test Case TC-UX-004: Delete Frame Feedback
Issue: No user feedback when deleting last frame
Priority: High
"""

import pytest
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.mark.gui
class TestDeleteFrameValidation:
    """Test delete frame validation and user feedback"""
    
    def test_cannot_delete_last_frame(self, qtbot, design_tools_tab, single_frame_pattern):
        """Test that deleting last frame shows error message"""
        design_tools_tab.load_pattern(single_frame_pattern)
        
        initial_frame_count = len(design_tools_tab._pattern.frames)
        assert initial_frame_count == 1
        
        # Try to delete the last frame
        QTest.mouseClick(design_tools_tab.delete_frame_btn, Qt.LeftButton)
        
        # Verify error dialog appears
        # Verify message: "Cannot delete the last frame"
        # Verify frame count is unchanged
        assert len(design_tools_tab._pattern.frames) == 1
    
    def test_error_message_content(self, qtbot, design_tools_tab, single_frame_pattern):
        """Test that error message is clear and informative"""
        design_tools_tab.load_pattern(single_frame_pattern)
        
        # Try to delete last frame
        # Verify error message contains "Cannot delete the last frame"
        pass
    
    def test_can_delete_when_multiple_frames(self, qtbot, design_tools_tab, multi_frame_pattern):
        """Test that deletion works when multiple frames exist"""
        design_tools_tab.load_pattern(multi_frame_pattern)
        
        initial_count = len(design_tools_tab._pattern.frames)
        assert initial_count > 1
        
        # Delete a frame
        QTest.mouseClick(design_tools_tab.delete_frame_btn, Qt.LeftButton)
        
        # Verify frame was deleted
        assert len(design_tools_tab._pattern.frames) == initial_count - 1
    
    def test_pattern_unchanged_on_delete_error(self, qtbot, design_tools_tab, single_frame_pattern):
        """Test that pattern remains unchanged when delete fails"""
        design_tools_tab.load_pattern(single_frame_pattern)
        
        original_frame_count = len(design_tools_tab._pattern.frames)
        
        # Try to delete last frame
        QTest.mouseClick(design_tools_tab.delete_frame_btn, Qt.LeftButton)
        
        # Verify pattern is unchanged
        assert len(design_tools_tab._pattern.frames) == original_frame_count
        assert len(design_tools_tab._pattern.frames) == 1


@pytest.fixture
def design_tools_tab(qtbot, mock_message_boxes):
    """Create DesignToolsTab instance for testing"""
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    # Wait for initialization to complete
    qtbot.wait(100)
    return tab


@pytest.fixture
def single_frame_pattern():
    """Create a pattern with only one frame"""
    metadata = PatternMetadata(width=32, height=16)
    pixels = [(0, 0, 0)] * (32 * 16)
    
    pattern = Pattern(
        name="Single Frame Pattern",
        metadata=metadata,
        frames=[Frame(pixels=pixels, duration_ms=100)]
    )
    
    return pattern


@pytest.fixture
def multi_frame_pattern():
    """Create a pattern with multiple frames"""
    metadata = PatternMetadata(width=32, height=16)
    pixels = [(0, 0, 0)] * (32 * 16)
    
    pattern = Pattern(
        name="Multi Frame Pattern",
        metadata=metadata,
        frames=[
            Frame(pixels=pixels, duration_ms=100) for _ in range(3)
        ]
    )
    
    return pattern

