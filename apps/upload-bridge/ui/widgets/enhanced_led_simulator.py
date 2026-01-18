"""
Enhanced LED Simulator Widget - Accurate pattern visualization
Shows exact pattern with correct matrix size and shape
"""

from typing import Dict
from math import cos, sin, pi
import math

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QSpinBox, QComboBox,
                               QGroupBox, QScrollArea, QFrame, QCheckBox)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern, Frame, PatternMetadata
from core.matrix_detector import MatrixDetector, MatrixLayout
from core.mapping.circular_mapper import CircularMapper


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
        self.apply_theme({}, {})
    
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
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(8)

        top_settings_row = QHBoxLayout()
        top_settings_row.setSpacing(12)
        top_settings_row.addWidget(QLabel("LED Size:"))
        self.led_size_spin = QSpinBox()
        self.led_size_spin.setRange(4, 32)
        self.led_size_spin.setValue(self.led_size)
        self.led_size_spin.valueChanged.connect(self.set_led_size)
        top_settings_row.addWidget(self.led_size_spin)

        top_settings_row.addWidget(QLabel("Zoom:"))
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(25, 400)
        self.zoom_spin.setValue(100)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self.set_zoom)
        top_settings_row.addWidget(self.zoom_spin)

        self.grid_checkbox = QComboBox()
        self.grid_checkbox.addItems(["No Grid", "Light Grid", "Dark Grid"])
        self.grid_checkbox.currentTextChanged.connect(self.set_grid_style)
        top_settings_row.addWidget(QLabel("Grid:"))
        top_settings_row.addWidget(self.grid_checkbox)

        self.numbers_checkbox = QComboBox()
        self.numbers_checkbox.addItems(["No Numbers", "Show Numbers"])
        self.numbers_checkbox.currentTextChanged.connect(self.set_show_numbers)
        top_settings_row.addWidget(QLabel("Numbers:"))
        top_settings_row.addWidget(self.numbers_checkbox)

        top_settings_row.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Matrix", "Circle", "Ring", "Radial", "Matrix + Circle"])
        self.layout_combo.currentTextChanged.connect(self.set_display_layout)
        top_settings_row.addWidget(self.layout_combo)

        top_settings_row.addStretch()
        settings_layout.addLayout(top_settings_row)

        bottom_settings_row = QHBoxLayout()
        bottom_settings_row.setSpacing(12)

        # Wiring mode (mapping from linear pixel order to matrix)
        bottom_settings_row.addWidget(QLabel("Wiring:"))
        self.wiring_combo = QComboBox()
        self.wiring_combo.addItems(["Serpentine", "Row-major", "Column-major", "Column-serpentine"])  # default serpentine (common)
        self.wiring_combo.currentTextChanged.connect(self.set_wiring_mode)
        bottom_settings_row.addWidget(self.wiring_combo)

        # Rotation and mirror controls removed - using layered architecture

        # Data-in corner (where index 0 enters)
        bottom_settings_row.addWidget(QLabel("Data In:"))
        self.datain_combo = QComboBox()
        self.datain_combo.addItems(["Left Top", "Left Bottom", "Right Top", "Right Bottom"])
        bottom_settings_row.addWidget(self.datain_combo)

        # File Format (what format the file is actually stored in)
        bottom_settings_row.addWidget(QLabel("File Format:"))
        self.file_format_combo = QComboBox()
        self.file_format_combo.addItems(["Auto-detect", "Serpentine", "Row-major", "Column-major", "Column-serpentine"])
        self.file_format_combo.setCurrentText("Auto-detect")  # Default: Auto-detect
        self.file_format_combo.setToolTip("Format of the loaded file (for preview unwrapping)")
        self.file_format_combo.currentTextChanged.connect(self.on_file_format_changed)
        bottom_settings_row.addWidget(self.file_format_combo)

        # File Data-In (where data enters in the file)
        bottom_settings_row.addWidget(QLabel("File Data-In:"))
        self.file_datain_combo = QComboBox()
        self.file_datain_combo.addItems(["Auto-detect", "Left Top", "Left Bottom", "Right Top", "Right Bottom"])
        self.file_datain_combo.setCurrentText("Auto-detect")  # Default: Auto-detect
        self.file_datain_combo.setToolTip("Data-in corner of the loaded file (for preview unwrapping)")
        self.file_datain_combo.currentTextChanged.connect(self.on_file_datain_changed)
        bottom_settings_row.addWidget(self.file_datain_combo)

        # Wiring visualization toggles
        self.path_checkbox = QCheckBox("Show Path")
        self.path_checkbox.setChecked(True)
        bottom_settings_row.addWidget(self.path_checkbox)
        self.din_checkbox = QCheckBox("Show Data In")
        self.din_checkbox.setChecked(True)
        bottom_settings_row.addWidget(self.din_checkbox)

        bottom_settings_row.addStretch()
        settings_layout.addLayout(bottom_settings_row)

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
        # Now that display exists, connect toggles
        self.path_checkbox.toggled.connect(self.led_display.set_show_path)
        self.din_checkbox.toggled.connect(self.led_display.set_show_din)
        self.datain_combo.currentTextChanged.connect(self.on_datain_changed)
        layout.addWidget(self.led_display)
        
        # Pattern info
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("No pattern loaded")
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
    
    def setup_timer(self):
        """Setup playback timer"""
        self.playback_timer.setSingleShot(False)
    
    def load_pattern(self, pattern: Pattern, layer_manager=None):
        """Load pattern for display
        
        Args:
            pattern: Pattern to display
            layer_manager: Optional LayerManager for animations
        """
        self.pattern = pattern
        self.layer_manager = layer_manager
        
        if not pattern:
            self.led_display.clear()
            self.info_label.setText("No pattern loaded")
            return
        
        # Prefer explicit metadata width/height when valid; fallback to detector
        # Add confidence checks for metadata validation
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            metadata = getattr(pattern, 'metadata', None)
            if metadata:
                dimension_source = getattr(metadata, 'dimension_source', 'unknown')
                dimension_confidence = getattr(metadata, 'dimension_confidence', 0.0)
                
                # Check if metadata dimensions are consistent and trustworthy
                width_height_match = metadata.width * metadata.height == pattern.led_count
                is_matrix = getattr(metadata, 'is_matrix', False)
                
                # Check for user override
                dimension_override = getattr(metadata, 'dimension_override', False)
                
                # Trust metadata if:
                # 1. User override (always trust) OR
                # 2. Dimensions match LED count AND (From header OR confidence >= 0.5)
                should_trust_metadata = (
                    dimension_override or
                    (width_height_match and
                     (dimension_source == 'header' or dimension_confidence >= 0.5))
                )
                
                if should_trust_metadata and is_matrix:
                    from core.matrix_detector import MatrixLayout
                    # Use metadata dimensions
                    confidence_value = 1.0 if dimension_source == 'header' else dimension_confidence
                    self.detected_layout = MatrixLayout(
                        width=metadata.width,
                        height=metadata.height,
                        total_leds=pattern.led_count,
                        layout_type="matrix",
                        confidence=confidence_value,
                    )
                    if dimension_source != 'header' and dimension_confidence < 0.7:
                        logger.warning(
                            f"Using metadata with medium confidence ({dimension_confidence:.0%}) "
                            f"from {dimension_source}. Dimensions: {metadata.width}×{metadata.height}"
                        )
                else:
                    # Metadata not trustworthy - re-detect
                    if not width_height_match:
                        logger.warning(
                            f"Metadata dimensions inconsistent: {metadata.width}×{metadata.height} "
                            f"≠ {pattern.led_count} LEDs. Re-detecting..."
                        )
                    elif dimension_source != 'header' and dimension_confidence < 0.5:
                        logger.warning(
                            f"Low confidence metadata ({dimension_confidence:.0%}) from {dimension_source}. "
                            "Re-detecting dimensions..."
                        )
                    
                    # Fallback to detection
                    self.detected_layout = self.matrix_detector.detect_layout(
                        pattern.led_count,
                        pattern.frames[0].pixels if pattern.frames else None
                    )
                    
                    # Log detected vs metadata if different
                    if metadata and self.detected_layout:
                        if (self.detected_layout.width != metadata.width or 
                            self.detected_layout.height != metadata.height):
                            logger.info(
                                f"Re-detected dimensions: {self.detected_layout.width}×{self.detected_layout.height} "
                                f"(was {metadata.width}×{metadata.height} in metadata)"
                            )
            else:
                # No metadata - use detector
                self.detected_layout = self.matrix_detector.detect_layout(
                    pattern.led_count,
                    pattern.frames[0].pixels if pattern.frames else None
                )
        except Exception as e:
            logger.error(f"Error in metadata validation, falling back to detector: {e}")
            self.detected_layout = self.matrix_detector.detect_layout(
                pattern.led_count,
                pattern.frames[0].pixels if pattern.frames else None
            )
        
        # Update frame controls
        self.frame_spin.setRange(0, max(0, pattern.frame_count - 1))
        self.total_frames_label.setText(str(pattern.frame_count))
        
        # Load into display with detected layout
        self.led_display.load_pattern(pattern, self.detected_layout, layer_manager=layer_manager)
        
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
    
    def stop(self, lazy_loader=None):
        """Stop playback and reset to first frame"""
        self.is_playing = False
        self.playback_timer.stop()
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        self.set_frame(0, lazy_loader=lazy_loader)
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

    def apply_theme(self, ui_palette: Dict[str, str], simulator_palette: Dict[str, str]) -> None:
        """
        Apply theme colours to the simulator chrome and LED canvas.
        """

        def pick(mapping: Dict[str, str], key: str, fallback: str) -> str:
            return mapping.get(key, fallback)

        background = pick(ui_palette, "surface", "#1E1E1E")
        surface_alt = pick(ui_palette, "surface_alt", background)
        text_primary = pick(ui_palette, "text_primary", "#F5F5F5")
        text_secondary = pick(ui_palette, "text_secondary", "#B5B5B5")
        control_bg = pick(ui_palette, "control_bg", "#2A2A2A")
        border = pick(ui_palette, "border", "#2E2E2E")
        accent = pick(ui_palette, "accent", "#4C8BF5")
        accent_hover = pick(ui_palette, "accent_hover", "#5B99FF")
        disabled_bg = pick(ui_palette, "control_disabled_bg", "#1A1A1A")
        disabled_text = pick(ui_palette, "control_disabled_text", "#666666")
        text_on_accent = pick(ui_palette, "text_on_accent", "#FFFFFF")

        self.setStyleSheet(
            f"""
            EnhancedLEDSimulatorWidget {{
                background-color: {background};
                color: {text_primary};
            }}
            EnhancedLEDSimulatorWidget QLabel {{
                color: {text_secondary};
            }}
            EnhancedLEDSimulatorWidget QLabel#infoLabel {{
                color: {text_primary};
            }}
            EnhancedLEDSimulatorWidget QPushButton {{
                background-color: {control_bg};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px 8px;
                color: {text_primary};
            }}
            EnhancedLEDSimulatorWidget QPushButton:hover {{
                background-color: {accent_hover};
                border-color: {accent_hover};
                color: {text_on_accent};
            }}
            EnhancedLEDSimulatorWidget QPushButton:pressed {{
                background-color: {accent};
                border-color: {accent};
                color: {text_on_accent};
            }}
            EnhancedLEDSimulatorWidget QPushButton:disabled {{
                background-color: {disabled_bg};
                color: {disabled_text};
                border-color: {border};
            }}
            EnhancedLEDSimulatorWidget QComboBox,
            EnhancedLEDSimulatorWidget QSpinBox,
            EnhancedLEDSimulatorWidget QSlider {{
                background-color: {control_bg};
                color: {text_primary};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            EnhancedLEDSimulatorWidget QComboBox QAbstractItemView {{
                background-color: {surface_alt};
                color: {text_primary};
                border: 1px solid {border};
            }}
            EnhancedLEDSimulatorWidget QGroupBox {{
                border: 1px solid {border};
            }}
            """
        )

        # Update the LED canvas palette
        self.led_display.apply_palette(simulator_palette)
        canvas_bg = pick(simulator_palette, "background", "#1A1A1A")
        canvas_border = pick(simulator_palette, "border", "#555555")
        self.led_display.setStyleSheet(
            f"""
            LEDDisplayWidget {{
                background-color: {canvas_bg};
                border: 1px solid {canvas_border};
            }}
            """
        )


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
        self._background_color = QColor("#1a1a1a")
        self._cell_border_color = QColor("#000000")
        self._grid_light_color = QColor("#c8c8c8")
        self._grid_dark_color = QColor("#646464")
        self._number_color = QColor("#111111")
        
        # Set minimum size
        self.setMinimumSize(400, 300)
        
        # Enable mouse tracking for interaction
        self.setMouseTracking(True)
    
    def load_pattern(self, pattern: Pattern, detected_layout: MatrixLayout = None, layer_manager=None):
        """Load pattern for display
        
        Args:
            pattern: Pattern to display
            detected_layout: Detected matrix layout
            layer_manager: Optional LayerManager for animations
        """
        self.pattern = pattern
        self.detected_layout = detected_layout
        self.layer_manager = layer_manager
        self.current_frame = 0
        self.update()
    
    def set_frame(self, frame_idx: int, lazy_loader=None):
        """Set current frame with optional lazy loading support"""
        if not self.pattern:
            return
        
        self.current_frame = max(0, min(frame_idx, self.pattern.frame_count - 1))
        
        # If lazy loader is provided, use it to load frame on-demand
        if lazy_loader and hasattr(self, 'pattern'):
            frame = lazy_loader.load_frame(self.current_frame)
            if frame:
                # Temporarily replace frame in pattern for rendering
                if self.current_frame < len(self.pattern.frames):
                    original_frame = self.pattern.frames[self.current_frame]
                    self.pattern.frames[self.current_frame] = frame
        
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

    def _current_dimensions(self) -> tuple[int, int]:
        """Return (width, height) for the active pattern."""
        if self.detected_layout:
            return max(0, self.detected_layout.width), max(0, self.detected_layout.height)
        if self.pattern and getattr(self.pattern, "metadata", None):
            return max(0, self.pattern.metadata.width), max(0, self.pattern.metadata.height)
        return 0, 0
    
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
        
        # Fill background with theme-aware color
        painter.fillRect(self.rect(), self._background_color)
        
        # Get current frame
        if self.current_frame >= len(self.pattern.frames):
            return
        
        frame = self.pattern.frames[self.current_frame]
        
        # Get composite pixels with animations if layer_manager is available
        pixels_to_use = None
        if self.layer_manager:
            try:
                composite = self.layer_manager.get_composite_pixels(self.current_frame)
                if composite and len(composite) == len(frame.pixels):
                    pixels_to_use = composite
            except Exception:
                # Fallback to frame.pixels if composite fails
                pass
        
        # Use composite pixels if available, otherwise use frame.pixels
        if pixels_to_use is None:
            pixels_to_use = frame.pixels
        
        width, height = self._current_dimensions()
        if width == 0 or height == 0:
            return
        
        # Calculate LED positions
        led_width = int(self.led_size * self.zoom_factor)
        led_height = int(self.led_size * self.zoom_factor)
        
        # Center the display
        total_width = width * led_width
        total_height = height * led_height
        
        start_x = (self.width() - total_width) // 2
        start_y = (self.height() - total_height) // 2
        
        # Check pattern metadata for circular layout
        # This follows the "lens, not new world" principle - same pattern data,
        # different interpretation based on layout_type
        layout_type = None
        if self.pattern and hasattr(self.pattern, 'metadata'):
            layout_type = getattr(self.pattern.metadata, 'layout_type', 'rectangular')
        
        # FIX: Allow user to force Matrix view (Rectangular) via dropdown
        # This overrides metadata layout (e.g. if auto-detected as circle but user wants grid check)
        if self.display_mode == "Matrix":
            layout_type = "rectangular"
        
        # Use circular rendering if pattern has circular layout
        # The preview uses the mapping table to get pixel colors from grid
        if layout_type and layout_type != "rectangular":
            if layout_type == "irregular":
                # Irregular shapes use matrix rendering but skip inactive cells
                self._paint_matrix(painter, frame, width, height, led_width, led_height, 
                                  self.rect(), metadata=self.pattern.metadata)
                return
            else:
                # Circular layouts use circular rendering
                self._paint_circular_layout(painter, frame, self.pattern.metadata, self.rect())
                return
        
        # Draw LEDs according to the selected display mode (for manual preview)
        if self.display_mode == "Circle":
            self._paint_circle(painter, frame, width, height, self.rect())
            return
        elif self.display_mode == "Ring":
            self._paint_ring(painter, frame, width, height, self.rect())
            return
        elif self.display_mode == "Radial":
            self._paint_radial(painter, frame, width, height, self.rect())
            return
        elif self.display_mode == "Matrix + Circle":
            # Draw matrix on left half and circle on right half
            matrix_rect = self.rect().adjusted(0, 0, -self.width()//2, 0)
            circle_rect = self.rect().adjusted(self.width()//2, 0, 0, 0)
            metadata = self.pattern.metadata if self.pattern and hasattr(self.pattern, 'metadata') else None
            self._paint_matrix(painter, frame, width, height, led_width, led_height, matrix_rect, metadata=metadata)
            self._paint_circle(painter, frame, width, height, circle_rect)
            return

        # Default: Matrix
        if self.detected_layout and self.detected_layout.suggested_arrangement:
            # Use detected arrangement
            for led_idx, (x, y) in enumerate(self.detected_layout.suggested_arrangement):
                if led_idx < len(pixels_to_use):
                    r, g, b = pixels_to_use[led_idx]
                    
                    # Calculate position
                    led_x = start_x + x * led_width
                    led_y = start_y + y * led_height
                    
                    # Draw LED
                    color = QColor(r, g, b)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(self._cell_border_color, 1))
                    painter.drawRect(led_x, led_y, led_width, led_height)
                    
                    # Draw grid if enabled
                    if self.show_grid:
                        grid_color = self._grid_light_color if self.grid_style == "Light Grid" else self._grid_dark_color
                        painter.setPen(QPen(grid_color, 1))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRect(led_x, led_y, led_width, led_height)
                    
                    # Draw numbers if enabled
                    if self.show_numbers and led_width > 12:
                        painter.setPen(QPen(self._number_color, 1))
                        font = QFont()
                        font.setPointSize(max(6, led_width // 4))
                        painter.setFont(font)
                        painter.drawText(led_x + 2, led_y + led_height - 2, str(led_idx))
        else:
            metadata = self.pattern.metadata if self.pattern and hasattr(self.pattern, 'metadata') else None
            # Get composite pixels for matrix painting
            pixels_to_use = frame.pixels
            if self.layer_manager:
                try:
                    composite = self.layer_manager.get_composite_pixels(self.current_frame)
                    if composite and len(composite) == len(frame.pixels):
                        pixels_to_use = composite
                except Exception:
                    pass
            # Create a temporary frame with composite pixels for matrix painting
            temp_frame = Frame(pixels=list(pixels_to_use), duration_ms=frame.duration_ms)
            self._paint_matrix(painter, temp_frame, width, height, led_width, led_height, self.rect(), metadata=metadata)
    
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
    def _paint_matrix(self, painter: QPainter, frame: Frame, width: int, height: int, led_w: int, led_h: int, rect, metadata=None):
        """
        LAYERED ARCHITECTURE IMPLEMENTATION:
        Layer 1: Base Matrix - Draw grid with sequential numbering (0..N-1, left-to-right, top-to-bottom)
        Layer 2: Design - Display pattern pixels in sequential order (pixel[i] → cell i)
        Layer 3: Wiring - Visual overlay only (doesn't affect pixel data)
        
        Args:
            metadata: Optional PatternMetadata for irregular shape support
        """
        # Get composite pixels with animations if layer_manager is available
        pixels_to_use = frame.pixels
        if self.layer_manager:
            try:
                composite = self.layer_manager.get_composite_pixels(self.current_frame)
                if composite and len(composite) == len(frame.pixels):
                    pixels_to_use = composite
            except Exception:
                pass
        
        # Compute centering based on rect
        total_w = width * led_w
        total_h = height * led_h
        start_x = rect.x() + (rect.width() - total_w)//2
        start_y = rect.y() + (rect.height() - total_h)//2
        
        # Check if irregular shape layout is enabled
        is_irregular = (metadata and 
                       getattr(metadata, 'irregular_shape_enabled', False) and
                       getattr(metadata, 'layout_type', 'rectangular') == 'irregular')
        
        # LAYER 1 + 2: Draw base matrix with design pixels
        # Simple sequential mapping: cell index = y * width + x
        for y in range(height):
            for x in range(width):
                # Skip inactive cells for irregular shapes - don't draw them at all
                if is_irregular:
                    from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                    if not IrregularShapeMapper.is_cell_active(x, y, metadata):
                        continue  # Skip inactive cells - make them transparent
                
                # Cell index is always sequential: 0, 1, 2, 3... (left-to-right, top-to-bottom)
                cell_idx = y * width + x
                
                # LAYER 2: Map pixel data 1:1 (pixel[i] → cell i)
                if cell_idx < len(pixels_to_use):
                    r, g, b = pixels_to_use[cell_idx]
                    led_x = start_x + x * led_w
                    led_y = start_y + y * led_h
                    color = QColor(r, g, b)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(self._cell_border_color, 1))
                    painter.drawRect(led_x, led_y, led_w, led_h)
                    
                    # Draw grid if enabled
                    if self.show_grid:
                        grid_color = self._grid_light_color if self.grid_style == "Light Grid" else self._grid_dark_color
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
                
                # Safety check: Skip inactive cells for irregular shapes
                is_irregular = (metadata and 
                               getattr(metadata, 'irregular_shape_enabled', False) and
                               getattr(metadata, 'layout_type', 'rectangular') == 'irregular')
                
                # Draw polyline through centers
                last = None
                for (dx, dy) in path:
                    # Additional safety check: verify cell is active if irregular
                    if is_irregular:
                        from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                        if not IrregularShapeMapper.is_cell_active(dx, dy, metadata):
                            continue  # Skip inactive cells
                    
                    cx = start_x + dx * led_w + led_w // 2
                    cy = start_y + dy * led_h + led_h // 2
                    if last is not None:
                        painter.drawLine(last[0], last[1], cx, cy)
                    last = (cx, cy)
                
                # Data-in marker at first active cell (only if path has active cells)
                if self.show_din and path:
                    # Find first active cell for DIN marker
                    din_x, din_y = None, None
                    for (dx, dy) in path:
                        if not is_irregular:
                            din_x, din_y = dx, dy
                            break
                        else:
                            from core.mapping.irregular_shape_mapper import IrregularShapeMapper
                            if IrregularShapeMapper.is_cell_active(dx, dy, metadata):
                                din_x, din_y = dx, dy
                                break
                    
                    if din_x is not None and din_y is not None:
                        scx = start_x + din_x * led_w + led_w // 2
                        scy = start_y + din_y * led_h + led_h // 2
                        painter.setBrush(QBrush(QColor(0, 200, 0)))
                        painter.setPen(QPen(self._cell_border_color, 1))
                        size = max(6, min(led_w, led_h) // 2)
                        painter.drawEllipse(scx - size//2, scy - size//2, size, size)
                        painter.setPen(QPen(QColor(0,200,0)))
                        painter.drawText(scx + size//2 + 3, scy, "DIN")

    def _paint_circle(self, painter: QPainter, frame: Frame, width: int, height: int, rect=None, *, inner_ratio: float = 0.0):
        """Render the pattern as concentric rings to approximate circular matrices."""
        # Get composite pixels with animations if layer_manager is available
        pixels_to_use = frame.pixels
        if self.layer_manager:
            try:
                composite = self.layer_manager.get_composite_pixels(self.current_frame)
                if composite and len(composite) == len(frame.pixels):
                    pixels_to_use = composite
            except Exception:
                pass
        
        rect = rect or self.rect()
        outer_radius = min(rect.width(), rect.height()) / 2 - 16
        if outer_radius <= 0:
            return
        inner_radius = max(0.0, outer_radius * inner_ratio)
        radius_steps = max(1, height - 1)
        radius_delta = (outer_radius - inner_radius) / radius_steps if radius_steps else 0
        pixel_size = max(4, int(self.led_size * self.zoom_factor * 0.8))
        center_x = rect.x() + rect.width() / 2
        center_y = rect.y() + rect.height() / 2

        for row in range(height):
            radius = inner_radius + radius_delta * row
            for col in range(width):
                idx = row * width + col
                if idx >= len(pixels_to_use):
                    continue
                angle = -pi / 2 + (2 * pi) * (col / max(1, width))
                x = center_x + radius * cos(angle)
                y = center_y + radius * sin(angle)
                r_val, g_val, b_val = pixels_to_use[idx]
                painter.setBrush(QBrush(QColor(r_val, g_val, b_val)))
                painter.setPen(QPen(self._cell_border_color, 1))
                painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)

    def _paint_ring(self, painter: QPainter, frame: Frame, width: int, height: int, rect=None):
        """Draw hollow ring preview (useful for circular LED strips)."""
        self._paint_circle(painter, frame, width, height, rect, inner_ratio=0.55)

    def _paint_radial(self, painter: QPainter, frame: Frame, width: int, height: int, rect=None):
        """Render semi-circular previews for arc / fan layouts."""
        # Get composite pixels with animations if layer_manager is available
        pixels_to_use = frame.pixels
        if self.layer_manager:
            try:
                composite = self.layer_manager.get_composite_pixels(self.current_frame)
                if composite and len(composite) == len(frame.pixels):
                    pixels_to_use = composite
            except Exception:
                pass
        
        rect = rect or self.rect()
        outer_radius = min(rect.width() / 2, rect.height()) - 24
        if outer_radius <= 0:
            return
        inner_radius = outer_radius * 0.15
        radius_steps = max(1, height - 1)
        radius_delta = (outer_radius - inner_radius) / radius_steps if radius_steps else 0
        pixel_size = max(4, int(self.led_size * self.zoom_factor * 0.8))
        center_x = rect.x() + rect.width() / 2
        center_y = rect.bottom() - 12  # anchor at bottom to mimic physical mounts

        for row in range(height):
            radius = inner_radius + radius_delta * row
            for col in range(width):
                idx = row * width + col
                if idx >= len(pixels_to_use):
                    continue
                angle = pi + (pi * (col / max(1, width)))  # sweep 180°
                x = center_x + radius * cos(angle)
                y = center_y + radius * sin(angle)
                r_val, g_val, b_val = pixels_to_use[idx]
                painter.setBrush(QBrush(QColor(r_val, g_val, b_val)))
                painter.setPen(QPen(self._cell_border_color, 1))
                painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
    
    def _paint_circular_layout(self, painter: QPainter, frame: Frame, metadata: PatternMetadata, rect):
        """
        Paint circular layout using CircularMapper to map grid pixels to LED positions.
        
        IMPORTANT: This method uses the mapping table (single source of truth) to get
        pixel colors from the grid. Display positions are calculated for rendering,
        but pixel data always comes from the mapping table lookup.
        
        For radial layouts, uses row/column interpretation (LMS-style):
        - Rows = number of concentric circles
        - Columns = LEDs per circle
        - Read pixels directly from grid: frame.pixels[row * width + col]
        
        This follows the "lens, not new world" philosophy - the grid is primary,
        circular layout is an interpretation layer.
        
        Args:
            painter: QPainter instance
            frame: Frame with pixel data (grid-based)
            metadata: PatternMetadata with circular layout configuration
            rect: Drawing rectangle
        """
        # Handle radial layout type (LMS-style: rows = circles, cols = LEDs per circle)
        if metadata.layout_type == "radial":
            # Use row/column interpretation (LMS-style)
            num_circles = metadata.height
            leds_per_circle = metadata.width
            
            # Calculate display parameters
            pixel_size = max(4, int(self.led_size * self.zoom_factor * 0.8))
            center_x = rect.x() + rect.width() / 2
            center_y = rect.y() + rect.height() / 2
            
            # Calculate radius range
            outer_radius = min(rect.width(), rect.height()) / 2 - 16
            inner_radius = outer_radius * 0.15
            radius_delta = (outer_radius - inner_radius) / max(1, num_circles - 1) if num_circles > 1 else 0
            
            # Render concentric circles
            for row in range(num_circles):
                # Calculate radius for this circle
                radius = inner_radius + radius_delta * row
                
                # Render LEDs around this circle
                for col in range(leds_per_circle):
                    # Calculate angle for this LED position
                    angle = 2 * pi * (col / max(1, leds_per_circle))
                    
                    # Calculate LED position
                    x = center_x + radius * cos(angle)
                    y = center_y + radius * sin(angle)
                    
                    # Get composite pixels with animations if layer_manager is available
                    pixels_to_use = frame.pixels
                    if self.layer_manager:
                        try:
                            composite = self.layer_manager.get_composite_pixels(self.current_frame)
                            if composite and len(composite) == len(frame.pixels):
                                pixels_to_use = composite
                        except Exception:
                            pass
                    
                    # Read pixel color directly from grid (row/column interpretation)
                    grid_idx = row * metadata.width + col
                    if grid_idx < len(pixels_to_use):
                        r, g, b = pixels_to_use[grid_idx]
                    else:
                        r, g, b = (0, 0, 0)
                    
                    # Draw LED
                    color = QColor(r, g, b)
                    painter.setBrush(QBrush(color))
                    painter.setPen(QPen(self._cell_border_color, 1))
                    painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
                    
                    # Draw LED index if enabled
                    if self.show_numbers and pixel_size > 12:
                        painter.setPen(QPen(Qt.white, 1))
                        font = QFont()
                        font.setPointSize(max(6, pixel_size // 4))
                        painter.setFont(font)
                        led_num = row * leds_per_circle + col
                        painter.drawText(int(x) - pixel_size // 2, int(y) - pixel_size // 2, 
                                        pixel_size, pixel_size, Qt.AlignCenter, str(led_num))
            
            return
        
        # Ensure mapping table exists and is up-to-date (regenerate to pick up any logic changes)
        # This handles edge cases like loading old patterns or mapping logic updates
        try:
            # Force regeneration to ensure we have the latest mapping logic
            metadata.circular_mapping_table = CircularMapper.generate_mapping_table(metadata)
        except Exception as e:
            import logging
            logging.warning(f"Failed to regenerate mapping table: {e}")
        
        if not CircularMapper.ensure_mapping_table(metadata):
            # Fallback to matrix rendering if mapping generation fails
            # This ensures the app never crashes due to circular layout issues
            import logging
            logging.warning(
                f"Failed to ensure mapping table for circular layout preview. "
                f"Falling back to matrix view."
            )
            self._paint_matrix(painter, frame, metadata.width, metadata.height,
                             int(self.led_size * self.zoom_factor),
                             int(self.led_size * self.zoom_factor), rect, metadata=metadata)
            return
        
        # Calculate display parameters
        led_count = metadata.circular_led_count or len(metadata.circular_mapping_table)
        pixel_size = max(4, int(self.led_size * self.zoom_factor * 0.8))
        
        # Calculate center and radius
        center_x = rect.x() + rect.width() / 2
        center_y = rect.y() + rect.height() / 2
        max_radius = min(rect.width(), rect.height()) / 2 - 16
        
        # Use generate_led_positions_for_preview for proper ray-based rendering of circular/ring layouts
        # This handles the row/column interpretation correctly (top row = outer circle, bottom row = inner circle)
        led_positions = CircularMapper.generate_led_positions_for_preview(
            metadata=metadata,
            center_x=center_x,
            center_y=center_y,
            max_radius=max_radius
        )
        
        # Draw each LED in index order (0 → N-1)
        # This matches the physical wiring order
        for led_idx in range(led_count):
            if led_idx >= len(metadata.circular_mapping_table):
                # Missing mapping - skip this LED
                continue
            
            # CRITICAL: Use mapping table to get grid coordinate (single source of truth)
            grid_pos = metadata.circular_mapping_table[led_idx]
            if grid_pos is None:
                continue
            
            grid_x, grid_y = grid_pos
            
            # Get composite pixels with animations if layer_manager is available
            pixels_to_use = frame.pixels
            if self.layer_manager:
                try:
                    composite = self.layer_manager.get_composite_pixels(self.current_frame)
                    if composite and len(composite) == len(frame.pixels):
                        pixels_to_use = composite
                except Exception:
                    pass
            
            # Get pixel color from grid using mapping table lookup
            # This is the key: we read from grid, not from live calculations
            if 0 <= grid_y < metadata.height and 0 <= grid_x < metadata.width:
                grid_idx = grid_y * metadata.width + grid_x
                if grid_idx < len(pixels_to_use):
                    r, g, b = pixels_to_use[grid_idx]
                else:
                    r, g, b = (0, 0, 0)
            else:
                r, g, b = (0, 0, 0)
            
            # Get LED position from preview generation (handles ray-based layouts correctly)
            if led_idx < len(led_positions):
                x, y = led_positions[led_idx]
            else:
                # Fallback: simple circular arrangement if positions not available
                angle = 2 * pi * (led_idx / led_count) if led_count > 0 else 0
                radius = max_radius * 0.8
                x = center_x + radius * cos(angle)
                y = center_y + radius * sin(angle)
            
            # Draw LED
            color = QColor(r, g, b)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(self._cell_border_color, 1))
            painter.drawEllipse(int(x) - pixel_size // 2, int(y) - pixel_size // 2, pixel_size, pixel_size)
            
            # Draw LED index if enabled
            if self.show_numbers and pixel_size > 12:
                painter.setPen(QPen(Qt.white, 1))
                font = QFont()
                font.setPointSize(max(6, pixel_size // 4))
                painter.setFont(font)
                text_rect = painter.boundingRect(int(x) - pixel_size // 2, int(y) - pixel_size // 2, 
                                                pixel_size, pixel_size, Qt.AlignCenter, str(led_idx))
                painter.fillRect(text_rect, QColor(0, 0, 0, 180))
                painter.drawText(int(x) - pixel_size // 2, int(y) - pixel_size // 2, 
                               pixel_size, pixel_size, Qt.AlignCenter, str(led_idx))

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
        
        # Step 3: Filter to active cells if irregular shape
        if self.pattern and hasattr(self.pattern, 'metadata'):
            metadata = self.pattern.metadata
            layout_type = getattr(metadata, 'layout_type', 'rectangular')
            is_irregular = (layout_type == 'irregular' and 
                           getattr(metadata, 'irregular_shape_enabled', False))
            
            if is_irregular:
                active_cell_coordinates = getattr(metadata, 'active_cell_coordinates', None)
                if active_cell_coordinates is not None:
                    active_set = set(active_cell_coordinates)
                    path = [(x, y) for (x, y) in path if (x, y) in active_set]
        
        return path

    def apply_palette(self, palette: Dict[str, str]) -> None:
        """
        Apply theme colours for the LED display canvas.
        """

        def to_color(value, fallback: QColor) -> QColor:
            if value is None:
                return fallback
            if isinstance(value, QColor):
                return value
            return QColor(value)

        self._background_color = to_color(palette.get("background"), self._background_color)
        self._cell_border_color = to_color(palette.get("border"), self._cell_border_color)
        self._grid_light_color = to_color(palette.get("grid_light"), self._grid_light_color)
        self._grid_dark_color = to_color(palette.get("grid_dark"), self._grid_dark_color)
        self._number_color = to_color(palette.get("number"), self._number_color)
        self.update()
