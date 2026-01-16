"""
Advanced Speed Controller Widget - Comprehensive pattern speed control
Complete PySide6 implementation with interpolation and easing
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QSlider, QSpinBox, QPushButton, QGroupBox,
                                QComboBox, QCheckBox, QDoubleSpinBox, QTabWidget,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QAbstractItemView, QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
import sys
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import Pattern, SpeedController


class SpeedCurveWidget(QWidget):
    """Widget for visualizing speed curves"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.curve_type = "linear"
        self.setMinimumSize(200, 150)
        self.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
    
    def set_curve_type(self, curve_type: str):
        """Set the curve type to display"""
        self.curve_type = curve_type
        self.update()
    
    def paintEvent(self, event):
        """Draw the speed curve"""
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
        painter.setPen(QPen(QColor(100, 150, 255), 2))
        
        # Get curve function
        curve_func = getattr(SpeedController, self.curve_type, SpeedController.linear_easing)
        
        # Draw curve points
        points = []
        for x in range(self.width()):
            input_val = x / (self.width() - 1)
            output_val = curve_func(input_val)
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


class SpeedKeyframeTable(QTableWidget):
    """Table widget for editing speed keyframes"""
    
    keyframe_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """Setup table structure"""
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Frame", "Speed Multiplier"])
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Enable editing
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        
        # Connect signals
        self.itemChanged.connect(self.on_item_changed)
    
    def add_keyframe(self, frame: int, speed: float):
        """Add a new keyframe"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Frame item
        frame_item = QTableWidgetItem(str(frame))
        frame_item.setFlags(frame_item.flags() | Qt.ItemIsEditable)
        self.setItem(row, 0, frame_item)
        
        # Speed item
        speed_item = QTableWidgetItem(f"{speed:.2f}")
        speed_item.setFlags(speed_item.flags() | Qt.ItemIsEditable)
        self.setItem(row, 1, speed_item)
    
    def get_keyframes(self):
        """Get all keyframes as list of tuples"""
        keyframes = []
        for row in range(self.rowCount()):
            frame_item = self.item(row, 0)
            speed_item = self.item(row, 1)
            
            if frame_item and speed_item:
                try:
                    frame = int(frame_item.text())
                    speed = float(speed_item.text())
                    keyframes.append((frame, speed))
                except ValueError:
                    continue
        
        return keyframes
    
    def set_keyframes(self, keyframes):
        """Set keyframes from list of tuples"""
        self.setRowCount(0)
        for frame, speed in keyframes:
            self.add_keyframe(frame, speed)
    
    def on_item_changed(self, item):
        """Item changed in table"""
        self.keyframe_changed.emit()
    
    def remove_selected(self):
        """Remove selected rows"""
        current_row = self.currentRow()
        if current_row >= 0:
            self.removeRow(current_row)
            self.keyframe_changed.emit()


class AdvancedSpeedController(QWidget):
    """
    Advanced speed control widget with interpolation and easing
    
    Features:
    - Variable speed with keyframes
    - Frame interpolation
    - Speed curves and easing
    - Real-time preview
    - Speed presets
    """
    
    # Signals
    speed_changed = Signal(float)  # Emitted when speed changes
    curve_changed = Signal(str)  # Emitted when curve type changes
    interpolation_changed = Signal(bool, float)  # Emitted when interpolation changes
    keyframes_changed = Signal(list)  # Emitted when keyframes change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.pattern: Pattern = None
        self.current_speed = 1.0
        self.current_curve = "linear"
        self.interpolation_enabled = False
        self.interpolation_factor = 2.0
        
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
        
        # Basic speed tab
        basic_tab = self.create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic")
        
        # Variable speed tab
        variable_tab = self.create_variable_tab()
        tab_widget.addTab(variable_tab, "Variable Speed")
        
        # Interpolation tab
        interpolation_tab = self.create_interpolation_tab()
        tab_widget.addTab(interpolation_tab, "Interpolation")
        
        # Curves tab
        curves_tab = self.create_curves_tab()
        tab_widget.addTab(curves_tab, "Speed Curves")
        
        layout.addWidget(tab_widget)
        
        # Set up scroll area
        self.scroll_area.setWidget(self.content_widget)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.scroll_area)
    
    def create_basic_tab(self):
        """Create basic speed control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Speed control
        speed_group = QGroupBox("Speed Control")
        speed_layout = QVBoxLayout()
        
        # Speed slider
        speed_slider_layout = QHBoxLayout()
        speed_slider_layout.addWidget(QLabel("Speed:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(10, 500)  # 0.1x to 5.0x speed
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self.on_speed_slider_changed)
        speed_slider_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("1.0x")
        self.speed_label.setMinimumWidth(50)
        speed_slider_layout.addWidget(self.speed_label)
        
        speed_layout.addLayout(speed_slider_layout)
        
        # Speed presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        
        for preset in [("0.5x", 0.5), ("1.0x", 1.0), ("1.5x", 1.5), ("2.0x", 2.0)]:
            btn = QPushButton(preset[0])
            btn.clicked.connect(lambda checked, val=preset[1]: self.set_speed(val))
            presets_layout.addWidget(btn)
        
        speed_layout.addLayout(presets_layout)
        speed_group.setLayout(speed_layout)
        layout.addWidget(speed_group)
        
        # Duration control
        duration_group = QGroupBox("Duration Control")
        duration_layout = QVBoxLayout()
        
        duration_slider_layout = QHBoxLayout()
        duration_slider_layout.addWidget(QLabel("Target Duration:"))
        
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(100, 60000)  # 100ms to 60s
        self.duration_spinbox.setValue(1000)
        self.duration_spinbox.setSuffix(" ms")
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        duration_slider_layout.addWidget(self.duration_spinbox)
        
        duration_layout.addLayout(duration_slider_layout)
        
        # Fit to duration button
        fit_button = QPushButton("Fit to Duration")
        fit_button.clicked.connect(self.fit_to_duration)
        duration_layout.addWidget(fit_button)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_variable_tab(self):
        """Create variable speed control tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Keyframes table
        keyframes_group = QGroupBox("Speed Keyframes")
        keyframes_layout = QVBoxLayout()
        
        self.keyframe_table = SpeedKeyframeTable()
        self.keyframe_table.keyframe_changed.connect(self.on_keyframes_changed)
        keyframes_layout.addWidget(self.keyframe_table)
        
        # Keyframe controls
        keyframe_controls = QHBoxLayout()
        
        add_keyframe_btn = QPushButton("Add Keyframe")
        add_keyframe_btn.clicked.connect(self.add_keyframe)
        keyframe_controls.addWidget(add_keyframe_btn)
        
        remove_keyframe_btn = QPushButton("Remove Selected")
        remove_keyframe_btn.clicked.connect(self.remove_keyframe)
        keyframe_controls.addWidget(remove_keyframe_btn)
        
        keyframe_controls.addStretch()
        keyframes_layout.addLayout(keyframe_controls)
        
        keyframes_group.setLayout(keyframes_layout)
        layout.addWidget(keyframes_group)
        
        # Apply variable speed
        apply_layout = QHBoxLayout()
        self.apply_variable_btn = QPushButton("Apply Variable Speed")
        self.apply_variable_btn.clicked.connect(self.apply_variable_speed)
        apply_layout.addWidget(self.apply_variable_btn)
        
        layout.addLayout(apply_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_interpolation_tab(self):
        """Create frame interpolation tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Interpolation settings
        interp_group = QGroupBox("Frame Interpolation")
        interp_layout = QVBoxLayout()
        
        # Enable interpolation
        enable_layout = QHBoxLayout()
        self.interpolation_checkbox = QCheckBox("Enable Frame Interpolation")
        self.interpolation_checkbox.toggled.connect(self.on_interpolation_toggled)
        enable_layout.addWidget(self.interpolation_checkbox)
        
        interp_layout.addLayout(enable_layout)
        
        # Interpolation factor
        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Interpolation Factor:"))
        
        self.interpolation_spinbox = QDoubleSpinBox()
        self.interpolation_spinbox.setRange(1.0, 10.0)
        self.interpolation_spinbox.setValue(2.0)
        self.interpolation_spinbox.setSingleStep(0.5)
        self.interpolation_spinbox.setSuffix("x")
        self.interpolation_spinbox.valueChanged.connect(self.on_interpolation_factor_changed)
        factor_layout.addWidget(self.interpolation_spinbox)
        
        interp_layout.addLayout(factor_layout)
        
        # Interpolation info
        self.interp_info_label = QLabel("Interpolation will double the number of frames")
        self.interp_info_label.setWordWrap(True)
        interp_layout.addWidget(self.interp_info_label)
        
        interp_group.setLayout(interp_layout)
        layout.addWidget(interp_group)
        
        # Apply interpolation
        apply_layout = QHBoxLayout()
        self.apply_interpolation_btn = QPushButton("Apply Interpolation")
        self.apply_interpolation_btn.clicked.connect(self.apply_interpolation)
        apply_layout.addWidget(self.apply_interpolation_btn)
        
        layout.addLayout(apply_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_curves_tab(self):
        """Create speed curves tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Curve selection
        curve_group = QGroupBox("Speed Curve")
        curve_layout = QVBoxLayout()
        
        curve_selection_layout = QHBoxLayout()
        curve_selection_layout.addWidget(QLabel("Curve Type:"))
        
        self.curve_combo = QComboBox()
        self.curve_combo.addItems([
            "linear", "ease_in_quad", "ease_out_quad", "ease_in_out_quad",
            "ease_in_cubic", "ease_out_cubic", "ease_in_out_cubic"
        ])
        self.curve_combo.currentTextChanged.connect(self.on_curve_changed)
        curve_selection_layout.addWidget(self.curve_combo)
        
        curve_layout.addLayout(curve_selection_layout)
        
        # Curve visualization
        self.curve_widget = SpeedCurveWidget()
        curve_layout.addWidget(self.curve_widget)
        
        curve_group.setLayout(curve_layout)
        layout.addWidget(curve_group)
        
        # Apply curve
        apply_layout = QHBoxLayout()
        self.apply_curve_btn = QPushButton("Apply Speed Curve")
        self.apply_curve_btn.clicked.connect(self.apply_speed_curve)
        apply_layout.addWidget(self.apply_curve_btn)
        
        layout.addLayout(apply_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def set_pattern(self, pattern: Pattern):
        """Load pattern and update controls"""
        self.pattern = pattern
        
        if pattern:
            # Update speed
            current_fps = pattern.average_fps
            if current_fps > 0:
                self.set_speed(1.0)  # Reset to normal speed
            
            # Update keyframes
            variable_speed = getattr(pattern.metadata, 'variable_speed', False)
            if variable_speed:
                speed_keyframes = getattr(pattern.metadata, 'speed_keyframes', [])
                self.keyframe_table.set_keyframes(speed_keyframes)
            
            # Update interpolation settings
            interpolation_enabled = getattr(pattern.metadata, 'interpolation_enabled', False)
            interpolation_factor = getattr(pattern.metadata, 'interpolation_factor', 1.0)
            self.interpolation_checkbox.setChecked(interpolation_enabled)
            self.interpolation_spinbox.setValue(interpolation_factor)
            
            # Update curve
            speed_curve = getattr(pattern.metadata, 'speed_curve', 'linear')
            self.curve_combo.setCurrentText(speed_curve)
            self.current_curve = speed_curve
            self.curve_widget.set_curve_type(speed_curve)
    
    def set_speed(self, speed: float):
        """Set speed multiplier"""
        self.current_speed = max(0.1, min(5.0, speed))
        
        # Update slider
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(int(self.current_speed * 100))
        self.speed_slider.blockSignals(False)
        
        self.update_labels()
        self.speed_changed.emit(self.current_speed)
    
    def on_speed_slider_changed(self, value: int):
        """Speed slider changed"""
        speed = value / 100.0
        self.set_speed(speed)
    
    def on_duration_changed(self, duration_ms: int):
        """Duration spinbox changed"""
        if self.pattern:
            self.pattern.fit_to_duration(duration_ms)
    
    def fit_to_duration(self):
        """Fit pattern to target duration"""
        if self.pattern:
            duration_ms = self.duration_spinbox.value()
            self.pattern.fit_to_duration(duration_ms)
    
    def on_curve_changed(self, curve_type: str):
        """Curve type changed"""
        self.current_curve = curve_type
        self.curve_widget.set_curve_type(curve_type)
        self.curve_changed.emit(curve_type)
    
    def set_curve_type(self, curve_type: str):
        """Set the speed curve type"""
        if curve_type in [self.curve_combo.itemText(i) for i in range(self.curve_combo.count())]:
            self.curve_combo.setCurrentText(curve_type)
            self.curve_widget.set_curve_type(curve_type)
            self.current_curve = curve_type
    
    def set_speed(self, speed: float):
        """Set the speed value"""
        self.current_speed = max(0.1, min(10.0, speed))
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(int(self.current_speed * 10))
        self.speed_slider.blockSignals(False)
        self.update_labels()
    
    def set_interpolation_enabled(self, enabled: bool):
        """Enable/disable frame interpolation"""
        self.interpolation_checkbox.setChecked(enabled)
        self.interpolation_enabled = enabled
    
    def set_interpolation_factor(self, factor: float):
        """Set the interpolation factor"""
        self.interpolation_factor = max(0.1, min(5.0, factor))
        self.interpolation_spinbox.blockSignals(True)
        self.interpolation_spinbox.setValue(self.interpolation_factor)
        self.interpolation_spinbox.blockSignals(False)
    
    def on_interpolation_toggled(self, enabled: bool):
        """Interpolation checkbox toggled"""
        self.interpolation_enabled = enabled
        self.interpolation_changed.emit(enabled, self.interpolation_factor)
    
    def on_interpolation_factor_changed(self, factor: float):
        """Interpolation factor changed"""
        self.interpolation_factor = factor
        self.interpolation_changed.emit(self.interpolation_enabled, factor)
        
        # Update info label
        if self.pattern:
            new_frames = int(self.pattern.frame_count * factor)
            self.interp_info_label.setText(f"Interpolation will create {new_frames} frames")
    
    def on_keyframes_changed(self):
        """Keyframes changed in table"""
        keyframes = self.keyframe_table.get_keyframes()
        self.keyframes_changed.emit(keyframes)
    
    def add_keyframe(self):
        """Add new keyframe"""
        if not self.pattern:
            return
        
        # Get current frame from pattern
        current_frame = 0
        if hasattr(self, 'current_frame_idx'):
            current_frame = self.current_frame_idx
        
        # Add keyframe at current frame
        self.keyframe_table.add_keyframe(current_frame, 1.0)
    
    def remove_keyframe(self):
        """Remove selected keyframe"""
        self.keyframe_table.remove_selected()
    
    def apply_variable_speed(self):
        """Apply variable speed to pattern (non-destructive)"""
        if not self.pattern:
            return
        
        keyframes = self.keyframe_table.get_keyframes()
        if not keyframes:
            QMessageBox.warning(self, "No Keyframes", "Please add at least one keyframe.")
            return
        
        # Update metadata only (non-destructive)
        self.pattern.metadata.variable_speed = True
        self.pattern.metadata.speed_keyframes = keyframes
    
    def apply_interpolation(self):
        """Apply frame interpolation to pattern (non-destructive)"""
        if not self.pattern:
            return
        
        factor = self.interpolation_spinbox.value()
        # Update metadata only (non-destructive)
        self.pattern.metadata.interpolation_enabled = True
        self.pattern.metadata.interpolation_factor = factor
    
    def apply_speed_curve(self):
        """Apply speed curve to pattern (non-destructive)"""
        if not self.pattern:
            return
        
        curve_type = self.curve_combo.currentText()
        # Update metadata only (non-destructive)
        self.pattern.metadata.speed_curve = curve_type
    
    def update_labels(self):
        """Update all labels"""
        self.speed_label.setText(f"{self.current_speed:.1f}x")
    
    def get_current_settings(self) -> dict:
        """Get current speed settings"""
        return {
            "speed": self.current_speed,
            "curve_type": self.current_curve,
            "interpolation_enabled": self.interpolation_enabled,
            "interpolation_factor": self.interpolation_factor,
            "keyframes": self.keyframe_table.get_keyframes()
        }
