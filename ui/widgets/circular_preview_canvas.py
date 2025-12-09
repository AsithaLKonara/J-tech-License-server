"""
Circular Preview Canvas - Read-only circular preview of grid data.

This widget displays the rectangular grid data in a circular/radial arrangement.
It's read-only and updates in real-time as the user draws on the main canvas.
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple, Optional
from math import cos, sin, pi

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtWidgets import QWidget, QLabel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import PatternMetadata

RGB = Tuple[int, int, int]


class CircularPreviewCanvas(QWidget):
    """
    Read-only circular preview canvas.
    
    Displays grid pixels in circular/radial arrangement based on layout_type.
    Updates in real-time when grid data changes.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._grid_data: Optional[List[List[RGB]]] = None
        self._pattern_metadata: Optional[PatternMetadata] = None
        self._background_color = QColor(34, 34, 34)
        self._pixel_border_color = QColor(18, 18, 18)
        
        # Add label
        self._label = QLabel("Circular Preview", self)
        self._label.setStyleSheet("color: #DDDDDD; font-weight: bold; padding: 4px;")
        self._label.setAlignment(Qt.AlignCenter)
        
        self.setMinimumWidth(200)
        self.setMinimumHeight(200)
        
    def set_grid_data(self, grid: List[List[RGB]]):
        """Update grid data and refresh preview."""
        self._grid_data = grid
        self.update()
    
    def set_pattern_metadata(self, metadata: Optional[PatternMetadata]):
        """Set pattern metadata for layout information."""
        self._pattern_metadata = metadata
        # Validate mapping table exists for circular layouts
        if metadata and metadata.layout_type != "rectangular":
            if not metadata.circular_mapping_table:
                import logging
                logging.warning(
                    f"CircularPreviewCanvas: No mapping table for layout type {metadata.layout_type}. "
                    f"Preview will not render correctly."
                )
        self.update()
    
    def paintEvent(self, event):
        """Paint circular preview."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background
        painter.fillRect(self.rect(), self._background_color)
        
        # Draw label at top
        label_rect = self.rect().adjusted(0, 0, 0, -self.height() + 30)
        self._label.setGeometry(label_rect)
        
        if not self._grid_data or not self._pattern_metadata:
            # No data to display
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "No pattern data")
            return
        
        layout_type = getattr(self._pattern_metadata, 'layout_type', 'rectangular')
        
        if layout_type == "rectangular":
            # Show message that circular preview is for circular layouts
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "Select circular layout\nto see preview")
            return
        
        # Validate mapping table exists (required for circular layouts)
        if not self._pattern_metadata.circular_mapping_table:
            painter.setPen(QColor(200, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "No mapping table\navailable")
            return
        
        # Get drawing area (below label)
        draw_rect = self.rect().adjusted(10, 35, -10, -10)
        
        # Render using mapping table only (passive rendering)
        self._paint_from_mapping_table(painter, draw_rect)
    
    def _paint_from_mapping_table(self, painter: QPainter, rect):
        """
        Paint preview using mapping table only (passive rendering).
        
        This method does NOT know about layout types. It only knows:
        - LED index -> grid coordinate mapping
        - Grid data (colors)
        - Visual arrangement is calculated from LED index order (simple circular)
        """
        if not self._grid_data or not self._pattern_metadata:
            return
        
        mapping_table = self._pattern_metadata.circular_mapping_table
        if not mapping_table:
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        max_radius = min(rect.width(), rect.height()) / 2 - 10
        pixel_size = max(4, int(max_radius / max(len(mapping_table), 1) * 0.15))
        
        # Render LEDs in index order (0, 1, 2, ...)
        # Visual arrangement: simple circular layout based on LED index
        led_count = len(mapping_table)
        
        for led_idx in range(led_count):
            # Get grid coordinate from mapping table (single source of truth)
            grid_x, grid_y = mapping_table[led_idx]
            
            # Get pixel color from grid
            if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                r, g, b = self._grid_data[grid_y][grid_x]
            else:
                r, g, b = (0, 0, 0)
            
            # Calculate visual position from LED index (simple circular arrangement)
            # This is a simple circular layout - LED index determines position
            # Angle based on LED index order
            angle = 2 * pi * (led_idx / led_count) if led_count > 0 else 0
            
            # For multi-ring or complex layouts, the mapping table already encodes
            # the correct grid positions. We just arrange them in a simple circle
            # for preview purposes. The actual physical layout is encoded in the
            # mapping table order.
            
            # Use a simple circular radius (could be enhanced to show structure)
            # For now, use a single radius for all LEDs
            radius = max_radius * 0.8
            
            # Calculate LED position
            x = center_x + radius * cos(angle)
            y = center_y + radius * sin(angle)
            
            # Draw LED
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self._pixel_border_color, 1))
            painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)

