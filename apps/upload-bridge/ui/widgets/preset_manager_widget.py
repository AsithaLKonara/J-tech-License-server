"""Preset Manager Widget for ESP32 Configurations"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QLabel, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QColor
import json
from pathlib import Path
from typing import Dict, Optional


class PresetManagerWidget(QWidget):
    """Widget for managing configuration presets"""
    
    # Signals
    preset_loaded = Signal(dict)  # Emitted when preset is loaded
    preset_saved = Signal(str)    # Emitted when preset is saved
    preset_deleted = Signal(str)  # Emitted when preset is deleted
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.presets_dir = Path.home() / '.upload_bridge' / 'presets' / 'esp32'
        self.current_config = {}
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        self.init_ui()
        self.load_presets()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        
        # Info label
        info = QLabel("💾 Save, load, and manage GPIO configurations as reusable presets")
        info.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(info)
        
        # Preset list
        list_label = QLabel("Available Presets:")
        layout.addWidget(list_label)
        
        self.preset_list = QListWidget()
        self.preset_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.preset_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("📂 Load")
        self.btn_load.clicked.connect(self._on_load)
        self.btn_load.setEnabled(False)
        btn_layout.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("💾 Save Current")
        self.btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)
        
        layout.addLayout(btn_layout)
        
        # Details
        self.details_label = QLabel("No preset selected")
        self.details_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.details_label)
        
        self.setLayout(layout)
    
    def _on_selection_changed(self):
        """Handle preset selection change"""
        selected = self.preset_list.selectedItems()
        has_selection = len(selected) > 0
        
        self.btn_load.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        
        if has_selection:
            preset_name = selected[0].text()
            self._show_preset_details(preset_name)
    
    def _show_preset_details(self, preset_name: str):
        """Show details of selected preset"""
        preset_path = self.presets_dir / f"{preset_name}.json"
        
        if preset_path.exists():
            try:
                with open(preset_path, 'r') as f:
                    preset = json.load(f)
                
                details = f"LED Pin: GPIO{preset.get('led_data_pin', 'N/A')} | "
                details += f"SD CLK: GPIO{preset.get('sd_clk_pin', 'N/A')} | "
                details += f"LEDs: {preset.get('num_leds', 'N/A')} | "
                details += f"Brightness: {preset.get('brightness', 'N/A')}"
                
                self.details_label.setText(details)
            except (json.JSONDecodeError, OSError) as e:
                logging.error(f"Failed to load preset details for {preset_name}: {e}")
                self.details_label.setText(f"Error loading preset: {e}")
    
    def _on_load(self):
        """Load selected preset"""
        selected = self.preset_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a preset to load")
            return
        
        preset_name = selected[0].text()
        preset_path = self.presets_dir / f"{preset_name}.json"
        
        if not preset_path.exists():
            QMessageBox.warning(self, "Error", f"Preset file not found: {preset_path}")
            return
        
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                preset = json.load(f)
            
            self.current_config = preset
            self.preset_loaded.emit(preset)
            QMessageBox.information(self, "Success", f"Loaded preset: {preset_name}")
        
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in preset {preset_name}: {e}")
            QMessageBox.critical(self, "Error", f"Invalid preset format: {e.msg}")
        except OSError as e:
            logging.error(f"Cannot read preset file {preset_path}: {e}")
            QMessageBox.critical(self, "Error", f"Cannot read preset: {e}")
        except Exception as e:
            logging.error(f"Unexpected error loading preset {preset_name}: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load preset: {e}")
    
    def _on_save(self):
        """Save current configuration as preset"""
        if not self.current_config:
            QMessageBox.warning(self, "No Configuration", 
                              "No configuration to save. Please configure GPIO first.")
            return
        
        # Get preset name from user
        preset_name, ok = QInputDialog.getText(self, "Save Preset", 
                                              "Enter preset name:",
                                              text="my_config")
        
        if not ok or not preset_name:
            return
        
        # Sanitize filename
        preset_name = preset_name.replace('/', '_').replace('\\', '_')
        preset_path = self.presets_dir / f"{preset_name}.json"
        
        # Check if already exists
        if preset_path.exists():
            reply = QMessageBox.question(self, "Overwrite?", 
                                        f"Preset '{preset_name}' already exists. Overwrite?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        try:
            with open(preset_path, 'w') as f:
                json.dump(self.current_config, f, indent=2)
            
            self.preset_saved.emit(preset_name)
            self.load_presets()
            QMessageBox.information(self, "Success", f"Preset saved: {preset_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preset: {e}")
    
    def _on_delete(self):
        """Delete selected preset"""
        selected = self.preset_list.selectedItems()
        if not selected:
            return
        
        preset_name = selected[0].text()
        preset_path = self.presets_dir / f"{preset_name}.json"
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Delete preset '{preset_name}'?",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
        
        try:
            preset_path.unlink()
            self.preset_deleted.emit(preset_name)
            self.load_presets()
            QMessageBox.information(self, "Success", f"Preset deleted: {preset_name}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete preset: {e}")
    
    def load_presets(self):
        """Load and display available presets"""
        self.preset_list.clear()
        
        if not self.presets_dir.exists():
            return
        
        preset_files = list(self.presets_dir.glob('*.json'))
        
        for preset_file in sorted(preset_files):
            preset_name = preset_file.stem
            item = QListWidgetItem(preset_name)
            self.preset_list.addItem(item)
    
    def set_current_config(self, config: Dict):
        """Set current configuration"""
        self.current_config = config.copy()
    
    def get_current_config(self) -> Dict:
        """Get current configuration"""
        return self.current_config.copy()
