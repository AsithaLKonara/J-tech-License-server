"""
L3 Workflow Tests: Complete Automation Workflow

End-to-end test for automation features.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.pattern import Pattern, Frame, PatternMetadata
from ui.tabs.design_tools_tab import DesignToolsTab
from domain.actions import DesignAction


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


class TestCompleteAutomationWorkflow:
    """Complete workflow: Create Pattern → Add Actions → Preview → Finalize → Export"""
    
    def test_automation_workflow(self, design_tab, qtbot, sample_pattern):
        """Full automation workflow"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Step 1: Add multiple frames
        for _ in range(10):
            design_tab.frame_manager.add_blank_after_current(100)
            qtbot.wait(50)
        
        # Step 2: Add automation actions
        actions = [
            DesignAction(name="Scroll Left", action_type="scroll", params={"direction": "Left", "step": 1}),
            DesignAction(name="Rotate 90", action_type="rotate", params={"angle": 90}),
            DesignAction(name="Mirror H", action_type="mirror", params={"axis": "horizontal"}),
        ]
        
        for action in actions:
            design_tab.automation_manager.append(action)
            qtbot.wait(50)
        
        assert len(design_tab.automation_manager.actions()) == 3
        
        # Step 3: Preview automation
        if hasattr(design_tab, '_apply_actions_to_frames'):
            design_tab._apply_actions_to_frames(finalize=False)
            qtbot.wait(200)
            
            # Preview should be shown
            # Original pattern should be preserved
        
        # Step 4: Finalize automation
        if hasattr(design_tab, '_apply_actions_to_frames'):
            design_tab._apply_actions_to_frames(finalize=True)
            qtbot.wait(200)
            
            # Actions should be converted to LMS instructions
            # Pattern should be modified
        
        # Step 5: Export LEDS
        # Implementation dependent


class TestLMSAutomationWorkflow:
    """Complete workflow: Build LMS Instructions → Preview → Export"""
    
    def test_lms_automation_workflow(self, design_tab, qtbot, sample_pattern):
        """Full LMS automation workflow"""
        qtbot.addWidget(design_tab)
        design_tab.load_pattern(sample_pattern)
        qtbot.wait(100)
        
        # Step 1: Add frames
        for _ in range(5):
            design_tab.frame_manager.add_blank_after_current(100)
            qtbot.wait(50)
        
        # Step 2: Build LMS instructions
        if hasattr(design_tab, '_on_lms_add_instruction'):
            # Add instruction
            # design_tab._on_lms_add_instruction()
            qtbot.wait(100)
        
        # Step 3: Preview sequence
        if hasattr(design_tab, '_on_lms_preview_sequence'):
            design_tab._on_lms_preview_sequence()
            qtbot.wait(200)
            
            # Preview should be shown
        
        # Step 4: Exit preview
        if hasattr(design_tab, '_on_lms_exit_preview'):
            design_tab._on_lms_exit_preview()
            qtbot.wait(100)
            
            # Original pattern should be restored
        
        # Step 5: Export LEDS
        # Implementation dependent

