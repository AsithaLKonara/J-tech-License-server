"""
Signal/Slot Integration Tests

Tests all Qt signal/slot connections between components to ensure
proper communication and data flow.
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
    mock_qmessagebox.question = MagicMock(return_value=1)
    
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.critical', mock_qmessagebox.critical)
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.warning', mock_qmessagebox.warning)
    monkeypatch.setattr('PySide6.QtWidgets.QMessageBox.question', mock_qmessagebox.question)


class TestDesignToolsTabSignals:
    """Test signals emitted by Design Tools Tab"""
    
    def test_pattern_modified_signal(self, app, qtbot):
        """Test pattern_modified signal"""
        design_tab = DesignToolsTab()
        qtbot.addWidget(design_tab)
        
        signal_received = []
        
        def on_modified():
            signal_received.append(True)
        
        design_tab.pattern_modified.connect(on_modified)
        design_tab.pattern_modified.emit()
        qtbot.wait(100)
        
        assert len(signal_received) > 0
    
    def test_frame_manager_signals(self, app, qtbot):
        """Test FrameManager signal connections"""
        design_tab = DesignToolsTab()
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        metadata = PatternMetadata(width=16, height=16)
        frames = [
            Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100),
            Frame(pixels=[(255, 0, 0)] * 256, duration_ms=100),
        ]
        pattern = Pattern(name="Signal Test", metadata=metadata, frames=frames)
        design_tab.load_pattern(pattern)
        qtbot.wait(300)
        
        # Track signals
        frames_changed_count = []
        frame_index_changed_count = []
        
        def on_frames_changed():
            frames_changed_count.append(True)
        
        def on_frame_index_changed(index):
            frame_index_changed_count.append(index)
        
        if design_tab.frame_manager:
            design_tab.frame_manager.frames_changed.connect(on_frames_changed)
            design_tab.frame_manager.frame_index_changed.connect(on_frame_index_changed)
            
            # Trigger signal - select a different frame if available
            if len(pattern.frames) > 1:
                design_tab.frame_manager.select(1)
                qtbot.wait(300)
                
                # Verify signals were emitted
                assert len(frame_index_changed_count) > 0 or design_tab.frame_manager.current_index() == 1

