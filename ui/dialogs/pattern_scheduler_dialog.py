"""
Pattern Scheduler Dialog - Schedule patterns to play on devices at specific times.
"""

from __future__ import annotations

import sys
import os
from typing import Optional, List
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QDateTimeEdit, QCheckBox, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QMessageBox, QTimeEdit, QDateEdit
)
from PySide6.QtCore import Qt, QDateTime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.services.device_manager import DeviceManager, ScheduledPattern
from core.pattern import Pattern


class PatternSchedulerDialog(QDialog):
    """Dialog for scheduling patterns on devices."""
    
    def __init__(self, parent=None, device_manager: Optional[DeviceManager] = None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Scheduler")
        self.setModal(True)
        self.resize(600, 500)
        
        self.device_manager = device_manager
        self.selected_pattern: Optional[Pattern] = None
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Device selection
        device_group = QGroupBox("Device")
        device_layout = QFormLayout()
        
        self.device_combo = QComboBox()
        self._update_device_list()
        device_layout.addRow("Device:", self.device_combo)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Pattern selection
        pattern_group = QGroupBox("Pattern")
        pattern_layout = QVBoxLayout()
        
        self.pattern_label = QLabel("No pattern selected")
        pattern_layout.addWidget(self.pattern_label)
        
        select_pattern_btn = QPushButton("Select Pattern...")
        select_pattern_btn.clicked.connect(self._on_select_pattern)
        pattern_layout.addWidget(select_pattern_btn)
        
        pattern_group.setLayout(pattern_layout)
        layout.addWidget(pattern_group)
        
        # Schedule settings
        schedule_group = QGroupBox("Schedule")
        schedule_layout = QFormLayout()
        
        # Start date/time
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(QDateTime.currentDateTime().addSecs(60))
        self.start_datetime.setCalendarPopup(True)
        schedule_layout.addRow("Start Date/Time:", self.start_datetime)
        
        # End date/time (optional)
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDateTime(QDateTime.currentDateTime().addHours(1))
        self.end_datetime.setCalendarPopup(True)
        schedule_layout.addRow("End Date/Time:", self.end_datetime)
        
        # Repeat checkbox
        self.repeat_checkbox = QCheckBox("Repeat daily")
        schedule_layout.addRow("", self.repeat_checkbox)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # Scheduled patterns list
        list_group = QGroupBox("Scheduled Patterns")
        list_layout = QVBoxLayout()
        
        self.schedule_list = QListWidget()
        list_layout.addWidget(self.schedule_list)
        
        # List buttons
        list_buttons = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_schedule_list)
        list_buttons.addWidget(refresh_btn)
        
        cancel_btn = QPushButton("Cancel Schedule")
        cancel_btn.clicked.connect(self._on_cancel_schedule)
        list_buttons.addWidget(cancel_btn)
        
        list_buttons.addStretch()
        list_layout.addLayout(list_buttons)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_dialog_btn = QPushButton("Close")
        cancel_dialog_btn.clicked.connect(self.accept)
        button_layout.addWidget(cancel_dialog_btn)
        
        schedule_btn = QPushButton("Schedule Pattern")
        schedule_btn.clicked.connect(self._on_schedule)
        schedule_btn.setDefault(True)
        button_layout.addWidget(schedule_btn)
        
        layout.addLayout(button_layout)
        
        # Initial refresh
        self._refresh_schedule_list()
    
    def _update_device_list(self):
        """Update device combo box."""
        self.device_combo.clear()
        
        if self.device_manager:
            for device in self.device_manager.list_devices():
                self.device_combo.addItem(f"{device.name} ({device.ip_address})", device.device_id)
    
    def _on_select_pattern(self):
        """Open pattern selection dialog."""
        from PySide6.QtWidgets import QFileDialog
        from core.project import load_project
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pattern",
            "",
            "LED Project Files (*.ledproj);;All Files (*.*)"
        )
        
        if file_path:
            try:
                pattern = load_project(file_path)
                self.selected_pattern = pattern
                self.pattern_label.setText(f"Pattern: {pattern.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load pattern: {e}")
    
    def _on_schedule(self):
        """Schedule the pattern."""
        if not self.device_manager:
            QMessageBox.warning(self, "No Device Manager", "Device manager not available")
            return
        
        if self.device_combo.currentData() is None:
            QMessageBox.warning(self, "No Device", "Please select a device")
            return
        
        if not self.selected_pattern:
            QMessageBox.warning(self, "No Pattern", "Please select a pattern")
            return
        
        device_id = self.device_combo.currentData()
        start_time = self.start_datetime.dateTime().toPython()
        end_time = self.end_datetime.dateTime().toPython()
        repeat = self.repeat_checkbox.isChecked()
        
        # Convert pattern to bytes
        from core.export.exporters import PatternExporter
        from pathlib import Path
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
                temp_path = Path(f.name)
            
            exporter = PatternExporter()
            exporter.export_binary(self.selected_pattern, temp_path)
            pattern_data = temp_path.read_bytes()
            temp_path.unlink()
            
            # Schedule pattern
            schedule_id = self.device_manager.schedule_pattern(
                device_id=device_id,
                pattern_name=self.selected_pattern.name or "Scheduled Pattern",
                pattern_data=pattern_data,
                start_time=start_time,
                end_time=end_time,
                repeat=repeat
            )
            
            QMessageBox.information(
                self,
                "Scheduled",
                f"Pattern scheduled successfully!\nSchedule ID: {schedule_id}"
            )
            
            self._refresh_schedule_list()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to schedule pattern: {e}")
    
    def _refresh_schedule_list(self):
        """Refresh scheduled patterns list."""
        self.schedule_list.clear()
        
        if not self.device_manager:
            return
        
        # Get all schedules (would need to expose this in DeviceManager)
        # For now, show message
        item = QListWidgetItem("Schedules are managed by DeviceManager")
        item.setFlags(Qt.NoItemFlags)  # Non-selectable
        self.schedule_list.addItem(item)
    
    def _on_cancel_schedule(self):
        """Cancel selected schedule."""
        item = self.schedule_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Please select a schedule to cancel")
            return
        
        # Get schedule ID from item data
        schedule_id = item.data(Qt.UserRole)
        if schedule_id and self.device_manager:
            if self.device_manager.cancel_schedule(schedule_id):
                QMessageBox.information(self, "Cancelled", "Schedule cancelled successfully")
                self._refresh_schedule_list()
            else:
                QMessageBox.warning(self, "Error", "Failed to cancel schedule")

