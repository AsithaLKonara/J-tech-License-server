"""
Enhanced LED Simulator Widget - Accurate pattern visualization
Shows exact pattern with correct matrix size and shape
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QSpinBox, QComboBox,
                               QGroupBox, QScrollArea, QFrame, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from core.pattern import Pattern, Frame
from core.matrix_detector import MatrixDetector, MatrixLayout


class EnhancedLEDSimulatorWidget(QWidget):
    """
    Enhanced LED simulator with accurate matrix visualization
    
    Features:
    - Exact matrix size and shape display
    - Real-time pattern playback
    - Frame-by-frame navigation
    - Zoom and pan controls
    - Color accuracy
    - Performance optimization for large patterns
    """
    
    # Signals
    frame_changed = Signal(int)  # Current frame index
    playback_state_changed = Signal(bool)  # Playing state
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.current_frame = 0
        self.is_playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.next_frame)
        
        # Display settings
        self.led_size = 8  # Size of each LED in pixels
        self.zoom_factor = 1.0
        self.show_grid = True
        self.show_numbers = False
        
        # Matrix detection
        self.matrix_detector = MatrixDetector()
        self.detected_layout: MatrixLayout = None
        
        # Flag to prevent resetting UI when pattern is updated (not freshly loaded)
        self._initial_load = True
        
        self.setup_ui()
        self.setup_timer()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Playback controls
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.play)
        controls_layout.addWidget(self.play_button)
        
        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.clicked.connect(self.pause)
        self.pause_button.setEnabled(False)
        controls_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)
        
        controls_layout.addStretch()
        
        # Frame controls
        controls_layout.addWidget(QLabel("Frame:"))
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(0, 0)
        self.frame_spin.valueChanged.connect(self.set_frame)
        controls_layout.addWidget(self.frame_spin)
        
        controls_layout.addWidget(QLabel("/ 0"))
        self.total_frames_label = QLabel("0")
        controls_layout.addWidget(self.total_frames_label)
        
        layout.addLayout(controls_layout)
        
        # Display settings
        settings_layout = QHBoxLayout()
        
        settings_layout.addWidget(QLabel("LED Size:"))
        self.led_size_spin = QSpinBox()
        self.led_size_spin.setRange(4, 32)
        self.led_size_spin.setValue(self.led_size)
        self.led_size_spin.valueChanged.connect(self.set_led_size)
        settings_layout.addWidget(self.led_size_spin)
        
        settings_layout.addWidget(QLabel("Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(25, 400)
        self.zoom_spin.setValue(100)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self.set_zoom)
        settings_layout.addWidget(self.zoom_spin)
        
        self.grid_checkbox = QComboBox()
        self.grid_checkbox.addItems(["No Grid", "Light Grid", "Dark Grid"])
        self.grid_checkbox.currentTextChanged.connect(self.set_grid_style)
        settings_layout.addWidget(QLabel("Grid:"))
        settings_layout.addWidget(self.grid_checkbox)
        
        self.numbers_checkbox = QComboBox()
        self.numbers_checkbox.addItems(["No Numbers", "Show Numbers"])
        self.numbers_checkbox.currentTextChanged.connect(self.set_show_numbers)
        settings_layout.addWidget(QLabel("Numbers:"))
        settings_layout.addWidget(self.numbers_checkbox)
        
        # Wiring mode (mapping from linear pixel order to matrix)
        settings_layout.addWidget(QLabel("Wiring:"))
        self.wiring_combo = QComboBox()
        self.wiring_combo.addItems(["Serpentine", "Row-major", "Column-major", "Column-serpentine"])  # default serpentine (common)
        self.wiring_combo.currentTextChanged.connect(self.set_wiring_mode)
        settings_layout.addWidget(self.wiring_combo)

        # Rotation and mirror controls removed - using layered architecture

        # Data-in corner (where index 0 enters)
        settings_layout.addWidget(QLabel("Data In:"))
        self.datain_combo = QComboBox()
        self.datain_combo.addItems(["Left Top", "Left Bottom", "Right Top", "Right Bottom"])
        settings_layout.addWidget(self.datain_combo)
        
        # File Format (what format the file is actually stored in)
        settings_layout.addWidget(QLabel("File Format:"))
        self.file_format_combo = QComboBox()
        self.file_format_combo.addItems(["Auto-detect", "Serpentine", "Row-major", "Column-major", "Column-serpentine"])
        self.file_format_combo.setCurrentText("Auto-detect")  # Default: Auto-detect
        self.file_format_combo.setToolTip("Format of the loaded file (for preview unwrapping)")
        self.file_format_combo.currentTextChanged.connect(self.on_file_format_changed)
        settings_layout.addWidget(self.file_format_combo)
        
        # File Data-In (where data enters in the file)
        settings_layout.addWidget(QLabel("File Data-In:"))
        self.file_datain_combo = QComboBox()
        self.file_datain_combo.addItems(["Auto-detect", "Left Top", "Left Bottom", "Right Top", "Right Bottom"])
        self.file_datain_combo.setCurrentText("Auto-detect")  # Default: Auto-detect
        self.file_datain_combo.setToolTip("Data-in corner of the loaded file (for preview unwrapping)")
        self.file_datain_combo.currentTextChanged.connect(self.on_file_datain_changed)
        settings_layout.addWidget(self.file_datain_combo)

        # Layout/Display mode
        settings_layout.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Matrix", "Circle", "Matrix + Circle"])
        self.layout_combo.currentTextChanged.connect(self.set_display_layout)
        settings_layout.addWidget(self.layout_combo)

        # Wiring visualization toggles
        self.path_checkbox = QCheckBox("Show Path")
        self.path_checkbox.setChecked(True)
        settings_layout.addWidget(self.path_checkbox)
        self.din_checkbox = QCheckBox("Show Data In")
        self.din_checkbox.setChecked(True)
        settings_layout.addWidget(self.din_checkbox)
        
        settings_layout.addStretch()
        
        layout.addLayout(settings_layout)
        
        # LED Display
        self.led_display = LEDDisplayWidget()
        self.led_display.frame_changed.connect(self.on_frame_changed)
        # Default wiring: serpentine
        self.led_display.set_wiring_mode("Serpentine")
        self.led_display.set_display_mode("Matrix")
        # Default Data In corner
        try:
            self.led_display.set_data_in_corner("LT")
        except Exception:
            pass
        self.led_display.setStyleSheet("""
            LEDDisplayWidget {
                background-color: #1a1a1a;
                border: 1px solid #555555;
            }
        """)
        # Now that display exists, connect toggles
        self.path_checkbox.toggled.connect(self.led_display.set_show_path)
        self.din_checkbox.toggled.connect(self.led_display.set_show_din)
        self.datain_combo.currentTextChanged.connect(self.on_datain_changed)
        layout.addWidget(self.led_display)
        
        # Pattern info
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("No pattern loaded")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
    
    def setup_timer(self):
        """Setup playback timer"""
        self.playback_timer.setSingleShot(False)
    
    def load_pattern(self, pattern: Pattern):
        """Load pattern for display"""
        self.pattern = pattern
        
        if not pattern:
            self.led_display.clear()
            self.info_label.setText("No pattern loaded")
            return
        
        # Prefer explicit metadata width/height when valid; fallback to detector
        try:
            if getattr(pattern, 'metadata', None) and getattr(pattern.metadata, 'is_matrix', False):
                if pattern.metadata.width * pattern.metadata.height == pattern.led_count:
                    from core.matrix_detector import MatrixLayout
                    self.detected_layout = MatrixLayout(
                        width=pattern.metadata.width,
                        height=pattern.metadata.height,
                        total_leds=pattern.led_count,
                        layout_type="matrix",
                        confidence=1.0,
                    )
                else:
                    # fallback to detection if inconsistent
                    self.detected_layout = self.matrix_detector.detect_layout(
                        pattern.led_count,
                        pattern.frames[0].pixels if pattern.frames else None
                    )
            else:
                self.detected_layout = self.matrix_detector.detect_layout(
                    pattern.led_count,
                    pattern.frames[0].pixels if pattern.frames else None
                )
        except Exception:
            self.detected_layout = self.matrix_detector.detect_layout(
                pattern.led_count,
                pattern.frames[0].pixels if pattern.frames else None
            )
        
        # Update frame controls
        self.frame_spin.setRange(0, max(0, pattern.frame_count - 1))
        self.total_frames_label.setText(str(pattern.frame_count))
        
        # Load into display with detected layout
        self.led_display.load_pattern(pattern, self.detected_layout)
        
        # Sync UI/display from metadata ONLY on initial load (not on preview updates)
        # This prevents overwriting user's UI selections when preview rebuilds
        if self._initial_load:
            try:
                meta = getattr(pattern, 'metadata', None)
                if meta:
                    # Wiring
                    if getattr(meta, 'wiring_mode', None):
                        self.led_display.set_wiring_mode(meta.wiring_mode)
                        idx = self.wiring_combo.findText(meta.wiring_mode)
                        if idx >= 0:
                            self.wiring_combo.setCurrentIndex(idx)
                    # Orientation (only if widget/methods exist)
                    if hasattr(self.led_display, 'set_orientation') and hasattr(self, 'orientation_combo'):
                        deg = int(getattr(meta, 'orientation_deg', 0))
                        text = {0:"0°",90:"90°",180:"180°",270:"270°"}.get(deg, "0°")
                        self.led_display.set_orientation(deg)
                        idx = self.orientation_combo.findText(text)
                        if idx >= 0:
                            self.orientation_combo.setCurrentIndex(idx)
                    # Mirror (only if widget/methods exist)
                    if hasattr(self.led_display, 'set_mirror') and hasattr(self, 'mirror_h_combo'):
                        mh = bool(getattr(meta, 'mirror_h', False))
                        mv = bool(getattr(meta, 'mirror_v', False))
                        self.led_display.set_mirror(mh, mv)
                        mirror_text = "No Mirror"
                        if mh and mv:
                            mirror_text = "Mirror HV"
                        elif mh:
                            mirror_text = "Mirror H"
                        elif mv:
                            mirror_text = "Mirror V"
                        idx = self.mirror_h_combo.findText(mirror_text)
                        if idx >= 0:
                            self.mirror_h_combo.setCurrentIndex(idx)
                    # Data In corner
                    corner = getattr(meta, 'data_in_corner', 'LT')
                    try:
                        self.led_display.set_data_in_corner(corner)
                    except Exception:
                        pass
                    corner_text = {
                        'LT': 'Left Top',
                        'LB': 'Left Bottom',
                        'RT': 'Right Top',
                        'RB': 'Right Bottom',
                    }.get(corner, 'Left Top')
                    idx = self.datain_combo.findText(corner_text)
                    if idx >= 0:
                        self.datain_combo.setCurrentIndex(idx)
            except Exception:
                pass
            finally:
                # After initial load, don't reset UI anymore
                self._initial_load = False
        else:
            # On subsequent loads (preview updates), just update the display without resetting UI
            pass
        
        # Update info
        self.update_info()
        
        # Reset to first frame
        self.set_frame(0)
    
    def play(self):
        """Start playback"""
        if not self.pattern or self.pattern.frame_count == 0:
            return
        
        self.is_playing = True
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        # Start timer with current frame duration
        if self.current_frame < len(self.pattern.frames):
            frame = self.pattern.frames[self.current_frame]
            self.playback_timer.start(max(20, frame.duration_ms))  # At least 20ms
        
        self.playback_state_changed.emit(True)
    
    def pause(self):
        """Pause playback"""
        self.is_playing = False
        self.playback_timer.stop()
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        self.playback_state_changed.emit(False)
    
    def stop(self):
        """Stop playback and reset to first frame"""
        self.is_playing = False
        self.playback_timer.stop()
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        self.set_frame(0)
        self.playback_state_changed.emit(False)
    
    def next_frame(self):
        """Advance to next frame"""
        if not self.pattern:
            return
        
        next_frame = (self.current_frame + 1) % self.pattern.frame_count
        self.set_frame(next_frame)
        
        # Continue playing if not at end
        if self.is_playing and next_frame != 0:
            if self.current_frame < len(self.pattern.frames):
                frame = self.pattern.frames[self.current_frame]
                self.playback_timer.start(max(20, frame.duration_ms))
        else:
            # End of pattern
            self.pause()
    
    def set_frame(self, frame_idx: int):
        """Set current frame"""
        if not self.pattern:
            return
        
        self.current_frame = max(0, min(frame_idx, self.pattern.frame_count - 1))
        
        # Update display
        self.led_display.set_frame(self.current_frame)
        
        # Update controls
        self.frame_spin.blockSignals(True)
        self.frame_spin.setValue(self.current_frame)
        self.frame_spin.blockSignals(False)
        
        self.frame_changed.emit(self.current_frame)
    
    def set_led_size(self, size: int):
        """Set LED size"""
        self.led_size = size
        self.led_display.set_led_size(size)
        self.update_info()
    
    def set_zoom(self, zoom_percent: int):
        """Set zoom level"""
        self.zoom_factor = zoom_percent / 100.0
        self.led_display.set_zoom(self.zoom_factor)
        self.update_info()
    
    def set_grid_style(self, style: str):
        """Set grid style"""
        if style == "No Grid":
            self.show_grid = False
        else:
            self.show_grid = True
            self.led_display.set_grid_style(style)
        
        self.led_display.set_show_grid(self.show_grid)
    
    def set_show_numbers(self, show: str):
        """Set show numbers"""
        self.show_numbers = show == "Show Numbers"
        self.led_display.set_show_numbers(self.show_numbers)

    def set_wiring_mode(self, mode: str):
        """Set wiring mode on the display widget"""
        self.led_display.set_wiring_mode(mode)
    
    # Orientation and mirror methods removed - using layered architecture

    def on_datain_changed(self, text: str):
        mapping = {
            "Left Top": "LT",
            "Left Bottom": "LB",
            "Right Top": "RT",
            "Right Bottom": "RB",
        }
        corner = mapping.get(text, "LT")
        try:
            self.led_display.set_data_in_corner(corner)
        except Exception:
            pass

    def set_display_layout(self, text: str):
        self.led_display.set_display_mode(text)
    
    def on_file_format_changed(self, format_text: str):
        """File format dropdown changed - trigger preview reload"""
        # Emit signal to preview tab to reload with new file format
        if hasattr(self, '_reload_callback') and self._reload_callback:
            self._reload_callback()
    
    def on_file_datain_changed(self, datain_text: str):
        """File data-in dropdown changed - trigger preview reload"""
        # Emit signal to preview tab to reload with new file format
        if hasattr(self, '_reload_callback') and self._reload_callback:
            self._reload_callback()
    
    def set_brightness(self, brightness: float):
        """Set brightness level (0.0-1.0)"""
        self.brightness = max(0.0, min(1.0, brightness))
        self.update_info()
    
    def on_frame_changed(self, frame_idx: int):
        """Handle frame change from display"""
        self.set_frame(frame_idx)
    
    def update_info(self):
        """Update pattern information"""
        if not self.pattern:
            self.info_label.setText("No pattern loaded")
            return
        
        info = f"<b>Pattern:</b> {self.pattern.name}<br>"
        info += f"<b>LEDs:</b> {self.pattern.led_count} "
        
        # Use detected layout if available
        if self.detected_layout:
            if self.detected_layout.layout_type == "matrix":
                info += f"({self.detected_layout.width}×{self.detected_layout.height} matrix)<br>"
            else:
                info += f"({self.detected_layout.layout_type})<br>"
            info += f"<b>Layout:</b> {self.detected_layout.layout_type} "
            info += f"(confidence: {self.detected_layout.confidence:.1%})<br>"
        elif self.pattern.metadata.is_matrix:
            info += f"({self.pattern.metadata.width}×{self.pattern.metadata.height} matrix)<br>"
        else:
            info += f"(strip)<br>"
        
        info += f"<b>Frames:</b> {self.pattern.frame_count}<br>"
        info += f"<b>Duration:</b> {self.pattern.duration_ms / 1000.0:.2f}s<br>"
        info += f"<b>FPS:</b> {self.pattern.average_fps:.1f}<br>"
        info += f"<b>Display:</b> {self.led_size}px LEDs, {int(self.zoom_factor * 100)}% zoom"
        
        self.info_label.setText(info)


class LEDDisplayWidget(QWidget):
    """
    LED display widget with accurate matrix visualization
    """
    
    # Signals
    frame_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.current_frame = 0
        self.led_size = 8
        self.zoom_factor = 1.0
        self.show_grid = True
        self.show_numbers = False
        self.grid_style = "Light Grid"
        self.detected_layout: MatrixLayout = None
        self.wiring_mode = "Serpentine"  # or "Row-major"
        # Removed: orientation_deg, mirror_h, mirror_v (using layered architecture)
        self.display_mode = "Matrix"  # "Matrix", "Circle", "Matrix + Circle"
        self.show_path = True
        self.show_din = True
        self.data_in_corner = "LT"
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
        # Enable mouse tracking for interaction
        self.setMouseTracking(True)
    
    def load_pattern(self, pattern: Pattern, detected_layout: MatrixLayout = None):
        """Load pattern for display"""
        self.pattern = pattern
        self.detected_layout = detected_layout
        self.current_frame = 0
        self.update()
    
    def set_frame(self, frame_idx: int):
        """Set current frame"""
        if not self.pattern:
            return
        
        self.current_frame = max(0, min(frame_idx, self.pattern.frame_count - 1))
        self.update()
    
    def set_led_size(self, size: int):
        """Set LED size"""
        self.led_size = size
        self.update()
    
    def set_zoom(self, zoom: float):
        """Set zoom factor"""
        self.zoom_factor = zoom
        self.update()
    
    def set_show_grid(self, show: bool):
        """Set show grid"""
        self.show_grid = show
        self.update()
    
    def set_grid_style(self, style: str):
        """Set grid style"""
        self.grid_style = style
        self.update()
    
    def set_show_numbers(self, show: bool):
        """Set show numbers"""
        self.show_numbers = show
        self.update()

    def set_wiring_mode(self, mode: str):
        """Set wiring mode ("Serpentine" or "Row-major")."""
        self.wiring_mode = mode or "Row-major"
        if self.pattern and getattr(self.pattern, 'metadata', None):
            self.pattern.metadata.wiring_mode = self.wiring_mode
        self.update()

    # Orientation and mirror methods removed - using layered architecture

    def set_display_mode(self, mode: str):
        self.display_mode = mode or "Matrix"
        self.update()

    def set_show_path(self, on: bool):
        self.show_path = bool(on)
        self.update()
    
    def set_show_din(self, on: bool):
        self.show_din = bool(on)
        self.update()
    
    def set_data_in_corner(self, corner: str):
        if corner in ("LT", "LB", "RT", "RB"):
            self.data_in_corner = corner
            # Save to pattern metadata for firmware generation
            if self.pattern and getattr(self.pattern, 'metadata', None):
                self.pattern.metadata.data_in_corner = self.data_in_corner
            self.update()
    
    def clear(self):
        """Clear display"""
        self.pattern = None
        self.current_frame = 0
        self.update()
    
    def paintEvent(self, event):
        """Paint LED display"""
        if not self.pattern or not self.pattern.frames:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill background with dark color
        painter.fillRect(self.rect(), QColor(26, 26, 26))  # Dark background
        
        # Get current frame
        if self.current_frame >= len(self.pattern.frames):
            return
        
        frame = self.pattern.frames[self.current_frame]
        
        # Calculate display dimensions using detected layout
        if self.detected_layout:
            width = self.detected_layout.width
            height = self.detected_layout.height
        else:
            width = self.pattern.metadata.width
            height = self.pattern.metadata.height
        
        # Calculate LED positions
        led_width = int(self.led_size * self.zoom_factor)
        led_height = int(self.led_size * self.zoom_factor)
        
        # Center the display
        total_width = width * led_width
        total_height = height * led_height
        
        start_x = (self.width() - total_width) // 2
        start_y = (self.height() - total_height) // 2
        
        # Draw LEDs according to the selected display mode
        if self.display_mode == "Circle":
            self._paint_circle(painter, frame)
            return
        elif self.display_mode == "Matrix + Circle":
            # Draw matrix on left half and circle on right half
            matrix_rect = self.rect().adjusted(0, 0, -self.width()//2, 0)
            circle_rect = self.rect().adjusted(self.width()//2, 0, 0, 0)
            self._paint_matrix(painter, frame, width, height, led_width, led_height, matrix_rect)
            self._paint_circle(painter, frame, circle_rect)
            return

        # Default: Matrix
        if self.detected_layout and self.detected_layout.suggested_arrangement:
            # Use detected arrangement
            for led_idx, (x, y) in enumerate(self.detected_layout.suggested_arrangement):
                if led_idx < len(frame.pixels):
                    r, g, b = frame.pixels[led_idx]
                    
                    # Calculate position
                    led_x = start_x + x * led_width
                    led_y = start_y + y * led_height
                    
                    # Draw LED
                    color = QColor(r, g, b)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawRect(led_x, led_y, led_width, led_height)
                    
                    # Draw grid if enabled
                    if self.show_grid:
                        grid_color = QColor(200, 200, 200) if self.grid_style == "Light Grid" else QColor(100, 100, 100)
                        painter.setPen(QPen(grid_color, 1))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRect(led_x, led_y, led_width, led_height)
                    
                    # Draw numbers if enabled
                    if self.show_numbers and led_width > 12:
                        painter.setPen(QPen(Qt.black, 1))
                        font = QFont()
                        font.setPointSize(max(6, led_width // 4))
                        painter.setFont(font)
                        painter.drawText(led_x + 2, led_y + led_height - 2, str(led_idx))
        else:
            self._paint_matrix(painter, frame, width, height, led_width, led_height, self.rect())
    
    def sizeHint(self):
        """Return preferred size"""
        if not self.pattern:
            return QSize(400, 300)
        
        width = self.pattern.metadata.width
        height = self.pattern.metadata.height
        
        led_width = int(self.led_size * self.zoom_factor)
        led_height = int(self.led_size * self.zoom_factor)
        
        return QSize(
            max(400, width * led_width + 40),
            max(300, height * led_height + 40)
        )

    # --- helper painters ---
    def _paint_matrix(self, painter: QPainter, frame: Frame, width: int, height: int, led_w: int, led_h: int, rect):
        """
        LAYERED ARCHITECTURE IMPLEMENTATION:
        Layer 1: Base Matrix - Draw grid with sequential numbering (0..N-1, left-to-right, top-to-bottom)
        Layer 2: Design - Display pattern pixels in sequential order (pixel[i] → cell i)
        Layer 3: Wiring - Visual overlay only (doesn't affect pixel data)
        """
        # Compute centering based on rect
        total_w = width * led_w
        total_h = height * led_h
        start_x = rect.x() + (rect.width() - total_w)//2
        start_y = rect.y() + (rect.height() - total_h)//2
        
        # LAYER 1 + 2: Draw base matrix with design pixels
        # Simple sequential mapping: cell index = y * width + x
        for y in range(height):
            for x in range(width):
                # Cell index is always sequential: 0, 1, 2, 3... (left-to-right, top-to-bottom)
                cell_idx = y * width + x
                
                # LAYER 2: Map pixel data 1:1 (pixel[i] → cell i)
                if cell_idx < len(frame.pixels):
                    r, g, b = frame.pixels[cell_idx]
                    led_x = start_x + x * led_w
                    led_y = start_y + y * led_h
                    color = QColor(r, g, b)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(Qt.black, 1))
                    painter.drawRect(led_x, led_y, led_w, led_h)
                    
                    # Draw grid if enabled
                    if self.show_grid:
                        grid_color = QColor(200, 200, 200) if self.grid_style == "Light Grid" else QColor(100, 100, 100)
                        painter.setPen(QPen(grid_color, 1))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRect(led_x, led_y, led_w, led_h)
                    
                    # LAYER 1: Show cell numbers if enabled
                    if self.show_numbers and led_w > 12:
                        painter.setPen(QPen(Qt.white, 1))
                        font = QFont()
                        font.setPointSize(max(6, led_w // 4))
                        painter.setFont(font)
                        # Draw with background for readability
                        text_rect = painter.boundingRect(led_x, led_y, led_w, led_h, Qt.AlignCenter, str(cell_idx))
                        painter.fillRect(text_rect, QColor(0, 0, 0, 180))
                        painter.drawText(led_x, led_y, led_w, led_h, Qt.AlignCenter, str(cell_idx))

        # Wiring path overlay
        if self.show_path:
            path = self._compute_display_path(width, height)
            if path:
                pen = QPen(QColor(255, 0, 0, 160), 2)
                painter.setPen(pen)
                # Draw polyline through centers
                last = None
                for (dx, dy) in path:
                    cx = start_x + dx * led_w + led_w // 2
                    cy = start_y + dy * led_h + led_h // 2
                    if last is not None:
                        painter.drawLine(last[0], last[1], cx, cy)
                    last = (cx, cy)
                # Data-in marker at first point
                if self.show_din and path:
                    sx, sy = path[0]
                    scx = start_x + sx * led_w + led_w // 2
                    scy = start_y + sy * led_h + led_h // 2
                    painter.setBrush(QBrush(QColor(0, 200, 0)))
                    painter.setPen(QPen(Qt.black, 1))
                    size = max(6, min(led_w, led_h) // 2)
                    painter.drawEllipse(scx - size//2, scy - size//2, size, size)
                    painter.setPen(QPen(QColor(0,200,0)))
                    painter.drawText(scx + size//2 + 3, scy, "DIN")

    def _paint_circle(self, painter: QPainter, frame: Frame, rect=None):
        rect = rect or self.rect()
        n = len(frame.pixels)
        if n == 0:
            return
        # Circle geometry
        cx = rect.x() + rect.width() // 2
        cy = rect.y() + rect.height() // 2
        r = int(min(rect.width(), rect.height()) * 0.4)
        size = max(4, int(self.led_size * self.zoom_factor * 0.8))
        for i in range(n):
            angle = 2 * 3.1415926535 * (i / n)
            x = cx + int(r * float(__import__('math').cos(angle)))
            y = cy + int(r * float(__import__('math').sin(angle)))
            r_, g_, b_ = frame.pixels[i]
            painter.setBrush(QBrush(QColor(r_, g_, b_)))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawEllipse(x - size//2, y - size//2, size, size)

    def _compute_display_path(self, w: int, h: int):
        """
        LAYER 3: Wiring visualization
        Compute the (x,y) traversal path showing how data flows through the physical matrix.
        This is visual only and doesn't affect the pixel data display.
        """
        # Step 1: Determine starting position based on data_in_corner
        if self.data_in_corner == "LB":
            start_x, start_y = 0, h - 1
        elif self.data_in_corner == "RT":
            start_x, start_y = w - 1, 0
        elif self.data_in_corner == "RB":
            start_x, start_y = w - 1, h - 1
        else:  # LT (default)
            start_x, start_y = 0, 0
        
        # Step 2: Build path according to wiring mode, starting from data_in_corner
        path = []
        wiring = getattr(self, 'wiring_mode', 'Row-major')
        
        if wiring == 'Serpentine':
            # Serpentine rows (zigzag left-right)
            if self.data_in_corner in ("LT", "RT"):
                # Start from top, go down
                for y in range(h):
                    if (y % 2 == 0 and start_x == 0) or (y % 2 == 1 and start_x == w - 1):
                        # Left to right
                        for x in range(w):
                            path.append((x, y))
                    else:
                        # Right to left
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
            else:  # LB or RB
                # Start from bottom, go up
                for y in range(h-1, -1, -1):
                    if ((h - 1 - y) % 2 == 0 and start_x == 0) or ((h - 1 - y) % 2 == 1 and start_x == w - 1):
                        # Left to right
                        for x in range(w):
                            path.append((x, y))
                    else:
                        # Right to left
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                            
        elif wiring == 'Row-major':
            # Simple row-major (always left-right or right-left)
            if self.data_in_corner in ("LT", "LB"):
                # Start from left
                if start_y == 0:  # Top
                    for y in range(h):
                        for x in range(w):
                            path.append((x, y))
                else:  # Bottom
                    for y in range(h-1, -1, -1):
                        for x in range(w):
                            path.append((x, y))
            else:  # RT or RB
                # Start from right
                if start_y == 0:  # Top
                    for y in range(h):
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                else:  # Bottom
                    for y in range(h-1, -1, -1):
                        for x in range(w-1, -1, -1):
                            path.append((x, y))
                            
        elif wiring == 'Column-major':
            # Simple column-major (always top-bottom or bottom-top)
            if self.data_in_corner in ("LT", "RT"):
                # Start from top
                if start_x == 0:  # Left
                    for x in range(w):
                        for y in range(h):
                            path.append((x, y))
                else:  # Right
                    for x in range(w-1, -1, -1):
                        for y in range(h):
                            path.append((x, y))
            else:  # LB or RB
                # Start from bottom
                if start_x == 0:  # Left
                    for x in range(w):
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
                else:  # Right
                    for x in range(w-1, -1, -1):
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
                            
        elif wiring == 'Column-serpentine':
            # Serpentine columns (zigzag up-down)
            if self.data_in_corner in ("LT", "LB"):
                # Start from left, go right
                for x in range(w):
                    if (x % 2 == 0 and start_y == 0) or (x % 2 == 1 and start_y == h - 1):
                        # Top to bottom
                        for y in range(h):
                            path.append((x, y))
                    else:
                        # Bottom to top
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
            else:  # RT or RB
                # Start from right, go left
                for x in range(w-1, -1, -1):
                    if ((w - 1 - x) % 2 == 0 and start_y == 0) or ((w - 1 - x) % 2 == 1 and start_y == h - 1):
                        # Top to bottom
                        for y in range(h):
                            path.append((x, y))
                    else:
                        # Bottom to top
                        for y in range(h-1, -1, -1):
                            path.append((x, y))
        else:
            # Fallback: simple row-major from top-left
            for y in range(h):
                for x in range(w):
                    path.append((x, y))
        
        return path
