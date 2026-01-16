"""
Enhanced Speed Controller - Comprehensive speed control options
Provides all speed control features for pattern playback
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSlider, QSpinBox, QComboBox, QGroupBox,
                               QPushButton, QCheckBox, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern


class EnhancedSpeedController(QWidget):
    """
    Enhanced speed controller with comprehensive options
    
    Features:
    - Global speed multiplier
    - Variable speed with keyframes
    - Speed curves (linear, ease-in, ease-out, etc.)
    - Frame interpolation
    - Speed presets
    - Real-time preview
    """
    
    # Signals
    speed_changed = Signal(float)  # Global speed multiplier
    curve_changed = Signal(str)  # Speed curve type
    interpolation_changed = Signal(bool, float)  # Interpolation enabled, factor
    keyframes_changed = Signal(list)  # Speed keyframes
    preset_changed = Signal(str)  # Speed preset
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.speed_multiplier = 1.0
        self.speed_curve = "linear"
        self.interpolation_enabled = False
        self.interpolation_factor = 1.0
        self.speed_keyframes = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout()
        
        # Speed multiplier
        speed_group = QGroupBox("Speed Control")
        speed_layout = QVBoxLayout()
        
        # Global speed
        global_speed_layout = QHBoxLayout()
        global_speed_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 500)  # 0.1x to 5.0x
        self.speed_slider.setValue(100)  # 1.0x
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        global_speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(40)
        global_speed_layout.addWidget(self.speed_label)
        
        speed_layout.addLayout(global_speed_layout)
        
        # Speed presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Custom",
            "Very Slow (0.25x)",
            "Slow (0.5x)",
            "Normal (1.0x)",
            "Fast (2.0x)",
            "Very Fast (4.0x)",
            "Ultra Fast (8.0x)"
        ])
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        speed_layout.addLayout(preset_layout)
        
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Speed curves
        curve_group = QGroupBox("Speed Curves")
        curve_layout = QVBoxLayout()
        
        curve_layout.addWidget(QLabel("Curve Type:"))
        
        self.curve_combo = QComboBox()
        self.curve_combo.addItems([
            "Linear",
            "Ease In",
            "Ease Out", 
            "Ease In-Out",
            "Ease In Quad",
            "Ease Out Quad",
            "Ease In-Out Quad",
            "Ease In Cubic",
            "Ease Out Cubic",
            "Ease In-Out Cubic",
            "Bounce",
            "Elastic",
            "Back"
        ])
        self.curve_combo.currentTextChanged.connect(self.on_curve_changed)
        curve_layout.addWidget(self.curve_combo)
        
        curve_group.setLayout(curve_layout)
        layout.addWidget(curve_group)
        
        # Variable speed
        variable_group = QGroupBox("Variable Speed")
        variable_layout = QVBoxLayout()
        
        self.variable_checkbox = QCheckBox("Enable Variable Speed")
        self.variable_checkbox.toggled.connect(self.on_variable_speed_changed)
        variable_layout.addWidget(self.variable_checkbox)
        
        # Keyframe controls
        keyframe_layout = QHBoxLayout()
        
        self.keyframe_spin = QSpinBox()
        self.keyframe_spin.setRange(0, 0)
        self.keyframe_spin.setSuffix(" frame")
        keyframe_layout.addWidget(QLabel("Frame:"))
        keyframe_layout.addWidget(self.keyframe_spin)
        
        self.keyframe_speed_spin = QDoubleSpinBox()
        self.keyframe_speed_spin.setRange(0.1, 10.0)
        self.keyframe_speed_spin.setValue(1.0)
        self.keyframe_speed_spin.setSuffix("x")
        keyframe_layout.addWidget(QLabel("Speed:"))
        keyframe_layout.addWidget(self.keyframe_speed_spin)
        
        self.add_keyframe_btn = QPushButton("Add")
        self.add_keyframe_btn.clicked.connect(self.add_keyframe)
        keyframe_layout.addWidget(self.add_keyframe_btn)
        
        self.remove_keyframe_btn = QPushButton("Remove")
        self.remove_keyframe_btn.clicked.connect(self.remove_keyframe)
        keyframe_layout.addWidget(self.remove_keyframe_btn)
        
        variable_layout.addLayout(keyframe_layout)
        
        # Keyframe list
        self.keyframe_list = QLabel("No keyframes")
        self.keyframe_list.setWordWrap(True)
        variable_layout.addWidget(self.keyframe_list)
        
        variable_group.setLayout(variable_layout)
        layout.addWidget(variable_group)
        
        # Frame interpolation
        interpolation_group = QGroupBox("Frame Interpolation")
        interpolation_layout = QVBoxLayout()
        
        self.interpolation_checkbox = QCheckBox("Enable Frame Interpolation")
        self.interpolation_checkbox.toggled.connect(self.on_interpolation_changed)
        interpolation_layout.addWidget(self.interpolation_checkbox)
        
        # Interpolation factor
        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Factor:"))
        
        self.interpolation_factor_spin = QDoubleSpinBox()
        self.interpolation_factor_spin.setRange(1.0, 10.0)
        self.interpolation_factor_spin.setValue(1.0)
        self.interpolation_factor_spin.setSuffix("x")
        self.interpolation_factor_spin.valueChanged.connect(self.on_interpolation_factor_changed)
        factor_layout.addWidget(self.interpolation_factor_spin)
        
        interpolation_layout.addLayout(factor_layout)
        
        interpolation_group.setLayout(interpolation_layout)
        layout.addWidget(interpolation_group)
        
        # Reset button
        reset_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Default")
        self.reset_btn.clicked.connect(self.reset_to_default)
        reset_layout.addWidget(self.reset_btn)
        
        reset_layout.addStretch()
        
        layout.addLayout(reset_layout)
        
        self.setLayout(layout)
    
    def set_pattern(self, pattern: Pattern):
        """Set pattern for speed control"""
        self.pattern = pattern
        
        if pattern:
            # Update keyframe range
            self.keyframe_spin.setRange(0, max(0, pattern.frame_count - 1))
            
            # Update keyframe list
            self.update_keyframe_list()
        else:
            self.keyframe_spin.setRange(0, 0)
            self.keyframe_list.setText("No keyframes")
    
    def on_speed_changed(self, value: int):
        """Handle speed slider change"""
        self.speed_multiplier = value / 100.0
        self.speed_label.setText(f"{self.speed_multiplier:.1f}x")
        
        # Update preset if not custom
        if self.preset_combo.currentText() != "Custom":
            self.preset_combo.setCurrentText("Custom")
        
        self.speed_changed.emit(self.speed_multiplier)
    
    def on_preset_changed(self, preset: str):
        """Handle preset change"""
        preset_speeds = {
            "Custom": None,
            "Very Slow (0.25x)": 0.25,
            "Slow (0.5x)": 0.5,
            "Normal (1.0x)": 1.0,
            "Fast (2.0x)": 2.0,
            "Very Fast (4.0x)": 4.0,
            "Ultra Fast (8.0x)": 8.0
        }
        
        if preset in preset_speeds and preset_speeds[preset] is not None:
            speed = preset_speeds[preset]
            self.speed_slider.setValue(int(speed * 100))
            self.speed_multiplier = speed
            self.speed_label.setText(f"{speed:.1f}x")
            self.speed_changed.emit(speed)
    
    def on_curve_changed(self, curve: str):
        """Handle curve change"""
        curve_map = {
            "Linear": "linear",
            "Ease In": "ease_in",
            "Ease Out": "ease_out",
            "Ease In-Out": "ease_in_out",
            "Ease In Quad": "ease_in_quad",
            "Ease Out Quad": "ease_out_quad",
            "Ease In-Out Quad": "ease_in_out_quad",
            "Ease In Cubic": "ease_in_cubic",
            "Ease Out Cubic": "ease_out_cubic",
            "Ease In-Out Cubic": "ease_in_out_cubic",
            "Bounce": "bounce",
            "Elastic": "elastic",
            "Back": "back"
        }
        
        self.speed_curve = curve_map.get(curve, "linear")
        self.curve_changed.emit(self.speed_curve)
    
    def on_variable_speed_changed(self, enabled: bool):
        """Handle variable speed toggle"""
        # Update keyframe controls
        self.keyframe_spin.setEnabled(enabled)
        self.keyframe_speed_spin.setEnabled(enabled)
        self.add_keyframe_btn.setEnabled(enabled)
        self.remove_keyframe_btn.setEnabled(enabled)
        
        if not enabled:
            self.speed_keyframes = []
            self.update_keyframe_list()
            self.keyframes_changed.emit([])
    
    def add_keyframe(self):
        """Add speed keyframe"""
        if not self.pattern:
            return
        
        frame = self.keyframe_spin.value()
        speed = self.keyframe_speed_spin.value()
        
        # Add or update keyframe
        self.speed_keyframes = [kf for kf in self.speed_keyframes if kf[0] != frame]
        self.speed_keyframes.append((frame, speed))
        self.speed_keyframes.sort()
        
        self.update_keyframe_list()
        self.keyframes_changed.emit(self.speed_keyframes)
    
    def remove_keyframe(self):
        """Remove speed keyframe"""
        frame = self.keyframe_spin.value()
        
        self.speed_keyframes = [kf for kf in self.speed_keyframes if kf[0] != frame]
        
        self.update_keyframe_list()
        self.keyframes_changed.emit(self.speed_keyframes)
    
    def update_keyframe_list(self):
        """Update keyframe list display"""
        if not self.speed_keyframes:
            self.keyframe_list.setText("No keyframes")
            return
        
        keyframe_text = "Keyframes:\n"
        for frame, speed in self.speed_keyframes:
            keyframe_text += f"Frame {frame}: {speed:.1f}x\n"
        
        self.keyframe_list.setText(keyframe_text.strip())
    
    def on_interpolation_changed(self, enabled: bool):
        """Handle interpolation toggle"""
        self.interpolation_enabled = enabled
        self.interpolation_factor_spin.setEnabled(enabled)
        
        self.interpolation_changed.emit(enabled, self.interpolation_factor)
    
    def on_interpolation_factor_changed(self, factor: float):
        """Handle interpolation factor change"""
        self.interpolation_factor = factor
        self.interpolation_changed.emit(self.interpolation_enabled, factor)
    
    def reset_to_default(self):
        """Reset all settings to default"""
        self.speed_slider.setValue(100)
        self.speed_multiplier = 1.0
        self.speed_label.setText("1.0x")
        
        self.curve_combo.setCurrentText("Linear")
        self.speed_curve = "linear"
        
        self.variable_checkbox.setChecked(False)
        self.speed_keyframes = []
        self.update_keyframe_list()
        
        self.interpolation_checkbox.setChecked(False)
        self.interpolation_enabled = False
        self.interpolation_factor = 1.0
        self.interpolation_factor_spin.setValue(1.0)
        
        self.preset_combo.setCurrentText("Normal (1.0x)")
        
        # Emit signals
        self.speed_changed.emit(1.0)
        self.curve_changed.emit("linear")
        self.keyframes_changed.emit([])
        self.interpolation_changed.emit(False, 1.0)
    
    def get_speed_settings(self) -> dict:
        """Get current speed settings"""
        return {
            'speed_multiplier': self.speed_multiplier,
            'speed_curve': self.speed_curve,
            'variable_speed': self.variable_checkbox.isChecked(),
            'speed_keyframes': self.speed_keyframes,
            'interpolation_enabled': self.interpolation_enabled,
            'interpolation_factor': self.interpolation_factor
        }
    
    def set_speed_settings(self, settings: dict):
        """Set speed settings"""
        if 'speed_multiplier' in settings:
            self.speed_slider.setValue(int(settings['speed_multiplier'] * 100))
            self.speed_multiplier = settings['speed_multiplier']
            self.speed_label.setText(f"{self.speed_multiplier:.1f}x")
        
        if 'speed_curve' in settings:
            curve_map = {v: k for k, v in {
                "Linear": "linear",
                "Ease In": "ease_in",
                "Ease Out": "ease_out",
                "Ease In-Out": "ease_in_out",
                "Ease In Quad": "ease_in_quad",
                "Ease Out Quad": "ease_out_quad",
                "Ease In-Out Quad": "ease_in_out_quad",
                "Ease In Cubic": "ease_in_cubic",
                "Ease Out Cubic": "ease_out_cubic",
                "Ease In-Out Cubic": "ease_in_out_cubic",
                "Bounce": "bounce",
                "Elastic": "elastic",
                "Back": "back"
            }.items()}
            
            curve_name = curve_map.get(settings['speed_curve'], "Linear")
            self.curve_combo.setCurrentText(curve_name)
            self.speed_curve = settings['speed_curve']
        
        if 'variable_speed' in settings:
            self.variable_checkbox.setChecked(settings['variable_speed'])
        
        if 'speed_keyframes' in settings:
            self.speed_keyframes = settings['speed_keyframes']
            self.update_keyframe_list()
        
        if 'interpolation_enabled' in settings:
            self.interpolation_checkbox.setChecked(settings['interpolation_enabled'])
            self.interpolation_enabled = settings['interpolation_enabled']
        
        if 'interpolation_factor' in settings:
            self.interpolation_factor_spin.setValue(settings['interpolation_factor'])
            self.interpolation_factor = settings['interpolation_factor']

