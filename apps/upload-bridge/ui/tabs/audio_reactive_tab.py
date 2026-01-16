"""
Audio-Reactive Effects Tab - Generate patterns from audio input
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QGroupBox, QProgressBar, QSpinBox, QDoubleSpinBox,
    QMessageBox, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern
from core.audio_reactive import AudioReactiveGenerator, AUDIO_AVAILABLE
import logging

logger = logging.getLogger(__name__)


class AudioCaptureWorker(QThread):
    """Worker thread for audio capture and pattern generation"""
    progress = Signal(int, int)  # current, total
    frame_ready = Signal(object)  # Frame data for preview
    finished = Signal(object)  # Pattern
    error = Signal(str)  # Error message
    
    def __init__(self, generator, duration, fps, mode, led_count, width, height):
        super().__init__()
        self.generator = generator
        self.duration = duration
        self.fps = fps
        self.mode = mode
        self.led_count = led_count
        self.width = width
        self.height = height
        self.should_stop = False
    
    def run(self):
        """Generate pattern from audio"""
        try:
            pattern = self.generator.generate_pattern_from_audio(
                duration_seconds=self.duration,
                fps=self.fps,
                visualization_mode=self.mode
            )
            self.finished.emit(pattern)
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop generation"""
        self.should_stop = True
        if self.generator:
            self.generator.stop_capture()


class AudioReactiveTab(QWidget):
    """
    Audio-Reactive Effects Tab
    
    Features:
    - Audio device selection
    - Real-time audio visualization
    - Pattern generation from audio
    - Multiple visualization modes
    """
    
    # Signals
    pattern_generated = Signal(Pattern)  # Emitted when pattern is generated
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.generator: AudioReactiveGenerator = None
        self.worker: AudioCaptureWorker = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.setup_ui()
        self.check_audio_availability()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Audio availability check
        self.availability_label = QLabel()
        self.availability_label.setWordWrap(True)
        content_layout.addWidget(self.availability_label)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # LED matrix size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Matrix Size:"))
        
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(1)
        self.width_spin.setMaximum(256)
        self.width_spin.setValue(32)
        self.width_spin.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(1)
        self.height_spin.setMaximum(256)
        self.height_spin.setValue(16)
        self.height_spin.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)
        
        size_layout.addStretch()
        config_layout.addLayout(size_layout)
        
        # Audio device
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Audio Device:"))
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        
        self.refresh_devices_button = QPushButton("🔄 Refresh")
        self.refresh_devices_button.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_devices_button)
        device_layout.addStretch()
        config_layout.addLayout(device_layout)
        
        # Visualization mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Visualization Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Frequency Bars",
            "Spectrum",
            "Volume Wave",
            "Peak Tracker"
        ])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        config_layout.addLayout(mode_layout)
        
        # Capture settings
        capture_layout = QHBoxLayout()
        capture_layout.addWidget(QLabel("Duration (seconds):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setMinimum(1.0)
        self.duration_spin.setMaximum(300.0)
        self.duration_spin.setValue(10.0)
        self.duration_spin.setSuffix(" s")
        capture_layout.addWidget(self.duration_spin)
        
        capture_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QDoubleSpinBox()
        self.fps_spin.setMinimum(1.0)
        self.fps_spin.setMaximum(60.0)
        self.fps_spin.setValue(30.0)
        capture_layout.addWidget(self.fps_spin)
        
        capture_layout.addStretch()
        config_layout.addLayout(capture_layout)
        
        config_group.setLayout(config_layout)
        content_layout.addWidget(config_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("No preview available")
        self.preview_label.setMinimumHeight(200)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #000; color: #fff;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        content_layout.addWidget(preview_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        content_layout.addWidget(progress_group)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("🎤 Start Capture")
        self.start_button.clicked.connect(self.start_capture)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop_capture)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        self.generate_button = QPushButton("🎵 Generate Pattern")
        self.generate_button.clicked.connect(self.generate_pattern)
        self.generate_button.setEnabled(False)
        controls_layout.addWidget(self.generate_button)
        
        controls_layout.addStretch()
        
        content_layout.addLayout(controls_layout)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Initialize
        self.refresh_devices()
        self.on_size_changed()
    
    def check_audio_availability(self):
        """Check if audio libraries are available"""
        if not AUDIO_AVAILABLE:
            self.availability_label.setText(
                "<b style='color: red;'>⚠ Audio libraries not available.</b><br>"
                "Install pyaudio and scipy to use audio-reactive effects:<br>"
                "<code>pip install pyaudio scipy</code>"
            )
            self.start_button.setEnabled(False)
            self.generate_button.setEnabled(False)
        else:
            self.availability_label.setText(
                "<b style='color: green;'>✓ Audio libraries available</b>"
            )
    
    def refresh_devices(self):
        """Refresh audio device list"""
        if not AUDIO_AVAILABLE:
            return
        
        try:
            if self.generator:
                devices = self.generator.list_audio_devices()
            else:
                # Create temporary generator to list devices
                temp_gen = AudioReactiveGenerator(led_count=32, width=32, height=1)
                devices = temp_gen.list_audio_devices()
                temp_gen.cleanup()
            
            self.device_combo.clear()
            self.device_combo.addItem("Default Device", None)
            for device_idx, device_name in devices:
                self.device_combo.addItem(device_name, device_idx)
            
            logger.info(f"Found {len(devices)} audio input device(s)")
        
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Device Refresh Failed",
                f"Failed to refresh audio devices:\n\n{str(e)}"
            )
    
    def on_device_changed(self):
        """Handle device selection change"""
        # Could restart capture if already running
        pass
    
    def on_size_changed(self):
        """Handle matrix size change"""
        width = self.width_spin.value()
        height = self.height_spin.value()
        led_count = width * height
        
        # Update generator if it exists
        if self.generator:
            self.generator.cleanup()
        
        try:
            if AUDIO_AVAILABLE:
                self.generator = AudioReactiveGenerator(
                    led_count=led_count,
                    width=width,
                    height=height
                )
        except Exception as e:
            logger.error(f"Error creating generator: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Generator Error",
                f"Failed to create audio generator:\n\n{str(e)}"
            )
    
    def start_capture(self):
        """Start audio capture for preview"""
        if not AUDIO_AVAILABLE or not self.generator:
            QMessageBox.warning(
                self,
                "Audio Not Available",
                "Audio libraries not available or generator not initialized."
            )
            return
        
        try:
            device_index = self.device_combo.currentData()
            self.generator.start_capture(device_index=device_index)
            
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            
            # Start preview timer
            self.preview_timer.start(33)  # ~30 FPS preview
            
            self.status_label.setText("Capturing audio...")
            logger.info("Audio capture started")
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Capture Failed",
                f"Failed to start audio capture:\n\n{str(e)}"
            )
            logger.error(f"Capture error: {e}", exc_info=True)
    
    def stop_capture(self):
        """Stop audio capture"""
        if self.generator:
            self.generator.stop_capture()
        
        self.preview_timer.stop()
        
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        self.status_label.setText("Stopped")
        self.preview_label.setText("No preview available")
        logger.info("Audio capture stopped")
    
    def update_preview(self):
        """Update preview display"""
        if not self.generator or not self.generator.is_capturing:
            return
        
        try:
            # Read audio chunk
            audio_data = self.generator.read_audio_chunk()
            if audio_data is None:
                return
            
            # Analyze audio
            analysis = self.generator.analyze_audio(audio_data)
            
            # Generate preview pixels
            mode = self.mode_combo.currentText().lower().replace(" ", "_")
            pixels = self.generator._generate_frame_pixels(analysis, mode)
            
            # Update preview label (simplified text representation)
            volume = analysis['volume']
            peak_freq = analysis['peak_frequency']
            preview_text = f"Volume: {volume:.2f} | Peak: {peak_freq:.0f} Hz\n"
            preview_text += f"LED Values: {len([v for v in analysis['led_values'] if v > 0.1])} active"
            self.preview_label.setText(preview_text)
        
        except Exception as e:
            logger.error(f"Preview update error: {e}", exc_info=True)
    
    def generate_pattern(self):
        """Generate pattern from audio"""
        if not AUDIO_AVAILABLE or not self.generator:
            QMessageBox.warning(
                self,
                "Audio Not Available",
                "Audio libraries not available or generator not initialized."
            )
            return
        
        if not self.generator.is_capturing:
            QMessageBox.warning(
                self,
                "Not Capturing",
                "Please start audio capture first."
            )
            return
        
        # Confirm
        duration = self.duration_spin.value()
        reply = QMessageBox.question(
            self,
            "Generate Pattern",
            f"Generate pattern from {duration} seconds of audio?\n\n"
            "This will capture audio and create a pattern.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Disable controls
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.generate_button.setEnabled(False)
        
        # Calculate progress
        fps = self.fps_spin.value()
        total_frames = int(duration * fps)
        self.progress_bar.setMaximum(total_frames)
        self.progress_bar.setValue(0)
        
        # Create and start worker
        mode = self.mode_combo.currentText().lower().replace(" ", "_")
        width = self.width_spin.value()
        height = self.height_spin.value()
        led_count = width * height
        
        # Create new generator for worker
        worker_generator = AudioReactiveGenerator(
            led_count=led_count,
            width=width,
            height=height
        )
        device_index = self.device_combo.currentData()
        
        self.worker = AudioCaptureWorker(
            worker_generator,
            duration,
            fps,
            mode,
            led_count,
            width,
            height
        )
        self.worker.progress.connect(self.on_generation_progress)
        self.worker.finished.connect(self.on_pattern_generated)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()
        
        self.status_label.setText("Generating pattern from audio...")
    
    def on_generation_progress(self, current: int, total: int):
        """Handle generation progress"""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Generating: {current}/{total} frames...")
    
    def on_pattern_generated(self, pattern: Pattern):
        """Handle pattern generation completion"""
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.status_label.setText("Pattern generated!")
        
        # Re-enable controls
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.generate_button.setEnabled(True)
        
        # Emit signal
        self.pattern_generated.emit(pattern)
        
        QMessageBox.information(
            self,
            "Pattern Generated",
            f"Successfully generated pattern:\n\n"
            f"Frames: {pattern.frame_count}\n"
            f"Duration: {pattern.duration_ms / 1000:.1f}s\n"
            f"LEDs: {pattern.led_count}"
        )
    
    def on_generation_error(self, error_msg: str):
        """Handle generation error"""
        self.status_label.setText("Generation failed")
        
        # Re-enable controls
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.generate_button.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Failed to generate pattern:\n\n{error_msg}"
        )
    
    def cleanup(self):
        """Cleanup resources"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        
        if self.generator:
            self.generator.cleanup()
        
        self.preview_timer.stop()

