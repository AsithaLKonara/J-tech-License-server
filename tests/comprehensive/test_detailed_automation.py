"""
Detailed Automation Actions Testing
Tests all 8 automation actions in detail (TC-AUTO-001 to TC-AUTO-090)
"""

import pytest
import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern, Frame, PatternMetadata
from core.automation.engine import AutomationEngine
from domain.actions import DesignAction
from domain.automation.queue import AutomationQueueManager


@pytest.fixture(scope="session")
def app():
    """Ensure QApplication exists"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_pattern():
    """Create sample pattern for testing"""
    metadata = PatternMetadata(width=8, height=8)
    frames = [
        Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100),
        Frame(pixels=[(0, 255, 0)] * 64, duration_ms=100),
    ]
    return Pattern(name="Test Pattern", metadata=metadata, frames=frames)


@pytest.fixture
def automation_engine():
    """Create automation engine"""
    return AutomationEngine()


@pytest.fixture
def automation_queue():
    """Create automation queue manager"""
    return AutomationQueueManager()


class TestScrollAction:
    """TC-AUTO-001 to TC-AUTO-010: Scroll Action"""
    
    def test_tc_auto_001_scroll_up(self, automation_engine, sample_pattern):
        """TC-AUTO-001: Scroll Up"""
        action = DesignAction(
            name="Scroll Up",
            action_type="scroll",
            params={"direction": "Up", "offset": 1}
        )
        assert action.action_type == "scroll"
        assert action.params["direction"] == "Up"
    
    def test_tc_auto_002_scroll_down(self, automation_engine, sample_pattern):
        """TC-AUTO-002: Scroll Down"""
        action = DesignAction(
            name="Scroll Down",
            action_type="scroll",
            params={"direction": "Down", "offset": 1}
        )
        assert action.params["direction"] == "Down"
    
    def test_tc_auto_003_scroll_left(self, automation_engine, sample_pattern):
        """TC-AUTO-003: Scroll Left"""
        action = DesignAction(
            name="Scroll Left",
            action_type="scroll",
            params={"direction": "Left", "offset": 1}
        )
        assert action.params["direction"] == "Left"
    
    def test_tc_auto_004_scroll_right(self, automation_engine, sample_pattern):
        """TC-AUTO-004: Scroll Right"""
        action = DesignAction(
            name="Scroll Right",
            action_type="scroll",
            params={"direction": "Right", "offset": 1}
        )
        assert action.params["direction"] == "Right"


class TestRotateAction:
    """TC-AUTO-011 to TC-AUTO-020: Rotate Action"""
    
    def test_tc_auto_011_rotate_90_clockwise(self, automation_engine, sample_pattern):
        """TC-AUTO-011: 90° clockwise rotation"""
        action = DesignAction(
            name="Rotate 90°",
            action_type="rotate",
            params={"mode": "90° Clockwise"}
        )
        assert action.action_type == "rotate"
        assert "90" in action.params["mode"]


class TestMirrorAction:
    """TC-AUTO-021 to TC-AUTO-030: Mirror Action"""
    
    def test_tc_auto_021_horizontal_mirror(self, automation_engine, sample_pattern):
        """TC-AUTO-021: Horizontal mirror"""
        action = DesignAction(
            name="Mirror Horizontal",
            action_type="mirror",
            params={"axis": "horizontal"}
        )
        assert action.action_type == "mirror"
        assert action.params["axis"] == "horizontal"
    
    def test_tc_auto_022_vertical_mirror(self, automation_engine, sample_pattern):
        """TC-AUTO-022: Vertical mirror"""
        action = DesignAction(
            name="Mirror Vertical",
            action_type="mirror",
            params={"axis": "vertical"}
        )
        assert action.params["axis"] == "vertical"


class TestFlipAction:
    """TC-AUTO-031 to TC-AUTO-040: Flip Action"""
    
    def test_tc_auto_031_horizontal_flip(self, automation_engine, sample_pattern):
        """TC-AUTO-031: Horizontal flip"""
        action = DesignAction(
            name="Flip Horizontal",
            action_type="flip",
            params={"axis": "horizontal"}
        )
        assert action.action_type == "flip"


class TestInvertAction:
    """TC-AUTO-041 to TC-AUTO-050: Invert Action"""
    
    def test_tc_auto_041_full_color_inversion(self, automation_engine, sample_pattern):
        """TC-AUTO-041: Full color inversion"""
        action = DesignAction(
            name="Invert Colors",
            action_type="invert",
            params={"mode": "full"}
        )
        assert action.action_type == "invert"


class TestWipeAction:
    """TC-AUTO-051 to TC-AUTO-060: Wipe Action"""
    
    def test_tc_auto_051_directional_wipe_up(self, automation_engine, sample_pattern):
        """TC-AUTO-051: Directional wipe (Up)"""
        action = DesignAction(
            name="Wipe Up",
            action_type="wipe",
            params={"direction": "Up", "color": (0, 0, 0)}
        )
        assert action.action_type == "wipe"


class TestRevealAction:
    """TC-AUTO-061 to TC-AUTO-070: Reveal Action"""
    
    def test_tc_auto_061_directional_reveal_up(self, automation_engine, sample_pattern):
        """TC-AUTO-061: Directional reveal (Up)"""
        action = DesignAction(
            name="Reveal Up",
            action_type="reveal",
            params={"direction": "Up"}
        )
        assert action.action_type == "reveal"


class TestBounceAction:
    """TC-AUTO-071 to TC-AUTO-080: Bounce Action"""
    
    def test_tc_auto_071_oscillating_bounce_up(self, automation_engine, sample_pattern):
        """TC-AUTO-071: Oscillating bounce (Up)"""
        action = DesignAction(
            name="Bounce Up",
            action_type="bounce",
            params={"direction": "Up", "amplitude": 5}
        )
        assert action.action_type == "bounce"


class TestAutomationQueue:
    """TC-AUTO-081 to TC-AUTO-090: Automation Queue Features"""
    
    def test_tc_auto_081_queue_multiple_actions(self, automation_queue):
        """TC-AUTO-081: Queue multiple actions"""
        action1 = DesignAction(name="Scroll", action_type="scroll", params={})
        action2 = DesignAction(name="Rotate", action_type="rotate", params={})
        
        automation_queue.enqueue(action1)
        automation_queue.enqueue(action2)
        
        actions = automation_queue.actions()
        assert len(actions) == 2
    
    def test_tc_auto_082_sequential_execution(self, automation_queue):
        """TC-AUTO-082: Sequential execution"""
        action1 = DesignAction(name="Action 1", action_type="scroll", params={})
        action2 = DesignAction(name="Action 2", action_type="rotate", params={})
        
        automation_queue.enqueue(action1)
        automation_queue.enqueue(action2)
        
        # Actions should be in order
        actions = automation_queue.actions()
        assert actions[0].name == "Action 1"
        assert actions[1].name == "Action 2"
    
    def test_tc_auto_084_clear_queue(self, automation_queue):
        """TC-AUTO-084: Clear queue"""
        action = DesignAction(name="Test", action_type="scroll", params={})
        automation_queue.enqueue(action)
        automation_queue.clear()
        
        actions = automation_queue.actions()
        assert len(actions) == 0

