"""
Irregular Shape Editor - Interactive widget for defining active/inactive cells.

This widget allows users to click on grid cells to toggle them active/inactive,
similar to LED Build's irregular shape editor.
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple, Optional
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QSize, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QImage
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QVBoxLayout, QLabel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import PatternMetadata
from core.mapping.irregular_shape_mapper import IrregularShapeMapper

RGB = Tuple[int, int, int]


class IrregularShapeEditor(QWidget):
    """
    Interactive editor for defining irregular shapes.
    
    Users can click cells to toggle them active/inactive.
    Supports background image overlay for template-based placement.
    """
    
    # Signal emitted when active cells change
    active_cells_changed = Signal()
    
    def __init__(self, width: int = 12, height: int = 12, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Grid dimensions
        self._grid_width: int = max(1, width)
        self._grid_height: int = max(1, height)
        
        # Active cell coordinates (sparse list)
        self._active_cells: List[Tuple[int, int]] = []
        
        # Background image
        self._background_image: Optional[QPixmap] = None
        self._background_image_path: Optional[str] = None
        self._background_scale: float = 1.0
        self._background_offset_x: float = 0.0
        self._background_offset_y: float = 0.0
        
        # Visual settings
        self._cell_size: int = 20  # Pixels per cell
        self._active_color = QColor(0, 255, 120)  # Green for active
        self._inactive_color = QColor(60, 60, 60)  # Dark gray for inactive
        self._grid_line_color = QColor(100, 100, 100)  # Gray grid lines
        self._background_color = QColor(34, 34, 34)  # Dark background
        
        # Editor mode
        self._mode: str = "paint"  # "paint" or "erase"
        
        # Initialize to all cells active
        self._initialize_all_active()
        
        self.setMinimumSize(300, 300)
        self.setMouseTracking(True)
    
    def set_grid_size(self, width: int, height: int):
        """Set grid dimensions."""
        self._grid_width = max(1, width)
        self._grid_height = max(1, height)
        self._initialize_all_active()
        self.update()
    
    def _initialize_all_active(self):
        """Initialize all cells as active."""
        self._active_cells = [
            (x, y) 
            for y in range(self._grid_height) 
            for x in range(self._grid_width)
        ]
    
    def set_background_image(self, image_path: str):
        """Load and set background image."""
        if not Path(image_path).exists():
            return
        
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self._background_image = pixmap
                self._background_image_path = image_path
                # Auto-scale to fit grid
                self._auto_scale_background()
                self.update()
        except Exception as e:
            print(f"Failed to load background image: {e}")
    
    def _auto_scale_background(self):
        """Auto-scale background image to fit grid."""
        if not self._background_image:
            return
        
        # Calculate target size (grid size in pixels)
        target_width = self._grid_width * self._cell_size
        target_height = self._grid_height * self._cell_size
        
        # Scale image to fit
        scaled = self._background_image.scaled(
            target_width, 
            target_height, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._background_image = scaled
        self._background_scale = 1.0
        self._background_offset_x = 0.0
        self._background_offset_y = 0.0
    
    def get_active_cells(self) -> List[Tuple[int, int]]:
        """Get list of active cell coordinates."""
        return self._active_cells.copy()
    
    def set_active_cells(self, cells: List[Tuple[int, int]]):
        """Set active cell coordinates."""
        # Validate coordinates
        valid_cells = [
            (x, y) for x, y in cells
            if 0 <= x < self._grid_width and 0 <= y < self._grid_height
        ]
        self._active_cells = valid_cells
        self.update()
        self.active_cells_changed.emit()
    
    def _cell_from_point(self, point: QPoint) -> Optional[Tuple[int, int]]:
        """Convert screen point to grid cell coordinates."""
        # Calculate grid bounds
        grid_width_px = self._grid_width * self._cell_size
        grid_height_px = self._grid_height * self._cell_size
        
        # Center grid in widget
        offset_x = (self.width() - grid_width_px) // 2
        offset_y = (self.height() - grid_height_px) // 2
        
        # Adjust for offset
        adj_x = point.x() - offset_x
        adj_y = point.y() - offset_y
        
        # Convert to cell coordinates
        if adj_x < 0 or adj_y < 0:
            return None
        
        cell_x = adj_x // self._cell_size
        cell_y = adj_y // self._cell_size
        
        if 0 <= cell_x < self._grid_width and 0 <= cell_y < self._grid_height:
            return (cell_x, cell_y)
        
        return None
    
    def _toggle_cell(self, x: int, y: int):
        """Toggle cell active/inactive state."""
        cell = (x, y)
        if cell in self._active_cells:
            self._active_cells.remove(cell)
        else:
            self._active_cells.append(cell)
        self.update()
        self.active_cells_changed.emit()
    
    def mousePressEvent(self, event):
        """Handle mouse click to toggle cells."""
        if event.button() == Qt.LeftButton:
            cell = self._cell_from_point(event.position().toPoint())
            if cell:
                x, y = cell
                self._toggle_cell(x, y)
    
    def mouseMoveEvent(self, event):
        """Handle mouse drag to toggle multiple cells."""
        if event.buttons() & Qt.LeftButton:
            cell = self._cell_from_point(event.position().toPoint())
            if cell:
                x, y = cell
                # Only toggle if not already in desired state
                cell_tuple = (x, y)
                if self._mode == "paint":
                    if cell_tuple not in self._active_cells:
                        self._active_cells.append(cell_tuple)
                        self.update()
                        self.active_cells_changed.emit()
                elif self._mode == "erase":
                    if cell_tuple in self._active_cells:
                        self._active_cells.remove(cell_tuple)
                        self.update()
                        self.active_cells_changed.emit()
    
    def paintEvent(self, event):
        """Paint the editor."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background
        painter.fillRect(self.rect(), self._background_color)
        
        # Calculate grid bounds
        grid_width_px = self._grid_width * self._cell_size
        grid_height_px = self._grid_height * self._cell_size
        
        # Center grid in widget
        offset_x = (self.width() - grid_width_px) // 2
        offset_y = (self.height() - grid_height_px) // 2
        
        # Draw background image if available
        if self._background_image:
            painter.setOpacity(0.3)  # Semi-transparent
            painter.drawPixmap(
                offset_x + int(self._background_offset_x),
                offset_y + int(self._background_offset_y),
                self._background_image
            )
            painter.setOpacity(1.0)
        
        # Draw grid cells
        for y in range(self._grid_height):
            for x in range(self._grid_width):
                cell_x = offset_x + x * self._cell_size
                cell_y = offset_y + y * self._cell_size
                
                # Determine if cell is active
                is_active = (x, y) in self._active_cells
                
                # Draw cell
                if is_active:
                    painter.setBrush(QBrush(self._active_color))
                else:
                    painter.setBrush(QBrush(self._inactive_color))
                
                painter.setPen(QPen(self._grid_line_color, 1))
                painter.drawRect(cell_x, cell_y, self._cell_size, self._cell_size)
        
        # Draw grid lines
        painter.setPen(QPen(self._grid_line_color, 1))
        for x in range(self._grid_width + 1):
            line_x = offset_x + x * self._cell_size
            painter.drawLine(line_x, offset_y, line_x, offset_y + grid_height_px)
        
        for y in range(self._grid_height + 1):
            line_y = offset_y + y * self._cell_size
            painter.drawLine(offset_x, line_y, offset_x + grid_width_px, line_y)
    
    def clear_all(self):
        """Clear all cells (make all inactive)."""
        self._active_cells = []
        self.update()
        self.active_cells_changed.emit()
    
    def fill_all(self):
        """Fill all cells (make all active)."""
        self._initialize_all_active()
        self.update()
        self.active_cells_changed.emit()
    
    def set_mode(self, mode: str):
        """Set editor mode: 'paint' or 'erase'."""
        if mode in ["paint", "erase"]:
            self._mode = mode

