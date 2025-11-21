"""
Shared pytest fixtures for the design tools test suite.

These placeholders allow the suite to run (skipped) until real implementations
are available. Replace with full implementations during refactor.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from core.pattern import Frame, Pattern, PatternMetadata
from domain.actions import DesignAction
from domain.automation.queue import AutomationQueueManager
from domain.canvas import CanvasController
from domain.frames import FrameManager
from domain.layers import LayerManager
from domain.pattern_state import PatternState


@pytest.fixture
def pattern_factory() -> Callable[[int, int, int], Pattern]:
    def factory(frame_count: int = 3, width: int = 4, height: int = 1) -> Pattern:
        metadata = PatternMetadata(width=width, height=height)
        frames: List[Frame] = []
        pixels_per_frame = width * height
        for idx in range(frame_count):
            pixels = [(idx * 10 + col, 0, 0) for col in range(pixels_per_frame)]
            frames.append(Frame(pixels=pixels, duration_ms=50))
        return Pattern(name="Test Pattern", metadata=metadata, frames=frames)

    return factory


@pytest.fixture
def pattern_state(pattern_factory) -> PatternState:
    pattern = pattern_factory()
    return PatternState(pattern)


@pytest.fixture
def frame_manager(pattern_state) -> FrameManager:
    manager = FrameManager(pattern_state)
    manager.set_pattern(pattern_state.pattern())
    return manager


@pytest.fixture
def layer_manager(pattern_state) -> LayerManager:
    manager = LayerManager(pattern_state)
    manager.set_pattern(pattern_state.pattern())
    return manager


@pytest.fixture
def automation_manager() -> AutomationQueueManager:
    return AutomationQueueManager()


@pytest.fixture
def canvas_controller(pattern_state) -> CanvasController:
    controller = CanvasController(pattern_state)
    controller.set_frame_supplier(lambda idx: pattern_state.frames()[idx])
    return controller


@pytest.fixture
def sample_action() -> DesignAction:
    return DesignAction(name="Scroll Right", action_type="scroll", params={"direction": "Right"})

