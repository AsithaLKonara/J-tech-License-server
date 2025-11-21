from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from core.pattern import Frame
from domain.pattern_state import PatternState


class FrameManager(QObject):
    """
    Encapsulates frame operations (add, duplicate, delete, move, duration).
    Emits Qt signals so UI components can react.
    """

    frames_changed = Signal()
    frame_index_changed = Signal(int)
    frame_duration_changed = Signal(int, int)  # index, duration

    def __init__(self, state: PatternState):
        super().__init__()
        self._state = state
        self._current_index: int = 0

    # Pattern lifecycle ------------------------------------------------

    def set_pattern(self, pattern) -> None:
        self._state.set_pattern(pattern)
        self._current_index = 0
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)

    # Access -----------------------------------------------------------

    def current_index(self) -> int:
        return self._current_index

    def frame(self, index: Optional[int] = None) -> Frame:
        index = self._normalise_index(index if index is not None else self._current_index)
        return self._state.frames()[index]

    # Selection --------------------------------------------------------

    def select(self, index: int) -> None:
        index = self._normalise_index(index)
        if index != self._current_index:
            self._current_index = index
            self.frame_index_changed.emit(index)

    # Mutations --------------------------------------------------------

    def add_blank_after_current(self, duration_ms: int) -> int:
        pattern = self._state.pattern()
        frame = self._state.create_blank_frame(duration_ms)
        insert_at = self._current_index + 1
        pattern.frames.insert(insert_at, frame)
        self._current_index = insert_at
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)
        return insert_at

    def duplicate(self, index: Optional[int] = None) -> int:
        index = self._normalise_index(index if index is not None else self._current_index)
        pattern = self._state.pattern()
        frame_copy = pattern.frames[index].copy()
        insert_at = index + 1
        pattern.frames.insert(insert_at, frame_copy)
        self._current_index = insert_at
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)
        return insert_at

    def delete(self, index: Optional[int] = None) -> None:
        pattern = self._state.pattern()
        if len(pattern.frames) <= 1:
            return
        index = self._normalise_index(index if index is not None else self._current_index)
        del pattern.frames[index]
        if self._current_index >= len(pattern.frames):
            self._current_index = len(pattern.frames) - 1
        self.frames_changed.emit()
        self.frame_index_changed.emit(self._current_index)

    def move(self, src: int, dest: int) -> None:
        pattern = self._state.pattern()
        src = self._normalise_index(src)
        dest = max(0, min(len(pattern.frames) - 1, dest))
        if src == dest:
            return
        frame = pattern.frames.pop(src)
        pattern.frames.insert(dest, frame)
        self._current_index = dest
        self.frames_changed.emit()
        self.frame_index_changed.emit(dest)

    def set_duration(self, index: int, duration_ms: int) -> None:
        index = self._normalise_index(index)
        frame = self._state.frames()[index]
        if frame.duration_ms != duration_ms:
            frame.duration_ms = duration_ms
            self.frame_duration_changed.emit(index, duration_ms)

    # Helpers ----------------------------------------------------------

    def _normalise_index(self, index: int) -> int:
        frames = self._state.frames()
        if not frames:
            raise RuntimeError("No frames available.")
        return max(0, min(len(frames) - 1, index))

