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
from typing import Dict, List, Tuple, Optional
from enum import Enum
from math import cos, sin, pi
import random

from PySide6.QtCore import Qt, QPoint, Signal, QSize, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

RGB = Tuple[int, int, int]


class DrawingMode(Enum):
    """Drawing tool modes."""
    PIXEL = "pixel"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    LINE = "line"
    RANDOM = "random"
    GRADIENT = "gradient"


class PixelShape(Enum):
    """Visual style for rendered pixels."""
    SQUARE = "square"
    ROUND = "round"
    ROUNDED = "rounded"


class GeometryOverlay(Enum):
    """Preview overlays that mirror LMS visualizations."""
    MATRIX = "matrix"
    CIRCLE = "circle"
    RING = "ring"
    RADIAL = "radial"


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
    painting_finished = Signal()  # Emitted when mouse is released after painting

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
        self._base_pixel_size = max(4, pixel_size)
        self._pixel_size = self._base_pixel_size
        self._grid: List[List[RGB]] = [
            [(0, 0, 0) for _ in range(self._matrix_width)]
            for _ in range(self._matrix_height)
        ]
        self._current_color: RGB = (255, 255, 255)
        self._erase_color: RGB = (0, 0, 0)
        self._hover_cell: Tuple[int, int] = (-1, -1)
        self._is_dragging = False
        self._drawing_mode = DrawingMode.PIXEL
        self._shape_filled = True
        self._shape_start: Optional[Tuple[int, int]] = None
        self._shape_end: Optional[Tuple[int, int]] = None
        self._preview_grid: Optional[List[List[RGB]]] = None
        self._brush_size = 1  # Brush size (1×1 to 8×8)
        self._background_color = QColor(34, 34, 34)
        self._grid_color = QColor(60, 60, 60)
        self._hover_color = QColor(0, 255, 120)
        self._pixel_border_color = QColor(18, 18, 18)
        self._pixel_shape = PixelShape.SQUARE
        self._geometry_overlay = GeometryOverlay.MATRIX
        self._random_palette: List[RGB] = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
        self._gradient_start: RGB = (255, 0, 0)
        self._gradient_end: RGB = (0, 0, 255)
        self._gradient_steps: int = 32
        self._gradient_step_index: int = 0
        self._dirty_regions: List[Tuple[int, int, int, int]] = []  # (x, y, w, h) dirty rectangles
        self._full_repaint_needed = False

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
        self._full_repaint_needed = True
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

    def set_drawing_mode(self, mode: DrawingMode):
        """Set the current drawing tool mode."""
        self._drawing_mode = mode
        self._shape_start = None
        self._shape_end = None
        self._preview_grid = None
        self.update()

    def set_shape_filled(self, filled: bool):
        """Set whether shapes should be filled or outlined."""
        self._shape_filled = filled

    def set_brush_size(self, size: int):
        """Set brush size (1-8)."""
        self._brush_size = max(1, min(8, size))

    def get_brush_size(self) -> int:
        """Get current brush size."""
        return self._brush_size

    def set_pixel_shape(self, shape: PixelShape | str):
        """Update rendered pixel style."""
        if isinstance(shape, str):
            try:
                shape = PixelShape(shape)
            except ValueError:
                shape = PixelShape.SQUARE
        if shape == self._pixel_shape:
            return
        self._pixel_shape = shape
        self._full_repaint_needed = True
        self.update()

    def set_geometry_overlay(self, mode: GeometryOverlay | str):
        """Toggle geometry preview overlay (matrix/circle/ring/radial)."""
        if isinstance(mode, str):
            try:
                mode = GeometryOverlay(mode)
            except ValueError:
                mode = GeometryOverlay.MATRIX
        if mode == self._geometry_overlay:
            return
        self._geometry_overlay = mode
        self.update()

    def set_random_palette(self, palette: List[RGB]) -> None:
        """Set palette used by random brush."""
        if palette:
            self._random_palette = [self._clamp_color(color) for color in palette]

    def set_gradient_brush(self, start: RGB, end: RGB, steps: int) -> None:
        """Configure gradient brush endpoints."""
        self._gradient_start = self._clamp_color(start)
        self._gradient_end = self._clamp_color(end)
        self._gradient_steps = max(2, int(steps))
        self._gradient_step_index = 0

    # ------------------------------------------------------------------
    # Zoom handling
    # ------------------------------------------------------------------
    def set_zoom_factor(self, factor: float) -> None:
        """Adjust the pixel rendering size without changing matrix dimensions."""
        factor = max(0.2, min(factor, 4.0))
        new_size = int(self._base_pixel_size * factor)
        new_size = max(4, min(new_size, 256))
        if new_size == self._pixel_size:
            return
        self._pixel_size = new_size
        self.updateGeometry()
        self.update()

    def reset_zoom(self) -> None:
        """Restore the default pixel size."""
        if self._pixel_size != self._base_pixel_size:
            self._pixel_size = self._base_pixel_size
            self.updateGeometry()
            self.update()

    # ------------------------------------------------------------------
    # Painting logic
    # ------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        return self.minimumSizeHint()

    def minimumSizeHint(self) -> QSize:
        return QSize(
            self._pixel_size * self._matrix_width + 2,
            self._pixel_size * self._matrix_height + 2,
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Fill background
        painter.fillRect(self.rect(), self._background_color)

        # Draw pixels (use preview grid if available, otherwise use actual grid)
        display_grid = self._preview_grid if self._preview_grid is not None else self._grid
        
        # Optimize: only repaint dirty regions if not doing full repaint
        if self._full_repaint_needed or not self._dirty_regions:
            # Full repaint
            for y in range(self._matrix_height):
                for x in range(self._matrix_width):
                    color = display_grid[y][x]
                    rect_x = x * self._pixel_size + 1
                    rect_y = y * self._pixel_size + 1
                    rect_w = self._pixel_size - 2
                    rect_h = self._pixel_size - 2

                    self._draw_pixel_tile(painter, rect_x, rect_y, rect_w, rect_h, color)
            
            # Draw grid lines
            painter.setPen(QPen(self._grid_color, 1))
            width_px = self._matrix_width * self._pixel_size
            height_px = self._matrix_height * self._pixel_size
            for x in range(self._matrix_width + 1):
                painter.drawLine(x * self._pixel_size, 0, x * self._pixel_size, height_px)
            for y in range(self._matrix_height + 1):
                painter.drawLine(0, y * self._pixel_size, width_px, y * self._pixel_size)
            
            self._full_repaint_needed = False
            self._dirty_regions.clear()
        else:
            # Partial repaint - only dirty regions
            for x, y, w, h in self._dirty_regions:
                for py in range(y, min(y + h, self._matrix_height)):
                    for px in range(x, min(x + w, self._matrix_width)):
                        color = display_grid[py][px]
                        rect_x = px * self._pixel_size + 1
                        rect_y = py * self._pixel_size + 1
                        rect_w = self._pixel_size - 2
                        rect_h = self._pixel_size - 2
                        self._draw_pixel_tile(painter, rect_x, rect_y, rect_w, rect_h, color)
            self._dirty_regions.clear()

        # Highlight hover cell
        hx, hy = self._hover_cell
        if 0 <= hx < self._matrix_width and 0 <= hy < self._matrix_height:
            painter.setPen(QPen(self._hover_color, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(
                hx * self._pixel_size + 1,
                hy * self._pixel_size + 1,
                self._pixel_size - 2,
                self._pixel_size - 2,
            )

        # Geometry overlay preview (after hover so highlight stays crisp)
        self._draw_geometry_overlay(painter)

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            if event.button() == Qt.LeftButton:
                self._gradient_step_index = 0
            cell = self._cell_from_point(event.position().toPoint())
            x, y = cell
            if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                if self._drawing_mode == DrawingMode.PIXEL:
                    self._is_dragging = True
                    self._handle_paint_event(event.position().toPoint(), event.button())
                else:
                    # Start shape drawing
                    self._is_dragging = True
                    self._shape_start = (x, y)
                    self._shape_end = (x, y)
                    self._preview_grid = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()
        cell = self._cell_from_point(pos)
        if cell != self._hover_cell:
            self._hover_cell = cell
            self.hover_changed.emit(cell[0], cell[1])
            self.update()
        
        if self._is_dragging:
            if self._drawing_mode == DrawingMode.PIXEL:
                if event.buttons() & (Qt.LeftButton | Qt.RightButton):
                    button = Qt.LeftButton if event.buttons() & Qt.LeftButton else Qt.RightButton
                    self._handle_paint_event(pos, button)
            else:
                # Update shape preview
                x, y = cell
                if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                    self._shape_end = (x, y)
                    self._update_preview()  # Update preview grid
                    self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        was_dragging = self._is_dragging
        if self._is_dragging and self._drawing_mode != DrawingMode.PIXEL:
            # Commit shape
            if self._shape_start and self._shape_end:
                self._commit_shape()
        self._is_dragging = False
        self._shape_start = None
        self._shape_end = None
        self._preview_grid = None
        self.update()
        
        # Emit painting finished signal if we were painting
        if was_dragging and self._drawing_mode == DrawingMode.PIXEL:
            self.painting_finished.emit()
        
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

        if button == Qt.RightButton:
            color = self._erase_color
        else:
            if self._drawing_mode == DrawingMode.RANDOM and self._random_palette:
                color = random.choice(self._random_palette)
            elif self._drawing_mode == DrawingMode.GRADIENT:
                color = self._next_gradient_color()
            else:
                color = self._current_color
        
        # Track dirty region for optimization
        brush_half = self._brush_size // 2
        
        # Apply brush size
        if self._brush_size > 1:
            # Paint brush-sized area
            for dy in range(-brush_half, brush_half + 1):
                for dx in range(-brush_half, brush_half + 1):
                    px, py = x + dx, y + dy
                    if 0 <= px < self._matrix_width and 0 <= py < self._matrix_height:
                        if self._grid[py][px] != color:
                            self._grid[py][px] = color
                            self.pixel_updated.emit(px, py, color)
                            # Add to dirty region
                            self._dirty_regions.append((px, py, 1, 1))
        else:
            # Single pixel
            if self._grid[y][x] == color:
                return
            self._grid[y][x] = color
            self.pixel_updated.emit(x, y, color)
            # Add to dirty region
            self._dirty_regions.append((x, y, 1, 1))
        
        self.update()

    def _commit_shape(self):
        """Commit the current shape to the grid."""
        if not self._shape_start or not self._shape_end:
            return
        
        color = self._current_color
        if self._drawing_mode == DrawingMode.RECTANGLE:
            self._draw_rectangle(self._shape_start[0], self._shape_start[1], 
                               self._shape_end[0], self._shape_end[1], color, preview=False)
        elif self._drawing_mode == DrawingMode.CIRCLE:
            self._draw_circle(self._shape_start[0], self._shape_start[1], 
                            self._shape_end[0], self._shape_end[1], color, preview=False)
        elif self._drawing_mode == DrawingMode.LINE:
            self._draw_line(self._shape_start[0], self._shape_start[1], 
                          self._shape_end[0], self._shape_end[1], color, preview=False)
        
        # Mark entire shape region as dirty
        if self._shape_start and self._shape_end:
            x_min = min(self._shape_start[0], self._shape_end[0])
            x_max = max(self._shape_start[0], self._shape_end[0])
            y_min = min(self._shape_start[1], self._shape_end[1])
            y_max = max(self._shape_start[1], self._shape_end[1])
            self._dirty_regions.append((x_min, y_min, x_max - x_min + 1, y_max - y_min + 1))
        
        # Emit updates for all changed pixels
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                self.pixel_updated.emit(x, y, self._grid[y][x])
        self.update()

    def _update_preview(self):
        """Update preview grid for shape drawing."""
        if not self._shape_start or not self._shape_end:
            self._preview_grid = None
            return
        
        # Create a copy of the grid for preview
        self._preview_grid = [[self._grid[y][x] for x in range(self._matrix_width)] 
                             for y in range(self._matrix_height)]
        
        color = self._current_color
        if self._drawing_mode == DrawingMode.RECTANGLE:
            self._draw_rectangle(self._shape_start[0], self._shape_start[1], 
                               self._shape_end[0], self._shape_end[1], color, preview=True)
        elif self._drawing_mode == DrawingMode.CIRCLE:
            self._draw_circle(self._shape_start[0], self._shape_start[1], 
                            self._shape_end[0], self._shape_end[1], color, preview=True)
        elif self._drawing_mode == DrawingMode.LINE:
            self._draw_line(self._shape_start[0], self._shape_start[1], 
                          self._shape_end[0], self._shape_end[1], color, preview=True)

    def _draw_rectangle(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
        """Draw a rectangle from (x1,y1) to (x2,y2)."""
        target_grid = self._preview_grid if preview else self._grid
        x_min, x_max = min(x1, x2), max(x1, x2)
        y_min, y_max = min(y1, y2), max(y1, y2)
        
        if self._shape_filled:
            # Filled rectangle
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        target_grid[y][x] = color
        else:
            # Empty rectangle (outline only)
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        # Draw only border pixels
                        if y == y_min or y == y_max or x == x_min or x == x_max:
                            target_grid[y][x] = color

    def _draw_circle(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
        """Draw a circle using midpoint algorithm."""
        target_grid = self._preview_grid if preview else self._grid
        # Calculate center and radius
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        radius_x = abs(x2 - x1) // 2
        radius_y = abs(y2 - y1) // 2
        
        if radius_x == 0 and radius_y == 0:
            # Single pixel
            if 0 <= center_x < self._matrix_width and 0 <= center_y < self._matrix_height:
                target_grid[center_y][center_x] = color
            return
        
        # Use ellipse approximation for non-square circles
        if self._shape_filled:
            # Filled circle
            for y in range(self._matrix_height):
                for x in range(self._matrix_width):
                    dx = x - center_x
                    dy = y - center_y
                    # Ellipse equation: (dx/rx)^2 + (dy/ry)^2 <= 1
                    if radius_x > 0 and radius_y > 0:
                        if (dx * dx) / (radius_x * radius_x) + (dy * dy) / (radius_y * radius_y) <= 1.0:
                            target_grid[y][x] = color
        else:
            # Empty circle (outline)
            for y in range(self._matrix_height):
                for x in range(self._matrix_width):
                    dx = x - center_x
                    dy = y - center_y
                    if radius_x > 0 and radius_y > 0:
                        dist = (dx * dx) / (radius_x * radius_x) + (dy * dy) / (radius_y * radius_y)
                        # Draw pixels near the border
                        if 0.8 <= dist <= 1.2:
                            target_grid[y][x] = color

    def _draw_line(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
        """Draw a line using Bresenham's algorithm."""
        target_grid = self._preview_grid if preview else self._grid
        # Bresenham's line algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        while True:
            if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                target_grid[y][x] = color
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

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

    def _draw_pixel_tile(self, painter: QPainter, rect_x: int, rect_y: int, rect_w: int, rect_h: int, color: RGB):
        """Render a pixel tile respecting the selected pixel shape."""
        painter.save()
        painter.setBrush(QBrush(QColor(*color)))
        if self._pixel_border_color.isValid():
            painter.setPen(QPen(self._pixel_border_color, 1))
        else:
            painter.setPen(Qt.NoPen)

        if self._pixel_shape == PixelShape.ROUND:
            painter.drawEllipse(rect_x, rect_y, rect_w, rect_h)
        elif self._pixel_shape == PixelShape.ROUNDED:
            radius = max(2, min(rect_w, rect_h) // 3)
            painter.drawRoundedRect(QRectF(rect_x, rect_y, rect_w, rect_h), radius, radius)
        else:
            painter.drawRect(rect_x, rect_y, rect_w, rect_h)
        painter.restore()

    def _draw_geometry_overlay(self, painter: QPainter):
        """Draw LMS-style overlays (circle/ring/radial) to preview alternate geometries."""
        if self._geometry_overlay == GeometryOverlay.MATRIX:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        overlay_pen = QPen(QColor(255, 255, 255, 80), 2, Qt.DashLine)
        painter.setPen(overlay_pen)
        bounds = self.rect().adjusted(6, 6, -6, -6)

        if self._geometry_overlay == GeometryOverlay.CIRCLE:
            painter.drawEllipse(bounds)
        elif self._geometry_overlay == GeometryOverlay.RING:
            painter.drawEllipse(bounds)
            inner = bounds.adjusted(
                bounds.width() * 0.2,
                bounds.height() * 0.2,
                -bounds.width() * 0.2,
                -bounds.height() * 0.2,
            )
            painter.drawEllipse(inner)
        elif self._geometry_overlay == GeometryOverlay.RADIAL:
            # Draw semi-circle with spokes
            painter.drawArc(bounds, 0, 180 * 16)
            steps = 8
            center = bounds.bottomLeft()
            radius = bounds.width()
            for i in range(steps + 1):
                angle = pi * (i / steps)
                x = center.x() + radius * cos(angle)
                y = center.y() - radius * sin(angle)
                painter.drawLine(center, QPoint(int(x), int(y)))

        painter.restore()

    def _next_gradient_color(self) -> RGB:
        """Return the next interpolated gradient colour."""
        steps = max(2, self._gradient_steps)
        t = (self._gradient_step_index % steps) / (steps - 1)
        self._gradient_step_index += 1
        r = int(self._gradient_start[0] + (self._gradient_end[0] - self._gradient_start[0]) * t)
        g = int(self._gradient_start[1] + (self._gradient_end[1] - self._gradient_start[1]) * t)
        b = int(self._gradient_start[2] + (self._gradient_end[2] - self._gradient_start[2]) * t)
        return self._clamp_color((r, g, b))

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------
    def apply_palette(self, palette: Dict[str, str]):
        """
        Update canvas colours from a palette dictionary.
        """

        def to_color(value, fallback: QColor) -> QColor:
            if value is None:
                return fallback
            if isinstance(value, QColor):
                return value
            return QColor(value)

        self._background_color = to_color(palette.get("background"), self._background_color)
        self._grid_color = to_color(palette.get("grid"), self._grid_color)
        self._hover_color = to_color(palette.get("hover"), self._hover_color)
        border_value = palette.get("pixel_border")
        self._pixel_border_color = to_color(border_value, self._pixel_border_color) if border_value else QColor()
        self.update()


