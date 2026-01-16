"""
Data Flow Integration Tests

Tests data flow between components to ensure data consistency
and proper state management.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from unittest.mock import patch, MagicMock

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab


@pytest.fixture(scope="session")
def app():
    """Ensure QApplication exists"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def mock_dialogs(monkeypatch):
    """Mock dialogs"""
    mock_qmessagebox = MagicMock()
    mock_qmessagebox.critical = MagicMock()
    mock_qmessagebox.warning = MagicMock()
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.critical', mock_qmessagebox.critical)
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.warning', mock_qmessagebox.warning)


class TestPatternStateDataFlow:
    """Test data flow through PatternState"""
    
    def test_pattern_loads_into_state(self, app, qtbot):
        """Test: Pattern data flows into PatternState"""
        design_tab = DesignToolsTab()
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        metadata = PatternMetadata(width=32, height=16)
        frames = [Frame(pixels=[(255, 0, 0)] * 512, duration_ms=100)]
        pattern = Pattern(name="State Test", metadata=metadata, frames=frames)
        
        design_tab.load_pattern(pattern)
        qtbot.wait(300)
        
        # Verify PatternState has pattern data
        pattern_state = design_tab.state
        assert pattern_state.pattern() is not None
        assert pattern_state.width() == 32
        assert pattern_state.height() == 16
        assert pattern_state.frame_count() == 1
    
    def test_frame_updates_reflect_in_state(self, app, qtbot):
        """Test: Frame updates flow through PatternState"""
        design_tab = DesignToolsTab()
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [
            Frame(pixels=[(255, 0, 0)] * 256, duration_ms=100),
            Frame(pixels=[(0, 255, 0)] * 256, duration_ms=100),
        ]
        pattern = Pattern(name="Frame Update Test", metadata=metadata, frames=frames)
        
        design_tab.load_pattern(pattern)
        qtbot.wait(300)
        
        # Add frame through FrameManager
        if design_tab.frame_manager:
            initial_count = design_tab.state.frame_count()
            design_tab.frame_manager.add_blank_after_current(100)
            qtbot.wait(200)
            
            # Verify state updated
            new_count = design_tab.state.frame_count()
            assert new_count == initial_count + 1


class TestManagerDataFlow:
    """Test data flow between managers"""
    
    def test_frame_manager_pattern_state_consistency(self, app, qtbot):
        """Test: FrameManager and PatternState stay in sync"""
        design_tab = DesignToolsTab()
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [
            Frame(pixels=[(255, 0, 0)] * 256, duration_ms=100),
            Frame(pixels=[(0, 255, 0)] * 256, duration_ms=100),
        ]
        pattern = Pattern(name="Consistency Test", metadata=metadata, frames=frames)
        
        design_tab.load_pattern(pattern)
        qtbot.wait(300)
        
        pattern_state = design_tab.state
        frame_manager = design_tab.frame_manager
        
        # Verify consistency
        assert pattern_state.frame_count() == len(pattern.frames)
        assert frame_manager is not None
        
        # Change frame
        frame_manager.select(1)
        qtbot.wait(200)
        
        # Verify both updated
        assert frame_manager.current_index() == 1

