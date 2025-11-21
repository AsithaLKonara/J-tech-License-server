from __future__ import annotations

import pytest

from domain.layers import LayerManager
from domain.pattern_state import PatternState


def test_apply_pixel_updates_frame(layer_manager: LayerManager, pattern_state: PatternState):
    width = pattern_state.width()
    height = pattern_state.height()
    layer_manager.apply_pixel(0, 0, 0, (10, 20, 30), width, height)

    frame = pattern_state.frames()[0]
    assert frame.pixels[0] == (10, 20, 30)


def test_resize_pixels_pads_missing(layer_manager: LayerManager, pattern_state: PatternState):
    layer_manager.resize_pixels(3, 3)
    frame = pattern_state.frames()[0]
    assert len(frame.pixels) == 9
    assert frame.pixels[-1] == (0, 0, 0)

