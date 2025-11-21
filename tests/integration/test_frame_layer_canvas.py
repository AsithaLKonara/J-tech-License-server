from __future__ import annotations

from domain.canvas import CanvasController
from domain.frames import FrameManager
from domain.layers import LayerManager
from domain.pattern_state import PatternState


def test_frame_layer_canvas_integration(
    frame_manager: FrameManager,
    layer_manager: LayerManager,
    canvas_controller: CanvasController,
    pattern_state: PatternState,
):
    captured = []
    canvas_controller.frame_ready.connect(captured.append)

    canvas_controller.render_frame(0)
    assert captured
    original_first_pixel = captured[-1].pixels[0]

    layer_manager.apply_pixel(0, 0, 0, (200, 10, 10), pattern_state.width(), pattern_state.height())
    canvas_controller.render_frame(0)
    assert captured[-1].pixels[0] == (200, 10, 10)

    new_index = frame_manager.duplicate()
    canvas_controller.render_frame(new_index)
    assert captured[-1].pixels[0] == (200, 10, 10)

