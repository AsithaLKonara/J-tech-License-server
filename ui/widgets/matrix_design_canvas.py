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
from collections import deque
import random

from PySide6.QtCore import Qt, QPoint, Signal, QSize, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QCursor, QFont
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
    BUCKET_FILL = "bucket_fill"
    EYEDROPPER = "eyedropper"


class PixelShape(Enum):
    """Visual style for rendered pixels."""
    SQUARE = "square"
    ROUND = "round"
    ROUNDED = "rounded"


class GeometryOverlay(Enum):
    """Preview overlays that mirror LMS visualizations."""
    MATRIX = "matrix"
    RING = "ring"
    IRREGULAR = "irregular"


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
    color_picked = Signal(int, int, int)  # r, g, b - Emitted when color is picked with eyedropper

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
        self._bucket_fill_tolerance: int = 0  # Color tolerance for bucket fill (0-255)
        self._border_width: int = 0  # Pixel border width (0 = no border, 1-3 = border width)
        
        # Zoom and pan support
        self._zoom_level = 1.0
        self._pan_offset = QPoint(0, 0)
        self._is_panning = False
        self._pan_start_pos: Optional[QPoint] = None
        
        # Onion skinning data
        self._onion_skin_prev_frames: List[List[List[RGB]]] = []  # List of previous frame grids
        self._onion_skin_next_frames: List[List[List[RGB]]] = []  # List of next frame grids
        self._onion_skin_prev_opacities: List[float] = []
        self._onion_skin_next_opacities: List[float] = []
        
        # Pattern metadata for circular layout support
        self._pattern_metadata: Optional['PatternMetadata'] = None
        self._show_led_indices = False  # Toggle for showing LED indices on active cells

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

    def get_grid_data(self) -> List[List[RGB]]:
        """Get current grid data as 2D list."""
        return self._grid
    
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
        
        # Update cursor based on tool
        if mode == DrawingMode.EYEDROPPER:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        self.update()

    def set_shape_filled(self, filled: bool):
        """Set whether shapes should be filled or outlined."""
        self._shape_filled = filled

    def mark_dirty(self, x: int, y: int, width: int = 1, height: int = 1) -> None:
        """
        Mark a region as dirty for optimized repainting.
        
        Args:
            x: X coordinate of dirty region
            y: Y coordinate of dirty region
            width: Width of dirty region (default: 1)
            height: Height of dirty region (default: 1)
        """
        # Clamp to matrix bounds
        x = max(0, min(x, self._matrix_width - 1))
        y = max(0, min(y, self._matrix_height - 1))
        width = max(1, min(width, self._matrix_width - x))
        height = max(1, min(height, self._matrix_height - y))
        
        self._dirty_regions.append((x, y, width, height))
        self.update()
    
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
    
    def set_border_width(self, width: int):
        """Set pixel border width (0-3)."""
        width = max(0, min(3, int(width)))
        if width == self._border_width:
            return
        self._border_width = width
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

    def set_bucket_fill_tolerance(self, tolerance: int) -> None:
        """Set color tolerance for bucket fill (0-255)."""
        self._bucket_fill_tolerance = max(0, min(255, int(tolerance)))

    def get_bucket_fill_tolerance(self) -> int:
        """Get current bucket fill tolerance."""
        return self._bucket_fill_tolerance

    def set_bucket_fill_tolerance(self, tolerance: int) -> None:
        """Set color tolerance for bucket fill (0-255)."""
        self._bucket_fill_tolerance = max(0, min(255, int(tolerance)))

    def get_bucket_fill_tolerance(self) -> int:
        """Get current bucket fill tolerance."""
        return self._bucket_fill_tolerance

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
        self._zoom_level = factor
        self.updateGeometry()
        self.update()

    def reset_zoom(self) -> None:
        """Restore the default pixel size."""
        if self._pixel_size != self._base_pixel_size:
            self._pixel_size = self._base_pixel_size
            self._zoom_level = 1.0
            self._pan_offset = QPoint(0, 0)
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

    def _draw_background_image(self, painter: QPainter, bounds):
        """Draw background image if available for irregular shapes."""
        if not self._pattern_metadata or not self._pattern_metadata.irregular_shape_enabled:
            return
        
        if not self._pattern_metadata.background_image_path:
            return
        
        try:
            from PySide6.QtGui import QPixmap
            from pathlib import Path
            
            image_path = Path(self._pattern_metadata.background_image_path)
            if not image_path.exists():
                return
            
            pixmap = QPixmap(str(image_path))
            if pixmap.isNull():
                return
            
            # Apply scale and offset
            scale = self._pattern_metadata.background_image_scale
            offset_x = self._pattern_metadata.background_image_offset_x
            offset_y = self._pattern_metadata.background_image_offset_y
            
            # Scale pixmap
            if scale != 1.0:
                scaled_size = pixmap.size() * scale
                pixmap = pixmap.scaled(scaled_size.toSize(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Draw semi-transparent background image
            painter.setOpacity(0.3)
            painter.drawPixmap(
                int(bounds.x() + offset_x),
                int(bounds.y() + offset_y),
                pixmap
            )
            painter.setOpacity(1.0)
        except Exception as e:
            import logging
            logging.warning(f"Failed to draw background image: {e}")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Fill background
        painter.fillRect(self.rect(), self._background_color)

        # Apply pan offset translation
        painter.translate(self._pan_offset)
        
        # Calculate bounds for background image
        width_px = self._matrix_width * self._pixel_size
        height_px = self._matrix_height * self._pixel_size
        bounds = painter.viewport().adjusted(0, 0, width_px, height_px)
        
        # Draw background image (before pixels, so it appears behind)
        self._draw_background_image(painter, bounds)

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
        
        # Onion skinning overlays (after geometry overlay)
        self._draw_onion_skins(painter)

    # ------------------------------------------------------------------
    # Bucket fill and eyedropper
    # ------------------------------------------------------------------
    def _flood_fill(self, x: int, y: int, target_color: RGB, fill_color: RGB, tolerance: int) -> List[Tuple[int, int, RGB]]:
        """
        Flood fill algorithm using BFS.
        
        Returns list of (x, y, new_color) tuples for all filled pixels.
        """
        if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
            return []
        
        # Check if starting cell is active (for irregular shapes)
        if self._pattern_metadata and self._pattern_metadata.irregular_shape_enabled:
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
            if not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                return []  # Can't fill inactive cell
        
        # Check if colors are similar within tolerance
        def colors_match(c1: RGB, c2: RGB, tol: int) -> bool:
            if tol == 0:
                return c1 == c2
            r1, g1, b1 = c1
            r2, g2, b2 = c2
            return (abs(r1 - r2) <= tol and 
                   abs(g1 - g2) <= tol and 
                   abs(b1 - b2) <= tol)
        
        # If target and fill colors match (within tolerance), nothing to do
        if colors_match(target_color, fill_color, tolerance):
            return []
        
        filled_pixels: List[Tuple[int, int, RGB]] = []
        visited = set()
        queue = deque([(x, y)])
        
        while queue:
            cx, cy = queue.popleft()
            
            # Skip if out of bounds
            if not (0 <= cx < self._matrix_width and 0 <= cy < self._matrix_height):
                continue
            
            # Skip if already visited
            if (cx, cy) in visited:
                continue
            
            # Skip if color doesn't match target (within tolerance)
            current_color = self._grid[cy][cx]
            if not colors_match(current_color, target_color, tolerance):
                continue
            
            # Check if cell is active (for irregular shapes)
            if self._pattern_metadata and self._pattern_metadata.irregular_shape_enabled:
                if not IrregularShapeMapper.is_cell_active(cx, cy, self._pattern_metadata):
                    continue  # Skip inactive cells
            
            # Fill this pixel
            self._grid[cy][cx] = fill_color
            filled_pixels.append((cx, cy, fill_color))
            visited.add((cx, cy))
            
            # Add neighbors to queue (only active cells for irregular shapes)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in visited:
                    # For irregular shapes, only add active neighbors
                    if self._pattern_metadata and self._pattern_metadata.irregular_shape_enabled:
                        if IrregularShapeMapper.is_cell_active(nx, ny, self._pattern_metadata):
                            queue.append((nx, ny))
                    else:
                        queue.append((nx, ny))
        
        return filled_pixels

    def _pick_color_at(self, x: int, y: int) -> Optional[RGB]:
        """
        Pick color from grid at given coordinates.
        
        Returns RGB tuple or None if coordinates are invalid.
        """
        if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
            return None
        return self._grid[y][x]

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        # Middle mouse button for panning
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.position().toPoint()
            event.accept()
            return
        
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            if event.button() == Qt.LeftButton:
                self._gradient_step_index = 0
            cell = self._cell_from_point(event.position().toPoint())
            x, y = cell
            if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                if self._drawing_mode == DrawingMode.EYEDROPPER:
                    # Pick color from canvas
                    picked_color = self._pick_color_at(x, y)
                    if picked_color:
                        self.color_picked.emit(picked_color[0], picked_color[1], picked_color[2])
                elif self._drawing_mode == DrawingMode.BUCKET_FILL:
                    # Bucket fill
                    target_color = self._grid[y][x]
                    fill_color = self._erase_color if event.button() == Qt.RightButton else self._current_color
                    tolerance = self._bucket_fill_tolerance
                    filled_pixels = self._flood_fill(x, y, target_color, fill_color, tolerance)
                    
                    # Emit pixel updates for all filled pixels
                    min_x, min_y = self._matrix_width, self._matrix_height
                    max_x, max_y = 0, 0
                    for px, py, color in filled_pixels:
                        self.pixel_updated.emit(px, py, color)
                        min_x = min(min_x, px)
                        min_y = min(min_y, py)
                        max_x = max(max_x, px)
                        max_y = max(max_y, py)
                    
                    # Mark dirty region
                    if filled_pixels:
                        self._dirty_regions.append((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1))
                        self.update()
                        self.painting_finished.emit()
                elif self._drawing_mode == DrawingMode.PIXEL:
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
        
        # Handle panning
        if self._is_panning and self._pan_start_pos is not None:
            delta = pos - self._pan_start_pos
            self._pan_offset += delta
            self._pan_start_pos = pos
            self.update()
            event.accept()
            return
        
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
        # Handle pan end
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self._pan_start_pos = None
            event.accept()
            return
        
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

    def wheelEvent(self, event):
        """Handle mouse wheel zoom."""
        from PySide6.QtCore import Qt
        delta = event.angleDelta().y()
        
        if delta > 0:
            # Zoom in
            self._zoom_level = min(5.0, self._zoom_level * 1.1)
        else:
            # Zoom out
            self._zoom_level = max(0.25, self._zoom_level * 0.9)
        
        # Adjust pixel size based on zoom
        self._pixel_size = int(self._base_pixel_size * self._zoom_level)
        
        self.updateGeometry()
        self.update()
        event.accept()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for zoom/pan."""
        from PySide6.QtCore import Qt
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_0:
                # Reset zoom
                self._zoom_level = 1.0
                self._pan_offset = QPoint(0, 0)
                self._pixel_size = self._base_pixel_size
                self.updateGeometry()
                self.update()
                event.accept()
                return
            elif event.key() == Qt.Key_1:
                # Fit to window
                self._fit_to_window()
                event.accept()
                return
        super().keyPressEvent(event)
    
    def _fit_to_window(self):
        """Fit canvas to window."""
        widget_width = self.width()
        widget_height = self.height()
        
        matrix_width_px = self._matrix_width * self._base_pixel_size
        matrix_height_px = self._matrix_height * self._base_pixel_size
        
        if matrix_width_px == 0 or matrix_height_px == 0:
            return
        
        zoom_x = (widget_width - 40) / matrix_width_px if matrix_width_px > 0 else 1.0
        zoom_y = (widget_height - 40) / matrix_height_px if matrix_height_px > 0 else 1.0
        
        self._zoom_level = min(zoom_x, zoom_y, 5.0)  # Cap at 5x
        self._zoom_level = max(0.25, self._zoom_level)  # Floor at 0.25x
        
        self._pixel_size = int(self._base_pixel_size * self._zoom_level)
        self._pan_offset = QPoint(0, 0)
        
        self.updateGeometry()
        self.update()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_paint_event(self, point: QPoint, button: Qt.MouseButton):
        cell = self._cell_from_point(point)
        x, y = cell
        if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
            return
        
        # Check if cell is active (for irregular shapes)
        if self._pattern_metadata and self._pattern_metadata.irregular_shape_enabled:
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
            if not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                return  # Ignore clicks on inactive cells

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
        
        # Check for irregular shapes
        check_active = (self._pattern_metadata and 
                       self._pattern_metadata.irregular_shape_enabled and 
                       not preview)
        if check_active:
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
        
        if self._shape_filled:
            # Filled rectangle
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        # Check if cell is active (for irregular shapes)
                        if check_active and not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                            continue
                        target_grid[y][x] = color
        else:
            # Empty rectangle (outline only)
            for y in range(y_min, y_max + 1):
                for x in range(x_min, x_max + 1):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        # Draw only border pixels
                        if y == y_min or y == y_max or x == x_min or x == x_max:
                            # Check if cell is active (for irregular shapes)
                            if check_active and not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                                continue
                            target_grid[y][x] = color

    def _draw_circle(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
        """Draw a circle using midpoint algorithm."""
        target_grid = self._preview_grid if preview else self._grid
        # Calculate center and radius
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        radius_x = abs(x2 - x1) // 2
        radius_y = abs(y2 - y1) // 2
        
        # Check for irregular shapes
        check_active = (self._pattern_metadata and 
                       self._pattern_metadata.irregular_shape_enabled and 
                       not preview)
        if check_active:
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
        
        if radius_x == 0 and radius_y == 0:
            # Single pixel
            if 0 <= center_x < self._matrix_width and 0 <= center_y < self._matrix_height:
                if not check_active or IrregularShapeMapper.is_cell_active(center_x, center_y, self._pattern_metadata):
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
                            # Check if cell is active (for irregular shapes)
                            if check_active and not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                                continue
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
                            # Check if cell is active (for irregular shapes)
                            if check_active and not IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                                continue
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
        
        # Check for irregular shapes
        check_active = (self._pattern_metadata and 
                       self._pattern_metadata.irregular_shape_enabled and 
                       not preview)
        if check_active:
            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
        
        x, y = x1, y1
        while True:
            if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                # Check if cell is active (for irregular shapes)
                if not check_active or IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
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
        # Account for pan offset
        adjusted_x = point.x() - self._pan_offset.x()
        adjusted_y = point.y() - self._pan_offset.y()
        x = adjusted_x // self._pixel_size
        y = adjusted_y // self._pixel_size
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
        
        # Set border pen based on border width setting
        if self._border_width > 0:
            border_color = self._pixel_border_color if self._pixel_border_color.isValid() else QColor(18, 18, 18)
            painter.setPen(QPen(border_color, self._border_width))
        elif self._pixel_border_color.isValid():
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

    def set_pattern_metadata(self, metadata: Optional['PatternMetadata']) -> None:
        """
        Set pattern metadata for circular layout support.
        
        This enables the canvas to:
        - Show circular/ring/arc bounds overlay
        - Highlight active grid cells that map to LEDs
        - Dim non-active cells
        
        The canvas itself remains grid-based - this is just visual feedback.
        All drawing tools continue to work on the grid normally.
        """
        from core.pattern import PatternMetadata
        self._pattern_metadata = metadata
        self.update()  # Trigger repaint to show updated overlay
    
    def _draw_geometry_overlay(self, painter: QPainter):
        """
        Draw LMS-style overlays (circle/ring/radial) to preview alternate geometries.
        
        This overlay is purely visual - it shows which grid cells map to LEDs
        and displays the circular bounds. It does NOT affect drawing behavior.
        
        Key principle: "Circular View is a lens, not a new world"
        - Grid-based editing remains primary
        - Overlay is interpretation layer only
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        bounds = self.rect().adjusted(6, 6, -6, -6)
        
        # Check if pattern has circular layout
        layout_type = None
        if self._pattern_metadata:
            layout_type = getattr(self._pattern_metadata, 'layout_type', 'rectangular')
        
        # For circular layouts and irregular shapes, dim unmapped/inactive cells
        if layout_type and layout_type != "rectangular":
            from core.mapping.circular_mapper import CircularMapper
            
            # Dim unmapped cells
            cell_width = bounds.width() / self._matrix_width if self._matrix_width > 0 else 1
            cell_height = bounds.height() / self._matrix_height if self._matrix_height > 0 else 1
            
            inactive_brush = QBrush(QColor(60, 60, 60, 40))
            painter.setBrush(inactive_brush)
            painter.setPen(Qt.NoPen)
            
            for y in range(self._matrix_height):
                for x in range(self._matrix_width):
                    # Check if this cell is mapped/active
                    is_active = True
                    if layout_type == "irregular":
                        from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                        is_active = IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata)
                    else:
                        is_active = CircularMapper.is_mapped(x, y, self._pattern_metadata)
                    
                    if not is_active:
                        # Dim inactive/unmapped cell
                        cell_x = bounds.x() + x * cell_width
                        cell_y = bounds.y() + y * cell_height
                        painter.drawRect(int(cell_x), int(cell_y), int(cell_width), int(cell_height))
            
            # Draw circular bounds overlay
            overlay_pen = QPen(QColor(0, 255, 120, 120), 2, Qt.SolidLine)
            painter.setPen(overlay_pen)
            painter.setBrush(Qt.NoBrush)
            
            if layout_type == "circle":
                painter.drawEllipse(bounds)
            elif layout_type == "ring":
                painter.drawEllipse(bounds)
                if self._pattern_metadata and self._pattern_metadata.circular_inner_radius:
                    # Calculate inner radius proportion
                    outer_radius = self._pattern_metadata.circular_radius or (min(bounds.width(), bounds.height()) / 2.0)
                    inner_radius = self._pattern_metadata.circular_inner_radius
                    ratio = inner_radius / outer_radius if outer_radius > 0 else 0.2
                    inner = bounds.adjusted(
                        int(bounds.width() * ratio / 2),
                        int(bounds.height() * ratio / 2),
                        -int(bounds.width() * ratio / 2),
                        -int(bounds.height() * ratio / 2),
                    )
                    painter.drawEllipse(inner)
            elif layout_type == "arc":
                # Draw arc based on start/end angles
                start_angle = getattr(self._pattern_metadata, 'circular_start_angle', 0.0) if self._pattern_metadata else 0.0
                end_angle = getattr(self._pattern_metadata, 'circular_end_angle', 360.0) if self._pattern_metadata else 360.0
                span_angle = int((end_angle - start_angle) * 16)  # Qt uses 1/16th degree units
                start_angle_qt = int(start_angle * 16)
                painter.drawArc(bounds, start_angle_qt, span_angle)
            elif layout_type == "radial":
                # Draw concentric circles (rows = circles, cols = LEDs per circle)
                # This matches the radial preview interpretation
                num_circles = self._pattern_metadata.height if self._pattern_metadata else 1
                
        painter.restore()
        
        # Wiring overlay removed - only geometry overlays (radial rings, rectangular, irregular) are shown
    
    def _draw_wiring_overlay(self, painter: QPainter, bounds):
        """
        Draw wiring path overlay showing LED strip order.
        
        This visualizes how the LED strip is physically wired through the matrix,
        showing the data flow path based on wiring_mode and data_in_corner.
        """
        if not self._pattern_metadata:
            return
        
        from core.wiring_mapper import WiringMapper
        
        # Get wiring configuration
        wiring_mode = getattr(self._pattern_metadata, 'wiring_mode', 'Row-major')
        data_in_corner = getattr(self._pattern_metadata, 'data_in_corner', 'LT')
        
        # Check layout type
        layout_type = getattr(self._pattern_metadata, 'layout_type', 'rectangular')
        if layout_type != 'rectangular':
            # For circular layouts, use circular wiring overlay
            self._draw_circular_wiring_overlay(painter, bounds)
            return
        
        # Create wiring mapper to get the path
        mapper = WiringMapper(
            width=self._pattern_metadata.width,
            height=self._pattern_metadata.height,
            wiring_mode=wiring_mode,
            data_in_corner=data_in_corner
        )
        
        # Build the wiring path
        mapping = mapper._build_mapping_table()
        
        # Calculate cell size
        cell_width = bounds.width() / self._pattern_metadata.width
        cell_height = bounds.height() / self._pattern_metadata.height
        
        # Draw wiring path as arrows/lines
        wiring_pen = QPen(QColor(255, 200, 0, 150), 2, Qt.SolidLine)
        painter.setPen(wiring_pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
                
        # Draw path connecting LEDs in hardware order
        prev_x, prev_y = None, None
        for hw_idx in range(len(mapping)):
            design_idx = mapping[hw_idx]
            grid_x = design_idx % self._pattern_metadata.width
            grid_y = design_idx // self._pattern_metadata.width
            
            # Calculate pixel position
            x = bounds.x() + (grid_x + 0.5) * cell_width
            y = bounds.y() + (grid_y + 0.5) * cell_height
            
            # Draw line from previous position
            if prev_x is not None:
                painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
            
            prev_x, prev_y = x, y
            
            # Draw LED number (small, semi-transparent)
            if hw_idx < 50:  # Only show numbers for first 50 LEDs to avoid clutter
                painter.setPen(QPen(QColor(255, 200, 0, 100), 1))
                painter.setFont(QFont("Arial", max(6, int(min(cell_width, cell_height) * 0.3))))
                painter.drawText(int(x - cell_width/4), int(y + cell_height/4), str(hw_idx))
                painter.setPen(wiring_pen)
            
    def _draw_circular_wiring_overlay(self, painter: QPainter, bounds):
        """
        Draw circular wiring path overlay showing LED index order.
        
        This visualizes the physical LED wiring order for circular layouts,
        following the mapping table order (LED 0, 1, 2, ...).
        """
        if not self._pattern_metadata or not self._pattern_metadata.circular_mapping_table:
            return
        
        mapping_table = self._pattern_metadata.circular_mapping_table
        if not mapping_table:
            return
        
        # Calculate cell size
        cell_width = bounds.width() / self._matrix_width if self._matrix_width > 0 else 1
        cell_height = bounds.height() / self._matrix_height if self._matrix_height > 0 else 1
        
        # Draw wiring path as arrows/lines
        wiring_pen = QPen(QColor(255, 200, 0, 150), 2, Qt.SolidLine)
        painter.setPen(wiring_pen)
        painter.setRenderHint(QPainter.Antialiasing, True)
                        
        # Draw path connecting LEDs in index order (0, 1, 2, ...)
        prev_x, prev_y = None, None
        for led_idx in range(len(mapping_table)):
            # Get grid coordinate from mapping table
            grid_x, grid_y = mapping_table[led_idx]
            
            # Calculate pixel position
            x = bounds.x() + (grid_x + 0.5) * cell_width
            y = bounds.y() + (grid_y + 0.5) * cell_height
            
            # Draw line from previous position
            if prev_x is not None:
                painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
                
                # Draw arrow head
                from math import atan2, cos, sin, pi
                angle = atan2(y - prev_y, x - prev_x)
                arrow_size = 8
                arrow_x1 = x - arrow_size * cos(angle - pi / 6)
                arrow_y1 = y - arrow_size * sin(angle - pi / 6)
                arrow_x2 = x - arrow_size * cos(angle + pi / 6)
                arrow_y2 = y - arrow_size * sin(angle + pi / 6)
                painter.drawLine(int(x), int(y), int(arrow_x1), int(arrow_y1))
                painter.drawLine(int(x), int(y), int(arrow_x2), int(arrow_y2))
            
            prev_x, prev_y = x, y
            
            # Draw LED number (first 20 LEDs to avoid clutter)
            if led_idx < 20:
                painter.setPen(QPen(QColor(255, 200, 0, 200), 1))
                from PySide6.QtGui import QFont
                painter.setFont(QFont("Arial", max(6, int(min(cell_width, cell_height) * 0.3))))
                painter.drawText(int(x - cell_width/4), int(y + cell_height/4), str(led_idx))
                painter.setPen(wiring_pen)
            
            # Color-code start (green) and end (red) points
            if led_idx == 0:
                # Start point - green
                start_brush = QBrush(QColor(0, 255, 0, 150))
                painter.setBrush(start_brush)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)
                painter.setPen(wiring_pen)
                painter.setBrush(Qt.NoBrush)
            elif led_idx == len(mapping_table) - 1:
                # End point - red
                end_brush = QBrush(QColor(255, 0, 0, 150))
                painter.setBrush(end_brush)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x - 4), int(y - 4), 8, 8)
                painter.setPen(wiring_pen)
                painter.setBrush(Qt.NoBrush)
        
        # Also draw manual overlay if set (for preview purposes)
        if self._geometry_overlay != GeometryOverlay.MATRIX:
            overlay_pen = QPen(QColor(255, 255, 255, 80), 2, Qt.DashLine)
            painter.setPen(overlay_pen)
            
            if self._geometry_overlay == GeometryOverlay.RING:
                # Draw radial rings (outer and inner circles)
                painter.drawEllipse(bounds)
                inner = bounds.adjusted(
                    bounds.width() * 0.2,
                    bounds.height() * 0.2,
                    -bounds.width() * 0.2,
                    -bounds.height() * 0.2,
                )
                painter.drawEllipse(inner)
            elif self._geometry_overlay == GeometryOverlay.IRREGULAR:
                # Draw irregular shape overlay (if metadata has irregular shape info)
                if self._pattern_metadata and self._pattern_metadata.irregular_shape_enabled:
                    # Draw outline based on irregular shape mapping
                    from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                    # Draw active cells as a visual guide
                    for y in range(self._matrix_height):
                        for x in range(self._matrix_width):
                            if IrregularShapeMapper.is_cell_active(x, y, self._pattern_metadata):
                                cell_x = bounds.x() + (x * bounds.width() / self._matrix_width)
                                cell_y = bounds.y() + (y * bounds.height() / self._matrix_height)
                                cell_w = bounds.width() / self._matrix_width
                                cell_h = bounds.height() / self._matrix_height
                                painter.drawRect(int(cell_x), int(cell_y), int(cell_w), int(cell_h))

        painter.restore()

    def set_onion_skin_frames(
        self,
        prev_frames: List[List[List[RGB]]],
        next_frames: List[List[List[RGB]]],
        prev_opacities: List[float],
        next_opacities: List[float]
    ) -> None:
        """
        Set onion skin frames to display as overlays.
        
        Args:
            prev_frames: List of previous frame grids (2D arrays)
            next_frames: List of next frame grids (2D arrays)
            prev_opacities: Opacity for each previous frame (0.0-1.0)
            next_opacities: Opacity for each next frame (0.0-1.0)
        """
        self._onion_skin_prev_frames = prev_frames
        self._onion_skin_next_frames = next_frames
        self._onion_skin_prev_opacities = prev_opacities
        self._onion_skin_next_opacities = next_opacities
        self.update()

    def _draw_onion_skins(self, painter: QPainter):
        """Draw onion skin overlays for previous and next frames."""
        if not self._onion_skin_prev_frames and not self._onion_skin_next_frames:
            return
        
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        # Draw previous frames (behind current, but we draw after so they appear ghosted)
        for i, (prev_grid, opacity) in enumerate(zip(self._onion_skin_prev_frames, self._onion_skin_prev_opacities)):
            if opacity <= 0.0 or not prev_grid:
                continue
            for y in range(min(len(prev_grid), self._matrix_height)):
                row = prev_grid[y] if prev_grid[y] else []
                for x in range(min(len(row), self._matrix_width)):
                    color = row[x]
                    if not color:
                        continue
                    rect_x = x * self._pixel_size + 1
                    rect_y = y * self._pixel_size + 1
                    rect_w = self._pixel_size - 2
                    rect_h = self._pixel_size - 2
                    
                    # Draw with reduced opacity
                    r, g, b = color if isinstance(color, tuple) else (color[0], color[1], color[2])
                    qcolor = QColor(r, g, b)
                    qcolor.setAlphaF(opacity)
                    painter.setBrush(QBrush(qcolor))
                    painter.setPen(Qt.NoPen)
                    self._draw_pixel_tile(painter, rect_x, rect_y, rect_w, rect_h, (r, g, b))
        
        # Draw next frames (on top, but still semi-transparent)
        for i, (next_grid, opacity) in enumerate(zip(self._onion_skin_next_frames, self._onion_skin_next_opacities)):
            if opacity <= 0.0 or not next_grid:
                continue
            for y in range(min(len(next_grid), self._matrix_height)):
                row = next_grid[y] if next_grid[y] else []
                for x in range(min(len(row), self._matrix_width)):
                    color = row[x]
                    if not color:
                        continue
                    rect_x = x * self._pixel_size + 1
                    rect_y = y * self._pixel_size + 1
                    rect_w = self._pixel_size - 2
                    rect_h = self._pixel_size - 2
                    
                    # Draw with reduced opacity
                    r, g, b = color if isinstance(color, tuple) else (color[0], color[1], color[2])
                    qcolor = QColor(r, g, b)
                    qcolor.setAlphaF(opacity)
                    painter.setBrush(QBrush(qcolor))
                    painter.setPen(Qt.NoPen)
                    self._draw_pixel_tile(painter, rect_x, rect_y, rect_w, rect_h, (r, g, b))
        
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


