"""
Arduino IDE Tab - Upload Bridge Application
Arduino IDE-like interface with Arduino CLI integration
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                                QLabel, QLineEdit, QPushButton, QComboBox,
                                QTextEdit, QGroupBox, QProgressBar, QCheckBox,
                                QSpinBox, QFileDialog, QMessageBox, QSplitter, 
                                QScrollArea, QTabWidget, QPlainTextEdit, QListWidget)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QProcess
from PySide6.QtGui import QFont, QTextCursor, QSyntaxHighlighter, QTextCharFormat, QColor
import os
import sys
import subprocess
import json
import time
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern import Pattern
from core.subprocess_utils import get_hidden_subprocess_kwargs


class ArduinoSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Arduino C++ code"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define highlighting rules
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(86, 156, 214))  # Blue
        keyword_format.setFontWeight(QFont.Bold)
        
        keywords = [
            '\\bint\\b', '\\bfloat\\b', '\\bdouble\\b', '\\bchar\\b', '\\bvoid\\b',
            '\\bbool\\b', '\\bbyte\\b', '\\bword\\b', '\\blong\\b', '\\bshort\\b',
            '\\bif\\b', '\\belse\\b', '\\bfor\\b', '\\bwhile\\b', '\\bdo\\b',
            '\\bswitch\\b', '\\bcase\\b', '\\bbreak\\b', '\\bcontinue\\b', '\\breturn\\b',
            '\\bclass\\b', '\\bstruct\\b', '\\benum\\b', '\\btypedef\\b',
            '\\bconst\\b', '\\bstatic\\b', '\\bextern\\b', '\\bvolatile\\b',
            '\\bpublic\\b', '\\bprivate\\b', '\\bprotected\\b',
            '\\bsetup\\b', '\\bloop\\b', '\\bdigitalWrite\\b', '\\bdigitalRead\\b',
            '\\banalogWrite\\b', '\\banalogRead\\b', '\\bpinMode\\b', '\\bdelay\\b',
            '\\bSerial\\b', '\\bWire\\b', '\\bSPI\\b', '\\bEEPROM\\b'
        ]
        
        for pattern in keywords:
            self.highlighting_rules.append((pattern, keyword_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(206, 145, 120))  # Orange
        self.highlighting_rules.append(('"[^"]*"', string_format))
        self.highlighting_rules.append(("'[^']*'", string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(106, 153, 85))  # Green
        self.highlighting_rules.append(('//[^\n]*', comment_format))
        self.highlighting_rules.append(('/\\*.*?\\*/', comment_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(181, 206, 168))  # Light green
        self.highlighting_rules.append(('\\b\\d+\\b', number_format))
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to text block"""
        for pattern, format in self.highlighting_rules:
            import re
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, format)


class ArduinoCLIWorker(QThread):
    """Worker thread for Arduino CLI operations"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    output_updated = Signal(str)
    operation_complete = Signal(bool, str)
    
    def __init__(self, operation, sketch_path, board=None, port=None):
        super().__init__()
        self.operation = operation  # 'compile', 'upload', 'verify'
        self.sketch_path = sketch_path
        self.board = board
        self.port = port
        self.cancelled = False
    
    def run(self):
        """Execute Arduino CLI operation"""
        try:
            if self.operation == 'compile':
                self.compile_sketch()
            elif self.operation == 'upload':
                self.upload_sketch()
            elif self.operation == 'verify':
                self.verify_sketch()
        except Exception as e:
            self.operation_complete.emit(False, f"Operation failed: {str(e)}")
    
    def compile_sketch(self):
        """Compile Arduino sketch"""
        self.status_updated.emit("Compiling sketch...")
        self.progress_updated.emit(10)
        
        cmd = ['arduino-cli', 'compile', '--fqbn', self.board, self.sketch_path]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            **get_hidden_subprocess_kwargs()
        )
        
        output_lines = []
        for line in process.stdout:
            if self.cancelled:
                process.terminate()
                return
            
            output_lines.append(line)
            self.output_updated.emit(line.strip())
            
            # Update progress based on output
            if "Compiling" in line:
                self.progress_updated.emit(30)
            elif "Linking" in line:
                self.progress_updated.emit(70)
            elif "Done" in line:
                self.progress_updated.emit(100)
        
        process.wait()
        
        if process.returncode == 0:
            self.operation_complete.emit(True, "Compilation successful!")
        else:
            self.operation_complete.emit(False, "Compilation failed")
    
    def upload_sketch(self):
        """Upload Arduino sketch"""
        self.status_updated.emit("Uploading sketch...")
        self.progress_updated.emit(10)
        
        cmd = ['arduino-cli', 'upload', '--fqbn', self.board, '--port', self.port, self.sketch_path]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            **get_hidden_subprocess_kwargs()
        )
        
        for line in process.stdout:
            if self.cancelled:
                process.terminate()
                return
            
            self.output_updated.emit(line.strip())
            
            if "Uploading" in line:
                self.progress_updated.emit(50)
            elif "Done uploading" in line:
                self.progress_updated.emit(100)
        
        process.wait()
        
        if process.returncode == 0:
            self.operation_complete.emit(True, "Upload successful!")
        else:
            self.operation_complete.emit(False, "Upload failed")
    
    def verify_sketch(self):
        """Verify Arduino sketch"""
        self.compile_sketch()
    
    def cancel(self):
        """Cancel the operation"""
        self.cancelled = True


class ArduinoIDETab(QWidget):
    """
    Arduino IDE-like tab for Upload Bridge
    
    Features:
    - Code editor with syntax highlighting
    - Arduino CLI integration
    - Board and port selection
    - Compile, upload, and verify operations
    - Serial monitor
    - File management
    """
    
    # Signals
    code_generated = Signal(str, str)  # code, file_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_sketch_path = None
        self.arduino_cli_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Create the Arduino IDE tab UI"""
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
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("🔧 Arduino IDE")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Arduino IDE-like interface with Arduino CLI integration")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 15px; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)
        
        # Left panel - Code editor and tools
        left_panel = self.create_code_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Tools and output
        right_panel = self.create_tools_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([800, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def create_code_panel(self):
        """Create the code editor panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # File management group
        file_group = QGroupBox("📁 File Management")
        file_layout = QVBoxLayout(file_group)
        
        # File path display
        file_path_layout = QHBoxLayout()
        self.file_path_label = QLabel("No sketch loaded")
        self.file_path_label.setStyleSheet("""
            QLabel {
                background-color: #3d3d3d;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 11px;
            }
        """)
        file_path_layout.addWidget(self.file_path_label)
        
        # File buttons
        file_buttons_layout = QHBoxLayout()
        
        self.new_button = QPushButton("📄 New")
        self.new_button.clicked.connect(self.new_sketch)
        self.new_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        file_buttons_layout.addWidget(self.new_button)
        
        self.open_button = QPushButton("📂 Open")
        self.open_button.clicked.connect(self.open_sketch)
        self.open_button.setStyleSheet("""
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
        file_buttons_layout.addWidget(self.open_button)
        
        self.save_button = QPushButton("💾 Save")
        self.save_button.clicked.connect(self.save_sketch)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        file_buttons_layout.addWidget(self.save_button)
        
        file_layout.addLayout(file_path_layout)
        file_layout.addLayout(file_buttons_layout)
        layout.addWidget(file_group)
        
        # Code editor group
        editor_group = QGroupBox("📝 Code Editor")
        editor_layout = QVBoxLayout(editor_group)
        
        # Code editor
        self.code_editor = QPlainTextEdit()
        self.code_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        # Set up syntax highlighting
        self.syntax_highlighter = ArduinoSyntaxHighlighter(self.code_editor.document())
        
        # Set default Arduino sketch template
        default_sketch = """void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize pins
  pinMode(LED_BUILTIN, OUTPUT);
  
  Serial.println("Arduino sketch started!");
}

void loop() {
  // Blink LED
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  
  Serial.println("LED blinked!");
}"""
        
        self.code_editor.setPlainText(default_sketch)
        editor_layout.addWidget(self.code_editor)
        
        layout.addWidget(editor_group)
        
        return panel
    
    def create_tools_panel(self):
        """Create the tools and output panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Board configuration group
        board_group = QGroupBox("🔧 Board Configuration")
        board_layout = QVBoxLayout(board_group)
        
        # Board selection
        board_layout.addWidget(QLabel("Board:"))
        self.board_combo = QComboBox()
        self.board_combo.addItems([
            "arduino:avr:uno",
            "arduino:avr:nano",
            "arduino:avr:mega",
            "esp32:esp32:esp32",
            "esp8266:esp8266:nodemcuv2"
        ])
        self.board_combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
        """)
        board_layout.addWidget(self.board_combo)
        
        # Port selection
        board_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
        """)
        board_layout.addWidget(self.port_combo)
        
        # Refresh ports button
        self.refresh_ports_button = QPushButton("🔄 Refresh Ports")
        self.refresh_ports_button.clicked.connect(self.refresh_ports)
        self.refresh_ports_button.setStyleSheet("""
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
        board_layout.addWidget(self.refresh_ports_button)
        
        layout.addWidget(board_group)
        
        # Operations group
        operations_group = QGroupBox("⚡ Operations")
        operations_layout = QVBoxLayout(operations_group)
        
        # Compile button
        self.compile_button = QPushButton("🔨 Compile")
        self.compile_button.clicked.connect(self.compile_sketch)
        self.compile_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        operations_layout.addWidget(self.compile_button)
        
        # Upload button
        self.upload_button = QPushButton("📤 Upload")
        self.upload_button.clicked.connect(self.upload_sketch)
        self.upload_button.setStyleSheet("""
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
        operations_layout.addWidget(self.upload_button)
        
        # Verify button
        self.verify_button = QPushButton("✅ Verify")
        self.verify_button.clicked.connect(self.verify_sketch)
        self.verify_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        operations_layout.addWidget(self.verify_button)
        
        # Cancel button
        self.cancel_button = QPushButton("⏹️ Cancel")
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        operations_layout.addWidget(self.cancel_button)
        
        layout.addWidget(operations_group)
        
        # Progress group
        progress_group = QGroupBox("📊 Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #3d3d3d;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 11px;
            padding: 5px;
            background-color: #3b3b3b;
            border: 1px solid #555555;
            border-radius: 4px;
        """)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Output group
        output_group = QGroupBox("📋 Output")
        output_layout = QVBoxLayout(output_group)
        
        # Output text
        self.output_text = QTextEdit()
        self.output_text.setMaximumHeight(200)
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        output_layout.addWidget(self.output_text)
        
        # Output controls
        output_controls_layout = QHBoxLayout()
        
        self.clear_output_button = QPushButton("🗑️ Clear")
        self.clear_output_button.clicked.connect(self.clear_output)
        self.clear_output_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 6px 10px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        output_controls_layout.addWidget(self.clear_output_button)
        
        output_layout.addLayout(output_controls_layout)
        layout.addWidget(output_group)
        
        return panel
    
    def new_sketch(self):
        """Create a new Arduino sketch"""
        self.code_editor.setPlainText("""void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Initialize pins
  pinMode(LED_BUILTIN, OUTPUT);
  
  Serial.println("Arduino sketch started!");
}

void loop() {
  // Blink LED
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
  
  Serial.println("LED blinked!");
}""")
        self.file_path_label.setText("New sketch (unsaved)")
        self.current_sketch_path = None
    
    def open_sketch(self):
        """Open an Arduino sketch file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Arduino Sketch", "", "Arduino Sketch (*.ino);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.code_editor.setPlainText(content)
                    self.file_path_label.setText(f"Opened: {os.path.basename(file_path)}")
                    self.current_sketch_path = file_path
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_sketch(self):
        """Save the current sketch"""
        if self.current_sketch_path:
            try:
                code = self.code_editor.toPlainText()
                with open(self.current_sketch_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.status_label.setText("Sketch saved successfully!")
                # Emit code generated signal
                self.code_generated.emit(code, self.current_sketch_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
        else:
            self.save_sketch_as()
    
    def save_sketch_as(self):
        """Save the current sketch with a new name"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Arduino Sketch", "", "Arduino Sketch (*.ino);;All Files (*)"
        )
        
        if file_path:
            try:
                code = self.code_editor.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.file_path_label.setText(f"Saved: {os.path.basename(file_path)}")
                self.current_sketch_path = file_path
                self.status_label.setText("Sketch saved successfully!")
                # Emit code generated signal
                self.code_generated.emit(code, file_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        try:
            result = subprocess.run(['arduino-cli', 'board', 'list'], 
                                  capture_output=True, text=True, timeout=10,
                                  **get_hidden_subprocess_kwargs())
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                ports = []
                
                for line in lines[1:]:  # Skip header
                    if line.strip() and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            port = parts[0].strip()
                            if port and port != 'Port':
                                ports.append(port)
                
                self.port_combo.clear()
                self.port_combo.addItems(ports)
                self.status_label.setText(f"Found {len(ports)} ports")
            else:
                self.status_label.setText("Failed to refresh ports")
                
        except Exception as e:
            self.status_label.setText(f"Error refreshing ports: {str(e)}")
    
    def compile_sketch(self):
        """Compile the current sketch"""
        if not self.current_sketch_path:
            QMessageBox.warning(self, "Warning", "Please save the sketch first")
            return
        
        board = self.board_combo.currentText()
        if not board:
            QMessageBox.warning(self, "Warning", "Please select a board")
            return
        
        self.start_operation('compile', board)
    
    def upload_sketch(self):
        """Upload the current sketch"""
        if not self.current_sketch_path:
            QMessageBox.warning(self, "Warning", "Please save the sketch first")
            return
        
        board = self.board_combo.currentText()
        port = self.port_combo.currentText()
        
        if not board or not port:
            QMessageBox.warning(self, "Warning", "Please select a board and port")
            return
        
        self.start_operation('upload', board, port)
    
    def verify_sketch(self):
        """Verify the current sketch"""
        if not self.current_sketch_path:
            QMessageBox.warning(self, "Warning", "Please save the sketch first")
            return
        
        board = self.board_combo.currentText()
        if not board:
            QMessageBox.warning(self, "Warning", "Please select a board")
            return
        
        self.start_operation('verify', board)
    
    def start_operation(self, operation, board, port=None):
        """Start an Arduino CLI operation"""
        if self.arduino_cli_worker and self.arduino_cli_worker.isRunning():
            QMessageBox.warning(self, "Warning", "Another operation is already running")
            return
        
        # Disable operation buttons
        self.compile_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.verify_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Clear output
        self.output_text.clear()
        
        # Start worker thread
        self.arduino_cli_worker = ArduinoCLIWorker(
            operation, self.current_sketch_path, board, port
        )
        
        self.arduino_cli_worker.progress_updated.connect(self.progress_bar.setValue)
        self.arduino_cli_worker.status_updated.connect(self.status_label.setText)
        self.arduino_cli_worker.output_updated.connect(self.output_text.append)
        self.arduino_cli_worker.operation_complete.connect(self.on_operation_complete)
        
        self.arduino_cli_worker.start()
    
    def cancel_operation(self):
        """Cancel the current operation"""
        if self.arduino_cli_worker and self.arduino_cli_worker.isRunning():
            self.arduino_cli_worker.cancel()
            self.arduino_cli_worker.wait()
            self.on_operation_complete(False, "Operation cancelled")
    
    def on_operation_complete(self, success, message):
        """Handle operation completion"""
        # Re-enable operation buttons
        self.compile_button.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.verify_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        # Update status
        self.status_label.setText(message)
        
        if success:
            self.progress_bar.setValue(100)
        else:
            self.progress_bar.setValue(0)
    
    def clear_output(self):
        """Clear the output text"""
        self.output_text.clear()

