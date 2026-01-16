"""
Pixel Mapping Widget - Configure and preview non-standard wiring patterns
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal

from core.wiring_mapper import WiringMapper


class PixelMappingWidget(QWidget):
    """
    Widget for configuring pixel mapping (wiring patterns).
    
    Allows users to configure:
    - Wiring mode (Row-major, Serpentine, Column-major, Column-serpentine)
    - Data-in corner (LT, LB, RT, RB)
    - Flip X/Y transformations
    """
    
    mapping_changed = Signal()  # Emitted when mapping configuration changes
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._width = 16
        self._height = 16
        self._wiring_mode = "Row-major"
        self._data_in_corner = "LT"
        self._flip_x = False
        self._flip_y = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Pixel Mapping Configuration")
        title.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title)
        
        # Wiring mode
        wiring_group = QGroupBox("Wiring Pattern")
        wiring_layout = QFormLayout()
        
        self.wiring_mode_combo = QComboBox()
        self.wiring_mode_combo.addItems([
            "Row-major",
            "Serpentine",
            "Column-major",
            "Column-serpentine"
        ])
        self.wiring_mode_combo.setCurrentText(self._wiring_mode)
        self.wiring_mode_combo.currentTextChanged.connect(self._on_wiring_mode_changed)
        wiring_layout.addRow("Wiring Mode:", self.wiring_mode_combo)
        
        self.data_in_combo = QComboBox()
        self.data_in_combo.addItems([
            "Left Top (LT)",
            "Left Bottom (LB)",
            "Right Top (RT)",
            "Right Bottom (RB)"
        ])
        self.data_in_combo.setCurrentIndex(0)  # LT
        self.data_in_combo.currentIndexChanged.connect(self._on_data_in_changed)
        wiring_layout.addRow("Data In Corner:", self.data_in_combo)
        
        wiring_group.setLayout(wiring_layout)
        layout.addWidget(wiring_group)
        
        # Transformations
        transform_group = QGroupBox("Transformations")
        transform_layout = QVBoxLayout()
        
        self.flip_x_checkbox = QCheckBox("Flip Horizontal (Mirror X)")
        self.flip_x_checkbox.setChecked(self._flip_x)
        self.flip_x_checkbox.toggled.connect(self._on_flip_x_changed)
        transform_layout.addWidget(self.flip_x_checkbox)
        
        self.flip_y_checkbox = QCheckBox("Flip Vertical (Mirror Y)")
        self.flip_y_checkbox.setChecked(self._flip_y)
        self.flip_y_checkbox.toggled.connect(self._on_flip_y_changed)
        transform_layout.addWidget(self.flip_y_checkbox)
        
        transform_group.setLayout(transform_layout)
        layout.addWidget(transform_group)
        
        # Info label
        self.info_label = QLabel("Configure how pixels are mapped from design order to hardware strip order.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
    
    def set_matrix_size(self, width: int, height: int):
        """Update matrix dimensions."""
        self._width = width
        self._height = height
        self._update_info()
    
    def get_mapper(self) -> WiringMapper:
        """Get WiringMapper instance with current configuration."""
        return WiringMapper(
            width=self._width,
            height=self._height,
            wiring_mode=self._wiring_mode,
            data_in_corner=self._data_in_corner,
            flip_x=self._flip_x,
            flip_y=self._flip_y
        )
    
    def get_config(self) -> dict:
        """Get current configuration as dictionary."""
        return {
            "wiring_mode": self._wiring_mode,
            "data_in_corner": self._data_in_corner,
            "flip_x": self._flip_x,
            "flip_y": self._flip_y,
        }
    
    def set_config(self, config: dict):
        """Set configuration from dictionary."""
        self._wiring_mode = config.get("wiring_mode", "Row-major")
        self._data_in_corner = config.get("data_in_corner", "LT")
        self._flip_x = config.get("flip_x", False)
        self._flip_y = config.get("flip_y", False)
        
        # Update UI
        self.wiring_mode_combo.setCurrentText(self._wiring_mode)
        corner_map = {"LT": 0, "LB": 1, "RT": 2, "RB": 3}
        self.data_in_combo.setCurrentIndex(corner_map.get(self._data_in_corner, 0))
        self.flip_x_checkbox.setChecked(self._flip_x)
        self.flip_y_checkbox.setChecked(self._flip_y)
    
    def _on_wiring_mode_changed(self, mode: str):
        """Handle wiring mode change."""
        self._wiring_mode = mode
        self._update_info()
        self.mapping_changed.emit()
    
    def _on_data_in_changed(self, index: int):
        """Handle data-in corner change."""
        corner_map = {0: "LT", 1: "LB", 2: "RT", 3: "RB"}
        self._data_in_corner = corner_map.get(index, "LT")
        self._update_info()
        self.mapping_changed.emit()
    
    def _on_flip_x_changed(self, checked: bool):
        """Handle flip X change."""
        self._flip_x = checked
        self.mapping_changed.emit()
    
    def _on_flip_y_changed(self, checked: bool):
        """Handle flip Y change."""
        self._flip_y = checked
        self.mapping_changed.emit()
    
    def _update_info(self):
        """Update info label with current configuration."""
        mapper = self.get_mapper()
        info = f"Wiring: {self._wiring_mode}, Data In: {self._data_in_corner}"
        if self._flip_x or self._flip_y:
            flips = []
            if self._flip_x:
                flips.append("X")
            if self._flip_y:
                flips.append("Y")
            info += f", Flip: {', '.join(flips)}"
        self.info_label.setText(info)

