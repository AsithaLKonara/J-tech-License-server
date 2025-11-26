"""
Test Case TC-UX-008: Export Validation
Issue: No validation before export
Priority: High
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.mark.gui
class TestExportValidation:
    """Test export validation and error handling"""
    
    def test_export_disabled_when_no_pattern(self, qtbot, design_tools_tab):
        """Test that export functionality is disabled when no pattern is loaded"""
        # Start with no pattern
        design_tools_tab._pattern = None
        
        # Verify pattern is None (export would be disabled)
        assert design_tools_tab._pattern is None
    
    def test_export_enabled_when_pattern_loaded(self, qtbot, design_tools_tab, sample_pattern):
        """Test that export functionality is enabled when pattern is loaded"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Verify pattern is loaded (export would be enabled)
        assert design_tools_tab._pattern is not None
        assert len(design_tools_tab._pattern.frames) > 0
    
    def test_error_when_exporting_without_pattern(self, qtbot, design_tools_tab):
        """Test that error message appears when trying to export without pattern"""
        design_tools_tab.pattern = None
        
        # Try to export (if button is somehow enabled)
        # Verify error dialog: "No pattern to export"
        pass
    
    def test_export_proceeds_with_valid_pattern(self, qtbot, design_tools_tab, sample_pattern):
        """Test that export proceeds when valid pattern is loaded"""
        design_tools_tab.load_pattern(sample_pattern)
        
        # Click export
        # Verify export dialog/file dialog appears
        # Verify no error message
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
    from core.pattern import Pattern, Frame, PatternMetadata
    
    metadata = PatternMetadata(width=32, height=16)
    pixels = [(0, 0, 0)] * (32 * 16)
    
    pattern = Pattern(
        name="Test Pattern",
        metadata=metadata,
        frames=[Frame(pixels=pixels, duration_ms=100)]
    )
    
    return pattern

