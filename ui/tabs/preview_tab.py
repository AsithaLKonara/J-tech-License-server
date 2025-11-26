"""
Preview Tab - Pattern visualization and playback
Complete PySide6 implementation
"""

import sys
import os

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QLabel, QSlider, QGroupBox, QSpinBox, QScrollArea,
                                QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
import logging

from core.pattern import Pattern, Frame, load_pattern_from_file, auto_detect_pattern_info
from core.pattern_exporter import PatternExporter
from core.services.export_service import ExportService
from core.repositories.pattern_repository import PatternRepository
from ui.widgets.enhanced_led_simulator import EnhancedLEDSimulatorWidget
from ui.widgets.fps_controller import FPSController
from ui.widgets.advanced_brightness_controller import AdvancedBrightnessController
from ui.widgets.enhanced_speed_controller import EnhancedSpeedController


class PreviewTab(QWidget):
    """
    Preview tab with LED simulator and playback controls
    
    Features:
    - Real-time LED preview
    - Play/pause/stop controls
    - Frame scrubber
    - FPS control
    - Brightness control
    - Pattern information display
    """
    
    # Signals
    pattern_modified = Signal()  # Emitted when pattern is modified
    playback_state_changed = Signal(bool)  # Emitted when playback state changes (True=playing, False=paused/stopped)
    frame_changed = Signal(int)  # Emitted when frame index changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize services
        self.export_service = ExportService()
        self.repository = PatternRepository.instance()
        
        # Legacy pattern reference (for backward compatibility)
        self.pattern: Pattern = None
        self._original_file_pattern: Pattern = None  # Original file data (before unwrapping)
        self._syncing_playback = False  # Flag to prevent signal loops
        self._syncing_frame = False  # Flag to prevent frame sync loops
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        # Create scroll area for better responsiveness
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create main content widget
        self.content_widget = QWidget()
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("👁️ Pattern Preview")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00ff88; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Preview and control your LED patterns in real-time")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 15px; font-size: 11px;")
        main_layout.addWidget(desc_label)
        
        # Top: LED Simulator
        simulator_group = QGroupBox("LED Preview")
        simulator_layout = QVBoxLayout()
        
        self.simulator = EnhancedLEDSimulatorWidget()
        self.simulator.frame_changed.connect(self.on_frame_changed)
        simulator_layout.addWidget(self.simulator)
        
        simulator_group.setLayout(simulator_layout)
        main_layout.addWidget(simulator_group, stretch=3)
        
        # Middle: Playback Controls
        controls_group = QGroupBox("Playback Controls")
        controls_layout = QVBoxLayout()
        
        # Play/Pause/Stop buttons
        button_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶ Play")
        self.play_button.clicked.connect(self.on_play)
        button_layout.addWidget(self.play_button)
        
        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.clicked.connect(self.on_pause)
        button_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.on_stop)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        controls_layout.addLayout(button_layout)
        
        # Frame scrubber
        scrubber_layout = QHBoxLayout()
        scrubber_layout.addWidget(QLabel("Frame:"))
        
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self.on_frame_slider_changed)
        scrubber_layout.addWidget(self.frame_slider)
        
        self.frame_label = QLabel("0 / 0")
        scrubber_layout.addWidget(self.frame_label)
        
        controls_layout.addLayout(scrubber_layout)
        
        controls_group.setLayout(controls_layout)
        main_layout.addWidget(controls_group, stretch=1)
        
        # Bottom row: Advanced Controls
        bottom_layout = QHBoxLayout()
        
        # FPS Controller (simplified)
        self.fps_controller = FPSController()
        self.fps_controller.fps_changed.connect(self.on_fps_changed)
        bottom_layout.addWidget(self.fps_controller)
        
        # Advanced Brightness Controller
        self.advanced_brightness = AdvancedBrightnessController()
        self.advanced_brightness.brightness_changed.connect(self.on_advanced_brightness_changed)
        self.advanced_brightness.curve_changed.connect(self.on_brightness_curve_changed)
        self.advanced_brightness.led_type_changed.connect(self.on_led_type_changed)
        self.advanced_brightness.per_channel_changed.connect(self.on_per_channel_changed)
        bottom_layout.addWidget(self.advanced_brightness)
        
        # Enhanced Speed Controller
        self.enhanced_speed = EnhancedSpeedController()
        self.enhanced_speed.speed_changed.connect(self.on_enhanced_speed_changed)
        self.enhanced_speed.curve_changed.connect(self.on_speed_curve_changed)
        self.enhanced_speed.interpolation_changed.connect(self.on_interpolation_changed)
        self.enhanced_speed.keyframes_changed.connect(self.on_keyframes_changed)
        bottom_layout.addWidget(self.enhanced_speed)
        
        # Pattern info
        info_group = QGroupBox("Pattern Information")
        info_layout = QVBoxLayout()
        
        self.info_label = QLabel("No pattern loaded")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        # Export button
        export_button = QPushButton("💾 Export Pattern")
        export_button.clicked.connect(self.on_export_pattern)
        export_button.setEnabled(False)
        self.export_button = export_button
        info_layout.addWidget(export_button)
        
        # Batch validation button
        batch_validate_button = QPushButton("🔍 Batch Validate Patterns...")
        batch_validate_button.clicked.connect(self.on_batch_validate)
        info_layout.addWidget(batch_validate_button)
        
        # Dimension override button
        override_button = QPushButton("⚙️ Override Dimensions...")
        override_button.clicked.connect(self.on_override_dimensions)
        info_layout.addWidget(override_button)
        
        info_group.setLayout(info_layout)
        bottom_layout.addWidget(info_group)
        
        main_layout.addLayout(bottom_layout)
        
        # Set up scroll area
        self.scroll_area.setWidget(self.content_widget)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.scroll_area)
    
    def load_pattern(self, pattern: Pattern, file_path: str = None):
        """
        Load pattern for preview with auto-detection
        
        Args:
            pattern: Pattern object to display
            file_path: Optional file path
        """
        # Store in repository and sync legacy reference
        self.repository.set_current_pattern(pattern, file_path)
        self.pattern = pattern  # Legacy reference for backward compatibility
        # Auto-unwrap serpentine patterns to display in design order (as per previous fix)
        # This ensures preview shows pattern correctly (what designer created)
        from core.pattern_converter import detect_serpentine_pattern, hardware_to_design_order
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Pattern loaded: {pattern.metadata.width}x{pattern.metadata.height}")
        
        logger.info("="*70)
        logger.info("PREVIEW LAYER - PATTERN LOAD")
        logger.info("="*70)
        logger.info(f"Pattern name: {pattern.name}")
        logger.info(f"Dimensions: {pattern.metadata.width}×{pattern.metadata.height}")
        logger.info(
            "Dimension source: %s (confidence %.0f%%)",
            getattr(pattern.metadata, 'dimension_source', 'unknown'),
            getattr(pattern.metadata, 'dimension_confidence', 0.0) * 100
        )
        if getattr(pattern.metadata, 'dimension_confidence', 0.0) < 0.5:
            logger.warning("Low confidence in detected dimensions; user verification recommended.")
        logger.info(f"LED count: {pattern.led_count}")
        logger.info(f"Frame count: {pattern.frame_count}")
        logger.info(f"Color order: {pattern.metadata.color_order}")
        logger.info(f"Is matrix: {pattern.metadata.is_matrix}")
        
        # Validate metadata before proceeding
        validation_result = self._validate_pattern_metadata(pattern)
        if not validation_result['valid']:
            logger.warning(f"⚠️ Metadata validation failed: {validation_result['reason']}")
            if validation_result.get('should_redetect'):
                # Try re-detection first
                logger.info("Attempting to re-detect dimensions from first few frames...")
                pattern = self._redetect_dimensions(pattern)
                
                # If still invalid or user has override preference, offer override dialog
                validation_result = self._validate_pattern_metadata(pattern)
                if not validation_result['valid'] or getattr(pattern.metadata, 'dimension_override', False):
                    # Check if user wants to override
                    from ui.widgets.dimension_override_dialog import DimensionOverrideDialog
                    from core.matrix_detector import get_shared_detector
                    
                    detector = get_shared_detector()
                    auto_detected = None
                    if pattern.frames:
                        detected_layout = detector.detect_layout(
                            pattern.led_count,
                            pattern.frames[0].pixels if pattern.frames else None
                        )
                        auto_detected = (detected_layout.width, detected_layout.height)
                    
                    dialog = DimensionOverrideDialog(
                        self,
                        current_width=pattern.metadata.width,
                        current_height=pattern.metadata.height,
                        led_count=pattern.led_count,
                        auto_detected=auto_detected
                    )
                    
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        dimensions, persist = dialog.get_result()
                        if dimensions:
                            pattern.metadata.width = dimensions[0]
                            pattern.metadata.height = dimensions[1]
                            pattern.metadata.dimension_override = True
                            pattern.metadata.dimension_override_source = 'user'
                            pattern.metadata.dimension_source = 'user'
                            pattern.metadata.dimension_confidence = 1.0
                            logger.info(f"User override: Dimensions set to {dimensions[0]}×{dimensions[1]}")
                            
                            # Store override preference if requested
                            if persist:
                                # Could store in config file or pattern metadata
                                logger.info("Override preference saved")
        
        # Initialize lazy frame loader for large patterns (>1000 frames)
        # Progressive loading improves memory usage and startup time
        if pattern.frame_count > 1000:
            logger.info(f"Large pattern detected ({pattern.frame_count} frames), initializing progressive frame loader...")
            from core.lazy_frame_loader import LazyFrameLoader
            # Adaptive cache size based on pattern size
            cache_size = min(100, max(50, pattern.frame_count // 100))
            self._lazy_loader = LazyFrameLoader(pattern, cache_size=cache_size)
            logger.info(f"Progressive frame loader initialized (cache size: {cache_size})")
        else:
            self._lazy_loader = None
        
        # CRITICAL: Store ORIGINAL pattern for flash tab
        # Flash tab will use the ORIGINAL file data (no conversion)
        # Optimize copying for large patterns (>1000 frames)
        import copy
        if pattern.frame_count > 1000:
            logger.info(f"Large pattern detected ({pattern.frame_count} frames), using optimized copying...")
            # For large patterns, use lazy copying - only copy metadata and frame references
            # Actual pixel data will be copied on-demand if needed
            self._original_file_pattern = Pattern(
                name=pattern.name,
                metadata=copy.deepcopy(pattern.metadata),
                frames=[Frame(pixels=list(frame.pixels), duration_ms=frame.duration_ms) 
                        for frame in pattern.frames[:100]]  # Only copy first 100 frames initially
            )
            # Store reference to original pattern for lazy loading
            self._original_file_pattern_ref = pattern
            logger.info("Optimized copy: Stored first 100 frames, remaining frames available via reference")
        else:
            # For smaller patterns, do full deep copy
            self._original_file_pattern = Pattern(
                name=pattern.name,
                metadata=copy.deepcopy(pattern.metadata),
                frames=[Frame(pixels=list(frame.pixels), duration_ms=frame.duration_ms) 
                        for frame in pattern.frames]  # Deep copy frames
            )
            self._original_file_pattern_ref = None
        
        # AUTO-DETECT file format, then allow user override
        from core.file_format_detector import detect_file_format_with_confidence
        
        detected_wiring, detected_corner, confidence, reason = detect_file_format_with_confidence(pattern)
        logger.info(f"🔍 Auto-detected file format: {detected_wiring} {detected_corner} (confidence={confidence:.2f}, reason={reason})")
        
        # Warn user if confidence is low
        if confidence < 0.6:
            logger.warning(
                "⚠️ Low confidence in auto-detection (%.0f%%). Please verify wiring mode and data-in corner manually.",
                confidence * 100
            )
        elif confidence < 0.75:
            logger.info(
                "ℹ️ Medium confidence in auto-detection (%.0f%%). Consider verifying wiring mode if pattern looks incorrect.",
                confidence * 100
            )
        
        # UNWRAP FOR PREVIEW ONLY using user-specified or auto-detected file format
        # Get file format from simulator UI (use auto-detected if not set)
        file_format = detected_wiring  # Use auto-detected as default
        file_datain = detected_corner  # Use auto-detected as default
        
        # Read from simulator dropdowns if available (user override)
        if hasattr(self.simulator, 'file_format_combo'):
            user_format = self.simulator.file_format_combo.currentText()
            if user_format and user_format != "Auto-detect":
                file_format = user_format
                logger.info(f"📝 User override: File Format = {file_format}")
        
        if hasattr(self.simulator, 'file_datain_combo'):
            user_datain_text = self.simulator.file_datain_combo.currentText()
            if user_datain_text and user_datain_text != "Auto-detect":
                file_datain = {
                    'Left Top': 'LT',
                    'Left Bottom': 'LB',
                    'Right Top': 'RT',
                    'Right Bottom': 'RB'
                }.get(user_datain_text, detected_corner)
                logger.info(f"📝 User override: File Data-In = {file_datain}")
        
        # Update UI dropdowns to show detected values (if not already set by user)
        if hasattr(self.simulator, 'file_format_combo'):
            if self.simulator.file_format_combo.currentText() in ["", "Auto-detect"]:
                # Set to detected value
                index = self.simulator.file_format_combo.findText(file_format)
                if index >= 0:
                    self.simulator.file_format_combo.setCurrentIndex(index)
        
        if hasattr(self.simulator, 'file_datain_combo'):
            corner_text_map = {
                'LT': 'Left Top',
                'LB': 'Left Bottom',
                'RT': 'Right Top',
                'RB': 'Right Bottom'
            }
            if self.simulator.file_datain_combo.currentText() in ["", "Auto-detect"]:
                corner_text = corner_text_map.get(file_datain, 'Left Top')
                index = self.simulator.file_datain_combo.findText(corner_text)
                if index >= 0:
                    self.simulator.file_datain_combo.setCurrentIndex(index)
        
        # This makes the preview look correct (all rows L→R)
        # But we keep the original file data for flashing
        logger.info(f"📂 File format specified: {file_format} {file_datain}")
        logger.info(f"📂 Unwrapping file for preview display...")
        logger.info(f"📂 Original file data preserved for flash (no conversion)")
        
        try:
            # Log BEFORE unwrapping
            import hashlib
            if pattern.frames and len(pattern.frames) > 0:
                before_unwrap = list(pattern.frames[0].pixels)
                before_checksum = hashlib.sha256(bytes([c for p in before_unwrap for c in p])).hexdigest()[:16]
                logger.info(f"📊 Frame 0 BEFORE unwrap ({file_format} {file_datain} format):")
                for i in range(min(6, len(before_unwrap))):
                    logger.info(f"     LED {i}: RGB{before_unwrap[i]}")
                logger.info(f"   Checksum BEFORE: {before_checksum}")
            
            # Unwrap from file format to design order
            unwrapped_pattern = hardware_to_design_order(pattern, file_format, file_datain)
            unwrapped_pattern.metadata.original_wiring_mode = file_format
            unwrapped_pattern.metadata.original_data_in_corner = file_datain
            unwrapped_pattern.metadata.already_unwrapped = True  # This is just for preview
            
            # Log AFTER unwrapping
            if unwrapped_pattern.frames and len(unwrapped_pattern.frames) > 0:
                after_unwrap = list(unwrapped_pattern.frames[0].pixels)
                after_checksum = hashlib.sha256(bytes([c for p in after_unwrap for c in p])).hexdigest()[:16]
                logger.info(f"📊 Frame 0 AFTER unwrap (design order):")
                for i in range(min(6, len(after_unwrap))):
                    logger.info(f"     LED {i}: RGB{after_unwrap[i]}")
                logger.info(f"   Checksum AFTER: {after_checksum}")
            
            logger.info(f"✓ Preview unwrapped from {file_format} {file_datain} → design order")
            logger.info(f"✓ Preview shows all rows L→R, T→B (design view)")
            logger.info(f"✓ Flash will use original file data and convert to target wiring")
            
            # Use unwrapped pattern for preview
            pattern = unwrapped_pattern
        except Exception as e:
            logger.error(f"❌ Failed to unwrap pattern: {e}")
            logger.error(f"Using original pattern for preview (may show flipped rows)")
            import traceback
            logger.error(traceback.format_exc())
            # Use original pattern if unwrapping fails
        
        # Log first frame sample
        if pattern.frames and len(pattern.frames) > 0:
            first_frame = pattern.frames[0]
            logger.info(f"First frame duration: {first_frame.duration_ms}ms")
            sample_size = min(12, len(first_frame.pixels))
            logger.info(f"First frame sample (first {sample_size} pixels in design order):")
            for i in range(sample_size):
                logger.info(f"  Cell {i}: RGB{first_frame.pixels[i]}")
        
        logger.info(f"Flash tab will convert design order → UI target format if needed")
        logger.info("="*70)
        
        # Keep a base pattern (unwrapped/design order) and a preview copy
        # The base pattern is in design order (all rows L→R) for correct preview
        # Flash tab will convert from design order to target hardware order
        logger.info(f"Setting pattern for preview: {pattern.name if pattern else 'None'}")
        logger.info(f"Pattern frames: {len(pattern.frames) if pattern and pattern.frames else 0}")
        
        self.pattern = pattern  # Design order (for preview)
        self._base_pattern = pattern  # Also design order (for preview rebuild)
        self._preview_pattern = None
        
        # No need to set frame_count explicitly; property is derived from frames
        
        # Reset simulator's initial load flag so UI gets updated from new pattern metadata
        if hasattr(self.simulator, '_initial_load'):
            self.simulator._initial_load = True
            logger.info("Reset simulator _initial_load flag")
        
        # Set reload callback so file format changes can trigger preview reload
        self.simulator._reload_callback = self._reload_from_original_file
        
        # Build preview pattern and load
        logger.info("Building preview pattern...")
        try:
            self._rebuild_preview_pattern()
            logger.info(f"Preview pattern built: {self._preview_pattern is not None}")
        except Exception as e:
            logger.error(f"❌ Failed to rebuild preview pattern: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Load into simulator
        logger.info("Loading pattern into simulator...")
        try:
            if self._preview_pattern:
                logger.info(f"Loading preview pattern ({len(self._preview_pattern.frames)} frames)")
                self.simulator.load_pattern(self._preview_pattern)
            else:
                logger.info(f"Loading base pattern ({len(self.pattern.frames)} frames)")
                self.simulator.load_pattern(self.pattern)
            logger.info("✓ Pattern loaded into simulator successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load pattern into simulator: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Update FPS controller
        self.fps_controller.set_pattern(self.pattern)
        
        # Update advanced controllers
        self.advanced_brightness.set_pattern(self.pattern)
        self.enhanced_speed.set_pattern(self.pattern)
        
        # Update frame slider
        self.frame_slider.setRange(0, self.pattern.frame_count - 1)
        self.frame_slider.setValue(0)
        
        # Update info
        self.update_info()
        
        # Enable export button
        if hasattr(self, 'export_button'):
            self.export_button.setEnabled(pattern is not None)
    
    def update_pattern(self, pattern: Pattern):
        """
        Update pattern for live preview (simpler than load_pattern, no unwrapping)
        
        Args:
            pattern: Updated Pattern object
        """
        if not pattern:
            return
        
        # Store in repository and sync legacy reference
        self.repository.set_current_pattern(pattern)
        self.pattern = pattern  # Legacy reference for backward compatibility
        
        # Rebuild preview pattern if needed
        try:
            self._rebuild_preview_pattern()
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to rebuild preview pattern: {e}")
        
        # Update simulator with new pattern
        try:
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            else:
                self.simulator.load_pattern(self.pattern)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to update simulator: {e}")
        
        # Update frame slider range
        if self.pattern:
            self.frame_slider.setRange(0, self.pattern.frame_count - 1)
            self.update_info()
    
    def load_pattern_from_file(self, file_path: str):
        """
        Load pattern from file with auto-detection
        
        Args:
            file_path: Path to pattern file
        """
        try:
            # Auto-detect pattern info first
            info = auto_detect_pattern_info(file_path)
            logging.getLogger(__name__).info("Auto-detected pattern info: %s", info)
            
            # Load pattern with auto-detection
            pattern = load_pattern_from_file(file_path)
            
            # Load into preview
            self.load_pattern(pattern)
            
            return pattern
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load pattern: {e}")
            return None
    
    def on_play(self):
        """Play button clicked"""
        if not self._syncing_playback:
            self.simulator.play()
            self.play_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.playback_state_changed.emit(True)
    
    def on_pause(self):
        """Pause button clicked"""
        if not self._syncing_playback:
            self.simulator.pause()
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.playback_state_changed.emit(False)
    
    def on_stop(self):
        """Stop button clicked"""
        if not self._syncing_playback:
            # Use lazy loader if available
            if self._lazy_loader:
                self.simulator.stop(lazy_loader=self._lazy_loader)
            else:
                self.simulator.stop()
            self.play_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.playback_state_changed.emit(False)
    
    def on_frame_changed(self, frame_idx: int):
        """Handle frame change from simulator (with lazy loading support)"""
        # Preload nearby frames if using lazy loader
        if self._lazy_loader:
            # Preload current frame and nearby frames for smooth scrubbing
            preload_range = 5
            start_idx = max(0, frame_idx - preload_range)
            end_idx = min(self.pattern.frame_count, frame_idx + preload_range + 1)
            self._lazy_loader.preload_range(start_idx, end_idx)
        
        # Update slider without triggering signal
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame_idx)
        self.frame_slider.blockSignals(False)
        
        # Update label
        if self.pattern:
            self.frame_label.setText(f"{frame_idx + 1} / {self.pattern.frame_count}")
        
        # Emit frame changed signal (if not syncing to prevent loops)
        if not self._syncing_frame:
            self.frame_changed.emit(frame_idx)
    
    def on_frame_slider_changed(self, value: int):
        """User moved frame slider"""
        self.simulator.pause()  # Pause playback when scrubbing
        
        # Use lazy loader if available for progressive loading
        if self._lazy_loader:
            self.simulator.set_frame(value, lazy_loader=self._lazy_loader)
        else:
            self.simulator.set_frame(value)
        
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
    
    def on_fps_changed(self, fps: float):
        """FPS changed in controller"""
        # Reload pattern in simulator with new durations
        if self.pattern:
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
                self.update_info()
                self.pattern_modified.emit()
    
    def sync_playback_state(self, is_playing: bool):
        """Sync playback state from another tab (called from signal)"""
        self._syncing_playback = True
        try:
            if is_playing:
                if self.play_button.isEnabled():  # Not currently playing
                    self.on_play()
            else:
                if not self.play_button.isEnabled():  # Currently playing
                    self.on_pause()
        finally:
            self._syncing_playback = False
    
    def sync_frame_selection(self, frame_idx: int):
        """Sync frame selection from another tab (called from signal)"""
        self._syncing_frame = True
        try:
            if self.pattern and 0 <= frame_idx < self.pattern.frame_count:
                self.simulator.pause()  # Pause when syncing frame
                self.simulator.set_frame(frame_idx)
                # Update UI without triggering signals
                self.frame_slider.blockSignals(True)
                self.frame_slider.setValue(frame_idx)
                self.frame_slider.blockSignals(False)
                if self.pattern:
                    self.frame_label.setText(f"{frame_idx + 1} / {self.pattern.frame_count}")
        finally:
            self._syncing_frame = False
    
    def on_advanced_brightness_changed(self, brightness: float):
        """Advanced brightness changed"""
        if self.pattern:
            # Update metadata
            self.pattern.metadata.brightness = brightness
            self.advanced_brightness.apply_to_pattern()
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
        self.simulator.set_brightness(brightness)
    
    def on_brightness_curve_changed(self, curve_type: str):
        """Brightness curve changed"""
        if self.pattern:
            self.pattern.metadata.brightness_curve = curve_type
            self.advanced_brightness.apply_to_pattern()
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            self.pattern_modified.emit()
    
    def on_led_type_changed(self, led_type: str):
        """LED type changed"""
        if self.pattern:
            self.pattern.metadata.led_type = led_type
            self.advanced_brightness.apply_to_pattern()
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            self.pattern_modified.emit()
    
    def on_per_channel_changed(self, enabled: bool):
        """Per-channel brightness changed"""
        if self.pattern:
            self.pattern.metadata.per_channel_brightness = enabled
            # Update metadata from controller and rebuild preview
            self.advanced_brightness.apply_to_pattern()
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            else:
                self.simulator.load_pattern(self.pattern)
            self.pattern_modified.emit()
    
    def on_enhanced_speed_changed(self, speed: float):
        """Enhanced speed changed"""
        if self.pattern:
            # Rebuild preview with new speed multiplier
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
                self.pattern_modified.emit()
    
    def on_speed_curve_changed(self, curve_type: str):
        """Speed curve changed"""
        if self.pattern:
            self.pattern.metadata.speed_curve = curve_type
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            self.pattern_modified.emit()
    
    def on_interpolation_changed(self, enabled: bool, factor: float):
        """Interpolation settings changed"""
        if self.pattern:
            self.pattern.metadata.interpolation_enabled = enabled
            self.pattern.metadata.interpolation_factor = factor
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            self.pattern_modified.emit()
    
    def on_keyframes_changed(self, keyframes: list):
        """Speed keyframes changed"""
        if self.pattern:
            self.pattern.metadata.speed_keyframes = keyframes
            self.pattern.metadata.variable_speed = len(keyframes) > 0
            self._rebuild_preview_pattern()
            if self._preview_pattern:
                self.simulator.load_pattern(self._preview_pattern)
            self.pattern_modified.emit()
    
    def _validate_pattern_metadata(self, pattern: Pattern) -> dict:
        """
        Validate pattern metadata consistency.
        
        Args:
            pattern: Pattern to validate
            
        Returns:
            dict with 'valid' (bool), 'reason' (str), and 'should_redetect' (bool)
        """
        if not pattern or not pattern.frames:
            return {'valid': False, 'reason': 'Pattern has no frames', 'should_redetect': False}
        
        # Check if width * height matches LED count
        expected_leds = pattern.metadata.width * pattern.metadata.height
        actual_leds = pattern.led_count
        
        if expected_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Dimension mismatch: {pattern.metadata.width}×{pattern.metadata.height}={expected_leds} but LED count={actual_leds}',
                'should_redetect': True
            }
        
        # Check if all frames have consistent LED count
        first_frame_leds = len(pattern.frames[0].pixels) if pattern.frames else 0
        if first_frame_leds != actual_leds:
            return {
                'valid': False,
                'reason': f'Frame LED count mismatch: first frame has {first_frame_leds} LEDs, expected {actual_leds}',
                'should_redetect': True
            }
        
        # Check dimension confidence for auto-detected dimensions
        dimension_source = getattr(pattern.metadata, 'dimension_source', 'unknown')
        dimension_confidence = getattr(pattern.metadata, 'dimension_confidence', 0.0)
        
        if dimension_source != 'header' and dimension_confidence < 0.5:
            # Low confidence detection - might be wrong
            return {
                'valid': False,
                'reason': f'Low confidence detection ({dimension_confidence:.0%}) from {dimension_source}',
                'should_redetect': True
            }
        
        return {'valid': True, 'reason': 'Metadata is consistent', 'should_redetect': False}
    
    def _redetect_dimensions(self, pattern: Pattern) -> Pattern:
        """
        Re-detect dimensions using first few frames only (for performance).
        
        Args:
            pattern: Pattern with potentially incorrect metadata
            
        Returns:
            Pattern with corrected metadata
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not pattern or not pattern.frames:
            return pattern
        
        # Sample first 3-5 frames for detection (for large patterns)
        sample_frames = min(5, len(pattern.frames))
        logger.info(f"Re-detecting dimensions using first {sample_frames} frames...")
        
        from core.matrix_detector import MatrixDetector, get_shared_detector
        from core.dimension_scorer import pick_best_layout
        
        # Use shared detector for caching benefits
        detector = get_shared_detector()
        first_frame_pixels = pattern.frames[0].pixels if pattern.frames else None
        
        if not first_frame_pixels:
            logger.warning("Cannot re-detect: no frame data available")
            return pattern
        
        # Detect layout using first frame
        detected_layout = detector.detect_layout(len(first_frame_pixels), first_frame_pixels)
        
        if detected_layout and detected_layout.confidence > 0.5:
            logger.info(f"Re-detected dimensions: {detected_layout.width}×{detected_layout.height} (confidence: {detected_layout.confidence:.0%})")
            
            # Update metadata
            pattern.metadata.width = detected_layout.width
            pattern.metadata.height = detected_layout.height
            pattern.metadata.dimension_source = "detector"
            pattern.metadata.dimension_confidence = detected_layout.confidence
            
            logger.info("✓ Metadata updated with re-detected dimensions")
        else:
            logger.warning("Re-detection failed or low confidence, keeping original metadata")
        
        return pattern
    
    def _reload_from_original_file(self):
        """Reload pattern from original file with new file format settings"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if we have the full original pattern or need to reconstruct from reference
        if hasattr(self, '_original_file_pattern_ref') and self._original_file_pattern_ref:
            # Use the reference pattern (for large patterns)
            original_pattern = self._original_file_pattern_ref
            logger.info("Using reference pattern for reload (large pattern optimization)")
        elif hasattr(self, '_original_file_pattern') and self._original_file_pattern:
            original_pattern = self._original_file_pattern
        else:
            logger.warning("No original file pattern available for reload")
            return
        
        logger.info("="*70)
        logger.info("RELOADING PREVIEW - File format changed")
        logger.info("="*70)
        
        # Reload the original pattern with new file format settings
        # This will re-unwrap using the new file format selection
        self.load_pattern(original_pattern)
    
    def update_info(self):
        """Update pattern information display"""
        if not (self._preview_pattern or self.pattern):
            self.info_label.setText("No pattern loaded")
            return
        
        pat = self._preview_pattern or self.pattern
        info = f"<b>Pattern Information:</b><br>"
        info += f"LEDs: {pat.led_count}<br>"
        info += f"Frames: {pat.frame_count}<br>"
        info += f"Duration: {pat.duration_ms / 1000.0:.2f}s<br>"
        info += f"Avg FPS: {pat.average_fps:.1f}<br>"
        info += f"Layout: {pat.metadata.width}"
        
        if pat.metadata.height > 1:
            info += f"×{pat.metadata.height} matrix"
        else:
            info += " strip"
        
        dim_source = getattr(pat.metadata, 'dimension_source', 'unknown')
        dim_conf = getattr(pat.metadata, 'dimension_confidence', None)
        dim_override = getattr(pat.metadata, 'dimension_override', False)
        
        if dim_conf is not None:
            info += f"<br>Dimension Source: {dim_source} ({dim_conf*100:.0f}% confidence)"
        else:
            info += f"<br>Dimension Source: {dim_source}"
        
        if dim_override:
            info += "<br><span style='color:#00ff88'>✓ Dimensions manually set by user</span>"
        elif isinstance(dim_conf, (int, float)) and dim_conf < 0.5:
            info += "<br><span style='color:#ffb347'>⚠ Low confidence layout detection — verify dimensions.</span>"
        
        info += f"<br>Color Order: {pat.metadata.color_order}<br>"
        info += f"<br><b>Brightness Settings:</b><br>"
        info += f"Curve: {getattr(pat.metadata, 'brightness_curve', 'gamma_corrected')}<br>"
        info += f"LED Type: {getattr(pat.metadata, 'led_type', 'ws2812')}<br>"
        info += f"Per-Channel: {'Yes' if getattr(pat.metadata, 'per_channel_brightness', False) else 'No'}<br>"
        
        if getattr(pat.metadata, 'per_channel_brightness', False):
            info += f"R: {getattr(pat.metadata, 'red_brightness', 1.0):.2f} "
            info += f"G: {getattr(pat.metadata, 'green_brightness', 1.0):.2f} "
            info += f"B: {getattr(pat.metadata, 'blue_brightness', 1.0):.2f}<br>"
        
        info += f"<br><b>Speed Settings:</b><br>"
        info += f"Curve: {getattr(pat.metadata, 'speed_curve', 'linear')}<br>"
        info += f"Variable Speed: {'Yes' if getattr(pat.metadata, 'variable_speed', False) else 'No'}<br>"
        info += f"Interpolation: {'Yes' if getattr(pat.metadata, 'interpolation_enabled', False) else 'No'}"
        
        if getattr(pat.metadata, 'interpolation_enabled', False):
            info += f" ({getattr(pat.metadata, 'interpolation_factor', 1.0):.1f}x)<br>"
        else:
            info += "<br>"
        
        info += f"<br>Size: ~{self._estimate_size():.1f}KB"
        
        self.info_label.setText(info)
    
    def _estimate_size(self) -> float:
        """Estimate firmware size in KB"""
        if not self.pattern:
            return 0.0
        
        pat = self._preview_pattern or self.pattern
        pattern_size = pat.estimate_memory_bytes()
        firmware_overhead = 40  # KB (approximate)
        
        return (pattern_size / 1024.0) + firmware_overhead

    def _rebuild_preview_pattern(self):
        """Build a preview copy applying current FPS, speed curves, keyframes, and interpolation."""
        if not self._base_pattern:
            self._preview_pattern = None
            return
        try:
            # Deep copy via dict
            pat_dict = self._base_pattern.to_dict()
            from core.pattern import Pattern
            p = Pattern.from_dict(pat_dict)
            # Apply FPS from controller
            fps = getattr(self.fps_controller, 'current_fps', None)
            if fps is None and hasattr(self.fps_controller, 'get_current_fps'):
                try:
                    fps = self.fps_controller.get_current_fps()
                except Exception:
                    fps = None
            if isinstance(fps, (int, float)) and fps > 0:
                p.set_global_fps(float(fps))
            # Apply brightness and per-channel mapping using metadata
            try:
                brightness = getattr(p.metadata, 'brightness', 1.0)
                curve_type = getattr(p.metadata, 'brightness_curve', 'gamma_corrected')
                led_type = getattr(p.metadata, 'led_type', 'ws2812')
                per_channel = None
                if getattr(p.metadata, 'per_channel_brightness', False):
                    per_channel = {
                        'red': getattr(p.metadata, 'red_brightness', 1.0),
                        'green': getattr(p.metadata, 'green_brightness', 1.0),
                        'blue': getattr(p.metadata, 'blue_brightness', 1.0),
                    }
                # Apply to frame pixels (destructive on preview copy only)
                p.apply_advanced_brightness(
                    brightness=brightness,
                    curve_type=curve_type,
                    per_channel=per_channel,
                    led_type=led_type,
                )
            except Exception:
                pass
            # Apply speed curve and variable speed if set in metadata
            curve = getattr(p.metadata, 'speed_curve', 'linear')
            if curve and curve != 'linear':
                p.apply_speed_curve(curve)
            if getattr(p.metadata, 'variable_speed', False):
                keyframes = getattr(p.metadata, 'speed_keyframes', [])
                if keyframes:
                    p.apply_variable_speed(keyframes)
            # Apply global speed multiplier from enhanced speed controller
            try:
                speed_mult = getattr(self.enhanced_speed, 'speed_multiplier', 1.0)
                if isinstance(speed_mult, (int, float)) and speed_mult > 0 and abs(speed_mult - 1.0) > 1e-6:
                    # scale_speed >1 slows; multiplier>1 should make faster → scale by 1/speed_mult
                    p.scale_speed(1.0 / float(speed_mult))
            except Exception:
                pass
            # Interpolation
            if getattr(p.metadata, 'interpolation_enabled', False):
                factor = getattr(p.metadata, 'interpolation_factor', 1.0)
                try:
                    if factor and factor > 1.0:
                        p.interpolate_frames(factor)
                except Exception:
                    pass
            self._preview_pattern = p
        except Exception:
            self._preview_pattern = None
    
    def on_export_pattern(self):
        """Export pattern to selected format"""
        # Get pattern from repository or legacy reference
        pattern = self.repository.get_current_pattern() or self.pattern
        if not pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern to export!")
            return
        
        # Get available export formats from ExportService
        formats = self.export_service.get_available_formats()
        
        # Create file filter string
        format_extensions = {
            'bin': '*.bin',
            'hex': '*.hex',
            'dat': '*.dat',
            'leds': '*.leds',
            'json': '*.json',
            'csv': '*.csv',
            'txt': '*.txt',
            'ledproj': '*.ledproj',
            'h': '*.h'
        }
        
        filter_parts = []
        for fmt in formats:
            ext = format_extensions.get(fmt, f"*.{fmt}")
            filter_parts.append(f"{fmt.upper()} files ({ext})")
        
        filter_string = ";;".join(filter_parts) + ";;All Files (*.*)"
        
        # Open save dialog
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Pattern",
            "",
            filter_string
        )
        
        if not filepath:
            return
        
        # Determine format from selected filter or file extension
        format_name = None
        for fmt in formats:
            if fmt.upper() in selected_filter or filepath.lower().endswith(f".{fmt}"):
                format_name = fmt
                break
        
        # Default to bin if format not determined
        if not format_name:
            format_name = 'bin'
        
        # Ensure file extension matches
        expected_ext = format_extensions.get(format_name, f".{format_name}")
        if not filepath.lower().endswith(expected_ext.replace('*', '')):
            filepath += expected_ext.replace('*', '')
        
        try:
            # Validate export first
            is_valid, error, preview = self.export_service.validate_export(pattern, format_name)
            if not is_valid:
                QMessageBox.warning(
                    self,
                    "Export Validation Failed",
                    f"Cannot export pattern in {format_name} format:\n\n{error or 'Unknown error'}"
                )
                return
            
            # Export pattern using ExportService
            output_path = self.export_service.export_pattern(pattern, filepath, format_name)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Pattern exported successfully to:\n{output_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export pattern:\n\n{str(e)}"
            )
    
    def on_batch_validate(self):
        """Open batch validation dialog"""
        from ui.dialogs.batch_validation_dialog import BatchValidationDialog
        
        dialog = BatchValidationDialog(self)
        dialog.exec()
    
    def on_override_dimensions(self):
        """Open dimension override dialog"""
        if not self.pattern:
            QMessageBox.warning(self, "No Pattern", "No pattern loaded to override dimensions.")
            return
        
        from ui.widgets.dimension_override_dialog import DimensionOverrideDialog
        from core.matrix_detector import get_shared_detector
        
        detector = get_shared_detector()
        auto_detected = None
        if self.pattern.frames:
            detected_layout = detector.detect_layout(
                self.pattern.led_count,
                self.pattern.frames[0].pixels if self.pattern.frames else None
            )
            auto_detected = (detected_layout.width, detected_layout.height)
        
        dialog = DimensionOverrideDialog(
            self,
            current_width=self.pattern.metadata.width,
            current_height=self.pattern.metadata.height,
            led_count=self.pattern.led_count,
            auto_detected=auto_detected
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            dimensions, persist = dialog.get_result()
            if dimensions:
                self.pattern.metadata.width = dimensions[0]
                self.pattern.metadata.height = dimensions[1]
                self.pattern.metadata.dimension_override = True
                self.pattern.metadata.dimension_override_source = 'user'
                self.pattern.metadata.dimension_source = 'user'
                self.pattern.metadata.dimension_confidence = 1.0
                
                # Reload pattern with new dimensions
                self.load_pattern(self.pattern)
                self.update_info()
                
                QMessageBox.information(
                    self,
                    "Dimensions Updated",
                    f"Dimensions set to {dimensions[0]}×{dimensions[1]}"
                )

