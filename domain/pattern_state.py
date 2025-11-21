from __future__ import annotations

from typing import Optional

from core.pattern import Frame, Pattern, PatternMetadata


class PatternState:
    """Lightweight holder for the active pattern."""

    def __init__(self, pattern: Optional[Pattern] = None) -> None:
        self._pattern: Optional[Pattern] = pattern

    # Basic accessors --------------------------------------------------

    def set_pattern(self, pattern: Pattern) -> None:
        if not isinstance(pattern, Pattern):
            raise TypeError(f"Expected Pattern, got {type(pattern).__name__}: {pattern}")
        self._pattern = pattern

    def pattern(self) -> Pattern:
        self._ensure_pattern()
        if not isinstance(self._pattern, Pattern):
            raise RuntimeError(f"Pattern state corrupted: expected Pattern, got {type(self._pattern).__name__}")
        return self._pattern  # type: ignore[return-value]

    def metadata(self) -> PatternMetadata:
        return self.pattern().metadata

    def frames(self) -> list[Frame]:
        return self.pattern().frames

    # Convenience helpers ----------------------------------------------

    def frame_count(self) -> int:
        return len(self.pattern().frames) if self._pattern else 0

    def width(self) -> int:
        return self.metadata().width if self._pattern else 0

    def height(self) -> int:
        return self.metadata().height if self._pattern else 0

    def create_blank_frame(self, duration_ms: int) -> Frame:
        width = max(1, self.width())
        height = max(1, self.height())
        pixels = [(0, 0, 0)] * (width * height)
        return Frame(pixels=pixels, duration_ms=duration_ms)

    def _ensure_pattern(self) -> None:
        if self._pattern is None:
            raise RuntimeError("Pattern state is not initialised.")

