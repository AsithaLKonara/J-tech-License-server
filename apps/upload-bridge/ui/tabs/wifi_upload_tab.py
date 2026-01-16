"""
WiFi Upload Tab - Upload Bridge Application
WiFi-enabled pattern upload functionality
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
                                QLabel, QLineEdit, QPushButton, QComboBox,
                                QTextEdit, QGroupBox, QProgressBar, QCheckBox,
                                QSpinBox, QFileDialog, QMessageBox, QSplitter, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QTextCursor
import os
import sys
import json
import requests
import threading
import time

# Add parent directories to path for imports
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern
from wifi_upload.upload_bridge_wifi_uploader import UploadBridgeWiFiUploader


class WiFiUploadWorker(QThread):
    """Worker thread for WiFi upload operations"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    upload_complete = Signal(bool, str)
    
    def __init__(self, file_path, esp_ip, esp_port=80):
        super().__init__()
        self.file_path = file_path
        self.esp_ip = esp_ip
        self.esp_port = esp_port
        self.cancelled = False
    
    def run(self):
        """Perform WiFi upload"""
        try:
            self.status_updated.emit("Connecting to ESP8266...")
            
            # Check connection
            if not self.check_connection():
                self.upload_complete.emit(False, "Cannot connect to ESP8266. Check IP address and WiFi connection.")
                return
            
            self.status_updated.emit("Uploading pattern...")
            
            # Upload file
            success, message = self.upload_pattern()
            self.upload_complete.emit(success, message)
            
        except Exception as e:
            self.upload_complete.emit(False, f"Upload error: {str(e)}")
    
    def check_connection(self):
        """Check if ESP8266 is reachable"""
        try:
            response = requests.get(f"http://{self.esp_ip}/api/status", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def upload_pattern(self):
        """Upload pattern file to ESP8266"""
        try:
            file_name = os.path.basename(self.file_path)
            file_size = os.path.getsize(self.file_path)
            
            # Validate file extension
            if not any(file_name.lower().endswith(ext) for ext in ['.bin', '.hex', '.dat', '.leds', '.ledadmin']):
                return False, "Invalid file format. Use .bin, .hex, .dat, .leds, or .ledadmin files."
            
            # Upload file
            url = f"http://{self.esp_ip}/api/upload"
            
            with open(self.file_path, 'rb') as f:
                files = {'pattern': (file_name, f, 'application/octet-stream')}
                
                response = requests.post(url, files=files, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        message = f"Pattern uploaded successfully: {result.get('message', '')}"
                        return True, message
                    else:
                        return False, f"Upload failed: {result.get('message', 'Unknown error')}"
                else:
                    return False, f"Upload failed with HTTP status {response.status_code}"
                    
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to ESP8266 at {self.esp_ip}. Check IP address and WiFi connection."
        except requests.exceptions.Timeout:
            return False, f"Upload timed out after 60 seconds"
        except Exception as e:
            return False, f"Upload error: {str(e)}"
    
    def cancel(self):
        """Cancel the upload operation"""
        self.cancelled = True


class WiFiUploadTab(QWidget):
    """
    WiFi Upload Tab for Upload Bridge
    
    Features:
    - ESP8266 WiFi configuration
    - Pattern file selection
    - Real-time upload progress
    - Status monitoring
    - Web interface integration
    """
    
    # Signals
    upload_started = Signal()
    upload_progress = Signal(int)  # percent
    upload_complete = Signal(bool, str)  # success, message
    brightness_changed = Signal(int)  # brightness value
    schedule_updated = Signal(dict)  # schedule dict
    
    def __init__(self):
        super().__init__()
        self.pattern = None
        self.wifi_uploader = UploadBridgeWiFiUploader()
        self.setup_ui()
    
    def setup_ui(self):
        """Create the WiFi Upload tab UI"""
        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("📡 WiFi Upload")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc_label = QLabel("Upload LED patterns wirelessly to ESP8266/ESP32 devices")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 15px; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Connection status indicator
        self.connection_status = QLabel("🔴 Disconnected")
        self.connection_status.setAlignment(Qt.AlignCenter)
        self.connection_status.setStyleSheet("""
            QLabel {
                background-color: #3b3b3b;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(self.connection_status)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)
        
        # Left panel - Configuration
        left_panel = self.create_configuration_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Status and controls
        right_panel = self.create_status_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def create_configuration_panel(self):
        """Create the configuration panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # WiFi Configuration Group
        wifi_group = QGroupBox("🌐 WiFi Configuration")
        wifi_layout = QVBoxLayout(wifi_group)
        
        # ESP8266 IP Address
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("ESP8266 IP:"))
        self.esp_ip_edit = QLineEdit("192.168.4.1")
        self.esp_ip_edit.setPlaceholderText("192.168.4.1")
        self.esp_ip_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        ip_layout.addWidget(self.esp_ip_edit)
        wifi_layout.addLayout(ip_layout)
        
        # WiFi SSID
        ssid_layout = QHBoxLayout()
        ssid_layout.addWidget(QLabel("WiFi SSID:"))
        self.wifi_ssid_edit = QLineEdit("LEDMatrix_ESP8266")
        self.wifi_ssid_edit.setPlaceholderText("LEDMatrix_ESP8266")
        self.wifi_ssid_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        ssid_layout.addWidget(self.wifi_ssid_edit)
        wifi_layout.addLayout(ssid_layout)
        
        # WiFi Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.wifi_password_edit = QLineEdit("ledmatrix123")
        self.wifi_password_edit.setEchoMode(QLineEdit.Password)
        self.wifi_password_edit.setPlaceholderText("ledmatrix123")
        self.wifi_password_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        password_layout.addWidget(self.wifi_password_edit)
        wifi_layout.addLayout(password_layout)
        
        # Scan button
        self.scan_button = QPushButton("🔍 Scan for ESP8266")
        self.scan_button.clicked.connect(self.scan_for_esp8266)
        self.scan_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        wifi_layout.addWidget(self.scan_button)
        
        # Test connection button
        self.test_button = QPushButton("🔗 Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        wifi_layout.addWidget(self.test_button)

        # Security notice (UI-level reminder that this is intended for trusted networks)
        security_label = QLabel(
            "Security note: WiFi upload is designed for a trusted local network.\n"
            "Avoid exposing the ESP8266 access point and HTTP API to the public internet."
        )
        security_label.setWordWrap(True)
        security_label.setStyleSheet(
            "color: #ffcc66; font-size: 10px; padding-top: 6px;"
        )
        wifi_layout.addWidget(security_label)

        # Quick link to WiFi integration docs
        open_wifi_docs = QPushButton("Open WiFi Upload Guide")
        open_wifi_docs.setToolTip("Open the WiFi upload integration guide and implementation notes.")
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        open_wifi_docs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path('wifi_upload/WIFI_INTEGRATION_COMPLETE.md').resolve()))))
        wifi_layout.addWidget(open_wifi_docs)

        layout.addWidget(wifi_group)
        
        # Pattern File Selection Group
        file_group = QGroupBox("📁 Pattern File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # File path
        file_path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select pattern file (.bin, .hex, .dat, etc.)")
        self.file_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        file_path_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("📂 Browse")
        self.browse_button.clicked.connect(self.browse_file)
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        file_path_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(file_path_layout)
        
        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("""
            color: #888888; 
            font-size: 10px;
            background-color: #2b2b2b;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        """)
        file_layout.addWidget(self.file_info_label)
        
        layout.addWidget(file_group)
        
        # Upload Controls Group
        upload_group = QGroupBox("Upload Controls")
        upload_layout = QVBoxLayout()
        
        # Upload button
        self.upload_button = QPushButton("📡 Upload via WiFi")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.upload_button.clicked.connect(self.start_upload)
        upload_layout.addWidget(self.upload_button)
        
        # Cancel button
        self.cancel_button = QPushButton("❌ Cancel Upload")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_upload)
        upload_layout.addWidget(self.cancel_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        upload_layout.addWidget(self.progress_bar)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Quick Actions Group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        # Web interface button
        self.web_button = QPushButton("🌐 Open Web Interface")
        self.web_button.clicked.connect(self.open_web_interface)
        actions_layout.addWidget(self.web_button)
        
        # Status check button
        self.status_button = QPushButton("📊 Check Status")
        self.status_button.clicked.connect(self.check_status)
        actions_layout.addWidget(self.status_button)
        
        # Flash WiFi firmware button
        self.flash_wifi_button = QPushButton("🔄 Flash WiFi Firmware")
        self.flash_wifi_button.clicked.connect(self.flash_wifi_firmware)
        actions_layout.addWidget(self.flash_wifi_button)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Phase 4: WiFi Upload Enhancements
        # Brightness Control Group
        brightness_group = QGroupBox("💡 Brightness Control")
        brightness_layout = QVBoxLayout(brightness_group)
        
        brightness_slider_layout = QHBoxLayout()
        brightness_slider_layout.addWidget(QLabel("Brightness:"))
        self.brightness_slider = QSpinBox()
        self.brightness_slider.setRange(0, 255)
        self.brightness_slider.setValue(255)
        self.brightness_slider.setSuffix(" / 255")
        brightness_slider_layout.addWidget(self.brightness_slider)
        
        self.set_brightness_button = QPushButton("Set Brightness")
        self.set_brightness_button.clicked.connect(self.set_brightness)
        brightness_slider_layout.addWidget(self.set_brightness_button)
        brightness_layout.addLayout(brightness_slider_layout)
        
        self.brightness_status_label = QLabel("Current: Not checked")
        self.brightness_status_label.setStyleSheet("color: #888888; font-size: 10px;")
        brightness_layout.addWidget(self.brightness_status_label)
        
        layout.addWidget(brightness_group)
        
        # Pattern Library Group
        library_group = QGroupBox("📚 Pattern Library")
        library_layout = QVBoxLayout(library_group)
        
        library_buttons_layout = QHBoxLayout()
        self.list_library_button = QPushButton("📋 List Patterns")
        self.list_library_button.clicked.connect(self.list_pattern_library)
        library_buttons_layout.addWidget(self.list_library_button)
        
        self.upload_to_library_button = QPushButton("⬆️ Upload to Library")
        self.upload_to_library_button.clicked.connect(self.upload_to_library)
        library_buttons_layout.addWidget(self.upload_to_library_button)
        
        library_layout.addLayout(library_buttons_layout)
        
        self.library_list_widget = QTextEdit()
        self.library_list_widget.setMaximumHeight(100)
        self.library_list_widget.setReadOnly(True)
        self.library_list_widget.setPlaceholderText("No patterns in library. Click 'List Patterns' to check.")
        library_layout.addWidget(self.library_list_widget)
        
        layout.addWidget(library_group)
        
        # Pattern Scheduling Group
        schedule_group = QGroupBox("⏰ Pattern Scheduling")
        schedule_layout = QVBoxLayout(schedule_group)
        
        schedule_form_layout = QFormLayout()
        self.schedule_pattern_combo = QComboBox()
        self.schedule_pattern_combo.setEditable(True)
        self.schedule_pattern_combo.setPlaceholderText("Enter pattern name")
        schedule_form_layout.addRow("Pattern:", self.schedule_pattern_combo)
        
        self.schedule_time_edit = QLineEdit()
        self.schedule_time_edit.setPlaceholderText("HH:MM (24-hour format)")
        self.schedule_time_edit.setText("12:00")
        schedule_form_layout.addRow("Time:", self.schedule_time_edit)
        
        self.schedule_repeat_checkbox = QCheckBox("Repeat daily")
        schedule_form_layout.addRow("", self.schedule_repeat_checkbox)
        
        schedule_layout.addLayout(schedule_form_layout)
        
        schedule_buttons_layout = QHBoxLayout()
        self.schedule_button = QPushButton("📅 Schedule Pattern")
        self.schedule_button.clicked.connect(self.schedule_pattern)
        schedule_buttons_layout.addWidget(self.schedule_button)
        
        self.get_schedule_button = QPushButton("📋 View Schedule")
        self.get_schedule_button.clicked.connect(self.get_schedule)
        schedule_buttons_layout.addWidget(self.get_schedule_button)
        
        schedule_layout.addLayout(schedule_buttons_layout)
        
        self.schedule_status_label = QLabel("")
        self.schedule_status_label.setStyleSheet("color: #888888; font-size: 10px;")
        schedule_layout.addWidget(self.schedule_status_label)
        
        layout.addWidget(schedule_group)
        
        # OTA Firmware Update Group
        ota_group = QGroupBox("🔄 OTA Firmware Update")
        ota_layout = QVBoxLayout(ota_group)
        
        ota_file_layout = QHBoxLayout()
        self.ota_firmware_path_edit = QLineEdit()
        self.ota_firmware_path_edit.setPlaceholderText("Select firmware .bin file")
        ota_file_layout.addWidget(self.ota_firmware_path_edit)
        
        self.ota_browse_button = QPushButton("📂 Browse")
        self.ota_browse_button.clicked.connect(self.browse_ota_firmware)
        ota_file_layout.addWidget(self.ota_browse_button)
        
        ota_layout.addLayout(ota_file_layout)
        
        self.ota_update_button = QPushButton("🚀 Update Firmware (OTA)")
        self.ota_update_button.clicked.connect(self.update_firmware_ota)
        self.ota_update_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        ota_layout.addWidget(self.ota_update_button)
        
        ota_warning = QLabel("⚠️ Warning: OTA updates will restart the device. Ensure stable WiFi connection.")
        ota_warning.setWordWrap(True)
        ota_warning.setStyleSheet("color: #ffcc66; font-size: 10px;")
        ota_layout.addWidget(ota_warning)
        
        layout.addWidget(ota_group)
        
        # Multi-Device Sync Group
        multi_device_group = QGroupBox("🔗 Multi-Device Sync")
        multi_device_layout = QVBoxLayout(multi_device_group)
        
        self.multi_device_ips_edit = QLineEdit()
        self.multi_device_ips_edit.setPlaceholderText("Enter IP addresses separated by commas (e.g., 192.168.4.1, 192.168.4.2)")
        multi_device_layout.addWidget(self.multi_device_ips_edit)
        
        self.sync_all_button = QPushButton("🔄 Sync Pattern to All Devices")
        self.sync_all_button.clicked.connect(self.sync_to_multiple_devices)
        multi_device_layout.addWidget(self.sync_all_button)
        
        self.multi_device_status_label = QLabel("")
        self.multi_device_status_label.setStyleSheet("color: #888888; font-size: 10px;")
        self.multi_device_status_label.setWordWrap(True)
        multi_device_layout.addWidget(self.multi_device_status_label)
        
        layout.addWidget(multi_device_group)
        
        panel.setLayout(layout)
        return panel
    
    def create_status_panel(self):
        """Create the status and monitoring panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Status Group
        status_group = QGroupBox("📊 ESP8266 Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        status_layout.addWidget(self.status_text)
        
        # Status controls
        status_controls_layout = QHBoxLayout()
        
        self.refresh_status_button = QPushButton("🔄 Refresh Status")
        self.refresh_status_button.clicked.connect(self.refresh_status)
        self.refresh_status_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        status_controls_layout.addWidget(self.refresh_status_button)
        
        self.clear_status_button = QPushButton("🗑️ Clear")
        self.clear_status_button.clicked.connect(self.clear_status)
        self.clear_status_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        status_controls_layout.addWidget(self.clear_status_button)
        
        status_layout.addLayout(status_controls_layout)
        layout.addWidget(status_group)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Instructions Group
        instructions_group = QGroupBox("WiFi Upload Instructions")
        instructions_layout = QVBoxLayout()
        
        instructions_text = """1. First, flash the WiFi-enabled firmware to your ESP8266 using the Flash tab
2. Connect to the ESP8266's WiFi network (SSID: LEDMatrix_ESP8266, Password: ledmatrix123)
3. Select your pattern file and click "Upload via WiFi"
4. The pattern will be uploaded over-the-air and start playing immediately
5. You can also open the web interface at http://192.168.4.1 for manual uploads

WiFi Network Details:
• SSID: LEDMatrix_ESP8266
• Password: ledmatrix123
• ESP8266 IP: 192.168.4.1
• Web Interface: http://192.168.4.1"""
        
        instructions_label = QLabel(instructions_text)
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("color: #cccccc; font-size: 11px; line-height: 1.4;")
        instructions_layout.addWidget(instructions_label)
        
        instructions_group.setLayout(instructions_layout)
        layout.addWidget(instructions_group)
        
        # Log Group
        log_group = QGroupBox("Upload Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border: 1px solid #3d3d3d;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # Clear log button
        clear_log_button = QPushButton("🗑️ Clear Log")
        clear_log_button.clicked.connect(self.clear_log)
        log_layout.addWidget(clear_log_button)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        panel.setLayout(layout)
        return panel
    
    def browse_file(self):
        """Browse for pattern file"""
        filetypes = [
            ("Pattern files", "*.bin *.hex *.dat *.leds *.ledadmin"),
            ("Binary files", "*.bin"),
            ("Hex files", "*.hex"),
            ("Data files", "*.dat"),
            ("LED files", "*.leds"),
            ("LEDAdmin files", "*.ledadmin"),
            ("All files", "*.*")
        ]
        
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pattern File for WiFi Upload",
            "",
            ";;".join([f"{desc} ({pattern})" for desc, pattern in filetypes])
        )
        
        if filename:
            self.file_path_edit.setText(filename)
            self.update_file_info(filename)
            self.log_message(f"Selected file: {os.path.basename(filename)}")
    
    def update_file_info(self, file_path):
        """Update file information display"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # Try to parse pattern info
            try:
                with open(file_path, 'rb') as f:
                    data = f.read(4)
                    if len(data) >= 4:
                        num_leds = data[0] | (data[1] << 8)
                        num_frames = data[2] | (data[3] << 8)
                        self.file_info_label.setText(f"File: {file_name} | Size: {file_size:,} bytes | LEDs: {num_leds} | Frames: {num_frames}")
                    else:
                        self.file_info_label.setText(f"File: {file_name} | Size: {file_size:,} bytes")
            except:
                self.file_info_label.setText(f"File: {file_name} | Size: {file_size:,} bytes")
                
        except Exception as e:
            self.file_info_label.setText(f"Error reading file: {str(e)}")
    
    def test_connection(self):
        """Test connection to ESP8266"""
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "Warning", "Please enter ESP8266 IP address")
            return
        
        self.connection_status.setText("🟡 Testing connection...")
        self.connection_status.setStyleSheet("""
            QLabel {
                background-color: #3b3b3b;
                border: 2px solid #FF9800;
                border-radius: 8px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        # Test connection in a separate thread
        import threading
        def test_thread():
            try:
                import requests
                response = requests.get(f"http://{esp_ip}/api/status", timeout=5)
                if response.status_code == 200:
                    self.connection_status.setText("🟢 Connected")
                    self.connection_status.setStyleSheet("""
                        QLabel {
                            background-color: #3b3b3b;
                            border: 2px solid #4CAF50;
                            border-radius: 8px;
                            padding: 10px;
                            font-size: 12px;
                            font-weight: bold;
                            margin-bottom: 10px;
                        }
                    """)
                else:
                    self.connection_status.setText("🔴 Connection failed")
                    self.connection_status.setStyleSheet("""
                        QLabel {
                            background-color: #3b3b3b;
                            border: 2px solid #f44336;
                            border-radius: 8px;
                            padding: 10px;
                            font-size: 12px;
                            font-weight: bold;
                            margin-bottom: 10px;
                        }
                    """)
            except:
                self.connection_status.setText("🔴 Connection failed")
                self.connection_status.setStyleSheet("""
                    QLabel {
                        background-color: #3b3b3b;
                        border: 2px solid #f44336;
                        border-radius: 8px;
                        padding: 10px;
                        font-size: 12px;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }
                """)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def refresh_status(self):
        """Refresh ESP8266 status"""
        self.status_text.append("Refreshing status...")
    
    def clear_status(self):
        """Clear status text"""
        self.status_text.clear()
    
    def scan_for_esp8266(self):
        """Scan for ESP8266 WiFi network"""
        self.log_message("Scanning for ESP8266 WiFi network...")
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning...")
        
        # Simulate scan (in real implementation, would use system WiFi APIs)
        QTimer.singleShot(2000, self.scan_complete)
    
    def scan_complete(self):
        """Complete the scan process"""
        self.scan_button.setEnabled(True)
        self.scan_button.setText("🔍 Scan for ESP8266")
        
        # Check if we can connect to the configured IP
        esp_ip = self.esp_ip_edit.text()
        try:
            response = requests.get(f"http://{esp_ip}/api/status", timeout=3)
            if response.status_code == 200:
                self.log_message(f"✓ Found ESP8266 at {esp_ip}")
                self.status_text.append(f"ESP8266 Status: Connected\nIP: {esp_ip}\nSSID: {self.wifi_ssid_edit.text()}")
            else:
                self.log_message(f"⚠ ESP8266 not responding at {esp_ip}")
        except:
            self.log_message(f"✗ Cannot connect to ESP8266 at {esp_ip}")
            self.log_message("Make sure ESP8266 is powered on and WiFi firmware is flashed")
    
    def start_upload(self):
        """Start WiFi upload process"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern Loaded", "Please load a pattern first using File > Open.")
            return
        
        esp_ip = self.esp_ip_edit.text()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        # Validate pattern for ESP8266
        is_valid, message = self.wifi_uploader.validate_pattern_for_esp8266(self.pattern)
        if not is_valid:
            QMessageBox.warning(self, "Pattern Validation Failed", message)
            return
        
        # Configure WiFi uploader
        self.wifi_uploader.set_esp_config(esp_ip)
        
        # Start upload using integrated uploader
        success = self.wifi_uploader.upload_pattern(
            self.pattern,
            progress_callback=self.update_progress,
            status_callback=self.log_message
        )
        
        if success:
            # Update UI
            self.upload_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            self.log_message("Starting WiFi upload...")
            
            # Emit started signal
            self.upload_started.emit()
            
            # Connect to upload worker signals
            if self.wifi_uploader.upload_worker:
                self.wifi_uploader.upload_worker.upload_complete.connect(self._on_upload_complete)
        else:
            QMessageBox.warning(self, "Upload Failed", "Failed to start upload. Check if another upload is in progress.")
    
    def cancel_upload(self):
        """Cancel the upload process"""
        self.wifi_uploader.cancel_upload()
        
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.log_message("Upload cancelled by user")
    
    def _on_upload_complete(self, success, message):
        """Handle upload completion"""
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        # Emit completion signal
        self.upload_complete.emit(success, message)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "Upload Successful", message)
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "Upload Failed", message)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        # Emit progress signal
        self.upload_progress.emit(value)
    
    def open_web_interface(self):
        """Open ESP8266 web interface in browser"""
        esp_ip = self.esp_ip_edit.text()
        if esp_ip:
            self.wifi_uploader.set_esp_config(esp_ip)
            if self.wifi_uploader.open_web_interface():
                self.log_message(f"Opened web interface: http://{esp_ip}")
            else:
                QMessageBox.warning(self, "Error", "Failed to open web interface.")
        else:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
    
    def check_status(self):
        """Check ESP8266 status"""
        esp_ip = self.esp_ip_edit.text()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        # Configure WiFi uploader
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message(f"Checking ESP8266 status at {esp_ip}...")
        
        status = self.wifi_uploader.get_status()
        if status:
            self.log_message("✓ ESP8266 Status Retrieved")
            
            status_text = f"""ESP8266 Status:
Status: {status.get('status', 'Unknown')}
WiFi Mode: {status.get('wifi_mode', 'Unknown')}
SSID: {status.get('ssid', 'Unknown')}
IP: {status.get('ip', 'Unknown')}"""
            
            if status.get('pattern_loaded'):
                status_text += f"""
Pattern Loaded: Yes
LEDs: {status.get('num_leds', 0)}
Frames: {status.get('num_frames', 0)}
Size: {status.get('pattern_size', 0):,} bytes"""
            else:
                status_text += "\nPattern Loaded: No"
            
            self.status_text.setText(status_text)
        else:
            self.log_message("✗ Cannot connect to ESP8266. Check IP address and WiFi connection.")
    
    def flash_wifi_firmware(self):
        """Flash WiFi-enabled firmware to ESP8266"""
        QMessageBox.information(self, "Flash WiFi Firmware", 
                               "This feature will flash WiFi-enabled firmware to your ESP8266.\n\n"
                               "Please use the Flash tab to flash the WiFi firmware first.\n\n"
                               "The WiFi firmware creates a WiFi network:\n"
                               "• SSID: LEDMatrix_ESP8266\n"
                               "• Password: ledmatrix123\n"
                               "• IP: 192.168.4.1")
    
    def log_message(self, message):
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.clear()
        self.log_message("Log cleared")
    
    def set_pattern(self, pattern: Pattern):
        """Set the current pattern"""
        self.pattern = pattern
        if pattern:
            self.log_message(f"Pattern loaded: {pattern.name}")
        else:
            self.log_message("No pattern loaded")
    
    def refresh_preview(self, pattern: Pattern = None):
        """Refresh preview with updated pattern (called from pattern_changed signal)"""
        if pattern is None:
            pattern = self.pattern
        if pattern:
            self.set_pattern(pattern)
    
    # ========== Phase 4: WiFi Upload Enhancements - Handler Methods ==========
    
    def set_brightness(self):
        """Set brightness on ESP8266"""
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        brightness = self.brightness_slider.value()
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message(f"Setting brightness to {brightness}/255...")
        success, message = self.wifi_uploader.set_brightness(brightness)
        
        if success:
            self.brightness_status_label.setText(f"Current: {brightness}/255")
            self.log_message(f"✅ {message}")
            # Emit brightness changed signal
            self.brightness_changed.emit(brightness)
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "Brightness Update Failed", message)
    
    def list_pattern_library(self):
        """List patterns in ESP8266 library"""
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message("Fetching pattern library...")
        patterns = self.wifi_uploader.list_pattern_library()
        
        if patterns is not None:
            if patterns:
                pattern_list = "\n".join([f"• {p}" for p in patterns])
                self.library_list_widget.setText(pattern_list)
                self.log_message(f"✅ Found {len(patterns)} pattern(s) in library")
            else:
                self.library_list_widget.setText("No patterns in library.")
                self.log_message("ℹ️ Pattern library is empty")
        else:
            self.log_message("❌ Failed to fetch pattern library. Check connection.")
            QMessageBox.warning(self, "Error", "Failed to fetch pattern library. Check connection.")
    
    def upload_to_library(self):
        """Upload current pattern to ESP8266 library"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "Please load a pattern first.")
            return
        
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        # Get pattern name from user
        from PySide6.QtWidgets import QInputDialog
        pattern_name, ok = QInputDialog.getText(
            self,
            "Pattern Name",
            "Enter a name for this pattern:",
            text=self.pattern.name or "pattern1"
        )
        
        if not ok or not pattern_name:
            return
        
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message(f"Uploading pattern '{pattern_name}' to library...")
        success, message = self.wifi_uploader.upload_to_library(self.pattern, pattern_name)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "Success", message)
            # Refresh library list
            self.list_pattern_library()
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "Upload Failed", message)
    
    def schedule_pattern(self):
        """Schedule a pattern to play at a specific time"""
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        pattern_name = self.schedule_pattern_combo.currentText().strip()
        if not pattern_name:
            QMessageBox.warning(self, "No Pattern Name", "Please enter a pattern name.")
            return
        
        schedule_time = self.schedule_time_edit.text().strip()
        if not schedule_time:
            QMessageBox.warning(self, "No Time", "Please enter a schedule time (HH:MM).")
            return
        
        # Validate time format
        try:
            hour, minute = schedule_time.split(':')
            hour = int(hour)
            minute = int(minute)
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError()
        except:
            QMessageBox.warning(self, "Invalid Time", "Time must be in HH:MM format (24-hour).")
            return
        
        repeat = self.schedule_repeat_checkbox.isChecked()
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message(f"Scheduling pattern '{pattern_name}' for {schedule_time}...")
        success, message = self.wifi_uploader.schedule_pattern(pattern_name, schedule_time, repeat)
        
        if success:
            self.schedule_status_label.setText(f"Scheduled: {pattern_name} at {schedule_time}" + (" (daily)" if repeat else ""))
            self.log_message(f"✅ {message}")
            # Emit schedule updated signal
            schedule_dict = {
                'pattern': pattern_name,
                'time': schedule_time,
                'repeat': repeat
            }
            self.schedule_updated.emit(schedule_dict)
            QMessageBox.information(self, "Scheduled", message)
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "Schedule Failed", message)
    
    def get_schedule(self):
        """Get current schedule from ESP8266"""
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message("Fetching schedule...")
        schedule = self.wifi_uploader.get_schedule()
        
        if schedule:
            schedule_text = f"Pattern: {schedule.get('pattern', 'N/A')}\n"
            schedule_text += f"Time: {schedule.get('time', 'N/A')}\n"
            schedule_text += f"Repeat: {'Yes' if schedule.get('repeat', False) else 'No'}"
            self.schedule_status_label.setText(schedule_text)
            self.log_message("✅ Schedule retrieved")
        else:
            self.schedule_status_label.setText("No schedule set")
            self.log_message("ℹ️ No schedule found")
    
    def browse_ota_firmware(self):
        """Browse for OTA firmware file"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Firmware File for OTA Update",
            "",
            "Firmware files (*.bin);;All files (*.*)"
        )
        
        if filename:
            self.ota_firmware_path_edit.setText(filename)
            self.log_message(f"Selected firmware: {os.path.basename(filename)}")
    
    def update_firmware_ota(self):
        """Update ESP8266 firmware via OTA"""
        firmware_path = self.ota_firmware_path_edit.text().strip()
        if not firmware_path:
            QMessageBox.warning(self, "No Firmware File", "Please select a firmware file.")
            return
        
        if not os.path.exists(firmware_path):
            QMessageBox.warning(self, "File Not Found", f"Firmware file not found: {firmware_path}")
            return
        
        esp_ip = self.esp_ip_edit.text().strip()
        if not esp_ip:
            QMessageBox.warning(self, "No IP Address", "Please enter ESP8266 IP address.")
            return
        
        # Confirm OTA update
        reply = QMessageBox.question(
            self,
            "Confirm OTA Update",
            f"Update firmware on ESP8266 at {esp_ip}?\n\n"
            f"File: {os.path.basename(firmware_path)}\n\n"
            "⚠️ Warning: This will restart the device. Ensure stable WiFi connection.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.wifi_uploader.set_esp_config(esp_ip)
        
        self.log_message(f"Starting OTA firmware update...")
        self.ota_update_button.setEnabled(False)
        
        # Run OTA update in a thread to avoid blocking UI
        import threading
        def ota_thread():
            success, message = self.wifi_uploader.update_firmware_ota(firmware_path)
            self.ota_update_button.setEnabled(True)
            
            if success:
                self.log_message(f"✅ {message}")
                QMessageBox.information(self, "OTA Update Successful", message)
            else:
                self.log_message(f"❌ {message}")
                QMessageBox.warning(self, "OTA Update Failed", message)
        
        threading.Thread(target=ota_thread, daemon=True).start()
    
    def sync_to_multiple_devices(self):
        """Sync pattern to multiple ESP8266 devices"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "Please load a pattern first.")
            return
        
        device_ips_text = self.multi_device_ips_edit.text().strip()
        if not device_ips_text:
            QMessageBox.warning(self, "No Devices", "Please enter device IP addresses.")
            return
        
        # Parse IP addresses
        device_ips = [ip.strip() for ip in device_ips_text.split(',') if ip.strip()]
        if not device_ips:
            QMessageBox.warning(self, "Invalid IPs", "Please enter valid IP addresses separated by commas.")
            return
        
        # Confirm sync
        reply = QMessageBox.question(
            self,
            "Confirm Multi-Device Sync",
            f"Sync pattern to {len(device_ips)} device(s)?\n\n"
            f"Devices: {', '.join(device_ips)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.log_message(f"Syncing pattern to {len(device_ips)} device(s)...")
        self.sync_all_button.setEnabled(False)
        
        # Run sync in a thread
        import threading
        def sync_thread():
            results = self.wifi_uploader.sync_to_multiple_devices(self.pattern, device_ips)
            
            # Display results
            success_count = sum(1 for success, _ in results.values() if success)
            result_text = f"Sync complete: {success_count}/{len(device_ips)} successful\n\n"
            
            for device_ip, (success, message) in results.items():
                status = "✅" if success else "❌"
                result_text += f"{status} {device_ip}: {message}\n"
                self.log_message(f"{status} {device_ip}: {message}")
            
            self.multi_device_status_label.setText(result_text)
            self.sync_all_button.setEnabled(True)
            
            if success_count == len(device_ips):
                QMessageBox.information(self, "Sync Complete", f"Successfully synced to all {len(device_ips)} device(s).")
            else:
                QMessageBox.warning(self, "Sync Partial", f"Synced to {success_count}/{len(device_ips)} device(s). Check log for details.")
        
        threading.Thread(target=sync_thread, daemon=True).start()

