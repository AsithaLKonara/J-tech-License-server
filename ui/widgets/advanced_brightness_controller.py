"""
Advanced Brightness Controller Widget - Comprehensive brightness control
Complete PySide6 implementation with hardware-specific mapping
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QSlider, QSpinBox, QPushButton, QGroupBox,
                                QComboBox, QCheckBox, QDoubleSpinBox, QTabWidget,
                                QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import Pattern, BrightnessCurve, HardwareBrightnessMapper


class BrightnessCurveWidget(QWidget):
    """Widget for visualizing brightness curves"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.curve_type = "gamma_corrected"
        self.setMinimumSize(200, 150)
        self.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
    
    def set_curve_type(self, curve_type: str):
        """Set the curve type to display"""
        self.curve_type = curve_type
        self.update()
    
    def paintEvent(self, event):
        """Draw the brightness curve"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(42, 42, 42))
        
        # Draw grid
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        for i in range(0, self.width(), 20):
            painter.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 20):
            painter.drawLine(0, i, self.width(), i)
        
        # Draw curve
        painter.setPen(QPen(QColor(0, 255, 100), 2))
        
        # Get curve function
        curve_type = getattr(BrightnessCurve, self.curve_type.upper(), BrightnessCurve.GAMMA_CORRECTED)
        
        # Draw curve points
        points = []
        for x in range(self.width()):
            input_val = x / (self.width() - 1)
            # Apply curve function based on type
            if curve_type == BrightnessCurve.LINEAR:
                output_val = input_val
            elif curve_type == BrightnessCurve.GAMMA_CORRECTED:
                output_val = input_val ** 2.2
            elif curve_type == BrightnessCurve.LOGARITHMIC:
                output_val = math.log(1 + input_val * 9) / math.log(10)
            elif curve_type == BrightnessCurve.EXPONENTIAL:
                output_val = input_val ** 0.5
            elif curve_type == BrightnessCurve.S_CURVE:
                output_val = 0.5 * (1 + math.sin(math.pi * (input_val - 0.5)))
            else:
                output_val = input_val
            y = int((1.0 - output_val) * (self.height() - 1))
            points.append((x, y))
        
        # Draw curve line
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Draw axes labels
        painter.setPen(QPen(QColor(200, 200, 200)))
        painter.drawText(5, 15, "1.0")
        painter.drawText(5, self.height() - 5, "0.0")
        painter.drawText(self.width() - 25, self.height() - 5, "1.0")


class AdvancedBrightnessController(QWidget):
    """
    Advanced brightness control widget with hardware-specific mapping
    
    Features:
    - Hardware-specific brightness curves
    - Per-channel brightness control
    - Real-time curve visualization
    - LED type selection
    - Brightness presets
    """
    
    # Signals
    brightness_changed = Signal(float)  # Emitted when brightness changes
    curve_changed = Signal(str)  # Emitted when curve type changes
    led_type_changed = Signal(str)  # Emitted when LED type changes
    per_channel_changed = Signal(bool)  # Emitted when per-channel mode changes
    channel_brightness_changed = Signal(str, float)  # Emitted when channel brightness changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.current_brightness = 1.0
        self.current_curve = "gamma_corrected"
        self.current_led_type = "ws2812"
        self.per_channel_mode = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements with scroll area"""
        # Create scroll area for better responsiveness
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        self.content_widget = QWidget()
        layout = QVBoxLayout(self.content_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Basic brightness tab
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic")
        
        # Advanced tab
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")
        
        # Per-channel tab
        per_channel_tab = self.create_per_channel_tab()
        tab_widget.addTab(per_channel_tab, "Per-Channel")
        
        layout.addWidget(tab_widget)
        
        # Set up scroll area
        self.scroll_area.setWidget(self.content_widget)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.scroll_area)
    
    def create_basic_tab(self):
        """Create basic brightness control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Brightness slider
        brightness_group = QGroupBox("Brightness Control")
        brightness_layout = QVBoxLayout()
        
        # Main brightness slider
        brightness_slider_layout = QHBoxLayout()
        brightness_slider_layout.addWidget(QLabel("Brightness:"))
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_brightness_slider_changed)
        brightness_slider_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        self.brightness_label.setMinimumWidth(50)
        brightness_slider_layout.addWidget(self.brightness_label)
        
        brightness_layout.addLayout(brightness_slider_layout)
        
        # Brightness presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        
        for preset in [("25%", 0.25), ("50%", 0.5), ("75%", 0.75), ("100%", 1.0)]:
            btn = QPushButton(preset[0])
            btn.clicked.connect(lambda checked, val=preset[1]: self.set_brightness(val))
            presets_layout.addWidget(btn)
        
        brightness_layout.addLayout(presets_layout)
        brightness_group.setLayout(brightness_layout)
        layout.addWidget(brightness_group)
        
        # LED type selection
        led_group = QGroupBox("LED Type")
        led_layout = QHBoxLayout()
        led_layout.addWidget(QLabel("Chip Type:"))
        
        self.led_type_combo = QComboBox()
        self.led_type_combo.addItems([
            "ws2811", "ws2812", "ws2812b", "sk6812", "apa102",
            "apa102c", "dotstar", "neopixel", "generic"
        ])
        self.led_type_combo.currentTextChanged.connect(self.on_led_type_changed)
        led_layout.addWidget(self.led_type_combo)
        
        led_group.setLayout(led_layout)
        layout.addWidget(led_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self):
        """Create advanced brightness control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Brightness curve selection
        curve_group = QGroupBox("Brightness Curve")
        curve_layout = QVBoxLayout()
        
        curve_selection_layout = QHBoxLayout()
        curve_selection_layout.addWidget(QLabel("Curve Type:"))
        
        self.curve_combo = QComboBox()
        self.curve_combo.addItems([
            "linear", "gamma_corrected", "logarithmic", 
            "exponential", "s_curve"
        ])
        self.curve_combo.currentTextChanged.connect(self.on_curve_changed)
        curve_selection_layout.addWidget(self.curve_combo)
        
        curve_layout.addLayout(curve_selection_layout)
        
        # Curve visualization
        self.curve_widget = BrightnessCurveWidget()
        curve_layout.addWidget(self.curve_widget)
        
        curve_group.setLayout(curve_layout)
        layout.addWidget(curve_group)
        
        # Apply button
        apply_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply to Pattern")
        self.apply_button.clicked.connect(self.apply_to_pattern)
        apply_layout.addWidget(self.apply_button)
        
        layout.addLayout(apply_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_per_channel_tab(self):
        """Create per-channel brightness control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Enable per-channel mode
        enable_group = QGroupBox("Per-Channel Control")
        enable_layout = QHBoxLayout()
        
        self.per_channel_checkbox = QCheckBox("Enable Per-Channel Brightness")
        self.per_channel_checkbox.toggled.connect(self.on_per_channel_toggled)
        enable_layout.addWidget(self.per_channel_checkbox)
        
        enable_group.setLayout(enable_layout)
        layout.addWidget(enable_group)
        
        # Channel controls
        self.channel_group = QGroupBox("Channel Brightness")
        channel_layout = QVBoxLayout()
        
        # Red channel
        red_layout = QHBoxLayout()
        red_layout.addWidget(QLabel("Red:"))
        
        self.red_slider = QSlider(Qt.Horizontal)
        self.red_slider.setRange(0, 100)
        self.red_slider.setValue(100)
        self.red_slider.valueChanged.connect(lambda v: self.on_channel_changed("red", v))
        red_layout.addWidget(self.red_slider)
        
        self.red_label = QLabel("100%")
        self.red_label.setMinimumWidth(50)
        red_layout.addWidget(self.red_label)
        
        channel_layout.addLayout(red_layout)
        
        # Green channel
        green_layout = QHBoxLayout()
        green_layout.addWidget(QLabel("Green:"))
        
        self.green_slider = QSlider(Qt.Horizontal)
        self.green_slider.setRange(0, 100)
        self.green_slider.setValue(100)
        self.green_slider.valueChanged.connect(lambda v: self.on_channel_changed("green", v))
        green_layout.addWidget(self.green_slider)
        
        self.green_label = QLabel("100%")
        self.green_label.setMinimumWidth(50)
        green_layout.addWidget(self.green_label)
        
        channel_layout.addLayout(green_layout)
        
        # Blue channel
        blue_layout = QHBoxLayout()
        blue_layout.addWidget(QLabel("Blue:"))
        
        self.blue_slider = QSlider(Qt.Horizontal)
        self.blue_slider.setRange(0, 100)
        self.blue_slider.setValue(100)
        self.blue_slider.valueChanged.connect(lambda v: self.on_channel_changed("blue", v))
        blue_layout.addWidget(self.blue_slider)
        
        self.blue_label = QLabel("100%")
        self.blue_label.setMinimumWidth(50)
        blue_layout.addWidget(self.blue_label)
        
        channel_layout.addLayout(blue_layout)
        
        self.channel_group.setLayout(channel_layout)
        self.channel_group.setEnabled(False)
        layout.addWidget(self.channel_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def set_pattern(self, pattern: Pattern):
        """Load pattern and update controls"""
        self.pattern = pattern
        
        if pattern:
            # Update brightness
            brightness = pattern.metadata.brightness
            self.set_brightness(brightness)
            
            # Update curve
            self.curve_combo.setCurrentText(pattern.metadata.brightness_curve)
            self.current_curve = pattern.metadata.brightness_curve
            
            # Update LED type
            led_type = getattr(pattern.metadata, 'led_type', 'ws2812')
            self.led_type_combo.setCurrentText(led_type)
            self.current_led_type = led_type
            
            # Update per-channel settings
            per_channel = getattr(pattern.metadata, 'per_channel_brightness', False)
            self.per_channel_checkbox.setChecked(per_channel)
            self.per_channel_mode = per_channel
            
            # Update channel sliders
            red_brightness = getattr(pattern.metadata, 'red_brightness', 1.0)
            green_brightness = getattr(pattern.metadata, 'green_brightness', 1.0)
            blue_brightness = getattr(pattern.metadata, 'blue_brightness', 1.0)
            self.red_slider.setValue(int(red_brightness * 100))
            self.green_slider.setValue(int(green_brightness * 100))
            self.blue_slider.setValue(int(blue_brightness * 100))
            
            self.update_labels()
    
    def set_brightness(self, brightness: float):
        """Set brightness value"""
        self.current_brightness = max(0.0, min(1.0, brightness))
        
        # Update slider
        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(int(self.current_brightness * 100))
        self.brightness_slider.blockSignals(False)
        
        self.update_labels()
        self.brightness_changed.emit(self.current_brightness)
    
    def on_brightness_slider_changed(self, value: int):
        """Brightness slider changed"""
        brightness = value / 100.0
        self.set_brightness(brightness)
    
    def on_curve_changed(self, curve_type: str):
        """Curve type changed"""
        self.current_curve = curve_type
        self.curve_widget.set_curve_type(curve_type)
        self.curve_changed.emit(curve_type)
    
    def on_led_type_changed(self, led_type: str):
        """LED type changed"""
        self.current_led_type = led_type
        self.led_type_changed.emit(led_type)
    
    def on_per_channel_toggled(self, enabled: bool):
        """Per-channel mode toggled"""
        self.per_channel_mode = enabled
        self.channel_group.setEnabled(enabled)
        self.per_channel_changed.emit(enabled)
    
    def set_curve_type(self, curve_type: str):
        """Set the brightness curve type"""
        if curve_type in [self.curve_combo.itemText(i) for i in range(self.curve_combo.count())]:
            self.curve_combo.setCurrentText(curve_type)
            self.curve_widget.set_curve_type(curve_type)
            self.current_curve = curve_type
    
    def set_led_type(self, led_type: str):
        """Set the LED type"""
        if led_type in [self.led_type_combo.itemText(i) for i in range(self.led_type_combo.count())]:
            self.led_type_combo.setCurrentText(led_type)
            self.current_led_type = led_type
    
    def set_per_channel_mode(self, enabled: bool):
        """Enable/disable per-channel brightness control"""
        self.per_channel_checkbox.setChecked(enabled)
        self.per_channel_mode = enabled
        self.channel_group.setVisible(enabled)

    def on_channel_changed(self, channel: str, value: int):
        """Channel brightness changed"""
        brightness = value / 100.0
        
        if channel == "red":
            self.red_label.setText(f"{value}%")
        elif channel == "green":
            self.green_label.setText(f"{value}%")
        elif channel == "blue":
            self.blue_label.setText(f"{value}%")
        
        self.channel_brightness_changed.emit(channel, brightness)
    
    def update_labels(self):
        """Update all labels"""
        self.brightness_label.setText(f"{int(self.current_brightness * 100)}%")
    
    def apply_to_pattern(self):
        """Apply current settings to pattern (non-destructive)"""
        if not self.pattern:
            return
        
        # Update metadata only (non-destructive)
        self.pattern.metadata.brightness = self.current_brightness
        self.pattern.metadata.brightness_curve = self.current_curve
        self.pattern.metadata.led_type = self.current_led_type
        
        # Update per-channel settings if enabled
        if self.per_channel_mode:
            self.pattern.metadata.per_channel_brightness = True
            self.pattern.metadata.red_brightness = self.red_slider.value() / 100.0
            self.pattern.metadata.green_brightness = self.green_slider.value() / 100.0
            self.pattern.metadata.blue_brightness = self.blue_slider.value() / 100.0
        else:
            self.pattern.metadata.per_channel_brightness = False
    
    def get_current_settings(self) -> dict:
        """Get current brightness settings"""
        return {
            "brightness": self.current_brightness,
            "curve_type": self.current_curve,
            "led_type": self.current_led_type,
            "per_channel": self.per_channel_mode,
            "red_brightness": self.red_slider.value() / 100.0,
            "green_brightness": self.green_slider.value() / 100.0,
            "blue_brightness": self.blue_slider.value() / 100.0
        }
