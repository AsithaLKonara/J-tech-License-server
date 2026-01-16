"""
LED Color Panel - Widget for LED-specific color adjustments

Provides brightness control, gamma correction, LED-safe color palette,
and color temperature adjustment for accurate LED matrix design.
"""

from __future__ import annotations

from typing import Optional, Tuple, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QComboBox,
    QPushButton,
    QGridLayout,
    QGroupBox,
    QCheckBox,
)
from PySide6.QtGui import QColor, QPalette

RGB = Tuple[int, int, int]


class LEDColorPanel(QWidget):
    """
    LED Color Panel widget for adjusting colors for LED displays.
    
    Features:
    - Brightness slider (0-100%)
    - Gamma correction (2.2, 2.5, 3.0)
    - LED-safe color palette
    - Color temperature adjustment (warm/cool)
    - Preview on LED mode toggle
    """
    
    # Signals emitted when color settings change
    brightness_changed = Signal(int)  # 0-100
    gamma_changed = Signal(float)  # 2.2, 2.5, 3.0
    color_selected = Signal(tuple)  # (r, g, b)
    color_temperature_changed = Signal(float)  # -1.0 (cool) to 1.0 (warm)
    preview_mode_changed = Signal(bool)  # True = preview on LED mode
    
    # LED-safe color palette (optimized for LED displays)
    LED_SAFE_COLORS: List[RGB] = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 255, 0),    # Yellow
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
        (255, 128, 0),    # Orange
        (255, 0, 128),    # Pink
        (128, 0, 255),    # Purple
        (0, 128, 255),    # Light Blue
        (128, 255, 0),    # Lime
        (255, 192, 128),  # Peach
        (192, 255, 192),  # Light Green
        (192, 192, 255),  # Light Blue
        (255, 255, 255),  # White
        (128, 128, 128),  # Gray
    ]
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._brightness = 100
        self._gamma = 2.2
        self._color_temperature = 0.0  # 0 = neutral, -1 = cool, +1 = warm
        self._preview_on_led = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Brightness control
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QVBoxLayout()
        
        brightness_row = QHBoxLayout()
        brightness_row.addWidget(QLabel("Brightness:"))
        self.brightness_label = QLabel("100%")
        brightness_row.addWidget(self.brightness_label)
        brightness_row.addStretch()
        brightness_layout.addLayout(brightness_row)
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setToolTip("Adjust brightness (0-100%)")
        self.brightness_slider.valueChanged.connect(self._on_brightness_changed)
        brightness_layout.addWidget(self.brightness_slider)
        
        brightness_group.setLayout(brightness_layout)
        layout.addWidget(brightness_group)
        
        # Gamma correction
        gamma_group = QGroupBox("Gamma Correction")
        gamma_layout = QVBoxLayout()
        
        gamma_row = QHBoxLayout()
        gamma_row.addWidget(QLabel("Gamma:"))
        self.gamma_combo = QComboBox()
        self.gamma_combo.addItems(["2.2 (Standard)", "2.5 (LED)", "3.0 (High Contrast)"])
        self.gamma_combo.setCurrentIndex(0)
        self.gamma_combo.setToolTip("Gamma correction for LED color accuracy")
        self.gamma_combo.currentIndexChanged.connect(self._on_gamma_changed)
        gamma_row.addWidget(self.gamma_combo)
        gamma_layout.addLayout(gamma_row)
        
        gamma_group.setLayout(gamma_layout)
        layout.addWidget(gamma_group)
        
        # Color temperature
        temp_group = QGroupBox("Color Temperature")
        temp_layout = QVBoxLayout()
        
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("Temperature:"))
        self.temp_label = QLabel("Neutral")
        temp_row.addWidget(self.temp_label)
        temp_row.addStretch()
        temp_layout.addLayout(temp_row)
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(-100, 100)
        self.temp_slider.setValue(0)
        self.temp_slider.setToolTip("Color temperature: Cool (left) to Warm (right)")
        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        temp_layout.addWidget(self.temp_slider)
        
        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)
        
        # LED-safe palette
        palette_group = QGroupBox("LED-Safe Colors")
        palette_layout = QGridLayout()
        palette_layout.setSpacing(4)
        
        self.palette_buttons: List[QPushButton] = []
        for i, color in enumerate(self.LED_SAFE_COLORS):
            btn = QPushButton()
            btn.setFixedSize(32, 32)
            btn.setToolTip(f"RGB{color}")
            btn.setStyleSheet(f"background-color: rgb{color}; border: 1px solid #666;")
            btn.clicked.connect(lambda checked, c=color: self._on_palette_color_clicked(c))
            row = i // 4
            col = i % 4
            palette_layout.addWidget(btn, row, col)
            self.palette_buttons.append(btn)
        
        palette_group.setLayout(palette_layout)
        layout.addWidget(palette_group)
        
        # Preview mode
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_checkbox = QCheckBox("Preview on LED")
        self.preview_checkbox.setToolTip("Simulate LED color rendering in preview")
        self.preview_checkbox.toggled.connect(self._on_preview_mode_toggled)
        preview_layout.addWidget(self.preview_checkbox)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        layout.addStretch()
    
    def _on_brightness_changed(self, value: int):
        """Handle brightness slider change."""
        self._brightness = value
        self.brightness_label.setText(f"{value}%")
        self.brightness_changed.emit(value)
    
    def _on_gamma_changed(self, index: int):
        """Handle gamma combo change."""
        gamma_values = [2.2, 2.5, 3.0]
        self._gamma = gamma_values[index]
        self.gamma_changed.emit(self._gamma)
    
    def _on_temp_changed(self, value: int):
        """Handle color temperature slider change."""
        self._color_temperature = value / 100.0  # Normalize to -1.0 to 1.0
        
        if value < -50:
            self.temp_label.setText("Cool")
        elif value > 50:
            self.temp_label.setText("Warm")
        else:
            self.temp_label.setText("Neutral")
        
        self.color_temperature_changed.emit(self._color_temperature)
    
    def _on_palette_color_clicked(self, color: RGB):
        """Handle LED-safe palette color click."""
        self.color_selected.emit(color)
    
    def _on_preview_mode_toggled(self, checked: bool):
        """Handle preview mode checkbox toggle."""
        self._preview_on_led = checked
        self.preview_mode_changed.emit(checked)
    
    def apply_led_transform(self, r: int, g: int, b: int) -> RGB:
        """
        Apply LED color transformations to RGB values.
        
        Args:
            r, g, b: Original RGB values (0-255)
        
        Returns:
            Transformed RGB tuple
        """
        # Apply brightness
        brightness_factor = self._brightness / 100.0
        r = int(r * brightness_factor)
        g = int(g * brightness_factor)
        b = int(b * brightness_factor)
        
        # Apply gamma correction
        gamma_factor = 1.0 / self._gamma
        r = int(255 * ((r / 255.0) ** gamma_factor))
        g = int(255 * ((g / 255.0) ** gamma_factor))
        b = int(255 * ((b / 255.0) ** gamma_factor))
        
        # Apply color temperature
        if self._color_temperature > 0:  # Warm
            # Increase red, decrease blue
            r = min(255, int(r + self._color_temperature * 30))
            b = max(0, int(b - self._color_temperature * 30))
        elif self._color_temperature < 0:  # Cool
            # Decrease red, increase blue
            r = max(0, int(r + self._color_temperature * 30))
            b = min(255, int(b - self._color_temperature * 30))
        
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
    
    def get_brightness(self) -> int:
        """Get current brightness (0-100)."""
        return self._brightness
    
    def get_gamma(self) -> float:
        """Get current gamma value."""
        return self._gamma
    
    def get_color_temperature(self) -> float:
        """Get current color temperature (-1.0 to 1.0)."""
        return self._color_temperature
    
    def is_preview_mode(self) -> bool:
        """Check if preview on LED mode is enabled."""
        return self._preview_on_led

