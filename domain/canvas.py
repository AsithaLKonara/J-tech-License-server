from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal

from core.pattern import Frame
from domain.pattern_state import PatternState


class CanvasController(QObject):
    """
    Bridges pattern data to the rendering canvas.
    Emits a signal when a new frame should be presented.
    """

    frame_ready = Signal(Frame)

    def __init__(self, state: PatternState):
        super().__init__()
        self._state = state
        self._frame_supplier: Optional[Callable[[int], Frame]] = None

    def set_frame_supplier(self, supplier: Callable[[int], Frame]) -> None:
        self._frame_supplier = supplier

    def render_frame(self, index: int) -> None:
        frame: Optional[Frame] = None
        if self._frame_supplier is not None:
            frame = self._frame_supplier(index)
        else:
            frames = self._state.frames()
            if 0 <= index < len(frames):
                frame = frames[index]
        if frame:
            self.frame_ready.emit(frame)

