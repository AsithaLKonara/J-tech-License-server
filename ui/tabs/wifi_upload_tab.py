"""
WiFi Upload Tab - Upload Bridge Application
WiFi-enabled pattern upload functionality
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

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
            
            # Connect to upload worker signals
            if self.wifi_uploader.upload_worker:
                self.wifi_uploader.upload_worker.upload_complete.connect(self.upload_complete)
        else:
            QMessageBox.warning(self, "Upload Failed", "Failed to start upload. Check if another upload is in progress.")
    
    def cancel_upload(self):
        """Cancel the upload process"""
        self.wifi_uploader.cancel_upload()
        
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.log_message("Upload cancelled by user")
    
    def upload_complete(self, success, message):
        """Handle upload completion"""
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        if success:
            self.log_message(f"✅ {message}")
            QMessageBox.information(self, "Upload Successful", message)
        else:
            self.log_message(f"❌ {message}")
            QMessageBox.warning(self, "Upload Failed", message)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
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

