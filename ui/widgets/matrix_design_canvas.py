"""
Matrix Design Canvas - interactive LED matrix editor widget.

This widget provides a pixel grid for designing LED matrix frames. Users can
paint pixels using the currently selected color, erase with right-click, and
preview the current frame. The widget keeps an internal RGB matrix and emits
signals when pixels are updated so that parent widgets can stay in sync.
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple, Optional

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

RGB = Tuple[int, int, int]


class MatrixDesignCanvas(QWidget):
    """
    Interactive LED matrix editor.

    Features:
        - Configurable matrix width/height
        - Pixel painting with left click (current color) and right click (erase)
        - Drag painting while holding mouse button
        - Selection highlight for hovered pixel
        - Signals for pixel updates and cursor changes
    """

    pixel_updated = Signal(int, int, tuple)  # x, y, (r, g, b)
    hover_changed = Signal(int, int)  # x, y under cursor (or -1, -1)

    def __init__(
        self,
        width: int = 16,
        height: int = 16,
        pixel_size: int = 24,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._matrix_width = max(1, width)
        self._matrix_height = max(1, height)
        self._pixel_size = max(8, pixel_size)
        self._grid: List[List[RGB]] = [
            [(0, 0, 0) for _ in range(self._matrix_width)]
            for _ in range(self._matrix_height)
        ]
        self._current_color: RGB = (255, 255, 255)
        self._erase_color: RGB = (0, 0, 0)
        self._hover_cell: Tuple[int, int] = (-1, -1)
        self._is_dragging = False

        self.setMouseTracking(True)
        self.updateGeometry()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------
    def matrix_size(self) -> Tuple[int, int]:
        return self._matrix_width, self._matrix_height

    def set_matrix_size(self, width: int, height: int, default_color: RGB = (0, 0, 0)):
        """Resize the matrix and reset pixels."""
        width = max(1, int(width))
        height = max(1, int(height))
        if width == self._matrix_width and height == self._matrix_height:
            return

        self._matrix_width = width
        self._matrix_height = height
        self._grid = [
            [default_color for _ in range(self._matrix_width)]
            for _ in range(self._matrix_height)
        ]
        self.updateGeometry()
        self.update()

    def set_frame_pixels(self, pixels: List[RGB]):
        """Load pixels from a linear list (row-major)."""
        expected = self._matrix_width * self._matrix_height
        if len(pixels) != expected:
            # Truncate or pad to match size
            if len(pixels) < expected:
                pixels = pixels + [(0, 0, 0)] * (expected - len(pixels))
            else:
                pixels = pixels[:expected]
        idx = 0
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                self._grid[y][x] = tuple(pixels[idx])
                idx += 1
        self.update()

    def to_pixels(self) -> List[RGB]:
        """Return current grid as linear row-major list."""
        pixels: List[RGB] = []
        for row in self._grid:
            pixels.extend(row)
        return pixels

    def set_current_color(self, color: RGB):
        self._current_color = self._clamp_color(color)

    def set_erase_color(self, color: RGB):
        self._erase_color = self._clamp_color(color)

    # ------------------------------------------------------------------
    # Painting logic
    # ------------------------------------------------------------------
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return self._pixel_size * self._matrix_width + 2, self._pixel_size * self._matrix_height + 2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Fill background
        painter.fillRect(self.rect(), QColor(34, 34, 34))

        # Draw pixels
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                color = self._grid[y][x]
                rect_x = x * self._pixel_size + 1
                rect_y = y * self._pixel_size + 1
                rect_w = self._pixel_size - 2
                rect_h = self._pixel_size - 2

                painter.fillRect(rect_x, rect_y, rect_w, rect_h, QColor(*color))

        # Draw grid lines
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        width_px = self._matrix_width * self._pixel_size
        height_px = self._matrix_height * self._pixel_size
        for x in range(self._matrix_width + 1):
            painter.drawLine(x * self._pixel_size, 0, x * self._pixel_size, height_px)
        for y in range(self._matrix_height + 1):
            painter.drawLine(0, y * self._pixel_size, width_px, y * self._pixel_size)

        # Highlight hover cell
        hx, hy = self._hover_cell
        if 0 <= hx < self._matrix_width and 0 <= hy < self._matrix_height:
            painter.setPen(QPen(QColor(0, 255, 120), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(
                hx * self._pixel_size + 1,
                hy * self._pixel_size + 1,
                self._pixel_size - 2,
                self._pixel_size - 2,
            )

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self._is_dragging = True
            self._handle_paint_event(event.position().toPoint(), event.button())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        cell = self._cell_from_point(pos)
        if cell != self._hover_cell:
            self._hover_cell = cell
            self.hover_changed.emit(cell[0], cell[1])
            self.update()
        if self._is_dragging and event.buttons() & (Qt.LeftButton | Qt.RightButton):
            button = Qt.LeftButton if event.buttons() & Qt.LeftButton else Qt.RightButton
            self._handle_paint_event(pos, button)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self._hover_cell = (-1, -1)
        self.hover_changed.emit(-1, -1)
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_paint_event(self, point: QPoint, button: Qt.MouseButton):
        cell = self._cell_from_point(point)
        x, y = cell
        if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
            return

        color = self._current_color if button == Qt.LeftButton else self._erase_color
        if self._grid[y][x] == color:
            return

        self._grid[y][x] = color
        self.pixel_updated.emit(x, y, color)
        self.update()

    def _cell_from_point(self, point: QPoint) -> Tuple[int, int]:
        x = point.x() // self._pixel_size
        y = point.y() // self._pixel_size
        return x, y

    @staticmethod
    def _clamp_color(color: RGB) -> RGB:
        r, g, b = color
        return (
            int(max(0, min(255, r))),
            int(max(0, min(255, g))),
            int(max(0, min(255, b))),
        )


