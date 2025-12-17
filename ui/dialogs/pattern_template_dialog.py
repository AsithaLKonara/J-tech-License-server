"""
Pattern Template Dialog - UI for selecting and customizing pattern templates
"""

from __future__ import annotations

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QWidget,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.pattern import Pattern
from core.pattern_templates import TemplateCategory, PatternTemplate
from core.services.pattern_service import PatternService

logger = logging.getLogger(__name__)


class PatternTemplateDialog(QDialog):
    """Dialog for selecting and customizing pattern templates."""
    
    pattern_generated = Signal(Pattern)  # Emitted when pattern is generated
    
    def __init__(self, parent=None, current_width: int = 16, current_height: int = 16):
        super().__init__(parent)
        self.setWindowTitle("Pattern Templates")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self.current_width = current_width
        self.current_height = current_height
        self.pattern_service = PatternService()
        self.selected_template: Optional[PatternTemplate] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        
        # Splitter for template list and preview/parameters
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Template list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        category_label = QLabel("Category:")
        left_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("All", None)
        for category in TemplateCategory:
            self.category_combo.addItem(category.value, category)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_combo)
        
        template_label = QLabel("Templates:")
        left_layout.addWidget(template_label)
        
        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self._on_template_selected)
        left_layout.addWidget(self.template_list)
        
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)
        
        # Right: Preview and parameters
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Description
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(80)
        right_layout.addWidget(self.description_text)
        
        # Parameters
        self.parameters_group = QGroupBox("Parameters")
        self.parameters_layout = QFormLayout()
        self.parameters_group.setLayout(self.parameters_layout)
        right_layout.addWidget(self.parameters_group)
        
        # Matrix size
        size_group = QGroupBox("Matrix Size")
        size_layout = QFormLayout()
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(self.current_width)
        size_layout.addRow("Width:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(self.current_height)
        size_layout.addRow("Height:", self.height_spin)
        
        size_group.setLayout(size_layout)
        right_layout.addWidget(size_group)
        
        right_layout.addStretch()
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Pattern")
        self.generate_btn.clicked.connect(self._on_generate)
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Populate template list
        self._refresh_template_list()
    
    def _refresh_template_list(self):
        """Refresh template list based on selected category."""
        self.template_list.clear()
        
        category = self.category_combo.currentData()
        templates = self.pattern_service.list_templates(category)
        
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.UserRole, template)
            self.template_list.addItem(item)
    
    def _on_category_changed(self):
        """Handle category selection change."""
        self._refresh_template_list()
    
    def _on_template_selected(self):
        """Handle template selection."""
        items = self.template_list.selectedItems()
        if not items:
            self.selected_template = None
            self.description_text.clear()
            self._clear_parameters()
            self.generate_btn.setEnabled(False)
            return
        
        template = items[0].data(Qt.UserRole)
        self.selected_template = template
        
        # Update description
        self.description_text.setText(template.description)
        
        # Create parameter controls
        self._clear_parameters()
        self._create_parameter_controls(template)
        
        self.generate_btn.setEnabled(True)
    
    def _clear_parameters(self):
        """Clear parameter controls."""
        while self.parameters_layout.rowCount() > 0:
            self.parameters_layout.removeRow(0)
        self._parameter_widgets = {}
    
    def _create_parameter_controls(self, template: PatternTemplate):
        """Create parameter input controls for template."""
        self._parameter_widgets = {}
        
        for param_name, param_value in template.parameters.items():
            if param_name in ["width", "height"]:
                continue  # Handled separately
            
            if isinstance(param_value, str):
                widget = QLineEdit(str(param_value))
                self._parameter_widgets[param_name] = widget
                self.parameters_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, int):
                widget = QSpinBox()
                widget.setRange(1, 1000)
                widget.setValue(param_value)
                self._parameter_widgets[param_name] = widget
                self.parameters_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, float):
                # Use spinbox for floats too
                widget = QSpinBox()
                widget.setRange(1, 1000)
                widget.setValue(int(param_value * 100))
                widget.setSuffix(" %")
                self._parameter_widgets[param_name] = widget
                self.parameters_layout.addRow(f"{param_name.title()}:", widget)
            elif isinstance(param_value, tuple) and len(param_value) == 3:
                # RGB color - use line edit for now
                widget = QLineEdit(f"{param_value[0]},{param_value[1]},{param_value[2]}")
                self._parameter_widgets[param_name] = widget
                self.parameters_layout.addRow(f"{param_name.title()}:", widget)
    
    def _on_generate(self):
        """Generate pattern from selected template."""
        if not self.selected_template:
            return
        
        # Collect parameters
        params = {}
        for param_name, widget in self._parameter_widgets.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
                # Try to parse as tuple for colors
                if "," in value:
                    try:
                        parts = [int(x.strip()) for x in value.split(",")]
                        if len(parts) == 3:
                            params[param_name] = tuple(parts)
                        else:
                            params[param_name] = value
                    except ValueError:
                        params[param_name] = value
                else:
                    params[param_name] = value
            elif isinstance(widget, QSpinBox):
                value = widget.value()
                if widget.suffix() == " %":
                    value = value / 100.0
                params[param_name] = value
        
        # Add matrix size
        params["width"] = self.width_spin.value()
        params["height"] = self.height_spin.value()
        
        try:
            # Generate pattern using PatternService
            pattern = self.pattern_service.generate_from_template(
                self.selected_template.name,
                params["width"],
                params["height"],
                **{k: v for k, v in params.items() if k not in ["width", "height"]}
            )
            
            # Emit signal
            self.pattern_generated.emit(pattern)
            
            QMessageBox.information(
                self,
                "Pattern Generated",
                f"Pattern '{pattern.name}' generated successfully!\n\n"
                f"Size: {pattern.metadata.width}×{pattern.metadata.height}\n"
                f"Frames: {len(pattern.frames)}"
            )
            
            self.accept()
        
        except Exception as e:
            logger.error(f"Failed to generate pattern: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Generation Failed",
                f"Failed to generate pattern:\n\n{str(e)}"
            )

