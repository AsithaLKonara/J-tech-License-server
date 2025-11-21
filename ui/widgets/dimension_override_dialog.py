"""
Dimension Override Dialog - Allow users to manually set pattern dimensions
"""

import logging
from typing import Optional, Tuple

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSpinBox, QGroupBox, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class DimensionOverrideDialog(QDialog):
    """Dialog for manually setting pattern dimensions"""
    
    def __init__(self, parent=None, current_width: int = 1, current_height: int = 1, 
                 led_count: int = 1, auto_detected: Optional[Tuple[int, int]] = None):
        super().__init__(parent)
        self.setWindowTitle("Override Pattern Dimensions")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.current_width = current_width
        self.current_height = current_height
        self.led_count = led_count
        self.auto_detected = auto_detected
        self.result_dimensions: Optional[Tuple[int, int]] = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create UI elements"""
        layout = QVBoxLayout(self)
        
        # Info
        info_label = QLabel(
            f"Current LED count: {self.led_count}\n"
            f"Current dimensions: {self.current_width}×{self.current_height}"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        if self.auto_detected:
            auto_label = QLabel(
                f"Auto-detected: {self.auto_detected[0]}×{self.auto_detected[1]}"
            )
            auto_label.setStyleSheet("color: #00ff88;")
            layout.addWidget(auto_label)
        
        # Dimension inputs
        dim_group = QGroupBox("Set Dimensions")
        dim_layout = QVBoxLayout()
        
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setMinimum(1)
        self.width_spin.setMaximum(10000)
        self.width_spin.setValue(self.current_width)
        self.width_spin.valueChanged.connect(self.on_dimension_changed)
        width_layout.addWidget(self.width_spin)
        width_layout.addStretch()
        dim_layout.addLayout(width_layout)
        
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setMinimum(1)
        self.height_spin.setMaximum(10000)
        self.height_spin.setValue(self.current_height)
        self.height_spin.valueChanged.connect(self.on_dimension_changed)
        height_layout.addWidget(self.height_spin)
        height_layout.addStretch()
        dim_layout.addLayout(height_layout)
        
        # Validation label
        self.validation_label = QLabel()
        self.validation_label.setWordWrap(True)
        self.on_dimension_changed()  # Initial validation
        dim_layout.addWidget(self.validation_label)
        
        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)
        
        # Use auto-detected button
        if self.auto_detected:
            auto_button = QPushButton(f"Use Auto-Detected ({self.auto_detected[0]}×{self.auto_detected[1]})")
            auto_button.clicked.connect(self.use_auto_detected)
            layout.addWidget(auto_button)
        
        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.persist_checkbox = QCheckBox("Remember this override for future loads")
        self.persist_checkbox.setChecked(True)
        options_layout.addWidget(self.persist_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_override)
        apply_button.setDefault(True)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
    
    def on_dimension_changed(self):
        """Validate dimensions when changed"""
        width = self.width_spin.value()
        height = self.height_spin.value()
        product = width * height
        
        # Suggest common dimensions if close
        suggestions = []
        if product != self.led_count:
            # Try to find close matches
            common_dims = [
                (1, self.led_count),  # Strip
                (self.led_count, 1),   # Reverse strip
            ]
            # Add square-ish options
            import math
            sqrt_leds = int(math.sqrt(self.led_count))
            for w in range(max(1, sqrt_leds - 5), sqrt_leds + 6):
                h = self.led_count // w
                if w * h == self.led_count:
                    common_dims.append((w, h))
            
            # Find closest match
            closest = min(common_dims, key=lambda d: abs(d[0] * d[1] - product))
            if closest[0] * closest[1] == self.led_count:
                suggestions.append(f"Try {closest[0]}×{closest[1]}")
        
        if product == self.led_count:
            self.validation_label.setText(
                f"✓ Valid: {width}×{height} = {product} LEDs"
            )
            self.validation_label.setStyleSheet("color: #00ff88;")
        elif product < self.led_count:
            msg = f"⚠ Too small: {width}×{height} = {product} LEDs (need {self.led_count})"
            if suggestions:
                msg += f"\n💡 {suggestions[0]}"
            self.validation_label.setText(msg)
            self.validation_label.setStyleSheet("color: #ffb347;")
        else:
            msg = f"⚠ Too large: {width}×{height} = {product} LEDs (have {self.led_count})"
            if suggestions:
                msg += f"\n💡 {suggestions[0]}"
            self.validation_label.setText(msg)
            self.validation_label.setStyleSheet("color: #ffb347;")
    
    def use_auto_detected(self):
        """Use auto-detected dimensions"""
        if self.auto_detected:
            self.width_spin.setValue(self.auto_detected[0])
            self.height_spin.setValue(self.auto_detected[1])
    
    def apply_override(self):
        """Apply dimension override"""
        width = self.width_spin.value()
        height = self.height_spin.value()
        product = width * height
        
        if product != self.led_count:
            reply = QMessageBox.question(
                self,
                "Dimension Mismatch",
                f"Dimensions {width}×{height} = {product} LEDs, but pattern has {self.led_count} LEDs.\n"
                "This may cause display issues. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.result_dimensions = (width, height)
        self.result_persist = self.persist_checkbox.isChecked()
        self.accept()
    
    def get_result(self) -> Tuple[Optional[Tuple[int, int]], bool]:
        """
        Get dialog result.
        
        Returns:
            Tuple of (dimensions, persist) or (None, False) if cancelled
        """
        if self.result_dimensions:
            return (self.result_dimensions, self.result_persist)
        return (None, False)

