"""
Create Animation Dialog - Quick access to common animations and templates
"""

from __future__ import annotations

from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QFormLayout,
    QButtonGroup,
    QRadioButton,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
    QMessageBox,
    QScrollArea,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from core.pattern import Pattern
from core.pattern_templates import TemplateLibrary, TemplateCategory


class CreateAnimationDialog(QDialog):
    """Dialog for quickly creating common animations."""
    
    pattern_generated = Signal(Pattern)  # Emitted when pattern is generated
    
    def __init__(self, parent=None, current_width: int = 16, current_height: int = 16):
        super().__init__(parent)
        self.setWindowTitle("Create Animation")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.current_width = current_width
        self.current_height = current_height
        self.template_library = TemplateLibrary()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create scroll area for dialog content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("✨ Create Animation")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Tabs for different animation types
        tabs = QTabWidget()
        
        # Quick Templates tab
        templates_tab = self._create_templates_tab()
        tabs.addTab(templates_tab, "📋 Templates")
        
        # Common Animations tab
        animations_tab = self._create_animations_tab()
        tabs.addTab(animations_tab, "🎬 Common Animations")
        
        layout.addWidget(tabs)
        
        # Matrix size
        size_group = QGroupBox("Matrix Size")
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(self.current_width)
        size_layout.addWidget(self.width_spin)
        
        size_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(self.current_height)
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        size_group.setLayout(size_layout)
        layout.addWidget(size_group)
        
        layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area, 1)
        
        # Buttons (outside scroll area)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_generate)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def _create_templates_tab(self) -> QWidget:
        """Create templates tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Select a template:"))
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- Select Template --", None)
        
        # Add templates by category
        for category in TemplateCategory:
            templates = [t for t in self.template_library.templates if t.category == category]
            if templates:
                self.template_combo.addItem(f"--- {category.value} ---", None)
                for template in templates:
                    self.template_combo.addItem(template.name, template)
        
        layout.addWidget(self.template_combo)
        self.template_combo.currentIndexChanged.connect(self._on_template_selected)
        
        # Template parameters will be shown here when template is selected
        self.template_params_group = QGroupBox("Template Parameters")
        self.template_params_layout = QFormLayout()
        self.template_params_group.setLayout(self.template_params_layout)
        self.template_params_group.setVisible(False)  # Hide until template selected
        layout.addWidget(self.template_params_group)
        
        layout.addStretch()
        
        return widget
    
    def _on_template_selected(self, index: int):
        """Handle template selection - show parameter controls."""
        template = self.template_combo.currentData()
        
        # Clear existing parameters
        while self.template_params_layout.rowCount() > 0:
            self.template_params_layout.removeRow(0)
        
        if template is None:
            self.template_params_group.setVisible(False)
            return
        
        # Show parameter controls
        self.template_params_group.setVisible(True)
        self._parameter_widgets = {}
        
        # Create controls for each parameter (except width/height which are handled separately)
        for param_name, param_value in template.parameters.items():
            if param_name in ["width", "height"]:
                continue
            
            if isinstance(param_value, str):
                from PySide6.QtWidgets import QLineEdit
                widget = QLineEdit(str(param_value))
                self._parameter_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, int):
                widget = QSpinBox()
                widget.setRange(1, 1000)
                widget.setValue(param_value)
                self._parameter_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, float):
                from PySide6.QtWidgets import QDoubleSpinBox
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 100.0)
                widget.setValue(param_value)
                widget.setDecimals(2)
                self._parameter_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, tuple) and len(param_value) == 3:
                # RGB color
                from PySide6.QtWidgets import QLineEdit
                widget = QLineEdit(f"{param_value[0]},{param_value[1]},{param_value[2]}")
                self._parameter_widgets[param_name] = widget
                self.template_params_layout.addRow(f"{param_name.title()}:", widget)
    
    def _create_animations_tab(self) -> QWidget:
        """Create common animations tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Quick animations:"))
        
        # Animation type
        anim_type_group = QGroupBox("Animation Type")
        anim_type_layout = QVBoxLayout()
        self.anim_type_group = QButtonGroup()
        
        animations = [
            ("Scrolling Text", "scrolling_text"),
            ("Bouncing Ball", "bouncing_ball"),
            ("Fade In/Out", "fade"),
            ("Rotate", "rotate"),
            ("Pulse", "pulse"),
            ("Rain Effect", "rain"),
            ("Fire Effect", "fire"),
        ]
        
        for i, (label, value) in enumerate(animations):
            radio = QRadioButton(label)
            if i == 0:
                radio.setChecked(True)
            self.anim_type_group.addButton(radio, i)
            self.anim_type_group.setId(radio, i)
            anim_type_layout.addWidget(radio)
        
        anim_type_group.setLayout(anim_type_layout)
        layout.addWidget(anim_type_group)
        
        # Animation parameters
        self.anim_params_group = QGroupBox("Animation Parameters")
        self.anim_params_layout = QFormLayout()
        
        # Frames
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 1000)
        self.frames_spin.setValue(30)
        self.anim_params_layout.addRow("Frames:", self.frames_spin)
        
        # Speed
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(1, 100)
        self.speed_spin.setValue(10)
        self.speed_spin.setToolTip("Animation speed (higher = faster)")
        self.anim_params_layout.addRow("Speed:", self.speed_spin)
        
        self.anim_params_group.setLayout(self.anim_params_layout)
        layout.addWidget(self.anim_params_group)
        
        layout.addStretch()
        
        return widget
    
    def _on_generate(self):
        """Generate pattern based on selected option."""
        width = self.width_spin.value()
        height = self.height_spin.value()
        
        # Check which tab is active
        tabs = self.findChild(QTabWidget)
        if tabs is None:
            return
        
        current_tab = tabs.currentIndex()
        
        if current_tab == 0:  # Templates tab
            template = self.template_combo.currentData()
            if template is None:
                QMessageBox.warning(self, "No Template Selected", "Please select a template.")
                return
            
            # Generate from template
            try:
                params = template.parameters.copy()
                params["width"] = width
                params["height"] = height
                
                # Collect parameter values from form
                if hasattr(self, '_parameter_widgets'):
                    for param_name, widget in self._parameter_widgets.items():
                        if isinstance(widget, QSpinBox):
                            params[param_name] = widget.value()
                        elif isinstance(widget, QComboBox):
                            params[param_name] = widget.currentText()
                        else:
                            # Handle QLineEdit and QDoubleSpinBox
                            from PySide6.QtWidgets import QLineEdit, QDoubleSpinBox
                            if isinstance(widget, QDoubleSpinBox):
                                params[param_name] = widget.value()
                            elif isinstance(widget, QLineEdit):
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
                            else:
                                # Try to get value from widget
                                if hasattr(widget, 'value'):
                                    params[param_name] = widget.value()
                                elif hasattr(widget, 'text'):
                                    params[param_name] = widget.text()
                
                pattern = self.template_library.generate_pattern(template.name, width, height, **params)
                self.pattern_generated.emit(pattern)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Generation Error", f"Failed to generate pattern: {e}")
        
        elif current_tab == 1:  # Animations tab
            # Get selected animation type
            selected_id = self.anim_type_group.checkedId()
            animations = [
                "scrolling_text", "bouncing_ball", "fade", "rotate", "pulse", "rain", "fire"
            ]
            anim_type = animations[selected_id] if 0 <= selected_id < len(animations) else "scrolling_text"
            
            # Generate animation pattern
            try:
                pattern = self._generate_animation_pattern(anim_type, width, height)
                self.pattern_generated.emit(pattern)
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Generation Error", f"Failed to generate animation: {e}")
    
    def _generate_animation_pattern(self, anim_type: str, width: int, height: int) -> Pattern:
        """Generate a pattern for the specified animation type."""
        from core.pattern import Pattern, Frame, PatternMetadata
        from datetime import datetime
        
        frames_count = self.frames_spin.value()
        speed = self.speed_spin.value()
        
        metadata = PatternMetadata(
            width=width,
            height=height,
            name=f"{anim_type.replace('_', ' ').title()} Animation",
            created_at=datetime.now().isoformat(),
        )
        
        frames = []
        
        if anim_type == "scrolling_text":
            # Use template library for scrolling text
            template = next((t for t in self.template_library.templates if t.name == "Scrolling Text"), None)
            if template:
                params = {"width": width, "height": height, "text": "HELLO", "frames": frames_count, "speed": speed}
                return self.template_library.generate_pattern(template, params)
        
        # For other animations, use template library if available
        template_map = {
            "bouncing_ball": "Bouncing Ball",
            "fade": "Fade In/Out",
            "rotate": "Rotate",
            "pulse": "Pulse",
            "rain": "Rain",
            "fire": "Fire",
        }
        
        template_name = template_map.get(anim_type)
        if template_name:
            params = {"frames": frames_count, "speed": speed}
            try:
                return self.template_library.generate_pattern(template_name, width, height, **params)
            except ValueError:
                pass  # Template not found, fall through to default
        
        # Fallback: create simple pattern
        for i in range(frames_count):
            pixels = [(0, 0, 0)] * (width * height)
            frames.append(Frame(pixels=pixels, duration_ms=100))
        
        return Pattern(metadata=metadata, frames=frames)

