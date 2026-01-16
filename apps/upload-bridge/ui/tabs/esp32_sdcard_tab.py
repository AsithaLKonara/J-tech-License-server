"""ESP32 SD Card Pattern Storage Tab"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QLabel,
    QPushButton, QComboBox, QSpinBox, QProgressBar, QTextEdit,
    QMessageBox, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QColor, QFont
import json
from pathlib import Path
from typing import Dict, Optional
import subprocess
import logging

from ui.widgets.gpio_selector_widget import GPIOSelectorWidget
from ui.widgets.preset_manager_widget import PresetManagerWidget

log = logging.getLogger(__name__)


class FirmwareBuilderThread(QThread):
    """Thread for building firmware without blocking UI"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, preset: str, config: Dict, builder_script: Path):
        super().__init__()
        self.preset = preset
        self.config = config
        self.builder_script = builder_script
    
    def run(self):
        """Execute firmware build"""
        try:
            self.progress.emit(f"Building {self.preset} firmware...")
            
            cmd = [
                'python', str(self.builder_script),
                '--preset', self.preset,
                '--led-pin', str(self.config.get('led_data_pin', 2)),
                '--num-leds', str(self.config.get('num_leds', 100)),
                '--brightness', str(self.config.get('brightness', 200)),
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.progress.emit("✓ Build successful!")
                self.finished.emit(True)
            else:
                self.progress.emit(f"✗ Build failed:\n{result.stderr}")
                self.finished.emit(False)
        
        except Exception as e:
            self.progress.emit(f"✗ Error: {e}")
            self.finished.emit(False)


class ESP32SDCardTab(QWidget):
    """Main ESP32 SD Card pattern storage tab"""
    
    firmware_built = Signal(str)
    ready_to_flash = Signal(dict)
    
    FIRMWARE_PRESETS = {
        'basic_sdcard': {
            'name': 'Basic SD Card',
            'description': 'SD pattern loading + LED playback (100 KB)',
            'features': ['SD Card', 'LED Playback', 'Serial CLI']
        },
        'wifi_enabled': {
            'name': 'WiFi Enabled',
            'description': 'Plus Web UI and OTA updates (250 KB)',
            'features': ['SD Card', 'LED Playback', 'WiFi', 'Web UI', 'OTA Updates']
        },
        'professional': {
            'name': 'Professional',
            'description': 'Full suite: WiFi, MQTT, OTA (350 KB)',
            'features': ['All above + MQTT support']
        }
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.firmware_dir = Path(__file__).parent.parent.parent / 'firmware' / 'esp32_sdcard'
        self.builder_script = Path(__file__).parent.parent.parent / 'firmware' / 'builders' / 'esp32_sdcard_builder.py'
        self.current_config = {}
        self.build_thread = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout()
        
        header = self._create_header()
        main_layout.addWidget(header)
        
        tabs = QTabWidget()
        tabs.addTab(self._create_firmware_tab(), "🔧 Firmware")
        
        self.gpio_widget = GPIOSelectorWidget()
        self.gpio_widget.config_changed.connect(self._on_gpio_config_changed)
        tabs.addTab(self.gpio_widget, "⚙️ GPIO Config")
        
        tabs.addTab(self._create_led_settings_tab(), "💡 LED Settings")
        
        self.preset_manager = PresetManagerWidget()
        self.preset_manager.preset_loaded.connect(self._on_preset_loaded)
        tabs.addTab(self.preset_manager, "💾 Presets")
        
        main_layout.addWidget(tabs)
        
        build_group = self._create_build_section()
        main_layout.addWidget(build_group)
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #0a0; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
    
    def _create_header(self) -> QGroupBox:
        """Create header section"""
        group = QGroupBox("ESP32 SD Card Pattern Player")
        layout = QVBoxLayout()
        
        title = QLabel("🚀 Build Custom Firmware for SD Card-Based LED Patterns")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title)
        
        desc = QLabel(
            "Configure GPIO pins, select firmware preset, and build custom firmware "
            "for unlimited LED pattern storage on SD card."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)
        
        group.setLayout(layout)
        return group
    
    def _create_firmware_tab(self) -> QWidget:
        """Create firmware selection tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Select Firmware Preset:"))
        
        self.combo_preset = QComboBox()
        for preset_id, preset_info in self.FIRMWARE_PRESETS.items():
            self.combo_preset.addItem(preset_info['name'], preset_id)
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        layout.addWidget(self.combo_preset)
        
        self.preset_desc = QLabel()
        self.preset_desc.setWordWrap(True)
        self.preset_desc.setStyleSheet("background: #222; padding: 10px; border-radius: 4px; color: #ccc;")
        layout.addWidget(self.preset_desc)
        
        self.features_label = QLabel()
        self.features_label.setWordWrap(True)
        layout.addWidget(self.features_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        
        self._on_preset_changed(0)
        
        return widget
    
    def _create_led_settings_tab(self) -> QWidget:
        """Create LED settings configuration tab"""
        widget = QWidget()
        layout = QFormLayout()
        
        self.spin_leds = QSpinBox()
        self.spin_leds.setRange(1, 2000)
        self.spin_leds.setValue(100)
        self.spin_leds.valueChanged.connect(lambda: self._update_config())
        layout.addRow("Number of LEDs:", self.spin_leds)
        
        self.spin_brightness = QSpinBox()
        self.spin_brightness.setRange(0, 255)
        self.spin_brightness.setValue(200)
        self.spin_brightness.valueChanged.connect(lambda: self._update_config())
        layout.addRow("Default Brightness (0-255):", self.spin_brightness)
        
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(1, 120)
        self.spin_fps.setValue(30)
        self.spin_fps.valueChanged.connect(lambda: self._update_config())
        layout.addRow("Default FPS:", self.spin_fps)
        
        self.combo_color_order = QComboBox()
        orders = {0: 'RGB', 1: 'GRB (WS2812B Default)', 2: 'BGR', 3: 'BRG', 4: 'RBG', 5: 'GBR'}
        for idx, name in orders.items():
            self.combo_color_order.addItem(name, idx)
        self.combo_color_order.currentIndexChanged.connect(lambda: self._update_config())
        layout.addRow("Color Order:", self.combo_color_order)
        
        widget.setLayout(layout)
        return widget
    
    def _create_build_section(self) -> QGroupBox:
        """Create build section"""
        group = QGroupBox("Build & Flash")
        layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        
        self.btn_build = QPushButton("🔨 Build Firmware")
        self.btn_build.clicked.connect(self._on_build)
        self.btn_build.setMinimumHeight(40)
        btn_layout.addWidget(self.btn_build)
        
        self.btn_flash = QPushButton("⚡ Flash to Device")
        self.btn_flash.clicked.connect(self._on_flash)
        self.btn_flash.setMinimumHeight(40)
        self.btn_flash.setEnabled(False)
        btn_layout.addWidget(self.btn_flash)
        
        layout.addLayout(btn_layout)
        
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.build_output = QTextEdit()
        self.build_output.setReadOnly(True)
        self.build_output.setMaximumHeight(150)
        self.build_output.setStyleSheet("background: #1e1e1e; color: #0a0; font-family: Courier; font-size: 9px;")
        layout.addWidget(QLabel("Build Output:"))
        layout.addWidget(self.build_output)
        
        group.setLayout(layout)
        return group
    
    def _on_preset_changed(self, index: int):
        """Handle firmware preset change"""
        preset_id = self.combo_preset.currentData()
        preset_info = self.FIRMWARE_PRESETS.get(preset_id, {})
        
        self.preset_desc.setText(preset_info.get('description', ''))
        
        features_text = "<b>Features:</b><br>" + "<br>".join(
            f"• {f}" for f in preset_info.get('features', [])
        )
        self.features_label.setText(features_text)
    
    def _on_gpio_config_changed(self, config: Dict):
        """Handle GPIO configuration change"""
        self.current_config.update(config)
        self.preset_manager.set_current_config(self.current_config)
    
    def _update_config(self):
        """Update configuration from LED settings"""
        self.current_config.update({
            'num_leds': self.spin_leds.value(),
            'brightness': self.spin_brightness.value(),
            'fps': self.spin_fps.value(),
            'color_order': self.combo_color_order.currentData(),
        })
        self.preset_manager.set_current_config(self.current_config)
    
    def _on_preset_loaded(self, preset: Dict):
        """Handle preset loaded"""
        self.current_config = preset.copy()
        self.gpio_widget.set_config(preset)
        self.spin_leds.setValue(preset.get('num_leds', 100))
        self.spin_brightness.setValue(preset.get('brightness', 200))
        self.spin_fps.setValue(preset.get('fps', 30))
        self._update_status("✓ Preset loaded", "#0a0")
    
    def _on_build(self):
        """Build firmware"""
        errors = self.gpio_widget.validate_config(self.current_config)
        if errors:
            error_msg = "Configuration errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            QMessageBox.warning(self, "Validation Failed", error_msg)
            self._update_status("✗ Build failed (validation error)", "#f00")
            return
        
        preset_id = self.combo_preset.currentData()
        self.build_thread = FirmwareBuilderThread(preset_id, self.current_config, self.builder_script)
        self.build_thread.progress.connect(self._on_build_progress)
        self.build_thread.finished.connect(self._on_build_finished)
        
        self._update_status("Building firmware...", "#ff0")
        self.build_output.clear()
        self.btn_build.setEnabled(False)
        self.progress.setValue(50)
        
        self.build_thread.start()
    
    def _on_build_progress(self, message: str):
        """Handle build progress message"""
        self.build_output.append(message)
    
    def _on_build_finished(self, success: bool):
        """Handle build completion"""
        self.btn_build.setEnabled(True)
        
        if success:
            self.progress.setValue(100)
            self.btn_flash.setEnabled(True)
            self._update_status("✓ Build successful - ready to flash!", "#0a0")
            self.firmware_built.emit(str(self.firmware_dir))
        else:
            self.progress.setValue(0)
            self._update_status("✗ Build failed", "#f00")
    
    def _on_flash(self):
        """Flash firmware to device"""
        self.ready_to_flash.emit(self.current_config)
        QMessageBox.information(self, "Ready to Flash", 
                              "Configuration saved. Use Flash tab to upload firmware.")
    
    def _update_status(self, message: str, color: str = "#0a0"):
        """Update status label"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
