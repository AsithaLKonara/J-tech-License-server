"""
Live Preview Widget - Display live preview from connected devices.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QImage
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.services.device_manager import DeviceManager


class LivePreviewWidget(QWidget):
    """Widget for displaying live preview from devices."""
    
    def __init__(self, parent: Optional[QWidget] = None, device_manager: Optional[DeviceManager] = None):
        super().__init__(parent)
        self.device_manager = device_manager
        self._device_id: Optional[str] = None
        self._preview_image: Optional[QImage] = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        self.label = QLabel("Live Preview")
        self.label.setStyleSheet("font-weight: bold; padding: 4px;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # Preview will be drawn in paintEvent
        self.setMinimumSize(200, 200)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_preview)
        self.update_timer.setInterval(100)  # 10 FPS
        
        # Setup preview callback
        if self.device_manager:
            self.device_manager.add_preview_callback(self._on_preview_received)
    
    def set_device(self, device_id: str):
        """Set device to preview."""
        self._device_id = device_id
        if device_id:
            self.update_timer.start()
            self.label.setText(f"Live Preview: {device_id}")
        else:
            self.update_timer.stop()
            self.label.setText("Live Preview")
            self._preview_image = None
            self.update()
    
    def _update_preview(self):
        """Update preview from device."""
        if not self._device_id or not self.device_manager:
            return
        
        preview_data = self.device_manager.get_live_preview(self._device_id)
        if preview_data:
            self._process_preview_data(preview_data)
    
    def _on_preview_received(self, device_id: str, preview_data: bytes):
        """Handle preview data from callback."""
        if device_id == self._device_id:
            self._process_preview_data(preview_data)
    
    def _process_preview_data(self, data: bytes):
        """Process preview data and create QImage."""
        try:
            # Assume RGB24 format (width x height x 3 bytes)
            # This is simplified - actual format would depend on device
            # For now, create a placeholder image
            width = 32  # Would get from device metadata
            height = 32
            
            if len(data) >= width * height * 3:
                image = QImage(width, height, QImage.Format_RGB888)
                
                for y in range(height):
                    for x in range(width):
                        idx = (y * width + x) * 3
                        if idx + 2 < len(data):
                            r = data[idx]
                            g = data[idx + 1]
                            b = data[idx + 2]
                            image.setPixel(x, y, QColor(r, g, b).rgb())
                
                self._preview_image = image
                self.update()
        except Exception as e:
            # Silently handle errors
            pass
    
    def paintEvent(self, event):
        """Paint preview image."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(20, 20, 30))
        
        if self._preview_image:
            # Scale image to fit widget
            scaled = self._preview_image.scaled(
                self.width() - 10,
                self.height() - 30,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2 + 15  # Account for label
            
            painter.drawImage(x, y, scaled)
        else:
            # Draw placeholder
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(
                self.rect().adjusted(0, 20, 0, 0),
                Qt.AlignCenter,
                "No preview available"
            )

