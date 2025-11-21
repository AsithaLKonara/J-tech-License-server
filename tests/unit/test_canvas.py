from __future__ import annotations

from domain.canvas import CanvasController
from domain.pattern_state import PatternState


def test_canvas_controller_emits_frame(canvas_controller: CanvasController, pattern_state: PatternState):
    captured = []
    canvas_controller.frame_ready.connect(captured.append)

    canvas_controller.render_frame(0)

    assert captured
    frame = captured[0]
    assert frame is pattern_state.frames()[0]

