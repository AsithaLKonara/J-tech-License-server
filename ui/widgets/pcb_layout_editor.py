"""
PCB Layout Editor - Basic PCB layout editor for LED placement.

This widget provides a simple interface for placing LEDs on a PCB layout
and exporting to PCB design tools.
"""

from __future__ import annotations

import sys
import os
from typing import List, Tuple, Optional
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pcb.pcb_exporter import PCBExporter


class PCBLayoutEditor(QWidget):
    """
    Basic PCB layout editor for LED placement.
    
    Allows placing LEDs on a PCB layout and exporting to PCB design tools.
    """
    
    # Signals
    positions_changed = Signal(list)  # Emitted when LED positions change
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._led_positions: List[Tuple[float, float]] = []
        self._board_width_mm = 100.0  # Default board size
        self._board_height_mm = 100.0
        self._scale = 1.0  # Pixels per mm
        self._selected_led: Optional[int] = None
        self._background_color = QColor(30, 30, 40)
        self._board_color = QColor(50, 50, 60)
        self._led_color = QColor(255, 200, 0)
        
        # UI
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton("Add LED")
        add_btn.clicked.connect(self._on_add_led)
        toolbar.addWidget(add_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_all)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        
        export_btn = QPushButton("Export...")
        export_btn.clicked.connect(self._on_export)
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        # Status label
        self._status_label = QLabel("Click 'Add LED' to place LEDs on the board")
        self._status_label.setStyleSheet("color: #AAAAAA; padding: 4px;")
        layout.addWidget(self._status_label)
        
        self.setMinimumSize(400, 400)
        self.setMouseTracking(True)
    
    def set_board_size(self, width_mm: float, height_mm: float):
        """Set board size in millimeters."""
        self._board_width_mm = width_mm
        self._board_height_mm = height_mm
        self._update_scale()
        self.update()
    
    def get_led_positions(self) -> List[Tuple[float, float]]:
        """Get current LED positions in mm."""
        return self._led_positions.copy()
    
    def set_led_positions(self, positions: List[Tuple[float, float]]):
        """Set LED positions in mm."""
        self._led_positions = positions.copy()
        self._update_status()
        self.update()
        self.positions_changed.emit(self._led_positions)
    
    def _update_scale(self):
        """Update scale factor based on board size and widget size."""
        if self._board_width_mm <= 0 or self._board_height_mm <= 0:
            self._scale = 1.0
            return
        
        # Leave 40px margin
        available_width = max(100, self.width() - 40)
        available_height = max(100, self.height() - 80)
        
        scale_x = available_width / self._board_width_mm
        scale_y = available_height / self._board_height_mm
        
        self._scale = min(scale_x, scale_y)
    
    def _update_status(self):
        """Update status label."""
        count = len(self._led_positions)
        self._status_label.setText(f"{count} LED(s) placed on board")
    
    def _mm_to_pixel(self, x_mm: float, y_mm: float) -> Tuple[int, int]:
        """Convert mm coordinates to pixel coordinates."""
        x_px = int(x_mm * self._scale) + 20
        y_px = int(y_mm * self._scale) + 60
        return x_px, y_px
    
    def _pixel_to_mm(self, x_px: int, y_px: int) -> Tuple[float, float]:
        """Convert pixel coordinates to mm coordinates."""
        x_mm = (x_px - 20) / self._scale
        y_mm = (y_px - 60) / self._scale
        return x_mm, y_mm
    
    def paintEvent(self, event):
        """Paint PCB layout."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background
        painter.fillRect(self.rect(), self._background_color)
        
        # Update scale
        self._update_scale()
        
        # Draw board outline
        board_x, board_y = self._mm_to_pixel(0, 0)
        board_w = int(self._board_width_mm * self._scale)
        board_h = int(self._board_height_mm * self._scale)
        
        painter.setBrush(QBrush(self._board_color))
        painter.setPen(QPen(QColor(100, 100, 120), 2))
        painter.drawRect(board_x, board_y, board_w, board_h)
        
        # Draw grid (optional)
        grid_pen = QPen(QColor(60, 60, 70), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        # Draw grid lines every 10mm
        for x_mm in range(0, int(self._board_width_mm) + 1, 10):
            x_px, _ = self._mm_to_pixel(x_mm, 0)
            painter.drawLine(x_px, board_y, x_px, board_y + board_h)
        
        for y_mm in range(0, int(self._board_height_mm) + 1, 10):
            _, y_px = self._mm_to_pixel(0, y_mm)
            painter.drawLine(board_x, y_px, board_x + board_w, y_px)
        
        # Draw LEDs
        led_size = max(6, int(self._scale * 2))  # 2mm LED size
        for i, (x_mm, y_mm) in enumerate(self._led_positions):
            x_px, y_px = self._mm_to_pixel(x_mm, y_mm)
            
            # Check if LED is on board
            if 0 <= x_mm <= self._board_width_mm and 0 <= y_mm <= self._board_height_mm:
                # Draw LED
                if i == self._selected_led:
                    color = QColor(255, 255, 255)
                    pen_width = 2
                else:
                    color = self._led_color
                    pen_width = 1
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(0, 0, 0), pen_width))
                painter.drawEllipse(x_px - led_size // 2, y_px - led_size // 2, 
                                   led_size, led_size)
                
                # Draw LED number
                painter.setPen(QPen(QColor(255, 255, 255), 1))
                painter.setFont(painter.font())
                painter.drawText(x_px + led_size // 2 + 2, y_px + 4, str(i + 1))
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for LED placement/selection."""
        if event.button() == Qt.LeftButton:
            x_mm, y_mm = self._pixel_to_mm(event.x(), event.y())
            
            # Check if clicking on existing LED
            led_size_mm = 2.0
            self._selected_led = None
            
            for i, (led_x, led_y) in enumerate(self._led_positions):
                dist = ((x_mm - led_x) ** 2 + (y_mm - led_y) ** 2) ** 0.5
                if dist < led_size_mm:
                    self._selected_led = i
                    self.update()
                    return
            
            # If in "add mode", add new LED
            # (In a full implementation, this would be controlled by a tool mode)
            if 0 <= x_mm <= self._board_width_mm and 0 <= y_mm <= self._board_height_mm:
                self._led_positions.append((x_mm, y_mm))
                self._update_status()
                self.update()
                self.positions_changed.emit(self._led_positions)
    
    def resizeEvent(self, event):
        """Handle resize to update scale."""
        self._update_scale()
        self.update()
        super().resizeEvent(event)
    
    def _on_add_led(self):
        """Handle add LED button (for future implementation)."""
        # In full implementation, this would switch to "add" mode
        self._status_label.setText("Click on the board to place LEDs")
    
    def _on_clear_all(self):
        """Clear all LED positions."""
        if self._led_positions:
            reply = QMessageBox.question(
                self, "Clear All", "Remove all LEDs from the board?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._led_positions.clear()
                self._selected_led = None
                self._update_status()
                self.update()
                self.positions_changed.emit(self._led_positions)
    
    def _on_export(self):
        """Export LED positions to PCB design tools."""
        if not self._led_positions:
            QMessageBox.warning(self, "No LEDs", "Please place LEDs on the board first.")
            return
        
        # Open file dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export PCB Layout",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;Gerber Files (*.gbr);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        file_path_obj = Path(file_path)
        
        try:
            if file_path_obj.suffix.lower() == '.csv':
                if 'easyeda' in file_path.lower():
                    PCBExporter.export_to_easyeda(self._led_positions, file_path_obj)
                else:
                    PCBExporter.export_to_csv(self._led_positions, file_path_obj)
            elif file_path_obj.suffix.lower() == '.json':
                PCBExporter.export_to_kicad(self._led_positions, file_path_obj)
            elif file_path_obj.suffix.lower() == '.gbr':
                PCBExporter.export_to_gerber(self._led_positions, file_path_obj)
            else:
                # Default to CSV
                PCBExporter.export_to_csv(self._led_positions, file_path_obj)
            
            QMessageBox.information(
                self, "Export Successful",
                f"LED positions exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to export PCB layout:\n{str(e)}"
            )

