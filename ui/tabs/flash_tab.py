"""
Flash Tab - Chip selection and firmware upload
Complete PySide6 implementation - REAL UPLOADING!
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QLabel, QComboBox, QGroupBox, QProgressBar,
                                QTextEdit, QSpinBox, QCheckBox, QMessageBox, QScrollArea, QFileDialog, QDialog, QTextBrowser, QTabWidget)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QTextCursor, QFont
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import Pattern, Frame
from core.wiring_mapper import WiringMapper
from core.matrix_detector import MatrixDetector
from uploaders.uploader_registry import UploaderRegistry, get_uploader
from uploaders.base import UploadStatus
from firmware.builder import FirmwareBuilder
import copy


class FlashThread(QThread):
    """Background thread for flashing to avoid UI freeze"""
    
    # Signals
    progress = Signal(str, float, str)  # status, progress (0-1), message
    finished = Signal(bool, str)  # success, message
    log = Signal(str)  # log message
    build_result_ready = Signal(object)  # build_result object
    
    def __init__(self, pattern, chip_id, port, gpio, verify):
        super().__init__()
        self.pattern = pattern
        self.chip_id = chip_id
        self.port = port
        self.gpio = gpio
        self.verify = verify
    
    def run(self):
        """Execute build and flash process"""
        try:
            # Step 1: Get uploader
            self.log.emit(f"Getting uploader for {self.chip_id}...")
            uploader = get_uploader(self.chip_id)
            
            if not uploader:
                self.finished.emit(False, f"No uploader found for {self.chip_id}")
                return
            
            # Set progress callback
            uploader.set_progress_callback(self.on_uploader_progress)
            
            # Step 2: Build firmware
            self.log.emit("Building firmware...")
            self.progress.emit("building", 0.0, "Building firmware...")
            
            builder = FirmwareBuilder()
            build_result = builder.build(self.pattern, self.chip_id, {
                'gpio_pin': self.gpio
            })
            
            if not build_result.success:
                self.finished.emit(False, f"Build failed: {build_result.error_message}")
                return
            
            self.log.emit(f"Build successful: {build_result.firmware_path}")
            self.log.emit(f"Firmware size: {build_result.size_bytes} bytes")
            
            # Emit build result so FlashTab can store it for save/view
            self.build_result_ready.emit(build_result)
            
            # Step 3: Upload
            self.log.emit(f"Uploading to {self.port}...")
            self.progress.emit("uploading", 0.5, f"Uploading to {self.port}...")
            
            upload_result = uploader.upload(build_result.firmware_path, {
                'port': self.port
            })
            
            if upload_result.success:
                self.log.emit(f"Upload successful!")
                self.log.emit(f"Duration: {upload_result.duration_seconds:.1f}s")
                self.log.emit(f"Bytes written: {upload_result.bytes_written}")
                
                # Step 4: Verify (if requested)
                if self.verify:
                    self.log.emit("Verifying...")
                    self.progress.emit("verifying", 0.9, "Verifying...")
                    
                    verified = uploader.verify(build_result.firmware_path, {
                        'port': self.port
                    })
                    
                    if verified:
                        self.log.emit("Verification successful!")
                    else:
                        self.log.emit("Warning: Verification failed")
                
                self.progress.emit("complete", 1.0, "Flash complete!")
                self.finished.emit(True, "Pattern uploaded successfully!")
            
            else:
                self.finished.emit(False, f"Upload failed: {upload_result.error_message}")
        
        except Exception as e:
            self.log.emit(f"ERROR: {str(e)}")
            self.finished.emit(False, f"Error: {str(e)}")
    
    def on_uploader_progress(self, status, progress, message):
        """Uploader progress callback"""
        self.progress.emit(status.value, progress, message)
        self.log.emit(f"  {message}")


class FlashTab(QWidget):
    """
    Flash tab for building and uploading firmware
    
    Features:
    - Chip selection (all supported chips)
    - Port auto-detection
    - GPIO configuration
    - Build and flash with progress
    - Real-time logging
    - Verification option
    """
    
    # Signals
    flash_complete = Signal(bool, str)  # success, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.flash_thread: FlashThread = None
        self.last_build_result = None  # Store build result for save/view
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
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
        title_label = QLabel("⚡ Flash to Device")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Select your microcontroller and flash the LED pattern")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 15px; font-size: 11px;")
        layout.addWidget(desc_label)
        
        # Chip selection
        chip_group = QGroupBox("Target Chip")
        chip_layout = QVBoxLayout()
        
        chip_select_layout = QHBoxLayout()
        chip_select_layout.addWidget(QLabel("Chip:"))
        
        self.chip_combo = QComboBox()
        self.populate_chip_list()
        self.chip_combo.currentTextChanged.connect(self.on_chip_changed)
        chip_select_layout.addWidget(self.chip_combo)
        
        chip_layout.addLayout(chip_select_layout)
        
        # Chip info display
        self.chip_info_label = QLabel("")
        self.chip_info_label.setWordWrap(True)
        chip_layout.addWidget(self.chip_info_label)
        
        chip_group.setLayout(chip_layout)
        layout.addWidget(chip_group)
        
        # Port selection
        port_group = QGroupBox("Serial Port")
        port_layout = QHBoxLayout()
        
        self.port_combo = QComboBox()
        port_layout.addWidget(self.port_combo)
        
        refresh_button = QPushButton("🔄 Refresh")
        refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_button)
        
        port_group.setLayout(port_layout)
        layout.addWidget(port_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Data GPIO:"))
        
        self.gpio_spin = QSpinBox()
        self.gpio_spin.setRange(0, 50)
        self.gpio_spin.setValue(2)
        config_layout.addWidget(self.gpio_spin)
        
        config_layout.addStretch()
        
        self.verify_checkbox = QCheckBox("Verify after flash")
        self.verify_checkbox.setChecked(True)
        config_layout.addWidget(self.verify_checkbox)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Flip Corrections (for physical panel orientation mismatches)
        flip_group = QGroupBox("🔧 Orientation Corrections")
        flip_layout = QHBoxLayout()
        
        flip_layout.addWidget(QLabel("Apply if hardware doesn't match preview:"))
        
        self.flip_x_checkbox = QCheckBox("Flip X (Horizontal)")
        self.flip_x_checkbox.setToolTip("Mirror left-right. Use if columns are reversed.")
        flip_layout.addWidget(self.flip_x_checkbox)
        
        self.flip_y_checkbox = QCheckBox("Flip Y (Vertical)")
        self.flip_y_checkbox.setToolTip("Mirror top-bottom. Use if rows are upside down.")
        flip_layout.addWidget(self.flip_y_checkbox)
        
        flip_layout.addStretch()
        
        flip_group.setLayout(flip_layout)
        layout.addWidget(flip_group)
        
        # Flash button
        self.flash_button = QPushButton("⚡ FLASH TO DEVICE")
        self.flash_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.flash_button.clicked.connect(self.on_flash)
        layout.addWidget(self.flash_button)
        
        # Progress
        progress_layout = QVBoxLayout()
        
        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        # Log output
        log_group = QGroupBox("Flash Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_controls.addWidget(clear_log_btn)
        
        # Firmware save/view buttons
        self.save_firmware_btn = QPushButton("💾 Save Firmware")
        self.save_firmware_btn.clicked.connect(self.save_firmware)
        self.save_firmware_btn.setEnabled(False)
        self.save_firmware_btn.setToolTip("Save firmware files to a custom location")
        log_controls.addWidget(self.save_firmware_btn)
        
        self.view_firmware_btn = QPushButton("👁 View Firmware")
        self.view_firmware_btn.clicked.connect(self.view_firmware)
        self.view_firmware_btn.setEnabled(False)
        self.view_firmware_btn.setToolTip("View firmware source files (pattern_data.h and .ino)")
        log_controls.addWidget(self.view_firmware_btn)
        
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Initial update
        self.on_chip_changed(self.chip_combo.currentText())
        self.refresh_ports()
    
    def populate_chip_list(self):
        """Fill chip dropdown from registry"""
        registry = UploaderRegistry.instance()
        chips = registry.list_supported_chips()
        
        for chip in sorted(chips):
            self.chip_combo.addItem(chip)
    
    def on_chip_changed(self, chip_id: str):
        """Display chip information"""
        registry = UploaderRegistry.instance()
        spec = registry.get_chip_spec(chip_id)
        
        if spec:
            info = f"<b>{chip_id.upper()}</b><br>"
            info += f"Family: {spec.get('family', 'unknown').upper()}<br>"
            
            # Handle flash size (could be string like "4MB" or number)
            flash_size = spec.get('flash_size', '0')
            if isinstance(flash_size, str):
                info += f"Flash: {flash_size} | "
            else:
                info += f"Flash: {flash_size // 1024}KB | "
            
            # Handle RAM size (could be string like "80KB" or number)
            ram_size = spec.get('ram_size', '0')
            if isinstance(ram_size, str):
                info += f"RAM: {ram_size}<br>"
            else:
                if ram_size >= 1024:
                    info += f"RAM: {ram_size // 1024}KB<br>"
                else:
                    info += f"RAM: {ram_size}B<br>"
            
            info += f"<i>Bootloader: {spec.get('bootloader_instructions', 'See docs')}</i>"
            
            self.chip_info_label.setText(info)
        else:
            self.chip_info_label.setText("Unknown chip")
    
    def refresh_ports(self):
        """Scan for serial ports"""
        self.log("Scanning for serial ports...")
        
        import platform
        ports = []
        
        try:
            # Try using serial.tools.list_ports (cross-platform)
            import serial.tools.list_ports
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
        except ImportError:
            # Fallback to manual detection
            if platform.system() == "Windows":
                # Windows COM ports
                for i in range(1, 21):
                    ports.append(f"COM{i}")
            else:
                # Unix-like systems
                import glob
                ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*') + glob.glob('/dev/cu.usb*')
        
        self.port_combo.clear()
        
        if ports:
            for port in sorted(ports):
                self.port_combo.addItem(port)
            self.log(f"Found {len(ports)} port(s): {', '.join(ports)}")
        else:
            self.log("No serial ports detected")
            self.log("Troubleshooting:")
            self.log("  1. Connect device via USB")
            self.log("  2. Install USB drivers (CH340, CP2102, or FTDI)")
            self.log("  3. Try different USB port or cable")
    
    def load_pattern(self, pattern: Pattern):
        """Set pattern to flash"""
        # Warn if pattern is locked (flash in progress)
        if hasattr(self, '_pattern_locked') and self._pattern_locked:
            self.log("⚠️ Warning: Pattern was modified/replaced during flash operation")
            self.log("⚠️ Flash will continue with original pattern")
        
        self.pattern = pattern
        self.log(f"Pattern loaded: {pattern.frame_count} frames, {pattern.led_count} LEDs")
        dim_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
        dim_conf = getattr(pattern.metadata, 'dimension_confidence', None)
        if dim_conf is not None:
            self.log(
                f"Layout: {pattern.metadata.width}×{pattern.metadata.height} "
                f"(source={dim_source}, confidence={dim_conf*100:.0f}%)"
            )
        else:
            self.log(
                f"Layout: {pattern.metadata.width}×{pattern.metadata.height} "
                f"(source={dim_source})"
            )
    
    def on_flash(self):
        """Flash button clicked - start build and upload"""
        # Validate
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "Please load a pattern first!")
            return
        
        chip_id = self.chip_combo.currentText()
        port = self.port_combo.currentText()
        
        if not port:
            QMessageBox.warning(self, "No Port", "Please select a serial port!")
            return
        
        gpio = self.gpio_spin.value()
        verify = self.verify_checkbox.isChecked()
        
        # CRITICAL: Use ORIGINAL file data, not the unwrapped preview data
        # Preview tab stores the original file pattern in _original_file_pattern
        import copy
        
        # Get original file pattern from preview tab
        main_window = self.window()
        original_pattern = None
        
        if hasattr(main_window, 'preview_tab') and main_window.preview_tab:
            if hasattr(main_window.preview_tab, '_original_file_pattern') and main_window.preview_tab._original_file_pattern:
                original_pattern = main_window.preview_tab._original_file_pattern
                self.log("📂 Using ORIGINAL file data (not unwrapped preview data)")
        
        # Fallback to preview pattern if original not available
        if original_pattern is None:
            original_pattern = self.pattern
            if original_pattern is None:
                QMessageBox.warning(self, "No Pattern", "Please load a pattern first!")
                return
            self.log("⚠️ Original file pattern not found, using current pattern")
        
        # Create working copy
        pattern_copy = Pattern(
            name=original_pattern.name,
            metadata=copy.deepcopy(original_pattern.metadata),  # Deep copy metadata only
            frames=original_pattern.frames  # Share frames (read-only during flash)
        )
        self.log("Created working copy with original file data")
        
        # Get wiring configuration from preview tab's simulator
        # Navigate to MainWindow: self -> tab widget -> main window
        main_window = self.window()
        if hasattr(main_window, 'preview_tab') and main_window.preview_tab:
            preview_tab = main_window.preview_tab
            if hasattr(preview_tab, 'simulator'):
                sim = preview_tab.simulator
                wiring_text = sim.wiring_combo.currentText()
                datain_text = sim.datain_combo.currentText()
                
                # Update TARGET wiring (not original file format)
                pattern_copy.metadata.wiring_mode = wiring_text
                pattern_copy.metadata.data_in_corner = {
                    'Left Top': 'LT',
                    'Left Bottom': 'LB',
                    'Right Top': 'RT',
                    'Right Bottom': 'RB'
                }.get(datain_text, 'LT')
                
                self.log(f"🔧 Target wiring from UI: {wiring_text}, Data-In: {datain_text}")
        
        # Get FPS setting from preview tab
        if hasattr(main_window, 'preview_tab') and main_window.preview_tab:
            preview_tab = main_window.preview_tab
            if hasattr(preview_tab, 'fps_controller'):
                target_fps = preview_tab.fps_controller.fps_spinbox.value()
                pattern_copy.metadata.target_fps = target_fps
                self.log(f"🔧 Target FPS from UI: {target_fps}")
            
            # Get brightness setting from preview tab
            if hasattr(preview_tab, 'advanced_brightness'):
                brightness_pct = preview_tab.advanced_brightness.brightness_slider.value()
                pattern_copy.metadata.brightness = brightness_pct / 100.0
                self.log(f"🔧 Brightness from UI: {brightness_pct}%")
        
        # Mark pattern as locked
        self._pattern_locked = True
        self._locked_pattern_id = id(self.pattern)
        
        # Disable UI during flash
        self.flash_button.setEnabled(False)
        self.chip_combo.setEnabled(False)
        self.port_combo.setEnabled(False)
        self.save_firmware_btn.setEnabled(False)
        self.view_firmware_btn.setEnabled(False)
        self.last_build_result = None
        
        self.log("="*60)
        self.log(f"FIRMWARE LAYER - FLASH PROCESS START")
        self.log("="*60)
        self.log(f"Target chip: {chip_id}")
        self.log(f"Target port: {port}")
        self.log(f"Data GPIO: {gpio}")
        self.log(f"Verify: {verify}")
        self.log(f"Pattern: {pattern_copy.frame_count} frames, {pattern_copy.led_count} LEDs")
        self.log(f"Matrix: {pattern_copy.metadata.width}×{pattern_copy.metadata.height}")
        self.log(f"Pattern name: {pattern_copy.name}")
        self.log(f"Color order: {pattern_copy.metadata.color_order}")
        self.log("⚠️ Pattern locked for flash operation")
        self.log("="*60)
        
        # Validate pattern data
        if pattern_copy.frames and len(pattern_copy.frames) > 0:
            first_frame = pattern_copy.frames[0]
            sample_pixels = first_frame.pixels[:12] if len(first_frame.pixels) >= 12 else first_frame.pixels
            self.log(f"✓ Pattern validation - first 12 pixels:")
            for i, px in enumerate(sample_pixels):
                self.log(f"    LED {i}: RGB{px}")
            
            # Check if all black (data corruption)
            all_black = all(p == (0, 0, 0) for p in first_frame.pixels)
            if all_black:
                self.log(f"")
                self.log(f"🚨 CRITICAL ERROR: Pattern has ALL BLACK PIXELS!")
                self.log(f"🚨 This indicates data corruption or zero brightness.")
                self.log(f"🚨 Cannot flash - pattern would produce blank output.")
                self.log(f"")
                self.log(f"Troubleshooting:")
                self.log(f"  1. Check brightness setting in Preview tab")
                self.log(f"  2. Reload the pattern file")
                self.log(f"  3. Verify preview shows colors (not all black)")
                self.log(f"")
                
                # Re-enable UI
                self.flash_button.setEnabled(True)
                self.chip_combo.setEnabled(True)
                self.port_combo.setEnabled(True)
                self._pattern_locked = False
                
                QMessageBox.critical(
                    self, 
                    "Invalid Pattern", 
                    "Pattern contains all black pixels!\n\n" +
                    "This may be caused by:\n" +
                    "• Zero brightness setting in Preview tab\n" +
                    "• Corrupted pattern data\n" +
                    "• Pattern loading error\n\n" +
                    "Please check brightness and reload the pattern."
                )
                return
        
        # Apply wiring mapper for hardware strip order (Layer 4)
        # Configuration comes from pattern metadata (set in Preview tab)
        try:
            width = pattern_copy.metadata.width
            height = pattern_copy.metadata.height
            
            # CONVERSION LOGIC: Convert from file format to target hardware format
            # Read file format from preview tab's simulator UI dropdowns
            
            # Get file format from preview tab simulator (or auto-detect)
            file_wiring_mode = 'Serpentine'  # Default
            file_data_in = 'LT'  # Default
            
            # Try to get from UI first
            if hasattr(main_window, 'preview_tab') and main_window.preview_tab:
                if hasattr(main_window.preview_tab, 'simulator'):
                    sim = main_window.preview_tab.simulator
                    if hasattr(sim, 'file_format_combo'):
                        user_format = sim.file_format_combo.currentText()
                        if user_format and user_format != "Auto-detect":
                            file_wiring_mode = user_format
                    if hasattr(sim, 'file_datain_combo'):
                        user_datain_text = sim.file_datain_combo.currentText()
                        if user_datain_text and user_datain_text != "Auto-detect":
                            file_data_in = {
                                'Left Top': 'LT',
                                'Left Bottom': 'LB',
                                'Right Top': 'RT',
                                'Right Bottom': 'RB'
                            }.get(user_datain_text, 'LT')
            
            # If still using defaults or "Auto-detect", try auto-detection
            if file_wiring_mode == 'Serpentine' and file_data_in == 'LT':
                # Check if we have original file pattern for auto-detection
                if hasattr(main_window, 'preview_tab') and main_window.preview_tab:
                    if hasattr(main_window.preview_tab, '_original_file_pattern'):
                        original = main_window.preview_tab._original_file_pattern
                        if original:
                            try:
                                from core.file_format_detector import detect_file_format
                                detected_wiring, detected_corner = detect_file_format(original)
                                file_wiring_mode = detected_wiring
                                file_data_in = detected_corner
                                self.log(f"🔍 Auto-detected file format: {file_wiring_mode} {file_data_in}")
                            except Exception as e:
                                self.log(f"⚠️  Auto-detection failed: {e}, using defaults")
            
            self.log(f"📂 File format from UI: {file_wiring_mode} {file_data_in}")
            self.log(f"📂 Will convert to target wiring if different")
            
            # Get target wiring from UI (already set in metadata from preview tab)
            target_wiring_mode = pattern_copy.metadata.wiring_mode
            target_data_in = pattern_copy.metadata.data_in_corner
            
            self.log(f"📄 File format: {file_wiring_mode} {file_data_in}")
            self.log(f"🎯 Target hardware: {target_wiring_mode} {target_data_in}")
            
            # Check if conversion is needed
            if file_wiring_mode != target_wiring_mode or file_data_in != target_data_in:
                self.log("🔄 Conversion needed - file format != target hardware")
                needs_conversion = True
            else:
                self.log("✓ File format matches target - using AS-IS")
                needs_conversion = False
            
            if needs_conversion and height > 1:
                self.log("")
                self.log("="*60)
                self.log("WIRING CONVERSION PIPELINE")
                self.log("="*60)
                self.log(f"Matrix: {width}×{height} ({width * height} LEDs)")
                self.log(f"Frames: {len(pattern_copy.frames)}")
                self.log(f"Step 1: File ({file_wiring_mode} {file_data_in}) → Design order")
                self.log(f"Step 2: Design order → Target ({target_wiring_mode} {target_data_in})")
                self.log(f"Flip X: {self.flip_x_checkbox.isChecked()}")
                self.log(f"Flip Y: {self.flip_y_checkbox.isChecked()}")
                self.log("="*60)
                self.log("")
                
                # STEP 1: Convert file's hardware order → design order
                from core.pattern_converter import hardware_to_design_order
                import hashlib
                
                # Log BEFORE Step 1
                self.log(f"🔄 STEP 1: Converting {file_wiring_mode} {file_data_in} → Design order")
                if len(pattern_copy.frames) > 0:
                    before_step1 = list(pattern_copy.frames[0].pixels)
                    before_checksum = hashlib.sha256(bytes([c for p in before_step1 for c in p])).hexdigest()[:16]
                    self.log(f"   Frame 0 BEFORE Step 1:")
                    for i in range(min(6, len(before_step1))):
                        self.log(f"     LED {i}: RGB{before_step1[i]}")
                    self.log(f"   Checksum BEFORE: {before_checksum}")
                
                pattern_copy = hardware_to_design_order(pattern_copy, file_wiring_mode, file_data_in)
                
                # Log AFTER Step 1
                if len(pattern_copy.frames) > 0:
                    after_step1 = list(pattern_copy.frames[0].pixels)
                    after_checksum = hashlib.sha256(bytes([c for p in after_step1 for c in p])).hexdigest()[:16]
                    self.log(f"   Frame 0 AFTER Step 1 (design order):")
                    for i in range(min(6, len(after_step1))):
                        self.log(f"     LED {i}: RGB{after_step1[i]}")
                    self.log(f"   Checksum AFTER: {after_checksum}")
                
                self.log(f"✓ Step 1 complete: Pattern now in design order")
                self.log("")
                
                # STEP 2: Convert design order → target hardware order
                # Get flip corrections from UI
                flip_x = self.flip_x_checkbox.isChecked()
                flip_y = self.flip_y_checkbox.isChecked()
                
                self.log(f"🔄 STEP 2: Converting Design order → {target_wiring_mode} {target_data_in}")
                if flip_x or flip_y:
                    self.log(f"   🔧 Flip corrections: Flip X={flip_x}, Flip Y={flip_y}")
                
                # Create mapper
                mapper = WiringMapper(width, height, target_wiring_mode, target_data_in, flip_x=flip_x, flip_y=flip_y)
                self.log(f"   Created WiringMapper for {target_wiring_mode} {target_data_in}")
                
                remapped_frames = []
                
                for frame_idx, frame in enumerate(pattern_copy.frames):
                    # Use fresh snapshot for each frame
                    design_pixels_snapshot = list(frame.pixels)
                    
                    # Log first frame BEFORE Step 2
                    if frame_idx == 0:
                        before_step2_checksum = hashlib.sha256(bytes([c for p in design_pixels_snapshot for c in p])).hexdigest()[:16]
                        self.log(f"   Frame 0 BEFORE Step 2 (design order):")
                        for i in range(min(6, len(design_pixels_snapshot))):
                            self.log(f"     LED {i}: RGB{design_pixels_snapshot[i]}")
                        self.log(f"   Checksum BEFORE Step 2: {before_step2_checksum}")
                    
                    # Convert to hardware order
                    hardware_pixels = mapper.design_to_hardware(design_pixels_snapshot)
                    
                    # Validation
                    if len(hardware_pixels) != width * height:
                        self.log(f"❌ ERROR: Frame {frame_idx} pixel count mismatch!")
                        self.log(f"   Expected: {width * height}, Got: {len(hardware_pixels)}")
                        raise ValueError(f"Pixel count mismatch in frame {frame_idx}")
                    
                    # Log first frame AFTER Step 2
                    if frame_idx == 0:
                        after_step2_checksum = hashlib.sha256(bytes([c for p in hardware_pixels for c in p])).hexdigest()[:16]
                        self.log(f"   Frame 0 AFTER Step 2 ({target_wiring_mode} {target_data_in}):")
                        for i in range(min(6, len(hardware_pixels))):
                            self.log(f"     LED {i}: RGB{hardware_pixels[i]}")
                        self.log(f"   Checksum AFTER Step 2: {after_step2_checksum}")
                    
                    remapped_frames.append(Frame(pixels=hardware_pixels, duration_ms=frame.duration_ms))
                
                pattern_copy.frames = remapped_frames
                self.log(f"✓ Step 2 complete: {len(remapped_frames)} frames converted to hardware order")
                self.log("")
                self.log("="*60)
                self.log(f"✅ CONVERSION COMPLETE")
                self.log("="*60)
                self.log(f"Pipeline: {file_wiring_mode} {file_data_in} → Design → {target_wiring_mode} {target_data_in}")
                self.log(f"Frames converted: {len(remapped_frames)}")
                self.log(f"Pixels per frame: {width * height}")
                self.log("="*60)
                self.log("")
                
            else:
                # No conversion needed or strip pattern
                if height > 1:
                    self.log(f"✓ File format matches target ({file_wiring_mode} {file_data_in})")
                    self.log(f"✓ Using file data AS-IS (no conversion)")
                else:
                    self.log(f"✓ Strip pattern - no wiring conversion needed")
            
        except Exception as e:
            self.log(f"Warning: wiring mapping failed ({e}); proceeding without remap")
        
        # Start flash thread with pattern copy
        self.flash_thread = FlashThread(pattern_copy, chip_id, port, gpio, verify)
        self.flash_thread.progress.connect(self.on_progress)
        self.flash_thread.finished.connect(self.on_flash_complete)
        self.flash_thread.log.connect(self.log)
        self.flash_thread.build_result_ready.connect(self.on_build_result_ready)
        self.flash_thread.start()
    
    def on_progress(self, status: str, progress: float, message: str):
        """Update progress during flash"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(int(progress * 100))
    
    def _dump_firmware_verification(self, pattern: Pattern, stage: str):
        """
        🔍 FIRMWARE VERIFICATION: Dump pixel order before firmware generation
        
        This shows exactly what pixel data will be written to the firmware,
        allowing comparison with preview and chip-side output.
        """
        if not pattern or not pattern.frames:
            return
        
        self.log("")
        self.log("="*60)
        self.log(f"🔍 FIRMWARE VERIFICATION DUMP - {stage}")
        self.log("="*60)
        
        # Pattern metadata
        width = pattern.metadata.width
        height = pattern.metadata.height
        wiring_mode = getattr(pattern.metadata, 'wiring_mode', 'Row-major')
        data_in_corner = getattr(pattern.metadata, 'data_in_corner', 'LT')
        already_unwrapped = getattr(pattern.metadata, 'already_unwrapped', False)
        
        self.log(f"Matrix: {width}×{height}")
        self.log(f"LEDs: {pattern.led_count}")
        self.log(f"Frames: {pattern.frame_count}")
        self.log(f"Wiring Mode: {wiring_mode}")
        self.log(f"Data-In Corner: {data_in_corner}")
        self.log(f"Already Unwrapped: {already_unwrapped}")
        self.log("")
        
        # First frame pixel data
        first_frame = pattern.frames[0]
        self.log("First Frame Pixel Data (as it will appear in firmware):")
        self.log("-" * 60)
        
        # For matrices, show first row visually
        if height > 1:
            self.log(f"First Row (LEDs 0-{width-1}):")
            row_pixels = first_frame.pixels[:width]
            for led_idx, pixel in enumerate(row_pixels):
                r, g, b = pixel
                self.log(f"  LED {led_idx:2d}: RGB({r:3d}, {g:3d}, {b:3d})")
            
            self.log("")
            self.log(f"Second Row (LEDs {width}-{width*2-1}):")
            row_pixels = first_frame.pixels[width:width*2]
            for led_idx, pixel in enumerate(row_pixels):
                r, g, b = pixel
                actual_idx = width + led_idx
                self.log(f"  LED {actual_idx:2d}: RGB({r:3d}, {g:3d}, {b:3d})")
        else:
            # Strip: show first 12 LEDs
            self.log("First 12 LEDs:")
            for led_idx in range(min(12, len(first_frame.pixels))):
                r, g, b = first_frame.pixels[led_idx]
                self.log(f"  LED {led_idx:2d}: RGB({r:3d}, {g:3d}, {b:3d})")
        
        self.log("")
        self.log("💡 TIP: Compare this with Serial Monitor output from the chip")
        self.log("   to verify pixel order matches hardware expectations!")
        self.log("="*60)
        self.log("")
    
    def on_flash_complete(self, success: bool, message: str):
        """Flash completed"""
        # Unlock pattern
        self._pattern_locked = False
        
        # Check if pattern was modified during flash
        if hasattr(self, '_locked_pattern_id') and self.pattern:
            if id(self.pattern) == self._locked_pattern_id:
                # Pattern wasn't replaced, but might have been modified
                # (We can't easily detect this without storing a hash)
                pass
        
        # Re-enable UI
        self.flash_button.setEnabled(True)
        self.chip_combo.setEnabled(True)
        self.port_combo.setEnabled(True)
        
        if success:
            self.log("="*60)
            self.log("✅ FLASH SUCCESSFUL!")
            self.log("="*60)
            self.progress_label.setText("✅ Flash successful!")
            self.progress_bar.setValue(100)
            
            QMessageBox.information(self, "Success", "Pattern uploaded successfully!\n\nYour LEDs should now display the pattern.")
        else:
            self.log("="*60)
            self.log(f"❌ FLASH FAILED: {message}")
            self.log("="*60)
            self.progress_label.setText(f"❌ Flash failed")
            self.progress_bar.setValue(0)
            
            QMessageBox.critical(self, "Flash Failed", f"Upload failed:\n\n{message}")
        
        self.flash_complete.emit(success, message)
    
    def on_build_result_ready(self, build_result):
        """Store build result and enable save/view buttons"""
        self.last_build_result = build_result
        self.save_firmware_btn.setEnabled(True)
        self.view_firmware_btn.setEnabled(True)
    
    def save_firmware(self):
        """Save firmware files to a custom location"""
        if not self.last_build_result:
            QMessageBox.warning(self, "No Firmware", "No firmware has been built yet. Please flash a pattern first.")
            return
        
        from pathlib import Path
        
        firmware_path = Path(self.last_build_result.firmware_path)
        build_dir = firmware_path.parent
        
        # Ask user where to save
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save Firmware",
            str(build_dir)
        )
        
        if not save_dir:
            return
        
        save_dir = Path(save_dir)
        
        try:
            # Copy firmware binary
            firmware_bin = build_dir / firmware_path.name
            if firmware_bin.exists():
                import shutil
                dest_bin = save_dir / firmware_bin.name
                shutil.copy2(firmware_bin, dest_bin)
                self.log(f"Saved firmware binary: {dest_bin}")
            
            # Copy source files (pattern_data.h and .ino)
            pattern_data_h = build_dir / "pattern_data.h"
            if pattern_data_h.exists():
                import shutil
                dest_h = save_dir / pattern_data_h.name
                shutil.copy2(pattern_data_h, dest_h)
                self.log(f"Saved pattern_data.h: {dest_h}")
            
            # Find .ino file
            ino_files = list(build_dir.glob("*.ino"))
            for ino_file in ino_files:
                import shutil
                dest_ino = save_dir / ino_file.name
                shutil.copy2(ino_file, dest_ino)
                self.log(f"Saved {ino_file.name}: {dest_ino}")
            
            QMessageBox.information(
                self,
                "Firmware Saved",
                f"Firmware files saved to:\n{save_dir}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save firmware:\n\n{str(e)}"
            )
    
    def view_firmware(self):
        """View firmware source files in a dialog"""
        if not self.last_build_result:
            QMessageBox.warning(self, "No Firmware", "No firmware has been built yet. Please flash a pattern first.")
            return
        
        from pathlib import Path
        
        firmware_path = Path(self.last_build_result.firmware_path)
        build_dir = firmware_path.parent
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Firmware Source Files")
        dialog.resize(900, 700)
        
        layout = QVBoxLayout(dialog)
        
        # Tab widget for multiple files
        tabs = QTabWidget()
        
        # Read and display pattern_data.h
        pattern_data_h = build_dir / "pattern_data.h"
        if pattern_data_h.exists():
            try:
                with open(pattern_data_h, 'r', encoding='utf-8') as f:
                    content = f.read()
                text_browser = QTextBrowser()
                text_browser.setPlainText(content)
                text_browser.setFont(QFont("Courier New", 9))
                tabs.addTab(text_browser, "pattern_data.h")
            except Exception as e:
                error_text = QTextBrowser()
                error_text.setPlainText(f"Error reading pattern_data.h:\n{str(e)}")
                tabs.addTab(error_text, "pattern_data.h (Error)")
        
        # Find and display .ino file
        ino_files = list(build_dir.glob("*.ino"))
        for ino_file in ino_files:
            try:
                with open(ino_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                text_browser = QTextBrowser()
                text_browser.setPlainText(content)
                text_browser.setFont(QFont("Courier New", 9))
                tabs.addTab(text_browser, ino_file.name)
            except Exception as e:
                error_text = QTextBrowser()
                error_text.setPlainText(f"Error reading {ino_file.name}:\n{str(e)}")
                tabs.addTab(error_text, f"{ino_file.name} (Error)")
        
        layout.addWidget(tabs)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        if tabs.count() == 0:
            QMessageBox.warning(self, "No Files", "No firmware source files found.")
            return
        
        dialog.exec()
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Auto-scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

