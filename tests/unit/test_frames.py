from __future__ import annotations

import pytest

from domain.frames import FrameManager
from domain.pattern_state import PatternState


def test_add_blank_frame_updates_count(frame_manager: FrameManager, pattern_state: PatternState):
    initial_count = pattern_state.frame_count()
    emitted_indices = []
    frame_manager.frame_index_changed.connect(emitted_indices.append)

    new_index = frame_manager.add_blank_after_current(80)

    assert pattern_state.frame_count() == initial_count + 1
    assert new_index == frame_manager.current_index()
    assert emitted_indices[-1] == new_index


def test_duplicate_frame_preserves_pixels(frame_manager: FrameManager):
    original = frame_manager.frame()
    duplicate_index = frame_manager.duplicate()
    dup_frame = frame_manager.frame(duplicate_index)

    assert dup_frame.pixels == original.pixels
    assert duplicate_index == frame_manager.current_index()


def test_move_and_delete_frame(frame_manager: FrameManager, pattern_state: PatternState):
    # ensure there are at least 3 frames
    while pattern_state.frame_count() < 3:
        frame_manager.add_blank_after_current(60)

    frame_manager.select(0)
    frame_manager.move(0, 2)
    assert frame_manager.current_index() == 2

    current_count = pattern_state.frame_count()
    frame_manager.delete()
    assert pattern_state.frame_count() == current_count - 1

