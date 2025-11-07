"""
Upload Bridge License Activation GUI
PySide6-based license activation dialog for Upload Bridge
"""

import sys
import os
import json
import requests
import webbrowser
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QFileDialog, QMessageBox, 
    QTabWidget, QWidget, QGroupBox, QProgressBar,
    QComboBox, QCheckBox, QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QIcon

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern
from core.license_manager import LicenseManager


class LicenseActivationWorker(QThread):
    """Worker thread for license activation operations"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    activation_complete = Signal(bool, str, dict)
    
    def __init__(self, license_data: Dict[str, Any], server_url: str):
        super().__init__()
        self.license_data = license_data
        self.server_url = server_url
        self.cancelled = False
    
    def run(self):
        """Perform license activation"""
        try:
            self.status_updated.emit("Connecting to license server...")
            self.progress_updated.emit(10)
            
            # Test server connection
            if not self.test_server_connection():
                self.activation_complete.emit(False, "Cannot connect to license server", {})
                return
            
            self.status_updated.emit("Validating license...")
            self.progress_updated.emit(30)
            
            # Validate license format
            if not self.validate_license_format():
                self.activation_complete.emit(False, "Invalid license format", {})
                return
            
            self.status_updated.emit("Activating license...")
            self.progress_updated.emit(60)
            
            # Activate license
            success, message, result = self.activate_license()
            self.activation_complete.emit(success, message, result)
            
        except Exception as e:
            self.activation_complete.emit(False, f"Activation error: {str(e)}", {})
    
    def test_server_connection(self) -> bool:
        """Test connection to license server"""
        try:
            response = requests.get(f"{self.server_url}/api/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def validate_license_format(self) -> bool:
        """Validate license data format"""
        try:
            required_fields = ['license_id', 'product_id', 'issued_to_email', 'expires_at']
            license_info = self.license_data.get('license', {})
            
            for field in required_fields:
                if field not in license_info:
                    return False
            
            return True
        except:
            return False
    
    def activate_license(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Activate license on server"""
        try:
            # Generate device ID (simplified for demo)
            device_id = f"ESP8266_{hash(str(self.license_data)):08X}"
            
            activation_data = {
                'license_token': json.dumps(self.license_data),
                'chip_id': device_id,
                'device_info': {
                    'firmware_version': '1.0.0',
                    'hardware_version': 'ESP8266',
                    'app_version': 'Upload Bridge v3.0'
                }
            }
            
            response = requests.post(
                f"{self.server_url}/api/activate",
                json=activation_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return True, "License activated successfully", result
            else:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', 'Activation failed'), {}
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}", {}
        except Exception as e:
            return False, f"Activation error: {str(e)}", {}


class LicenseActivationDialog(QDialog):
    """
    License Activation Dialog for Upload Bridge
    
    Features:
    - License file upload and validation
    - Online activation with progress tracking
    - License status display
    - Server configuration
    - Offline activation support
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_data = None
        self.server_url = "http://localhost:3000"
        self.activation_worker = None
        self.license_manager = LicenseManager(self.server_url)
        
        self.setWindowTitle("🔐 Upload Bridge License Activation (Offline)")
        self.setModal(True)
        self.resize(600, 500)
        
        self.setup_ui()
        self.load_settings()
        
        # Update server URL in license manager when changed
        if hasattr(self, 'server_url_edit'):
            self.server_url_edit.textChanged.connect(self.update_license_manager_url)
    
    def setup_ui(self):
        """Create the license activation UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(":/icons/license.png").scaled(48, 48))
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Upload Bridge License Activation")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Single key-entry panel (offline activation)
        key_group = QGroupBox("Enter License Key")
        key_layout = QVBoxLayout(key_group)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("e.g., ABCD-1234-EFGH-5678")
        key_layout.addWidget(self.key_edit)

        layout.addWidget(key_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to activate license")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("🚀 Activate License")
        self.activate_button.setEnabled(False)
        self.activate_button.clicked.connect(self.activate_license_offline)
        
        self.cancel_button = QPushButton("❌ Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.help_button = QPushButton("❓ Help")
        self.help_button.clicked.connect(self.show_help)
        
        button_layout.addWidget(self.help_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.activate_button)
        
        layout.addLayout(button_layout)
    
    def create_upload_tab(self) -> QWidget:
        # Legacy; not used in offline mode
        return QWidget()
    
    def create_activation_tab(self) -> QWidget:
        return QWidget()
    
    def create_status_tab(self) -> QWidget:
        """Create license status tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Current status
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(200)
        
        status_layout.addWidget(self.status_display)
        
        refresh_button = QPushButton("🔄 Refresh Status")
        refresh_button.clicked.connect(self.refresh_status)
        
        status_layout.addWidget(refresh_button)
        
        layout.addWidget(status_group)
        
        # Activation history
        history_group = QGroupBox("Activation History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        
        history_layout.addWidget(self.history_display)
        
        layout.addWidget(history_group)
        
        layout.addStretch()
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Server settings
        server_group = QGroupBox("License Server Settings")
        server_layout = QFormLayout(server_group)
        
        self.server_url_edit = QLineEdit(self.server_url)
        self.server_url_edit.textChanged.connect(self.on_server_url_changed)
        
        test_button = QPushButton("🧪 Test Connection")
        test_button.clicked.connect(self.test_server_connection)
        
        server_layout.addRow("Server URL:", self.server_url_edit)
        server_layout.addRow("", test_button)
        
        layout.addWidget(server_group)
        
        # Activation settings
        activation_group = QGroupBox("Activation Settings")
        activation_layout = QFormLayout(activation_group)
        
        self.auto_activate_checkbox = QCheckBox("Auto-activate on startup")
        self.auto_activate_checkbox.setChecked(True)
        
        self.validate_periodic_checkbox = QCheckBox("Periodic validation")
        self.validate_periodic_checkbox.setChecked(True)
        
        self.validation_interval_spinbox = QSpinBox()
        self.validation_interval_spinbox.setRange(1, 168)  # 1 hour to 1 week
        self.validation_interval_spinbox.setValue(24)  # 24 hours
        self.validation_interval_spinbox.setSuffix(" hours")
        
        activation_layout.addRow("", self.auto_activate_checkbox)
        activation_layout.addRow("", self.validate_periodic_checkbox)
        activation_layout.addRow("Validation Interval:", self.validation_interval_spinbox)
        
        layout.addWidget(activation_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        self.debug_mode_checkbox = QCheckBox("Debug mode")
        self.debug_mode_checkbox.setChecked(False)
        
        self.offline_mode_checkbox = QCheckBox("Offline mode")
        self.offline_mode_checkbox.setChecked(False)
        
        advanced_layout.addRow("", self.debug_mode_checkbox)
        advanced_layout.addRow("", self.offline_mode_checkbox)
        
        layout.addWidget(advanced_group)
        
        # Save settings
        save_button = QPushButton("💾 Save Settings")
        save_button.clicked.connect(self.save_settings)
        
        layout.addWidget(save_button)
        
        layout.addStretch()
        return widget
    
    def browse_license_file(self):
        """Browse for license file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select License File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.load_license_file(file_path)
    
    def load_license_file(self, file_path: str):
        """Load and validate license file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.license_data = json.load(f)
            
            # Validate license format
            if self.validate_license_data():
                self.update_license_preview()
                self.update_activation_tab()
                self.validation_label.setText("✅ License file loaded successfully")
                self.validation_label.setStyleSheet("color: green; font-weight: bold;")
                self.activate_button.setEnabled(True)
            else:
                self.validation_label.setText("❌ Invalid license file format")
                self.validation_label.setStyleSheet("color: red; font-weight: bold;")
                self.activate_button.setEnabled(False)
                
        except Exception as e:
            self.validation_label.setText(f"❌ Error loading license file: {str(e)}")
            self.validation_label.setStyleSheet("color: red; font-weight: bold;")
            self.activate_button.setEnabled(False)
    
    def validate_license_data(self) -> bool:
        """Validate license data structure"""
        if not self.license_data:
            return False
        
        try:
            license_info = self.license_data.get('license', {})
            required_fields = ['license_id', 'product_id', 'issued_to_email', 'expires_at']
            
            for field in required_fields:
                if field not in license_info:
                    return False
            
            # Check signature
            if 'signature' not in self.license_data:
                return False
            
            return True
        except:
            return False
    
    def update_license_preview(self):
        """Update license preview display"""
        if not self.license_data:
            return
        
        license_info = self.license_data.get('license', {})
        
        preview_text = f"""
License ID: {license_info.get('license_id', 'N/A')}
Product: {license_info.get('product_id', 'N/A')}
Email: {license_info.get('issued_to_email', 'N/A')}
Issued: {license_info.get('issued_at', 'N/A')}
Expires: {license_info.get('expires_at', 'N/A')}
Features: {', '.join(license_info.get('features', []))}
Max Devices: {license_info.get('max_devices', 'N/A')}
        """.strip()
        
        self.license_preview.setText(preview_text)
    
    def update_activation_tab(self):
        """Update activation tab with license information"""
        if not self.license_data:
            return
        
        license_info = self.license_data.get('license', {})
        
        # Generate device ID
        device_id = f"ESP8266_{hash(str(self.license_data)):08X}"
        self.device_id_edit.setText(device_id)
        
        # Update license fields
        self.license_id_edit.setText(license_info.get('license_id', ''))
        self.product_edit.setText(license_info.get('product_id', ''))
        self.email_edit.setText(license_info.get('issued_to_email', ''))
        self.expires_edit.setText(license_info.get('expires_at', ''))
        
        # Update features
        features = license_info.get('features', [])
        self.features_list.setText('\n'.join(f"• {feature}" for feature in features))
    
    def activate_license_offline(self):
        key = self.key_edit.text().strip() if hasattr(self, 'key_edit') else ""
        if not key:
            QMessageBox.warning(self, "License Key", "Please enter a license key.")
            return
        # Try signed token first (more secure). If fails, fall back to premade keys.
        ok, msg = self.license_manager.activate_signed_token(key)
        if not ok:
            ok, msg = self.license_manager.activate_premade_key(key)
        if ok:
            self.status_label.setText("✅ " + msg)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            QMessageBox.information(self, "Activation Successful", msg)
            self.accept()
        else:
            self.status_label.setText("❌ " + msg)
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.warning(self, "Activation Failed", msg)
    
    def update_status_display(self, result: Dict[str, Any]):
        """Update status display with activation result"""
        status_text = f"""
Activation Status: ✅ Success
License ID: {result.get('device', {}).get('license_id', 'N/A')}
Device ID: {result.get('device', {}).get('chip_id', 'N/A')}
Bound At: {result.get('device', {}).get('bound_at', 'N/A')}
Last Seen: {result.get('device', {}).get('last_seen', 'N/A')}
        """.strip()
        
        self.status_display.setText(status_text)
    
    def refresh_status(self):
        """Refresh license status"""
        try:
            if not self.license_data:
                self.status_display.setText("No license loaded. Please load a license file first.")
                return
            
            license_info = self.license_data.get('license', {})
            license_id = license_info.get('license_id', '')
            
            if not license_id:
                self.status_display.setText("Invalid license: missing license ID")
                return
            
            # Try to validate license with server
            try:
                # Generate device ID
                device_id = f"ESP8266_{hash(str(self.license_data)):08X}"
                
                validation_data = {
                    'license_id': license_id,
                    'chip_id': device_id
                }
                
                response = requests.post(
                    f"{self.server_url}/api/validate",
                    json=validation_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('valid'):
                        status_text = f"""Activation Status: ✅ Active
License ID: {license_id}
Device ID: {device_id}
Status: {result.get('status', 'unknown')}
Message: {result.get('message', 'License is valid')}
Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}"""
                        self.status_display.setText(status_text)
                    else:
                        self.status_display.setText(f"License Status: ❌ {result.get('status', 'invalid')}\n{result.get('message', 'License validation failed')}")
                else:
                    self.status_display.setText(f"Server error: {response.status_code}\nUnable to refresh status")
                    
            except requests.exceptions.RequestException as e:
                self.status_display.setText(f"Connection error: {str(e)}\n\nLicense loaded locally but cannot verify online.")
            
        except Exception as e:
            self.status_display.setText(f"Error refreshing status: {str(e)}")
    
    def test_server_connection(self):
        QMessageBox.information(self, "Connection Test", "Offline licensing: no server connection required.")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        <h3>Upload Bridge Offline Licensing</h3>
        <p>Enter a pre-made license key to activate this device.</p>
        <p>No email, no server required.</p>
        <h4>Troubleshooting:</h4>
        <p>• Check the key spelling (use dashes exactly as given)</p>
        <p>• Contact support to obtain a valid key</p>
        """
        
        QMessageBox.information(self, "Help", help_text)
    
    def on_file_path_changed(self):
        """Handle file path change"""
        file_path = self.file_path_edit.text()
        if file_path and os.path.exists(file_path):
            self.load_license_file(file_path)
    
    def on_activation_method_changed(self):
        """Handle activation method change"""
        # Update UI based on selected method
        pass
    
    def on_server_url_changed(self):
        """Handle server URL change"""
        self.server_url = self.server_url_edit.text()
        self.update_license_manager_url()
    
    def update_license_manager_url(self):
        """Update license manager with new server URL"""
        if hasattr(self, 'license_manager'):
            self.license_manager.server_url = self.server_url_edit.text()
    
    def load_settings(self):
        """Load settings from configuration"""
        # Offline mode: nothing to load
        pass
    
    def save_settings(self):
        """Save settings to configuration"""
        QMessageBox.information(self, "Settings", "Offline licensing: no settings to save.")


def show_license_activation_dialog(parent=None) -> bool:
    """Show license activation dialog and return success status"""
    dialog = LicenseActivationDialog(parent)
    return dialog.exec() == QDialog.Accepted


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    dialog = LicenseActivationDialog()
    dialog.show()
    
    sys.exit(app.exec())

