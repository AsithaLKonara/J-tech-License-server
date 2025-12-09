"""
Device Control Panel - UI for real-time device control and monitoring.
"""

from __future__ import annotations

import sys
import os
from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QSpinBox, QSlider, QProgressBar, QTextEdit, QComboBox
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.services.device_manager import DeviceManager, BudurasmalaDevice, DeviceStatus, DeviceCommand
from core.pattern import Pattern


class DeviceControlPanel(QWidget):
    """Panel for controlling and monitoring Budurasmala devices."""
    
    # Signals
    device_selected = Signal(str)  # device_id
    pattern_upload_requested = Signal(str, Pattern)  # device_id, pattern
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.device_manager = DeviceManager()
        self._selected_device_id: Optional[str] = None
        
        # Setup UI
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Device list
        devices_group = QGroupBox("Devices")
        devices_layout = QVBoxLayout()
        
        self.device_list = QListWidget()
        self.device_list.itemClicked.connect(self._on_device_selected)
        devices_layout.addWidget(self.device_list)
        
        # Discovery button
        discover_btn = QPushButton("Discover Devices")
        discover_btn.clicked.connect(self._on_discover)
        devices_layout.addWidget(discover_btn)
        
        devices_group.setLayout(devices_layout)
        layout.addWidget(devices_group)
        
        # Device control
        control_group = QGroupBox("Device Control")
        control_layout = QVBoxLayout()
        
        # Status display
        self.status_label = QLabel("No device selected")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        control_layout.addWidget(self.status_label)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._on_play)
        self.play_btn.setEnabled(False)
        buttons_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._on_pause)
        self.pause_btn.setEnabled(False)
        buttons_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)
        
        control_layout.addLayout(buttons_layout)
        
        # Brightness control
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        self.brightness_slider.setEnabled(False)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        self.brightness_label.setMinimumWidth(50)
        brightness_layout.addWidget(self.brightness_label)
        
        control_layout.addLayout(brightness_layout)
        
        # Upload pattern button
        upload_btn = QPushButton("Upload Pattern")
        upload_btn.clicked.connect(self._on_upload_pattern)
        upload_btn.setEnabled(False)
        control_layout.addWidget(upload_btn)
        self.upload_btn = upload_btn
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Device info
        info_group = QGroupBox("Device Information")
        info_layout = QFormLayout()
        
        self.info_name_label = QLabel("-")
        info_layout.addRow("Name:", self.info_name_label)
        
        self.info_ip_label = QLabel("-")
        info_layout.addRow("IP Address:", self.info_ip_label)
        
        self.info_version_label = QLabel("-")
        info_layout.addRow("Firmware:", self.info_version_label)
        
        self.info_pattern_label = QLabel("-")
        info_layout.addRow("Current Pattern:", self.info_pattern_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Status log
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Setup callbacks
        self.device_manager.add_status_callback(self._on_device_status_changed)
        
        # Start monitoring
        self.device_manager.start_monitoring()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_device_list)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def _on_discover(self):
        """Discover devices on network."""
        self.log_text.append("Scanning network for devices...")
        devices = self.device_manager.discover_devices()
        self.log_text.append(f"Found {len(devices)} device(s)")
        self._update_device_list()
    
    def _update_device_list(self):
        """Update device list widget."""
        self.device_list.clear()
        
        for device in self.device_manager.list_devices():
            item = QListWidgetItem(f"{device.name} ({device.ip_address})")
            item.setData(Qt.UserRole, device.device_id)
            
            # Color code by status
            if device.status == DeviceStatus.ONLINE:
                item.setForeground(QColor(0, 255, 0))
            elif device.status == DeviceStatus.PLAYING:
                item.setForeground(QColor(255, 255, 0))
            elif device.status == DeviceStatus.OFFLINE:
                item.setForeground(QColor(128, 128, 128))
            else:
                item.setForeground(QColor(255, 128, 0))
            
            self.device_list.addItem(item)
    
    def _on_device_selected(self, item: QListWidgetItem):
        """Handle device selection."""
        device_id = item.data(Qt.UserRole)
        self._selected_device_id = device_id
        self._update_device_info()
        self.device_selected.emit(device_id)
    
    def _update_device_info(self):
        """Update device information display."""
        if not self._selected_device_id:
            self.status_label.setText("No device selected")
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.brightness_slider.setEnabled(False)
            self.upload_btn.setEnabled(False)
            return
        
        device = self.device_manager.get_device(self._selected_device_id)
        if not device:
            return
        
        # Update status
        status_text = f"Status: {device.status.value.upper()}"
        if device.status == DeviceStatus.ONLINE:
            status_text += " ✓"
        self.status_label.setText(status_text)
        
        # Update info
        self.info_name_label.setText(device.name)
        self.info_ip_label.setText(f"{device.ip_address}:{device.port}")
        self.info_version_label.setText(device.firmware_version or "Unknown")
        self.info_pattern_label.setText(device.current_pattern or "None")
        
        # Enable controls if online
        is_online = device.status in [DeviceStatus.ONLINE, DeviceStatus.PLAYING, DeviceStatus.PAUSED, DeviceStatus.STOPPED]
        self.play_btn.setEnabled(is_online)
        self.pause_btn.setEnabled(is_online)
        self.stop_btn.setEnabled(is_online)
        self.brightness_slider.setEnabled(is_online)
        self.upload_btn.setEnabled(is_online)
        
        # Update brightness
        self.brightness_slider.setValue(device.brightness)
        self.brightness_label.setText(f"{device.brightness}%")
    
    def _on_play(self):
        """Play on selected device."""
        if not self._selected_device_id:
            return
        
        command = DeviceCommand("play")
        if self.device_manager.send_command(self._selected_device_id, command):
            self.log_text.append(f"Play command sent to device")
        else:
            self.log_text.append(f"Failed to send play command")
    
    def _on_pause(self):
        """Pause selected device."""
        if not self._selected_device_id:
            return
        
        if self.device_manager.pause_device(self._selected_device_id):
            self.log_text.append(f"Device paused")
        else:
            self.log_text.append(f"Failed to pause device")
    
    def _on_stop(self):
        """Stop selected device."""
        if not self._selected_device_id:
            return
        
        if self.device_manager.stop_device(self._selected_device_id):
            self.log_text.append(f"Device stopped")
        else:
            self.log_text.append(f"Failed to stop device")
    
    def _on_brightness_changed(self, value: int):
        """Handle brightness slider change."""
        self.brightness_label.setText(f"{value}%")
        
        if not self._selected_device_id:
            return
        
        if self.device_manager.set_brightness(self._selected_device_id, value):
            self.log_text.append(f"Brightness set to {value}%")
    
    def _on_upload_pattern(self):
        """Request pattern upload."""
        if not self._selected_device_id:
            return
        
        # This will emit signal - parent widget should handle pattern selection
        self.log_text.append("Pattern upload requested - select pattern in main window")
        # Signal will be handled by parent
    
    def _on_device_status_changed(self, device_id: str, status: DeviceStatus):
        """Handle device status change callback."""
        if device_id == self._selected_device_id:
            self._update_device_info()
            self.log_text.append(f"Device status changed: {status.value}")
    
    def upload_pattern_to_device(self, pattern: Pattern):
        """Upload pattern to selected device."""
        if not self._selected_device_id:
            return False
        
        # Convert pattern to bytes (simplified - would use actual export)
        from core.export.exporters import PatternExporter
        from pathlib import Path
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
                temp_path = Path(f.name)
            
            exporter = PatternExporter()
            exporter.export_binary(pattern, temp_path)
            
            pattern_data = temp_path.read_bytes()
            pattern_name = pattern.name or "Pattern"
            
            success = self.device_manager.play_pattern(
                self._selected_device_id,
                pattern_data,
                pattern_name
            )
            
            temp_path.unlink()  # Clean up
            
            if success:
                self.log_text.append(f"Pattern '{pattern_name}' uploaded and playing")
            else:
                self.log_text.append(f"Failed to upload pattern")
            
            return success
        except Exception as e:
            self.log_text.append(f"Upload error: {e}")
            return False

