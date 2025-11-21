"""
New Pattern Dialog - Create a new LED matrix pattern with configuration options.
"""

from __future__ import annotations

import os
import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QButtonGroup, QRadioButton, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class NewPatternDialog(QDialog):
    """Dialog for creating a new pattern with matrix dimensions and LED type."""
    
    def __init__(self, parent=None, default_width: int = 12, default_height: int = 6):
        super().__init__(parent)
        self.setWindowTitle("New Pattern")
        self.setModal(True)
        self.resize(400, 250)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Matrix dimensions
        dims_group = QGroupBox("Matrix Dimensions")
        dims_layout = QFormLayout()
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(default_width)
        self.width_spin.setToolTip("Matrix width in pixels (1-256)")
        dims_layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(default_height)
        self.height_spin.setToolTip("Matrix height in pixels (1-256)")
        dims_layout.addRow("Height:", self.height_spin)
        
        dims_group.setLayout(dims_layout)
        layout.addWidget(dims_group)
        
        # LED type
        led_group = QGroupBox("LED Type")
        led_layout = QVBoxLayout()
        
        self.led_type_group = QButtonGroup(self)
        
        self.rgb_radio = QRadioButton("RGB (Red-Green-Blue)")
        self.rgb_radio.setChecked(True)
        self.led_type_group.addButton(self.rgb_radio, 0)
        led_layout.addWidget(self.rgb_radio)
        
        self.grb_radio = QRadioButton("GRB (Green-Red-Blue)")
        self.led_type_group.addButton(self.grb_radio, 1)
        led_layout.addWidget(self.grb_radio)
        
        self.single_color_radio = QRadioButton("Single Color (White only)")
        self.led_type_group.addButton(self.single_color_radio, 2)
        led_layout.addWidget(self.single_color_radio)
        
        led_group.setLayout(led_layout)
        layout.addWidget(led_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create")
        create_btn.setDefault(True)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def get_width(self) -> int:
        """Get selected matrix width."""
        return self.width_spin.value()
    
    def get_height(self) -> int:
        """Get selected matrix height."""
        return self.height_spin.value()
    
    def get_led_type(self) -> str:
        """Get selected LED type: 'RGB', 'GRB', or 'SINGLE'."""
        if self.single_color_radio.isChecked():
            return "SINGLE"
        elif self.grb_radio.isChecked():
            return "GRB"
        else:
            return "RGB"
    
    def is_single_color(self) -> bool:
        """Check if single color mode is selected."""
        return self.single_color_radio.isChecked()

