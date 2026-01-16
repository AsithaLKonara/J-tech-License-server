"""
Batch Flash Tab - Flash pattern to multiple devices simultaneously
Complete PySide6 implementation
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QProgressBar, QTextEdit, QSpinBox,
    QCheckBox, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QTextCursor, QFont
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern
from core.batch_flasher import BatchFlasher, FlashJob, FlashJobResult
from uploaders.uploader_registry import UploaderRegistry
from firmware.builder import FirmwareBuilder
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)


class BatchFlashWorker(QThread):
    """Worker thread for batch flashing"""
    progress = Signal(int, int, object)  # completed, remaining, last_result
    finished = Signal(list)  # results
    log = Signal(str)  # log message
    
    def __init__(self, pattern, chip_id, ports, gpio_pin, max_concurrent):
        super().__init__()
        self.pattern = pattern
        self.chip_id = chip_id
        self.ports = ports
        self.gpio_pin = gpio_pin
        self.max_concurrent = max_concurrent
        self.firmware_path = None
    
    def run(self):
        """Execute batch flash"""
        try:
            # Step 1: Build firmware once
            self.log.emit("Building firmware...")
            builder = FirmwareBuilder()
            build_result = builder.build(self.pattern, self.chip_id, {
                'gpio_pin': self.gpio_pin
            })
            
            if not build_result.success:
                self.log.emit(f"Build failed: {build_result.error_message}")
                self.finished.emit([])
                return
            
            self.firmware_path = build_result.firmware_path
            self.log.emit(f"Build successful: {build_result.firmware_path}")
            self.log.emit(f"Firmware size: {build_result.size_bytes} bytes")
            
            # Step 2: Create batch flasher
            flasher = BatchFlasher(max_concurrent=self.max_concurrent)
            flasher.set_progress_callback(self.on_progress)
            
            # Step 3: Add jobs
            self.log.emit(f"Adding {len(self.ports)} flash jobs...")
            for i, port in enumerate(self.ports):
                job = FlashJob(
                    job_id=f"job_{i}",
                    port=port,
                    chip_id=self.chip_id,
                    firmware_path=self.firmware_path,
                    gpio_pin=self.gpio_pin
                )
                flasher.add_job(job)
                self.log.emit(f"Added job for {port}")
            
            # Step 4: Execute all
            self.log.emit("Starting batch flash...")
            results = flasher.flash_all()
            
            # Step 5: Report summary
            summary = flasher.get_summary()
            self.log.emit("=" * 70)
            self.log.emit("Batch Flash Summary:")
            self.log.emit(f"  Total: {summary['total_jobs']}")
            self.log.emit(f"  Successful: {summary['successful']}")
            self.log.emit(f"  Failed: {summary['failed']}")
            self.log.emit(f"  Success Rate: {summary['success_rate']*100:.1f}%")
            self.log.emit(f"  Total Duration: {summary['total_duration_seconds']:.1f}s")
            self.log.emit("=" * 70)
            
            self.finished.emit(results)
            
        except Exception as e:
            self.log.emit(f"Batch flash error: {str(e)}")
            logger.error(f"Batch flash error: {e}", exc_info=True)
            self.finished.emit([])
    
    def on_progress(self, completed, remaining, last_result):
        """Handle progress callback"""
        self.progress.emit(completed, remaining, last_result)
        if last_result:
            status = "✓" if last_result.success else "✗"
            self.log.emit(f"{status} {last_result.port}: {last_result.duration_seconds:.1f}s")


class BatchFlashTab(QWidget):
    """
    Batch Flash Tab for flashing pattern to multiple devices
    
    Features:
    - Multi-device selection
    - Concurrent flashing support
    - Per-device progress tracking
    - Results table
    - Queue management
    """
    
    # Signals
    pattern_required = Signal()  # Emitted when pattern is needed
    batch_flash_started = Signal(int)  # total count
    batch_flash_progress = Signal(int, int)  # done, total
    batch_flash_complete = Signal(dict)  # results dict {port: (success, message), ...}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.worker: BatchFlashWorker = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # Scroll area for responsiveness
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Pattern info
        pattern_group = QGroupBox("Pattern")
        pattern_layout = QVBoxLayout()
        
        self.pattern_label = QLabel("No pattern loaded")
        self.pattern_label.setWordWrap(True)
        pattern_layout.addWidget(self.pattern_label)
        
        pattern_group.setLayout(pattern_layout)
        content_layout.addWidget(pattern_group)
        
        # Device selection
        device_group = QGroupBox("Device Selection")
        device_layout = QVBoxLayout()
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Available Ports:"))
        
        self.refresh_ports_button = QPushButton("🔄 Refresh")
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_ports_button)
        port_layout.addStretch()
        
        device_layout.addLayout(port_layout)
        
        # Port list
        ports_layout = QHBoxLayout()
        
        self.available_ports_list = QListWidget()
        self.available_ports_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.available_ports_list.setMaximumHeight(150)
        ports_layout.addWidget(self.available_ports_list)
        
        # Buttons
        buttons_layout = QVBoxLayout()
        
        self.add_selected_button = QPushButton("→ Add Selected")
        self.add_selected_button.clicked.connect(self.add_selected_ports)
        buttons_layout.addWidget(self.add_selected_button)
        
        self.add_all_button = QPushButton("→ Add All")
        self.add_all_button.clicked.connect(self.add_all_ports)
        buttons_layout.addWidget(self.add_all_button)
        
        self.remove_selected_button = QPushButton("← Remove Selected")
        self.remove_selected_button.clicked.connect(self.remove_selected_ports)
        buttons_layout.addWidget(self.remove_selected_button)
        
        self.clear_all_button = QPushButton("← Clear All")
        self.clear_all_button.clicked.connect(self.clear_selected_ports)
        buttons_layout.addWidget(self.clear_all_button)
        
        buttons_layout.addStretch()
        ports_layout.addLayout(buttons_layout)
        
        device_layout.addLayout(ports_layout)
        
        # Selected ports
        selected_layout = QHBoxLayout()
        selected_layout.addWidget(QLabel("Selected Ports:"))
        device_layout.addLayout(selected_layout)
        
        self.selected_ports_list = QListWidget()
        self.selected_ports_list.setMaximumHeight(100)
        device_layout.addWidget(self.selected_ports_list)
        
        device_group.setLayout(device_layout)
        content_layout.addWidget(device_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Chip selection
        chip_layout = QHBoxLayout()
        chip_layout.addWidget(QLabel("Chip:"))
        self.chip_combo = QComboBox()
        self.chip_combo.currentTextChanged.connect(self.on_chip_changed)
        chip_layout.addWidget(self.chip_combo)
        chip_layout.addStretch()
        config_layout.addLayout(chip_layout)
        
        # GPIO pin
        gpio_layout = QHBoxLayout()
        gpio_layout.addWidget(QLabel("GPIO Pin:"))
        self.gpio_spin = QSpinBox()
        self.gpio_spin.setMinimum(0)
        self.gpio_spin.setMaximum(40)
        self.gpio_spin.setValue(2)
        gpio_layout.addWidget(self.gpio_spin)
        gpio_layout.addStretch()
        config_layout.addLayout(gpio_layout)
        
        # Concurrency
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Max Concurrent:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(1)
        self.concurrent_spin.setToolTip("Number of devices to flash simultaneously")
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        config_layout.addLayout(concurrent_layout)
        
        config_group.setLayout(config_layout)
        content_layout.addWidget(config_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        self.overall_progress.setValue(0)
        progress_layout.addWidget(self.overall_progress)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        content_layout.addWidget(progress_group)
        
        # Results table
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Port", "Status", "Duration", "Bytes Written", "Error"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        content_layout.addWidget(results_group, stretch=1)
        
        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        content_layout.addWidget(log_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🚀 Start Batch Flash")
        self.start_button.clicked.connect(self.start_batch_flash)
        self.start_button.setEnabled(False)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop_batch_flash)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_log_button)
        
        content_layout.addLayout(button_layout)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Initialize
        self.populate_chips()
        self.refresh_ports()
    
    def populate_chips(self):
        """Populate chip selection combo"""
        registry = UploaderRegistry.instance()
        chips = registry.list_supported_chips()
        
        self.chip_combo.clear()
        for chip in sorted(chips):
            spec = registry.get_chip_spec(chip)
            chip_name = spec.get('name', chip) if spec else chip
            self.chip_combo.addItem(f"{chip_name} ({chip})", chip)
        
        # Default to ESP8266 if available
        esp8266_index = self.chip_combo.findData("esp8266")
        if esp8266_index >= 0:
            self.chip_combo.setCurrentIndex(esp8266_index)
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        self.available_ports_list.clear()
        
        try:
            ports = [p.device for p in serial.tools.list_ports.comports()]
            
            if ports:
                for port in sorted(ports):
                    item = QListWidgetItem(port)
                    self.available_ports_list.addItem(item)
                self.log(f"Found {len(ports)} port(s)")
            else:
                self.log("No serial ports detected")
        except Exception as e:
            self.log(f"Error scanning ports: {e}")
            logger.error(f"Error scanning ports: {e}", exc_info=True)
    
    def add_selected_ports(self):
        """Add selected ports to flash queue"""
        selected_items = self.available_ports_list.selectedItems()
        
        for item in selected_items:
            port = item.text()
            # Check if already added
            existing_items = [
                self.selected_ports_list.item(i).text()
                for i in range(self.selected_ports_list.count())
            ]
            if port not in existing_items:
                self.selected_ports_list.addItem(port)
        
        self.update_start_button()
    
    def add_all_ports(self):
        """Add all available ports to flash queue"""
        for i in range(self.available_ports_list.count()):
            item = self.available_ports_list.item(i)
            port = item.text()
            # Check if already added
            existing_items = [
                self.selected_ports_list.item(i).text()
                for i in range(self.selected_ports_list.count())
            ]
            if port not in existing_items:
                self.selected_ports_list.addItem(port)
        
        self.update_start_button()
    
    def remove_selected_ports(self):
        """Remove selected ports from flash queue"""
        selected_items = self.selected_ports_list.selectedItems()
        for item in selected_items:
            row = self.selected_ports_list.row(item)
            self.selected_ports_list.takeItem(row)
        
        self.update_start_button()
    
    def clear_selected_ports(self):
        """Clear all selected ports"""
        self.selected_ports_list.clear()
        self.update_start_button()
    
    def update_start_button(self):
        """Update start button enabled state"""
        has_pattern = self.pattern is not None
        has_ports = self.selected_ports_list.count() > 0
        not_running = self.worker is None or not self.worker.isRunning()
        
        self.start_button.setEnabled(has_pattern and has_ports and not_running)
    
    def on_chip_changed(self):
        """Handle chip selection change"""
        # Update GPIO default based on chip
        chip_id = self.chip_combo.currentData()
        if chip_id:
            registry = UploaderRegistry.instance()
            spec = registry.get_chip_spec(chip_id)
            if spec:
                default_gpio = spec.get('default_gpio', 2)
                self.gpio_spin.setValue(default_gpio)
    
    def load_pattern(self, pattern: Pattern):
        """Load pattern for batch flashing"""
        self.pattern = pattern
        
        if pattern:
            info = f"Pattern: {pattern.name}\n"
            info += f"LEDs: {pattern.led_count}\n"
            info += f"Frames: {pattern.frame_count}\n"
            info += f"Duration: {pattern.duration_ms / 1000:.1f}s"
            self.pattern_label.setText(info)
        else:
            self.pattern_label.setText("No pattern loaded")
        
        self.update_start_button()
    
    def update_pattern(self, pattern: Pattern = None):
        """Update pattern from external source (called from pattern_changed signal)"""
        if pattern is None:
            pattern = self.pattern
        if pattern:
            self.load_pattern(pattern)
    
    def use_firmware(self, firmware_path: str):
        """Use pre-built firmware from FlashTab (for firmware sharing)"""
        if firmware_path and os.path.exists(firmware_path):
            self.log(f"Using shared firmware: {os.path.basename(firmware_path)}")
            # Store firmware path for batch flash to use
            self._shared_firmware_path = firmware_path
            # Note: This would need to be integrated into the batch flash worker
            # For now, we just log it
    
    def start_batch_flash(self):
        """Start batch flash operation"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "Please load a pattern first.")
            return
        
        selected_ports = [
            self.selected_ports_list.item(i).text()
            for i in range(self.selected_ports_list.count())
        ]
        
        if not selected_ports:
            QMessageBox.warning(self, "No Ports", "Please select at least one port.")
            return
        
        chip_id = self.chip_combo.currentData()
        if not chip_id:
            QMessageBox.warning(self, "No Chip", "Please select a chip.")
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Confirm Batch Flash",
            f"Flash pattern to {len(selected_ports)} device(s)?\n\n"
            f"Chip: {chip_id}\n"
            f"GPIO: {self.gpio_spin.value()}\n"
            f"Ports: {', '.join(selected_ports)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Clear previous results
        self.results_table.setRowCount(0)
        self.overall_progress.setValue(0)
        self.status_label.setText("Starting...")
        
        # Disable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Create and start worker
        self.worker = BatchFlashWorker(
            self.pattern,
            chip_id,
            selected_ports,
            self.gpio_spin.value(),
            self.concurrent_spin.value()
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log.connect(self.log)
        self.worker.start()
        
        # Initialize results table
        self.results_table.setRowCount(len(selected_ports))
        for i, port in enumerate(selected_ports):
            self.results_table.setItem(i, 0, QTableWidgetItem(port))
            self.results_table.setItem(i, 1, QTableWidgetItem("Pending..."))
            self.results_table.setItem(i, 2, QTableWidgetItem(""))
            self.results_table.setItem(i, 3, QTableWidgetItem(""))
            self.results_table.setItem(i, 4, QTableWidgetItem(""))
        
        self.overall_progress.setMaximum(len(selected_ports))
        self.log(f"Starting batch flash to {len(selected_ports)} device(s)...")
        
        # Emit started signal
        self.batch_flash_started.emit(len(selected_ports))
    
    def stop_batch_flash(self):
        """Stop batch flash operation"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Stop Batch Flash",
                "Are you sure you want to stop the batch flash?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                self.log("Batch flash stopped by user")
                self.on_finished([])
    
    def on_progress(self, completed, remaining, last_result):
        """Handle progress update"""
        total = completed + remaining
        progress = (completed / total * 100) if total > 0 else 0
        
        self.overall_progress.setValue(completed)
        self.status_label.setText(f"Completed: {completed}/{total} | Remaining: {remaining}")
        
        # Update results table
        if last_result:
            # Find row for this port
            for i in range(self.results_table.rowCount()):
                if self.results_table.item(i, 0).text() == last_result.port:
                    # Update status
                    status_item = QTableWidgetItem("✓ Success" if last_result.success else "✗ Failed")
                    status_item.setForeground(
                        Qt.GlobalColor.green if last_result.success else Qt.GlobalColor.red
                    )
                    self.results_table.setItem(i, 1, status_item)
                    
                    # Update duration
                    self.results_table.setItem(i, 2, QTableWidgetItem(f"{last_result.duration_seconds:.1f}s"))
                    
                    # Update bytes written
                    self.results_table.setItem(i, 3, QTableWidgetItem(f"{last_result.bytes_written:,}"))
                    
                    # Update error
                    error_text = last_result.error_message if last_result.error_message else ""
                    self.results_table.setItem(i, 4, QTableWidgetItem(error_text))
                    
                    break
        
        # Resize columns
        self.results_table.resizeColumnsToContents()
        
        # Emit progress signal
        self.batch_flash_progress.emit(completed, total)
    
    def on_finished(self, results):
        """Handle batch flash completion"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        if results:
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)
            
            self.status_label.setText(f"Complete: {success_count}/{total_count} successful")
            self.overall_progress.setValue(total_count)
            
            # Show summary
            if success_count == total_count:
                QMessageBox.information(
                    self,
                    "Batch Flash Complete",
                    f"Successfully flashed {success_count} device(s)!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Batch Flash Complete",
                    f"Completed: {success_count}/{total_count} successful\n\n"
                    f"Failed: {total_count - success_count} device(s)"
                )
            
            # Build results dict for signal
            results_dict = {}
            for r in results:
                results_dict[r.port] = (r.success, r.error_message if r.error_message else "Success")
            
            # Emit completion signal
            self.batch_flash_complete.emit(results_dict)
        else:
            self.status_label.setText("Failed or cancelled")
            # Emit completion signal with empty dict
            self.batch_flash_complete.emit({})
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear log text"""
        self.log_text.clear()

