"""
3D Preview Widget - 3D visualization of Budurasmala halo around statue.

This widget provides a 3D perspective view of the circular LED display
showing how it appears as a halo around a Buddha statue.
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple, Optional
from math import cos, sin, pi, radians

from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF
from PySide6.QtWidgets import QWidget, QLabel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import PatternMetadata, Frame

RGB = Tuple[int, int, int]


class Budurasmala3DPreview(QWidget):
    """
    3D preview widget showing Budurasmala halo around statue.
    
    Uses perspective projection to show a 3D view of the circular LED display.
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._pattern_metadata: Optional[PatternMetadata] = None
        self._current_frame: Optional[Frame] = None
        self._grid_data: Optional[List[List[RGB]]] = None
        self._background_color = QColor(20, 20, 30)
        
        # 3D view parameters
        self._view_angle = 45.0  # Viewing angle in degrees
        self._rotation_angle = 0.0  # Rotation around Y axis
        self._statue_height_ratio = 0.6  # Statue height as ratio of display radius
        
        # Add label
        self._label = QLabel("3D Preview", self)
        self._label.setStyleSheet("color: #DDDDDD; font-weight: bold; padding: 4px;")
        self._label.setAlignment(Qt.AlignCenter)
        
        self.setMinimumWidth(300)
        self.setMinimumHeight(300)
    
    def set_pattern_metadata(self, metadata: Optional[PatternMetadata]):
        """Set pattern metadata."""
        self._pattern_metadata = metadata
        self.update()
    
    def set_frame(self, frame: Optional[Frame]):
        """Set current frame to display."""
        self._current_frame = frame
        self.update()
    
    def set_grid_data(self, grid: List[List[RGB]]):
        """Set grid data for preview."""
        self._grid_data = grid
        self.update()
    
    def set_view_angle(self, angle: float):
        """Set viewing angle (0-90 degrees)."""
        self._view_angle = max(0.0, min(90.0, angle))
        self.update()
    
    def set_rotation(self, angle: float):
        """Set rotation angle around Y axis (0-360 degrees)."""
        self._rotation_angle = angle
        self.update()
    
    def paintEvent(self, event):
        """Paint 3D preview."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background
        painter.fillRect(self.rect(), self._background_color)
        
        # Draw label
        label_rect = self.rect().adjusted(0, 0, 0, -self.height() + 30)
        self._label.setGeometry(label_rect)
        
        if not self._pattern_metadata:
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(self.rect(), Qt.AlignCenter, "No pattern data")
            return
        
        # Get drawing area
        draw_rect = self.rect().adjusted(10, 35, -10, -10)
        
        # Draw 3D scene
        self._draw_3d_scene(painter, draw_rect)
    
    def _draw_3d_scene(self, painter: QPainter, rect):
        """Draw 3D scene with statue and halo."""
        center_x = rect.center().x()
        center_y = rect.center().y()
        
        # Calculate display radius
        display_radius = min(rect.width(), rect.height()) / 2 - 20
        
        # Convert view angle to perspective factor
        view_rad = radians(self._view_angle)
        perspective_factor = sin(view_rad)  # 0 (top view) to 1 (side view)
        
        # Draw ground plane
        ground_y = center_y + display_radius * 0.3
        ground_pen = QPen(QColor(40, 40, 50), 1)
        painter.setPen(ground_pen)
        painter.drawLine(
            int(rect.left()),
            int(ground_y),
            int(rect.right()),
            int(ground_y)
        )
        
        # Draw statue (simplified as a vertical rectangle)
        statue_width = display_radius * 0.2
        statue_height = display_radius * self._statue_height_ratio
        
        # Apply perspective to statue
        statue_top_y = ground_y - statue_height * (1 - perspective_factor * 0.3)
        statue_bottom_y = ground_y
        
        statue_rect = QPolygonF([
            QPointF(center_x - statue_width / 2, statue_bottom_y),
            QPointF(center_x + statue_width / 2, statue_bottom_y),
            QPointF(center_x + statue_width / 2 * (1 - perspective_factor * 0.2), statue_top_y),
            QPointF(center_x - statue_width / 2 * (1 - perspective_factor * 0.2), statue_top_y),
        ])
        
        statue_brush = QBrush(QColor(200, 180, 150))
        statue_pen = QPen(QColor(150, 130, 100), 2)
        painter.setBrush(statue_brush)
        painter.setPen(statue_pen)
        painter.drawPolygon(statue_rect)
        
        # Draw halo (circular LED display)
        if self._pattern_metadata.layout_type != "rectangular":
            self._draw_3d_halo(painter, center_x, ground_y - statue_height * 0.7, 
                             display_radius, perspective_factor)
    
    def _draw_3d_halo(self, painter: QPainter, center_x: float, center_y: float, 
                     radius: float, perspective_factor: float):
        """Draw 3D halo (circular LED display) around statue."""
        # Calculate ellipse for perspective view
        # Horizontal radius stays same, vertical radius shrinks with perspective
        ellipse_width = radius * 2
        ellipse_height = radius * 2 * (1 - perspective_factor * 0.5)
        
        # Apply rotation
        rotation_rad = radians(self._rotation_angle)
        
        # Draw LED ring
        if self._pattern_metadata.circular_mapping_table and self._grid_data:
            led_count = len(self._pattern_metadata.circular_mapping_table)
            
            for led_idx in range(led_count):
                if led_idx >= len(self._pattern_metadata.circular_mapping_table):
                    continue
                
                # Get LED angle
                angle = (2 * pi * led_idx / led_count) + rotation_rad
                
                # Calculate 3D position (on circle)
                x_3d = cos(angle) * radius
                y_3d = sin(angle) * radius
                z_3d = 0  # On the plane
                
                # Apply perspective projection
                # Simple perspective: x stays, y shrinks, z affects y
                x_2d = center_x + x_3d
                y_2d = center_y + y_3d * (1 - perspective_factor * 0.3) - z_3d * perspective_factor * 0.2
                
                # Get LED color
                grid_x, grid_y = self._pattern_metadata.circular_mapping_table[led_idx]
                if 0 <= grid_y < len(self._grid_data) and 0 <= grid_x < len(self._grid_data[grid_y]):
                    r, g, b = self._grid_data[grid_y][grid_x]
                else:
                    r, g, b = (50, 50, 50)
                
                # Draw LED
                led_size = max(3, int(radius / led_count * 2))
                color = QColor(r, g, b)
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawEllipse(int(x_2d - led_size / 2), int(y_2d - led_size / 2), 
                                   led_size, led_size)
        else:
            # Fallback: draw simple circle
            ellipse_rect = QPolygonF([
                QPointF(center_x - ellipse_width / 2, center_y - ellipse_height / 2),
                QPointF(center_x + ellipse_width / 2, center_y - ellipse_height / 2),
                QPointF(center_x + ellipse_width / 2, center_y + ellipse_height / 2),
                QPointF(center_x - ellipse_width / 2, center_y + ellipse_height / 2),
            ])
            
            halo_pen = QPen(QColor(255, 215, 0, 150), 2)
            painter.setPen(halo_pen)
            painter.setBrush(QBrush(QColor(255, 215, 0, 30)))
            painter.drawEllipse(int(center_x - ellipse_width / 2), 
                               int(center_y - ellipse_height / 2),
                               int(ellipse_width), int(ellipse_height))

