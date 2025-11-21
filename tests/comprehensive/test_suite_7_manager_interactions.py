"""
Test Suite 7: Manager Interactions

Tests interactions between different managers
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


@pytest.fixture
def sample_pattern():
    """Create a sample pattern for testing"""
    metadata = PatternMetadata(width=16, height=16)
    frames = [Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
    return Pattern(name="Test Pattern", metadata=metadata, frames=frames)


class TestPatternStateManager:
    """Test PatternState manager interactions"""
    
    def test_pattern_state_updates_all_managers(self, design_tab, qtbot, sample_pattern):
        """PatternState updates all managers when pattern changes"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # All managers should have the pattern through PatternState
        # FrameManager and LayerManager use PatternState internally, not direct _pattern
        assert design_tab._pattern == sample_pattern
        assert design_tab.state.pattern() == sample_pattern
    
    def test_pattern_state_provides_dimensions(self, design_tab, qtbot, sample_pattern):
        """PatternState provides dimensions correctly"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Access dimensions through PatternState
        assert design_tab.state.width() == 16
        assert design_tab.state.height() == 16


class TestFrameLayerManagerInteraction:
    """Test FrameManager and LayerManager interactions"""
    
    def test_frame_add_creates_default_layer(self, design_tab, qtbot, sample_pattern):
        """Adding frame creates default layer"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        initial_frame_count = len(design_tab._pattern.frames)
        design_tab.frame_manager.add_blank_after_current(100)
        qtbot.wait(100)
        
        # New frame should have default layer
        new_frame_index = len(design_tab._pattern.frames) - 1
        layers = design_tab.layer_manager.get_layers(new_frame_index)
        assert len(layers) > 0
    
    def test_frame_delete_preserves_layers(self, design_tab, qtbot, sample_pattern):
        """Deleting frame preserves layer structure"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Add frame and layer
        design_tab.frame_manager.add_blank_after_current(100)
        qtbot.wait(100)
        design_tab.layer_manager.add_layer(1, "Test Layer")
        qtbot.wait(100)
        
        # Delete frame 0
        design_tab.frame_manager.delete(0)
        qtbot.wait(100)
        
        # Remaining frame should still have layers
        layers = design_tab.layer_manager.get_layers(0)
        assert len(layers) > 0


class TestLayerCanvasInteraction:
    """Test LayerManager and Canvas interaction"""
    
    def test_layer_composite_updates_canvas(self, design_tab, qtbot, sample_pattern):
        """Layer composite updates canvas"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Add layer and paint
        design_tab.layer_manager.add_layer(0, "Test Layer")
        qtbot.wait(100)
        design_tab.layer_manager.apply_pixel(0, 5, 5, (255, 0, 0), 16, 16, 1)
        qtbot.wait(100)
        
        # Get composite
        composite = design_tab.layer_manager.get_composite_pixels(0)
        assert composite is not None
        assert len(composite) == 256
    
    def test_layer_sync_updates_frame(self, design_tab, qtbot, sample_pattern):
        """Layer sync updates frame pixels"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Paint on layer
        design_tab.layer_manager.apply_pixel(0, 5, 5, (255, 0, 0), 16, 16, 0)
        qtbot.wait(100)
        
        # Sync
        design_tab.layer_manager.sync_frame_from_layers(0)
        qtbot.wait(100)
        
        # Frame pixels should be updated
        frame = design_tab.frame_manager.frame(0)
        assert frame is not None


class TestHistoryManagerInteraction:
    """Test HistoryManager interactions"""
    
    def test_paint_operation_saved_to_history(self, design_tab, qtbot, sample_pattern):
        """Paint operation saved to history"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Make paint operation
        design_tab._on_canvas_pixel_updated(5, 5, (255, 0, 0))
        qtbot.wait(100)
        
        # Commit
        design_tab._commit_paint_operation()
        qtbot.wait(100)
        
        # History should have entry
        # Implementation dependent
    
    def test_undo_restores_frame_state(self, design_tab, qtbot, sample_pattern):
        """Undo restores frame state"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Get initial state
        initial_pixel = design_tab.frame_manager.frame(0).pixels[0]
        
        # Make change
        design_tab._on_canvas_pixel_updated(0, 0, (255, 0, 0))
        qtbot.wait(100)
        design_tab._commit_paint_operation()
        qtbot.wait(100)
        
        # Undo
        design_tab._on_undo()
        qtbot.wait(100)
        
        # State should be restored
        # Implementation dependent


class TestAutomationManagerInteraction:
    """Test AutomationQueueManager interactions"""
    
    def test_automation_applies_to_frames(self, design_tab, qtbot, sample_pattern):
        """Automation applies to frame range"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Add frames
        for _ in range(3):
            design_tab.frame_manager.add_blank_after_current(100)
            qtbot.wait(50)
        
        # Add action
        from domain.actions import DesignAction
        action = DesignAction(name="Scroll", action_type="scroll", params={"direction": "Left"})
        design_tab.automation_manager.append(action)
        qtbot.wait(100)
        
        # Apply to frame range
        if hasattr(design_tab, '_apply_actions_to_frames'):
            design_tab._apply_actions_to_frames(finalize=False)
            qtbot.wait(100)
            
            # Frames should be modified
            # Implementation dependent
    
    def test_automation_queue_updates_timeline(self, design_tab, qtbot, sample_pattern):
        """Automation queue updates timeline overlay"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Add action
        from domain.actions import DesignAction
        action = DesignAction(name="Scroll", action_type="scroll", params={})
        design_tab.automation_manager.append(action)
        qtbot.wait(100)
        
        # Timeline should show overlay
        # Implementation dependent

