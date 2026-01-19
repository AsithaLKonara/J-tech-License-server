"""
FPS Controller Widget - Control animation frame rate
Complete PySide6 implementation
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                                QSlider, QSpinBox, QPushButton, QGroupBox)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern


class FPSController(QWidget):
    """
    Widget for controlling pattern playback speed
    
    Features:
    - FPS slider (1-120)
    - Duration display
    - Speed presets (0.5x, 1x, 2x)
    - Fit to duration
    """
    
    # Signals
    fps_changed = Signal(float)  # Emitted when FPS changes
    speed_changed = Signal(float)  # Emitted when speed multiplier changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.original_fps = 30.0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout()
        
        # FPS Control
        fps_group = QGroupBox("Frame Rate")
        fps_layout = QHBoxLayout()
        
        fps_layout.addWidget(QLabel("FPS:"))
        
        # FPS slider
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(1, 120)
        self.fps_slider.setValue(30)
        self.fps_slider.setTickPosition(QSlider.TicksBelow)
        self.fps_slider.setTickInterval(10)
        self.fps_slider.valueChanged.connect(self.on_fps_slider_changed)
        fps_layout.addWidget(self.fps_slider)
        
        # FPS spinbox
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(1, 120)
        self.fps_spinbox.setValue(30)
        self.fps_spinbox.setSuffix(" FPS")
        self.fps_spinbox.valueChanged.connect(self.on_fps_spinbox_changed)
        fps_layout.addWidget(self.fps_spinbox)
        
        fps_group.setLayout(fps_layout)
        layout.addWidget(fps_group)
        
        # Speed presets
        presets_group = QGroupBox("Speed Presets")
        presets_layout = QHBoxLayout()
        
        half_speed_btn = QPushButton("0.5x")
        half_speed_btn.clicked.connect(lambda: self.set_speed_multiplier(0.5))
        presets_layout.addWidget(half_speed_btn)
        
        normal_speed_btn = QPushButton("1.0x")
        normal_speed_btn.clicked.connect(lambda: self.set_speed_multiplier(1.0))
        presets_layout.addWidget(normal_speed_btn)
        
        double_speed_btn = QPushButton("2.0x")
        double_speed_btn.clicked.connect(lambda: self.set_speed_multiplier(2.0))
        presets_layout.addWidget(double_speed_btn)
        
        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)
        
        # Duration info
        info_group = QGroupBox("Pattern Info")
        info_layout = QVBoxLayout()
        
        self.duration_label = QLabel("Duration: --")
        self.frame_count_label = QLabel("Frames: --")
        
        info_layout.addWidget(self.duration_label)
        info_layout.addWidget(self.frame_count_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def set_pattern(self, pattern: Pattern):
        """
        Load pattern and calculate current FPS
        
        Args:
            pattern: Pattern object
        """
        self.pattern = pattern
        
        if pattern:
            current_fps = pattern.average_fps
            self.original_fps = current_fps
            
            # Block signals while updating
            self.fps_slider.blockSignals(True)
            self.fps_spinbox.blockSignals(True)
            
            self.fps_slider.setValue(int(current_fps))
            self.fps_spinbox.setValue(int(current_fps))
            
            self.fps_slider.blockSignals(False)
            self.fps_spinbox.blockSignals(False)
            
            self.update_info()
    
    def on_fps_slider_changed(self, value):
        """FPS slider moved"""
        self.fps_spinbox.blockSignals(True)
        self.fps_spinbox.setValue(value)
        self.fps_spinbox.blockSignals(False)
        
        self.apply_fps(value)
    
    def on_fps_spinbox_changed(self, value):
        """FPS spinbox changed"""
        self.fps_slider.blockSignals(True)
        self.fps_slider.setValue(value)
        self.fps_slider.blockSignals(False)
        
        self.apply_fps(value)
    
    def apply_fps(self, fps: float):
        """Apply FPS to pattern"""
        if not self.pattern:
            return
        
        self.pattern.set_global_fps(fps)
        if hasattr(self.pattern, 'metadata'):
            self.pattern.metadata.fps = float(fps)
            
        self.update_info()
        self.fps_changed.emit(fps)
    
    def set_fps(self, fps: float):
        """Set the FPS value"""
        fps = max(1.0, min(120.0, fps))
        self.fps_slider.blockSignals(True)
        self.fps_spinbox.blockSignals(True)
        
        self.fps_slider.setValue(int(fps))
        self.fps_spinbox.setValue(int(fps))
        
        self.fps_slider.blockSignals(False)
        self.fps_spinbox.blockSignals(False)
        
        self.apply_fps(fps)
    
    def set_speed_multiplier(self, multiplier: float):
        """
        Apply speed multiplier to pattern
        
        Args:
            multiplier: Speed multiplier (0.5 = half speed, 2.0 = double speed)
        """
        if not self.pattern:
            return
        
        # Calculate new FPS
        new_fps = self.original_fps * multiplier
        new_fps = max(1, min(120, new_fps))
        
        self.fps_slider.blockSignals(True)
        self.fps_spinbox.blockSignals(True)
        
        self.fps_slider.setValue(int(new_fps))
        self.fps_spinbox.setValue(int(new_fps))
        
        self.fps_slider.blockSignals(False)
        self.fps_spinbox.blockSignals(False)
        
        self.apply_fps(new_fps)
        self.speed_changed.emit(multiplier)
    
    def update_info(self):
        """Update duration and frame count display"""
        if not self.pattern:
            self.duration_label.setText("Duration: --")
            self.frame_count_label.setText("Frames: --")
            return
        
        duration_s = self.pattern.duration_ms / 1000.0
        self.duration_label.setText(f"Duration: {duration_s:.2f}s")
        self.frame_count_label.setText(f"Frames: {self.pattern.frame_count}")

