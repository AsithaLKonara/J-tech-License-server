"""
New Pattern Dialog - Create a new LED matrix pattern with configuration options.
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QButtonGroup, QRadioButton, QGroupBox, QFormLayout,
    QComboBox, QTabWidget, QWidget, QColorDialog, QCheckBox,
    QDoubleSpinBox, QLineEdit, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.pattern_templates import TemplateLibrary, TemplateCategory


class NewPatternDialog(QDialog):
    """Dialog for creating a new pattern with matrix dimensions and LED type."""
    
    def __init__(self, parent=None, default_width: int = 12, default_height: int = 6):
        super().__init__(parent)
        self.setWindowTitle("Create")
        self.setModal(True)
        self.resize(600, 750)
        
        # Initialize template library
        self.template_library = TemplateLibrary()
        self.selected_template = None
        self.template_param_widgets: Dict[str, Any] = {}
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Tabs: Custom and From Preset
        self.tabs = QTabWidget()
        
        # Custom tab
        custom_tab = self._create_custom_tab(default_width, default_height)
        self.tabs.addTab(custom_tab, "Custom")
        
        # From Preset tab
        preset_tab = self._create_preset_tab()
        self.tabs.addTab(preset_tab, "From Preset")
        
        # Track which tab is active
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create")
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._on_create_clicked)
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
    
    def _create_custom_tab(self, default_width: int, default_height: int) -> QWidget:
        """Create the Custom tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Info text (RGB mode description)
        info_text = QLabel(
            "RGB. Pixels can be any colour from a 24 bit RGB palette. "
            "Use this mode with any RGB pixel device. Uses 4 bytes per pixel to store data (unoptimised)."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #AAAAAA; padding: 8px; background-color: #2A2A2A; border-radius: 4px;")
        layout.addWidget(info_text)
        
        # Matrix Options section
        matrix_group = QGroupBox("Matrix Options")
        matrix_layout = QVBoxLayout()
        matrix_layout.setSpacing(8)
        
        # RGB dropdown
        self.rgb_combo = QComboBox()
        self.rgb_combo.addItems(["RGB", "GRB", "SINGLE"])
        self.rgb_combo.setCurrentText("RGB")
        matrix_layout.addWidget(self.rgb_combo)
        
        # Dimensions: Width x Height
        dims_layout = QHBoxLayout()
        dims_layout.setSpacing(5)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(default_width)
        self.width_spin.valueChanged.connect(self._validate_inputs)
        dims_layout.addWidget(self.width_spin)
        
        dims_layout.addWidget(QLabel("x"))
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(default_height)
        self.height_spin.valueChanged.connect(self._validate_inputs)
        dims_layout.addWidget(self.height_spin)
        
        dims_layout.addStretch()
        matrix_layout.addLayout(dims_layout)
        
        # Shape dropdown
        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Rectangular", "Circle", "Ring", "Arc", "Radial", "Multi-Ring", "Radial Rays", "Custom Positions"])
        self.shape_combo.setCurrentText("Circle")
        self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
        matrix_layout.addWidget(self.shape_combo)
        
        # Circular shape parameters (initially hidden)
        self.circular_params_group = QGroupBox("Circular Layout Parameters")
        circular_params_layout = QFormLayout()
        circular_params_layout.setSpacing(8)
        
        # LED count
        self.led_count_spin = QSpinBox()
        self.led_count_spin.setRange(1, 512)
        self.led_count_spin.setValue(60)
        self.led_count_spin.setToolTip("Number of LEDs in circular layout")
        circular_params_layout.addRow("LED Count:", self.led_count_spin)
        
        # Outer radius
        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(1.0, 1000.0)
        self.radius_spin.setValue(10.0)
        self.radius_spin.setDecimals(1)
        self.radius_spin.setSuffix(" units")
        self.radius_spin.setToolTip("Outer radius for circular layout")
        circular_params_layout.addRow("Outer Radius:", self.radius_spin)
        
        # Inner radius (for Ring)
        self.inner_radius_spin = QDoubleSpinBox()
        self.inner_radius_spin.setRange(0.0, 999.0)
        self.inner_radius_spin.setValue(5.0)
        self.inner_radius_spin.setDecimals(1)
        self.inner_radius_spin.setSuffix(" units")
        self.inner_radius_spin.setToolTip("Inner radius (for ring layouts only)")
        self.inner_radius_spin.setEnabled(False)
        circular_params_layout.addRow("Inner Radius:", self.inner_radius_spin)
        
        # Start angle (for Arc)
        self.start_angle_spin = QDoubleSpinBox()
        self.start_angle_spin.setRange(0.0, 359.0)
        self.start_angle_spin.setValue(0.0)
        self.start_angle_spin.setDecimals(1)
        self.start_angle_spin.setSuffix("°")
        self.start_angle_spin.setToolTip("Start angle in degrees (for arc layouts)")
        self.start_angle_spin.setEnabled(False)
        circular_params_layout.addRow("Start Angle:", self.start_angle_spin)
        
        # End angle (for Arc)
        self.end_angle_spin = QDoubleSpinBox()
        self.end_angle_spin.setRange(1.0, 360.0)
        self.end_angle_spin.setValue(360.0)
        self.end_angle_spin.setDecimals(1)
        self.end_angle_spin.setSuffix("°")
        self.end_angle_spin.setToolTip("End angle in degrees (for arc layouts)")
        self.end_angle_spin.setEnabled(False)
        circular_params_layout.addRow("End Angle:", self.end_angle_spin)
        
        self.circular_params_group.setLayout(circular_params_layout)
        self.circular_params_group.setVisible(False)  # Hidden by default
        matrix_layout.addWidget(self.circular_params_group)
        
        # Multi-ring parameters (initially hidden)
        self.multi_ring_params_group = QGroupBox("Multi-Ring Layout Parameters")
        multi_ring_layout = QVBoxLayout()
        multi_ring_layout.setSpacing(8)
        
        # Ring count
        ring_count_layout = QHBoxLayout()
        ring_count_layout.addWidget(QLabel("Number of Rings:"))
        self.multi_ring_count_spin = QSpinBox()
        self.multi_ring_count_spin.setRange(1, 5)
        self.multi_ring_count_spin.setValue(3)
        self.multi_ring_count_spin.setToolTip("Number of concentric rings (1-5)")
        self.multi_ring_count_spin.valueChanged.connect(self._on_multi_ring_count_changed)
        ring_count_layout.addWidget(self.multi_ring_count_spin)
        ring_count_layout.addStretch()
        multi_ring_layout.addLayout(ring_count_layout)
        
        # Ring spacing
        ring_spacing_layout = QHBoxLayout()
        ring_spacing_layout.addWidget(QLabel("Ring Spacing:"))
        self.ring_spacing_spin = QDoubleSpinBox()
        self.ring_spacing_spin.setRange(0.0, 100.0)
        self.ring_spacing_spin.setValue(2.0)
        self.ring_spacing_spin.setDecimals(1)
        self.ring_spacing_spin.setSuffix(" units")
        self.ring_spacing_spin.setToolTip("Spacing between rings (0 = auto-calculate)")
        ring_spacing_layout.addWidget(self.ring_spacing_spin)
        ring_spacing_layout.addStretch()
        multi_ring_layout.addLayout(ring_spacing_layout)
        
        # Ring configuration (scrollable area for multiple rings)
        self.ring_config_scroll = QScrollArea()
        self.ring_config_scroll.setWidgetResizable(True)
        self.ring_config_widget = QWidget()
        self.ring_config_layout = QVBoxLayout(self.ring_config_widget)
        self.ring_config_layout.setSpacing(5)
        self.ring_config_scroll.setWidget(self.ring_config_widget)
        self.ring_config_scroll.setMaximumHeight(200)
        multi_ring_layout.addWidget(QLabel("Ring Configuration:"))
        multi_ring_layout.addWidget(self.ring_config_scroll)
        
        # Store ring parameter widgets
        self.ring_led_count_spins: List[QSpinBox] = []
        self.ring_radius_spins: List[QDoubleSpinBox] = []
        
        self.multi_ring_params_group.setLayout(multi_ring_layout)
        self.multi_ring_params_group.setVisible(False)
        matrix_layout.addWidget(self.multi_ring_params_group)
        
        # Initialize ring configuration UI
        self._update_ring_config_ui()
        
        # Radial ray parameters (initially hidden)
        self.radial_ray_params_group = QGroupBox("Radial Ray Layout Parameters")
        radial_ray_layout = QFormLayout()
        radial_ray_layout.setSpacing(8)
        
        # Ray count
        self.ray_count_spin = QSpinBox()
        self.ray_count_spin.setRange(1, 64)
        self.ray_count_spin.setValue(8)
        self.ray_count_spin.setToolTip("Number of rays extending from center")
        radial_ray_layout.addRow("Ray Count:", self.ray_count_spin)
        
        # LEDs per ray
        self.leds_per_ray_spin = QSpinBox()
        self.leds_per_ray_spin.setRange(1, 100)
        self.leds_per_ray_spin.setValue(10)
        self.leds_per_ray_spin.setToolTip("Number of LEDs along each ray")
        radial_ray_layout.addRow("LEDs per Ray:", self.leds_per_ray_spin)
        
        # Ray spacing angle
        self.ray_spacing_angle_spin = QDoubleSpinBox()
        self.ray_spacing_angle_spin.setRange(1.0, 360.0)
        self.ray_spacing_angle_spin.setValue(45.0)
        self.ray_spacing_angle_spin.setDecimals(1)
        self.ray_spacing_angle_spin.setSuffix("°")
        self.ray_spacing_angle_spin.setToolTip("Angle between rays (0 = auto-calculate evenly)")
        radial_ray_layout.addRow("Ray Spacing Angle:", self.ray_spacing_angle_spin)
        
        self.radial_ray_params_group.setLayout(radial_ray_layout)
        self.radial_ray_params_group.setVisible(False)
        matrix_layout.addWidget(self.radial_ray_params_group)
        
        # Custom position parameters (initially hidden)
        self.custom_position_params_group = QGroupBox("Custom LED Position Parameters")
        custom_position_layout = QVBoxLayout()
        custom_position_layout.setSpacing(8)
        
        # Import button
        import_layout = QHBoxLayout()
        self.import_positions_btn = QPushButton("Import LED Positions...")
        self.import_positions_btn.setToolTip("Import LED positions from CSV or JSON file")
        self.import_positions_btn.clicked.connect(self._on_import_positions)
        import_layout.addWidget(self.import_positions_btn)
        import_layout.addStretch()
        custom_position_layout.addLayout(import_layout)
        
        # Units selection
        units_layout = QHBoxLayout()
        units_layout.addWidget(QLabel("Units:"))
        self.position_units_combo = QComboBox()
        self.position_units_combo.addItems(["mm", "inches", "grid"])
        self.position_units_combo.setCurrentText("mm")
        self.position_units_combo.setToolTip("Units for LED positions (mm, inches, or grid units)")
        units_layout.addWidget(self.position_units_combo)
        units_layout.addStretch()
        custom_position_layout.addLayout(units_layout)
        
        # Status label
        self.custom_position_status_label = QLabel("No positions imported")
        self.custom_position_status_label.setStyleSheet("color: #888; font-size: 10px;")
        custom_position_layout.addWidget(self.custom_position_status_label)
        
        # Store imported positions
        self.imported_positions: List[Tuple[float, float]] = []
        
        self.custom_position_params_group.setLayout(custom_position_layout)
        self.custom_position_params_group.setVisible(False)
        matrix_layout.addWidget(self.custom_position_params_group)
        
        # Background: Color swatch with radio buttons
        bg_layout = QHBoxLayout()
        bg_layout.setSpacing(10)
        
        self.background_color_btn = QPushButton()
        self.background_color = QColor(0, 0, 0)  # Black default
        self._update_background_color_btn()
        self.background_color_btn.setFixedSize(40, 30)
        self.background_color_btn.clicked.connect(self._pick_background_color)
        bg_layout.addWidget(self.background_color_btn)
        
        self.background_group = QButtonGroup(self)
        self.background_common_radio = QRadioButton("Common")
        self.background_all_radio = QRadioButton("All")
        self.background_all_radio.setChecked(True)
        self.background_group.addButton(self.background_common_radio, 0)
        self.background_group.addButton(self.background_all_radio, 1)
        self.background_common_radio.toggled.connect(self._update_background_mode_feedback)
        self.background_all_radio.toggled.connect(self._update_background_mode_feedback)
        bg_layout.addWidget(self.background_common_radio)
        bg_layout.addWidget(self.background_all_radio)
        bg_layout.addStretch()
        
        # Background mode feedback label
        self.background_mode_label = QLabel()
        self.background_mode_label.setStyleSheet("color: #888; font-size: 10px;")
        self._update_background_mode_feedback()
        bg_layout.addWidget(self.background_mode_label)
        
        matrix_layout.addLayout(bg_layout)
        
        # Border dropdown
        self.border_combo = QComboBox()
        self.border_combo.addItems(["n/a", "1px", "2px", "3px"])
        self.border_combo.setCurrentText("n/a")
        matrix_layout.addWidget(self.border_combo)
        
        matrix_group.setLayout(matrix_layout)
        layout.addWidget(matrix_group)
        
        # Pixel Shape section
        pixel_shape_group = QGroupBox("Pixel Shape")
        pixel_shape_layout = QHBoxLayout()
        pixel_shape_layout.setSpacing(15)
        
        self.pixel_shape_group = QButtonGroup(self)
        
        # Square option
        square_btn = QPushButton()
        square_btn.setFixedSize(50, 50)
        square_btn.setCheckable(True)
        square_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #666;
                background-color: transparent;
            }
            QPushButton:checked {
                border: 2px solid #00FF78;
            }
            QPushButton:hover {
                border: 2px solid #888;
            }
        """)
        self.pixel_shape_group.addButton(square_btn, 0)
        pixel_shape_layout.addWidget(square_btn)
        
        # Circle option (selected by default)
        circle_btn = QPushButton()
        circle_btn.setFixedSize(50, 50)
        circle_btn.setCheckable(True)
        circle_btn.setChecked(True)
        circle_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #00FF78;
                background-color: #00FF78;
                border-radius: 25px;
            }
            QPushButton:checked {
                border: 2px solid #00FF78;
                background-color: #00FF78;
            }
            QPushButton:hover {
                border: 2px solid #00FFAA;
                background-color: #00FFAA;
            }
        """)
        self.pixel_shape_group.addButton(circle_btn, 1)
        pixel_shape_layout.addWidget(circle_btn)
        
        # Another square option (rounded square)
        square2_btn = QPushButton()
        square2_btn.setFixedSize(50, 50)
        square2_btn.setCheckable(True)
        square2_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #666;
                background-color: transparent;
                border-radius: 5px;
            }
            QPushButton:checked {
                border: 2px solid #00FF78;
            }
            QPushButton:hover {
                border: 2px solid #888;
            }
        """)
        self.pixel_shape_group.addButton(square2_btn, 2)
        pixel_shape_layout.addWidget(square2_btn)
        
        pixel_shape_layout.addStretch()
        pixel_shape_group.setLayout(pixel_shape_layout)
        layout.addWidget(pixel_shape_group)
        
        # Animation section
        animation_group = QGroupBox("Animation")
        animation_layout = QFormLayout()
        animation_layout.setSpacing(10)
        
        # Start with X animation frames
        frames_layout = QHBoxLayout()
        frames_layout.setSpacing(5)
        
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 1000)
        self.frames_spin.setValue(1)
        self.frames_spin.valueChanged.connect(self._validate_inputs)
        self.frames_spin.valueChanged.connect(self._update_background_mode_feedback)
        frames_layout.addWidget(self.frames_spin)
        
        frames_layout.addWidget(QLabel("animation frames"))
        frames_layout.addStretch()
        animation_layout.addRow("Start with", frames_layout)
        
        # Clear all animation/matrix data checkbox
        self.clear_data_checkbox = QCheckBox("Clear all animation/matrix data")
        animation_layout.addRow("", self.clear_data_checkbox)
        
        animation_group.setLayout(animation_layout)
        layout.addWidget(animation_group)
        
        # Validation error label
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        layout.addWidget(self.validation_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_preset_tab(self) -> QWidget:
        """Create the From Preset tab content."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        info_label = QLabel("Select a preset template or matrix size:")
        layout.addWidget(info_label)
        
        # Matrix size presets
        size_group = QGroupBox("Matrix Size Presets")
        size_layout = QVBoxLayout()
        
        self.size_preset_combo = QComboBox()
        self.size_preset_combo.addItem("-- Select Size Preset --", None)
        size_presets = [
            ("8×8", 8, 8),
            ("16×16", 16, 16),
            ("32×8", 32, 8),
            ("32×32", 32, 32),
            ("64×32", 64, 32),
            ("128×64", 128, 64),
        ]
        for label, w, h in size_presets:
            self.size_preset_combo.addItem(label, (w, h))
        self.size_preset_combo.currentIndexChanged.connect(self._on_size_preset_changed)
        size_layout.addWidget(self.size_preset_combo)
        
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        # Pattern templates
        template_group = QGroupBox("Pattern Templates")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- Select Template --", None)
        
        # Add templates by category
        for category in TemplateCategory:
            templates = [t for t in self.template_library.templates if t.category == category]
            if templates:
                self.template_combo.addItem(f"--- {category.value} ---", None)
                for template in templates:
                    self.template_combo.addItem(template.name, template)
        
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_combo)
        
        # Template description
        self.template_description = QLabel()
        self.template_description.setWordWrap(True)
        self.template_description.setStyleSheet("color: #AAAAAA; padding: 5px;")
        self.template_description.setVisible(False)
        template_layout.addWidget(self.template_description)
        
        # Template parameters (dynamic)
        self.template_params_group = QGroupBox("Template Parameters")
        self.template_params_layout = QFormLayout()
        self.template_params_group.setLayout(self.template_params_layout)
        self.template_params_group.setVisible(False)
        template_layout.addWidget(self.template_params_group)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        layout.addStretch()
        
        return widget
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - validate inputs."""
        self._validate_inputs()
    
    def _on_shape_changed(self, shape_text: str):
        """Handle shape selection change - show/hide circular parameters."""
        shape_lower = shape_text.lower().replace("-", "_").replace(" ", "_")
        is_circular = shape_lower in ["circle", "ring", "arc", "radial"]
        is_multi_ring = shape_lower == "multi_ring"
        is_radial_rays = shape_lower == "radial_rays"
        is_custom_positions = shape_lower == "custom_positions"
        
        # Show/hide parameter groups
        self.circular_params_group.setVisible(is_circular)
        self.multi_ring_params_group.setVisible(is_multi_ring)
        self.radial_ray_params_group.setVisible(is_radial_rays)
        self.custom_position_params_group.setVisible(is_custom_positions)
        
        if is_circular:
            # Enable/disable specific fields based on shape
            if shape_lower == "ring":
                self.inner_radius_spin.setEnabled(True)
            else:
                self.inner_radius_spin.setEnabled(False)
            
            if shape_lower == "arc":
                self.start_angle_spin.setEnabled(True)
                self.end_angle_spin.setEnabled(True)
            else:
                self.start_angle_spin.setEnabled(False)
                self.end_angle_spin.setEnabled(False)
                if shape_lower == "circle":
                    self.start_angle_spin.setValue(0.0)
                    self.end_angle_spin.setValue(360.0)
        
        if is_multi_ring:
            # Update ring configuration UI when multi-ring is selected
            self._update_ring_config_ui()
    
    def _on_multi_ring_count_changed(self, count: int):
        """Handle multi-ring count change - update ring configuration UI."""
        self._update_ring_config_ui()
    
    def _update_ring_config_ui(self):
        """Update ring configuration UI based on current ring count."""
        # Clear existing widgets
        for i in reversed(range(self.ring_config_layout.count())):
            item = self.ring_config_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.ring_led_count_spins.clear()
        self.ring_radius_spins.clear()
        
        # Get current ring count
        ring_count = self.multi_ring_count_spin.value() if hasattr(self, 'multi_ring_count_spin') else 3
        
        # Calculate default radii (evenly spaced)
        max_radius = 10.0
        min_radius = 2.0
        if ring_count > 1:
            radius_step = (max_radius - min_radius) / (ring_count - 1)
        else:
            radius_step = 0
        
        # Create widgets for each ring
        for ring_idx in range(ring_count):
            ring_group = QGroupBox(f"Ring {ring_idx + 1}")
            ring_layout = QFormLayout()
            
            # LEDs per ring
            led_spin = QSpinBox()
            led_spin.setRange(1, 512)
            # Default: outer rings have more LEDs
            default_leds = int(60 - ring_idx * 10) if ring_idx < 6 else 20
            led_spin.setValue(default_leds)
            led_spin.setToolTip(f"Number of LEDs in ring {ring_idx + 1}")
            ring_layout.addRow("LEDs:", led_spin)
            self.ring_led_count_spins.append(led_spin)
            
            # Radius for this ring
            radius_spin = QDoubleSpinBox()
            radius_spin.setRange(0.5, 1000.0)
            default_radius = min_radius + radius_step * ring_idx if ring_count > 1 else max_radius
            radius_spin.setValue(default_radius)
            radius_spin.setDecimals(1)
            radius_spin.setSuffix(" units")
            radius_spin.setToolTip(f"Radius for ring {ring_idx + 1}")
            ring_layout.addRow("Radius:", radius_spin)
            self.ring_radius_spins.append(radius_spin)
            
            ring_group.setLayout(ring_layout)
            self.ring_config_layout.addWidget(ring_group)
    
    def _on_size_preset_changed(self, index: int):
        """Handle size preset selection."""
        if index > 0:
            size_data = self.size_preset_combo.currentData()
            if size_data:
                width, height = size_data
                # Update custom tab dimensions if we're on preset tab
                # (will be applied when switching to custom tab or creating)
                self._pending_width = width
                self._pending_height = height
    
    def _on_template_selected(self, index: int):
        """Handle template selection - show parameters."""
        template = self.template_combo.currentData()
        
        # Clear existing parameter widgets
        self._clear_template_params()
        self.template_param_widgets.clear()
        
        if template is None:
            self.template_description.setVisible(False)
            self.template_params_group.setVisible(False)
            self.selected_template = None
            return
        
        self.selected_template = template
        
        # Show description
        self.template_description.setText(template.description)
        self.template_description.setVisible(True)
        
        # Create parameter widgets
        for param_name, param_value in template.parameters.items():
            if param_name in ["width", "height"]:
                continue  # These are handled separately
            
            if isinstance(param_value, str):
                widget = QLineEdit(str(param_value))
                self.template_param_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, int):
                widget = QSpinBox()
                widget.setRange(1, 1000)
                widget.setValue(param_value)
                self.template_param_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 100.0)
                widget.setValue(param_value)
                widget.setDecimals(2)
                self.template_param_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, tuple) and len(param_value) == 3:
                # RGB color
                widget = QLineEdit(f"{param_value[0]},{param_value[1]},{param_value[2]}")
                self.template_param_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
        
        self.template_params_group.setVisible(len(self.template_param_widgets) > 0)
    
    def _clear_template_params(self):
        """Clear template parameter form."""
        while self.template_params_layout.rowCount() > 0:
            self.template_params_layout.removeRow(0)
    
    def _update_background_color_btn(self):
        """Update background color button appearance."""
        color = self.background_color
        self.background_color_btn.setStyleSheet(
            f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); "
            "border: 1px solid #666; border-radius: 3px;"
        )
    
    def _update_background_mode_feedback(self):
        """Update background mode visual feedback."""
        # Check if frames_spin exists (may not be created yet)
        if not hasattr(self, 'frames_spin') or self.frames_spin is None:
            return
        
        mode = "all" if self.background_all_radio.isChecked() else "common"
        frames_count = self.frames_spin.value()
        
        if mode == "all":
            self.background_mode_label.setText(f"(Background applied to all {frames_count} frame(s))")
        else:
            self.background_mode_label.setText("(Background applied to first frame only)")
    
    def _pick_background_color(self):
        """Open color picker for background color."""
        color = QColorDialog.getColor(self.background_color, self, "Select Background Color")
        if color.isValid():
            self.background_color = color
            self._update_background_color_btn()
    
    def _validate_inputs(self) -> bool:
        """Validate dialog inputs and show errors."""
        errors = []
        
        # Validate dimensions
        width = self.width_spin.value()
        height = self.height_spin.value()
        if width < 1 or width > 256:
            errors.append("Width must be between 1 and 256")
        if height < 1 or height > 256:
            errors.append("Height must be between 1 and 256")
        if width * height > 10000:
            errors.append("Total LEDs (width × height) cannot exceed 10,000")
        
        # Validate frames
        frames = self.frames_spin.value()
        if frames < 1 or frames > 1000:
            errors.append("Frame count must be between 1 and 1000")
        
        # Validate circular parameters if circular shape is selected
        if self.circular_params_group.isVisible():
            led_count = self.led_count_spin.value()
            if led_count < 1 or led_count > 512:
                errors.append("LED count must be between 1 and 512")
            
            radius = self.radius_spin.value()
            inner_radius = self.inner_radius_spin.value()
            if inner_radius >= radius:
                errors.append("Inner radius must be less than outer radius")
        
        # Validate multi-ring parameters
        if self.multi_ring_params_group.isVisible():
            ring_count = self.multi_ring_count_spin.value()
            if ring_count < 1 or ring_count > 5:
                errors.append("Ring count must be between 1 and 5")
            
            if len(self.ring_led_count_spins) != ring_count:
                errors.append("Ring configuration incomplete")
            else:
                for i, led_spin in enumerate(self.ring_led_count_spins):
                    if led_spin.value() < 1:
                        errors.append(f"Ring {i+1} LED count must be >= 1")
                for i, radius_spin in enumerate(self.ring_radius_spins):
                    if radius_spin.value() <= 0:
                        errors.append(f"Ring {i+1} radius must be > 0")
        
        # Validate radial ray parameters
        if self.radial_ray_params_group.isVisible():
            ray_count = self.ray_count_spin.value()
            if ray_count < 1 or ray_count > 64:
                errors.append("Ray count must be between 1 and 64")
            
            leds_per_ray = self.leds_per_ray_spin.value()
            if leds_per_ray < 1 or leds_per_ray > 100:
                errors.append("LEDs per ray must be between 1 and 100")
            
            if self.ray_spacing_angle_spin.value() <= 0 or self.ray_spacing_angle_spin.value() > 360:
                errors.append("Ray spacing angle must be between 1 and 360 degrees")
        
        # Show/hide validation label
        if errors:
            self.validation_label.setText("⚠ " + " | ".join(errors))
            self.validation_label.setVisible(True)
            self.create_btn.setEnabled(False)
            return False
        else:
            self.validation_label.setVisible(False)
            self.create_btn.setEnabled(True)
            return True
    
    def _on_create_clicked(self):
        """Handle create button click with validation."""
        if not self._validate_inputs():
            QMessageBox.warning(self, "Validation Error", 
                              "Please fix the errors before creating the pattern.")
            return
        
        # If preset tab is active and template is selected, handle differently
        if self.tabs.currentIndex() == 1 and self.selected_template:
            # This will be handled by the caller
            pass
        
        self.accept()
    
    def get_width(self) -> int:
        """Get selected matrix width."""
        if hasattr(self, '_pending_width'):
            return self._pending_width
        return self.width_spin.value()
    
    def get_height(self) -> int:
        """Get selected matrix height."""
        if hasattr(self, '_pending_height'):
            return self._pending_height
        return self.height_spin.value()
    
    def get_led_type(self) -> str:
        """Get selected LED type: 'RGB', 'GRB', or 'SINGLE'."""
        return self.rgb_combo.currentText()
    
    def is_single_color(self) -> bool:
        """Check if single color mode is selected."""
        return self.rgb_combo.currentText() == "SINGLE"
    
    def get_shape(self) -> str:
        """Get selected shape: 'rectangular', 'circle', 'ring', 'arc', 'radial', 'multi_ring', 'radial_rays'."""
        shape = self.shape_combo.currentText().lower().replace("-", "_").replace(" ", "_")
        if shape == "rectangular":
            return "rectangular"
        elif shape == "multi_ring":
            return "multi_ring"
        elif shape == "radial_rays":
            return "radial_rays"
        return shape
    
    def get_layout_type(self) -> str:
        """Get layout type based on shape selection."""
        shape = self.get_shape()
        if shape == "rectangular":
            return "rectangular"
        return "circular"
    
    def get_background_color(self) -> tuple:
        """Get background color as RGB tuple."""
        return (self.background_color.red(), self.background_color.green(), self.background_color.blue())
    
    def get_background_mode(self) -> str:
        """Get background mode: 'common' or 'all'."""
        if self.background_all_radio.isChecked():
            return "all"
        return "common"
    
    def get_border(self) -> str:
        """Get border setting."""
        return self.border_combo.currentText()
    
    def get_pixel_shape(self) -> str:
        """Get selected pixel shape: 'square', 'circle', or 'rounded'."""
        checked_id = self.pixel_shape_group.checkedId()
        if checked_id == 1:  # Circle
            return "circle"
        elif checked_id == 2:  # Second square (could be rounded)
            return "rounded"
        return "square"
    
    def get_initial_frames(self) -> int:
        """Get number of initial animation frames."""
        return self.frames_spin.value()
    
    def should_clear_data(self) -> bool:
        """Check if data should be cleared."""
        return self.clear_data_checkbox.isChecked()
    
    def get_selected_template(self):
        """Get selected template if preset tab is active."""
        return self.selected_template
    
    def get_template_parameters(self) -> Dict[str, Any]:
        """Get template parameter values."""
        params = {}
        for param_name, widget in self.template_param_widgets.items():
            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
                # Try to parse as RGB tuple if it looks like one
                if ',' in text and param_name.lower() in ['color', 'colour']:
                    try:
                        parts = [int(x.strip()) for x in text.split(',')]
                        if len(parts) == 3:
                            params[param_name] = tuple(parts)
                        else:
                            params[param_name] = text
                    except ValueError:
                        params[param_name] = text
                else:
                    params[param_name] = text
            elif isinstance(widget, QSpinBox):
                params[param_name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[param_name] = widget.value()
        return params
    
    def is_preset_tab_active(self) -> bool:
        """Check if preset tab is currently active."""
        return self.tabs.currentIndex() == 1
    
    # Legacy methods for backward compatibility
    def get_circular_layout_type(self) -> str:
        """Get circular layout subtype (for backward compatibility)."""
        shape = self.get_shape()
        if shape == "rectangular":
            return "circle"
        return shape
    
    def get_circular_led_count(self) -> Optional[int]:
        """Get circular LED count."""
        if self.get_layout_type() == "circular":
            return self.led_count_spin.value()
        return None
    
    def get_circular_radius(self) -> Optional[float]:
        """Get outer radius."""
        if self.get_layout_type() == "circular":
            radius = self.radius_spin.value()
            if radius > 1.0:
                return radius
        return None
    
    def get_circular_inner_radius(self) -> Optional[float]:
        """Get inner radius (for ring layouts)."""
        if self.get_layout_type() == "circular" and self.shape_combo.currentText().lower() == "ring":
            inner_radius = self.inner_radius_spin.value()
            if inner_radius > 0.0:
                return inner_radius
        return None
    
    def get_circular_start_angle(self) -> float:
        """Get start angle in degrees."""
        if self.get_layout_type() == "circular":
            return self.start_angle_spin.value()
        return 0.0
    
    def get_circular_end_angle(self) -> float:
        """Get end angle in degrees."""
        if self.get_layout_type() == "circular":
            return self.end_angle_spin.value()
        return 360.0
    
    def get_multi_ring_count(self) -> Optional[int]:
        """Get multi-ring count."""
        if self.get_shape() == "multi_ring":
            return self.multi_ring_count_spin.value()
        return None
    
    def get_ring_led_counts(self) -> List[int]:
        """Get LEDs per ring for multi-ring layout."""
        if self.get_shape() == "multi_ring":
            return [spin.value() for spin in self.ring_led_count_spins]
        return []
    
    def get_ring_radii(self) -> List[float]:
        """Get radii for each ring in multi-ring layout."""
        if self.get_shape() == "multi_ring":
            return [spin.value() for spin in self.ring_radius_spins]
        return []
    
    def get_ring_spacing(self) -> Optional[float]:
        """Get ring spacing for multi-ring layout."""
        if self.get_shape() == "multi_ring":
            spacing = self.ring_spacing_spin.value()
            return spacing if spacing > 0 else None
        return None
    
    def get_ray_count(self) -> Optional[int]:
        """Get ray count for radial ray layout."""
        if self.get_shape() == "radial_rays":
            return self.ray_count_spin.value()
        return None
    
    def get_leds_per_ray(self) -> Optional[int]:
        """Get LEDs per ray for radial ray layout."""
        if self.get_shape() == "radial_rays":
            return self.leds_per_ray_spin.value()
        return None
    
    def get_ray_spacing_angle(self) -> Optional[float]:
        """Get ray spacing angle for radial ray layout."""
        if self.get_shape() == "radial_rays":
            angle = self.ray_spacing_angle_spin.value()
            return angle if angle > 0 else None
        return None
    
    def _on_import_positions(self):
        """Handle import LED positions button click."""
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        from core.io.custom_position_importer import import_positions_from_csv, import_positions_from_json
        
        # Open file dialog
        file_path, selected_filter = QFileDialog.getOpenFileName(
            self,
            "Import LED Positions",
            "",
            "CSV Files (*.csv);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        file_path_obj = Path(file_path)
        
        try:
            # Import based on file extension
            if file_path_obj.suffix.lower() == '.csv':
                positions = import_positions_from_csv(
                    file_path_obj,
                    x_column=0,
                    y_column=1,
                    skip_header=True,
                    units=self.position_units_combo.currentText()
                )
            elif file_path_obj.suffix.lower() == '.json':
                positions = import_positions_from_json(
                    file_path_obj,
                    x_key="x",
                    y_key="y",
                    units=self.position_units_combo.currentText()
                )
            else:
                QMessageBox.warning(self, "Invalid File", "Please select a CSV or JSON file.")
                return
            
            # Store imported positions
            self.imported_positions = positions
            
            # Update status label
            self.custom_position_status_label.setText(
                f"✓ Imported {len(positions)} LED positions from {file_path_obj.name}"
            )
            self.custom_position_status_label.setStyleSheet("color: #00FF78; font-size: 10px;")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import LED positions:\n{str(e)}"
            )
            self.custom_position_status_label.setText("Import failed")
            self.custom_position_status_label.setStyleSheet("color: #FF6B6B; font-size: 10px;")
    
    def get_custom_led_positions(self) -> Optional[List[Tuple[float, float]]]:
        """Get imported custom LED positions."""
        if self.get_shape() == "custom_positions" and self.imported_positions:
            return self.imported_positions
        return None
    
    def get_led_position_units(self) -> str:
        """Get LED position units."""
        if self.get_shape() == "custom_positions":
            return self.position_units_combo.currentText()
        return "grid"
