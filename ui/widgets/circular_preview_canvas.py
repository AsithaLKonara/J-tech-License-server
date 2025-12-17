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
from core.mapping.circular_mapper import CircularMapper

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
        # Always regenerate mapping table for circular layouts to ensure latest logic
        if metadata and metadata.layout_type not in ["rectangular", "irregular"]:
            try:
                # Force regeneration - don't rely on ensure_mapping_table which may skip if valid
                metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
            except Exception as e:
                import logging
                logging.warning(
                    f"CircularPreviewCanvas: Failed to generate mapping table for layout type {metadata.layout_type}: {e}"
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
        
        if layout_type == "irregular":
            # Show message that circular preview is for circular layouts
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "Irregular shapes use\nthe main canvas view")
            return
        
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
        Paint preview using mapping table and actual LED positions from layout geometry.
        
        This method uses the actual LED physical positions (like LED Matrix Studio would):
        - LED index -> grid coordinate mapping (from mapping table)
        - Grid data (colors)
        - Actual LED positions from layout geometry (angle, radius from layout parameters)
        
        This matches the LED Matrix Studio approach where LEDs are positioned at their
        actual physical locations based on the layout configuration.
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
        
        # Get actual LED positions from layout geometry (LED Matrix Studio style)
        # This uses the real physical positions based on layout parameters
        led_positions = CircularMapper.generate_led_positions_for_preview(
            metadata=self._pattern_metadata,
            center_x=center_x,
            center_y=center_y,
            max_radius=max_radius
        )
        
        # Render LEDs using actual positions
        led_count = len(mapping_table)
        
        # Debug logging to verify mapping table order
        if led_count > 0:
            import logging
            logger = logging.getLogger(__name__)
            # Log first few mappings to verify order
            for i in range(min(3, led_count)):
                grid_x, grid_y = mapping_table[i]
                logger.debug(f"LED {i} -> grid({grid_x}, {grid_y}) = row {grid_y}")
            if led_count > 3:
                grid_x, grid_y = mapping_table[led_count - 1]
                logger.debug(f"LED {led_count-1} -> grid({grid_x}, {grid_y}) = row {grid_y}")
        
        for led_idx in range(led_count):
            # Get grid coordinate from mapping table (single source of truth)
            grid_x, grid_y = mapping_table[led_idx]
            
            # Get pixel color from grid
            if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                r, g, b = self._grid_data[grid_y][grid_x]
            else:
                r, g, b = (0, 0, 0)
            
            # Get actual LED position from layout geometry
            if led_idx < len(led_positions):
                x, y = led_positions[led_idx]
            else:
                # Fallback: simple circular arrangement if positions not available
                angle = 2 * pi * (led_idx / led_count) if led_count > 0 else 0
                radius = max_radius * 0.8
                x = center_x + radius * cos(angle)
                y = center_y + radius * sin(angle)
            
            # Draw LED at actual position
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self._pixel_border_color, 1))
            painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)

