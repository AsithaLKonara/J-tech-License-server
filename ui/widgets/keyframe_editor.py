"""
Keyframe Editor Widget - UI for editing keyframe animations.
"""

from __future__ import annotations

from typing import Optional, List, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QColorDialog, QGroupBox, QListWidget,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from domain.animation.keyframe import Keyframe, KeyframeType
from domain.animation.animation_curve import CurveType


class KeyframeEditorWidget(QWidget):
    """Widget for editing keyframe animations."""
    
    keyframe_changed = Signal()  # Emitted when keyframes change
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._keyframes: List[Keyframe] = []
        self._current_frame = 0
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Keyframe type selection
        type_group = QGroupBox("Keyframe Type")
        type_layout = QHBoxLayout()
        self.keyframe_type_combo = QComboBox()
        self.keyframe_type_combo.addItems([
            "Color", "Position", "Scale", "Rotation", "Opacity"
        ])
        type_layout.addWidget(QLabel("Type:"))
        type_layout.addWidget(self.keyframe_type_combo)
        type_layout.addStretch()
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Current frame
        frame_group = QGroupBox("Frame")
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("Frame:"))
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(0, 9999)
        self.frame_spin.setValue(0)
        self.frame_spin.valueChanged.connect(self._on_frame_changed)
        frame_layout.addWidget(self.frame_spin)
        frame_layout.addStretch()
        frame_group.setLayout(frame_layout)
        layout.addWidget(frame_group)
        
        # Keyframe value editor
        value_group = QGroupBox("Value")
        value_layout = QVBoxLayout()
        
        # Color picker (for color keyframes)
        self.color_button = QPushButton("Select Color")
        self.color_button.clicked.connect(self._on_color_clicked)
        self.color_button.setStyleSheet("background-color: rgb(255, 255, 255);")
        value_layout.addWidget(self.color_button)
        
        # Numeric value (for other keyframes)
        numeric_layout = QHBoxLayout()
        numeric_layout.addWidget(QLabel("Value:"))
        self.value_spin = QSpinBox()
        self.value_spin.setRange(0, 1000)
        self.value_spin.setValue(100)
        numeric_layout.addWidget(self.value_spin)
        numeric_layout.addStretch()
        value_layout.addLayout(numeric_layout)
        
        value_group.setLayout(value_layout)
        layout.addWidget(value_group)
        
        # Curve selection
        curve_group = QGroupBox("Interpolation Curve")
        curve_layout = QHBoxLayout()
        curve_layout.addWidget(QLabel("Curve:"))
        self.curve_combo = QComboBox()
        self.curve_combo.addItems([
            "Linear", "Ease In", "Ease Out", "Ease In Out",
            "Ease In Quad", "Ease Out Quad", "Ease In Out Quad",
            "Ease In Cubic", "Ease Out Cubic", "Ease In Out Cubic",
            "Bounce", "Elastic"
        ])
        curve_layout.addWidget(self.curve_combo)
        curve_layout.addStretch()
        curve_group.setLayout(curve_layout)
        layout.addWidget(curve_group)
        
        # Keyframe list
        list_group = QGroupBox("Keyframes")
        list_layout = QVBoxLayout()
        self.keyframe_list = QListWidget()
        self.keyframe_list.itemSelectionChanged.connect(self._on_keyframe_selected)
        list_layout.addWidget(self.keyframe_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.add_keyframe_btn = QPushButton("Add Keyframe")
        self.add_keyframe_btn.clicked.connect(self._on_add_keyframe)
        self.remove_keyframe_btn = QPushButton("Remove Keyframe")
        self.remove_keyframe_btn.clicked.connect(self._on_remove_keyframe)
        button_layout.addWidget(self.add_keyframe_btn)
        button_layout.addWidget(self.remove_keyframe_btn)
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        layout.addStretch()
        
        self._update_ui()
    
    def _on_frame_changed(self, value: int):
        """Handle frame number change."""
        self._current_frame = value
        self._update_ui()
    
    def _on_color_clicked(self):
        """Handle color button click."""
        current_color = QColor(255, 255, 255)
        color = QColorDialog.getColor(current_color, self, "Select Color")
        if color.isValid():
            rgb = (color.red(), color.green(), color.blue())
            self.color_button.setStyleSheet(f"background-color: rgb{rgb};")
    
    def _on_keyframe_selected(self):
        """Handle keyframe selection."""
        items = self.keyframe_list.selectedItems()
        if items:
            item = items[0]
            keyframe = item.data(Qt.UserRole)
            if keyframe:
                self.frame_spin.setValue(keyframe.frame_index)
                self.keyframe_type_combo.setCurrentText(keyframe.keyframe_type.value.title())
                self.curve_combo.setCurrentText(keyframe.curve_type.replace("_", " ").title())
                if keyframe.keyframe_type == KeyframeType.COLOR:
                    self.color_button.setStyleSheet(f"background-color: rgb{keyframe.value};")
    
    def _on_add_keyframe(self):
        """Add a new keyframe."""
        frame_index = self.frame_spin.value()
        keyframe_type_str = self.keyframe_type_combo.currentText().lower()
        
        # Map UI string to KeyframeType
        type_map = {
            "color": KeyframeType.COLOR,
            "position": KeyframeType.POSITION,
            "scale": KeyframeType.SCALE,
            "rotation": KeyframeType.ROTATION,
            "opacity": KeyframeType.OPACITY,
        }
        keyframe_type = type_map.get(keyframe_type_str, KeyframeType.CUSTOM)
        
        # Get value
        if keyframe_type == KeyframeType.COLOR:
            color_str = self.color_button.styleSheet()
            # Extract RGB from style sheet
            import re
            match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
            if match:
                value = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
            else:
                value = (255, 255, 255)
        else:
            value = self.value_spin.value()
        
        # Get curve
        curve_str = self.curve_combo.currentText().lower().replace(" ", "_")
        
        keyframe = Keyframe(
            frame_index=frame_index,
            keyframe_type=keyframe_type,
            value=value,
            curve_type=curve_str
        )
        
        # Remove existing keyframe at same frame and type
        self._keyframes = [
            kf for kf in self._keyframes
            if not (kf.frame_index == frame_index and kf.keyframe_type == keyframe_type)
        ]
        
        self._keyframes.append(keyframe)
        self._keyframes.sort(key=lambda kf: kf.frame_index)
        self._update_keyframe_list()
        self.keyframe_changed.emit()
    
    def _on_remove_keyframe(self):
        """Remove selected keyframe."""
        items = self.keyframe_list.selectedItems()
        if not items:
            return
        
        item = items[0]
        keyframe = item.data(Qt.UserRole)
        if keyframe:
            self._keyframes = [
                kf for kf in self._keyframes
                if not (kf.frame_index == keyframe.frame_index and kf.keyframe_type == keyframe.keyframe_type)
            ]
            self._update_keyframe_list()
            self.keyframe_changed.emit()
    
    def _update_keyframe_list(self):
        """Update the keyframe list widget."""
        self.keyframe_list.clear()
        for kf in self._keyframes:
            item_text = f"Frame {kf.frame_index}: {kf.keyframe_type.value} = {kf.value}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, kf)
            self.keyframe_list.addItem(item)
    
    def _update_ui(self):
        """Update UI based on current state."""
        # Show/hide appropriate value editor
        keyframe_type_str = self.keyframe_type_combo.currentText().lower()
        is_color = keyframe_type_str == "color"
        self.color_button.setVisible(is_color)
        self.value_spin.setVisible(not is_color)
    
    def get_keyframes(self) -> List[Keyframe]:
        """Get all keyframes."""
        return self._keyframes.copy()
    
    def set_keyframes(self, keyframes: List[Keyframe]):
        """Set keyframes."""
        self._keyframes = keyframes.copy()
        self._keyframes.sort(key=lambda kf: kf.frame_index)
        self._update_keyframe_list()

