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
        
        # Get drawing area (below label)
        draw_rect = self.rect().adjusted(10, 35, -10, -10)
        
        if layout_type == "radial":
            self._paint_radial_preview(painter, draw_rect)
        elif layout_type == "multi_ring":
            self._paint_multi_ring_preview(painter, draw_rect)
        elif layout_type == "radial_rays":
            self._paint_radial_ray_preview(painter, draw_rect)
        elif layout_type == "custom_positions":
            self._paint_custom_position_preview(painter, draw_rect)
        else:
            self._paint_circular_preview(painter, draw_rect)
    
    def _paint_radial_preview(self, painter: QPainter, rect):
        """Paint radial preview: rows = circles, columns = LEDs per circle."""
        if not self._grid_data:
            return
        
        num_circles = len(self._grid_data)  # rows
        if num_circles == 0:
            return
        
        leds_per_circle = len(self._grid_data[0]) if self._grid_data[0] else 0
        if leds_per_circle == 0:
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        max_radius = min(rect.width(), rect.height()) / 2 - 10
        min_radius = max_radius * 0.15
        radius_delta = (max_radius - min_radius) / max(1, num_circles - 1) if num_circles > 1 else 0
        
        # Calculate pixel size
        pixel_size = max(4, int(max_radius / max(num_circles, 1) * 0.3))
        
        # Render concentric circles
        for row in range(num_circles):
            if row >= len(self._grid_data):
                continue
            
            # Calculate radius for this circle
            radius = min_radius + radius_delta * row
            
            # Render LEDs around this circle
            for col in range(leds_per_circle):
                if col >= len(self._grid_data[row]):
                    continue
                
                # Calculate angle for this LED position
                angle = 2 * pi * (col / max(1, leds_per_circle))
                
                # Calculate LED position
                x = center_x + radius * cos(angle)
                y = center_y + radius * sin(angle)
                
                # Get pixel color from grid
                r, g, b = self._grid_data[row][col]
                
                # Draw LED
                color = QColor(r, g, b)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(self._pixel_border_color, 1))
                painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
    
    def _paint_circular_preview(self, painter: QPainter, rect):
        """Paint circular/ring/arc preview using mapping table."""
        if not self._grid_data or not self._pattern_metadata:
            return
        
        # Ensure mapping table exists
        if not CircularMapper.ensure_mapping_table(self._pattern_metadata):
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignCenter, "Failed to generate\nmapping table")
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        outer_radius = min(rect.width(), rect.height()) / 2 - 10
        pixel_size = max(4, int(outer_radius / 20))
        
        # Get LED positions
        led_count = self._pattern_metadata.circular_led_count or len(self._pattern_metadata.circular_mapping_table)
        
        if not self._pattern_metadata.circular_mapping_table:
            return
        
        # Get LED positions in polar coordinates
        positions = CircularMapper.generate_circular_positions(
            led_count=led_count,
            radius=self._pattern_metadata.circular_radius or outer_radius,
            start_angle=self._pattern_metadata.circular_start_angle,
            end_angle=self._pattern_metadata.circular_end_angle,
            inner_radius=self._pattern_metadata.circular_inner_radius
        )
        
        # Draw each LED
        for led_idx in range(min(led_count, len(self._pattern_metadata.circular_mapping_table))):
            # Get grid coordinate from mapping table
            grid_x, grid_y = self._pattern_metadata.circular_mapping_table[led_idx]
            
            # Get pixel color from grid
            if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                r, g, b = self._grid_data[grid_y][grid_x]
            else:
                r, g, b = (0, 0, 0)
            
            # Get LED position
            if led_idx < len(positions):
                angle, led_radius = positions[led_idx]
                x = center_x + led_radius * cos(angle)
                y = center_y + led_radius * sin(angle)
            else:
                continue
            
            # Draw LED
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self._pixel_border_color, 1))
            painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
    
    def _paint_multi_ring_preview(self, painter: QPainter, rect):
        """Paint multi-ring preview: multiple concentric rings (Budurasmala)."""
        if not self._grid_data or not self._pattern_metadata:
            return
        
        # Ensure mapping table exists
        if not CircularMapper.ensure_mapping_table(self._pattern_metadata):
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignCenter, "Failed to generate\nmapping table")
            return
        
        if not self._pattern_metadata.circular_mapping_table:
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        max_radius = min(rect.width(), rect.height()) / 2 - 10
        pixel_size = max(4, int(max_radius / 30))
        
        # Get ring configuration
        ring_count = self._pattern_metadata.multi_ring_count or 1
        ring_led_counts = self._pattern_metadata.ring_led_counts or []
        ring_radii = self._pattern_metadata.ring_radii or []
        
        if not ring_led_counts or not ring_radii:
            # Fallback: use mapping table directly
            self._paint_circular_preview(painter, rect)
            return
        
        # Scale radii to fit display
        max_physical_radius = max(ring_radii) if ring_radii else 10.0
        scale_factor = (max_radius * 0.9) / max_physical_radius if max_physical_radius > 0 else 1.0
        
        # Draw each ring
        led_idx = 0
        for ring_idx in range(ring_count):
            if ring_idx >= len(ring_led_counts) or ring_idx >= len(ring_radii):
                continue
            
            led_count_for_ring = ring_led_counts[ring_idx]
            physical_radius = ring_radii[ring_idx]
            display_radius = physical_radius * scale_factor
            
            # Draw LEDs for this ring
            for led_in_ring in range(led_count_for_ring):
                if led_idx >= len(self._pattern_metadata.circular_mapping_table):
                    break
                
                # Get grid coordinate from mapping table
                grid_x, grid_y = self._pattern_metadata.circular_mapping_table[led_idx]
                
                # Get pixel color from grid
                if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                    r, g, b = self._grid_data[grid_y][grid_x]
                else:
                    r, g, b = (0, 0, 0)
                
                # Calculate angle for this LED in the ring
                angle = 2 * pi * (led_in_ring / max(1, led_count_for_ring))
                
                # Calculate LED position
                x = center_x + display_radius * cos(angle)
                y = center_y + display_radius * sin(angle)
                
                # Draw LED with slightly different color intensity per ring for visibility
                color = QColor(r, g, b)
                # Slightly dim inner rings for visual distinction
                if ring_idx > 0:
                    color.setRed(int(color.red() * 0.9))
                    color.setGreen(int(color.green() * 0.9))
                    color.setBlue(int(color.blue() * 0.9))
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(self._pixel_border_color, 1))
                painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
                
                led_idx += 1
    
    def _paint_radial_ray_preview(self, painter: QPainter, rect):
        """Paint radial ray preview: LEDs along rays extending from center (Budurasmala)."""
        if not self._grid_data or not self._pattern_metadata:
            return
        
        # Ensure mapping table exists
        if not CircularMapper.ensure_mapping_table(self._pattern_metadata):
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignCenter, "Failed to generate\nmapping table")
            return
        
        if not self._pattern_metadata.circular_mapping_table:
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        max_radius = min(rect.width(), rect.height()) / 2 - 10
        pixel_size = max(4, int(max_radius / 25))
        
        # Get ray configuration
        ray_count = self._pattern_metadata.ray_count or 8
        leds_per_ray = self._pattern_metadata.leds_per_ray or 10
        
        # Calculate ray spacing angle
        if self._pattern_metadata.ray_spacing_angle:
            ray_spacing_rad = pi * self._pattern_metadata.ray_spacing_angle / 180.0
        else:
            ray_spacing_rad = (2 * pi) / ray_count
        
        # Draw each ray
        led_idx = 0
        for ray_idx in range(ray_count):
            ray_angle = ray_idx * ray_spacing_rad
            
            # Draw LEDs along this ray
            for led_in_ray in range(leds_per_ray):
                if led_idx >= len(self._pattern_metadata.circular_mapping_table):
                    break
                
                # Get grid coordinate from mapping table
                grid_x, grid_y = self._pattern_metadata.circular_mapping_table[led_idx]
                
                # Get pixel color from grid
                if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                    r, g, b = self._grid_data[grid_y][grid_x]
                else:
                    r, g, b = (0, 0, 0)
                
                # Calculate distance from center (evenly spaced along ray)
                t = (led_in_ray + 1) / leds_per_ray  # 0 to 1
                led_radius = t * max_radius
                
                # Calculate LED position
                x = center_x + led_radius * cos(ray_angle)
                y = center_y + led_radius * sin(ray_angle)
                
                # Draw LED
                color = QColor(r, g, b)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(self._pixel_border_color, 1))
                painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
                
                led_idx += 1
    
    def _paint_custom_position_preview(self, painter: QPainter, rect):
        """Paint custom position preview: LEDs at custom (x, y) positions (Budurasmala)."""
        if not self._grid_data or not self._pattern_metadata:
            return
        
        if not self._pattern_metadata.custom_led_positions:
            # No custom positions defined
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignCenter, "No custom positions\ndefined")
            return
        
        # Calculate display parameters
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        # Get bounds of custom positions to scale them
        positions = self._pattern_metadata.custom_led_positions
        if not positions:
            return
        
        # Find min/max for scaling
        x_coords = [p[0] for p in positions]
        y_coords = [p[1] for p in positions]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Calculate scale to fit in preview
        width_range = max_x - min_x if max_x > min_x else 1.0
        height_range = max_y - min_y if max_y > min_y else 1.0
        max_range = max(width_range, height_range)
        
        # Scale factor to fit in preview (leave 20px margin)
        available_width = rect.width() - 20
        available_height = rect.height() - 20
        scale = min(available_width / max_range, available_height / max_range) if max_range > 0 else 1.0
        
        # Calculate pixel size
        pixel_size = max(4, int(min(available_width, available_height) / max(len(positions), 1) * 0.1))
        
        # Ensure mapping table exists
        if not self._pattern_metadata.circular_mapping_table:
            from core.mapping.circular_mapper import CircularMapper
            CircularMapper.ensure_mapping_table(self._pattern_metadata)
        
        # Draw each LED at its custom position
        for led_idx, (pos_x, pos_y) in enumerate(positions):
            # Normalize position to 0-based
            normalized_x = (pos_x - min_x) / max_range if max_range > 0 else 0.5
            normalized_y = (pos_y - min_y) / max_range if max_range > 0 else 0.5
            
            # Scale to preview coordinates
            x = center_x + (normalized_x - 0.5) * available_width
            y = center_y + (normalized_y - 0.5) * available_height
            
            # Get pixel color from grid using mapping table
            if led_idx < len(self._pattern_metadata.circular_mapping_table):
                grid_x, grid_y = self._pattern_metadata.circular_mapping_table[led_idx]
                if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                    r, g, b = self._grid_data[grid_y][grid_x]
                else:
                    r, g, b = (0, 0, 0)
            else:
                r, g, b = (0, 0, 0)
            
            # Draw LED
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self._pixel_border_color, 1))
            painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)

