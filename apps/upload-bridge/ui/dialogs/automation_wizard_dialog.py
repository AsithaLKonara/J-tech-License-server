from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox,
    QLabel,
)
from PySide6.QtCore import Qt

from domain.actions import DesignAction


class AutomationWizardDialog(QDialog):
    """Guided builder for stacking automation actions."""

    def __init__(self, action_config: Dict[str, Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Automation Wizard")
        self.resize(520, 560)
        self._action_config = action_config
        self._sequence: List[DesignAction] = []
        self._result_actions: List[DesignAction] = []
        self._param_widgets: Dict[str, object] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        action_row.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        for name in sorted(action_config.keys()):
            self.action_combo.addItem(name.title(), name)
        self.action_combo.currentTextChanged.connect(self._rebuild_param_form)
        action_row.addWidget(self.action_combo, 1)

        self.add_step_btn = QPushButton("Add Step")
        self.add_step_btn.clicked.connect(self._add_step)
        action_row.addWidget(self.add_step_btn)
        layout.addLayout(action_row)

        self.param_form = QFormLayout()
        layout.addLayout(self.param_form)

        list_row = QHBoxLayout()
        self.sequence_list = QListWidget()
        list_row.addWidget(self.sequence_list, 1)
        side_buttons = QVBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_step)
        side_buttons.addWidget(remove_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_steps)
        side_buttons.addWidget(clear_btn)
        side_buttons.addStretch()
        list_row.addLayout(side_buttons)
        layout.addLayout(list_row)

        hooks_group = QVBoxLayout()
        hooks_group.addWidget(QLabel("Post-processing hooks:"))
        self.fade_in_checkbox = QCheckBox("Fade in across frames")
        hooks_group.addWidget(self.fade_in_checkbox)
        self.fade_out_checkbox = QCheckBox("Fade out across frames")
        hooks_group.addWidget(self.fade_out_checkbox)
        self.layer_checkbox = QCheckBox("Duplicate frames to new overlay layer")
        hooks_group.addWidget(self.layer_checkbox)
        layout.addLayout(hooks_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._rebuild_param_form()

    def _rebuild_param_form(self) -> None:
        while self.param_form.rowCount():
            self.param_form.removeRow(0)
        self._param_widgets.clear()
        action_key = self.action_combo.currentData()
        config = self._action_config.get(action_key, {})
        for param, meta in config.items():
            widget = self._create_widget_for_param(meta)
            self._param_widgets[param] = widget
            label = meta.get("label", param.title())
            self.param_form.addRow(label + ":", widget)
        # Common repeat + gap fields
        repeat = QSpinBox()
        repeat.setRange(1, 999)
        repeat.setValue(1)
        self.param_form.addRow("Repeat:", repeat)
        self._param_widgets["repeat"] = repeat
        gap = QSpinBox()
        gap.setRange(0, 5000)
        gap.setSuffix(" ms")
        self.param_form.addRow("Gap:", gap)
        self._param_widgets["gap_ms"] = gap

    def _create_widget_for_param(self, meta: Dict):
        param_type = meta.get("type", "str")
        default = meta.get("default")
        if param_type == "choice":
            combo = QComboBox()
            for choice in meta.get("choices", []):
                combo.addItem(choice, choice)
            if default:
                idx = combo.findData(default)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            return combo
        if param_type == "int":
            spin = QSpinBox()
            spin.setRange(int(meta.get("min", -999)), int(meta.get("max", 999)))
            spin.setValue(int(default or 0))
            return spin
        if param_type == "float":
            dspin = QDoubleSpinBox()
            dspin.setDecimals(2)
            dspin.setRange(float(meta.get("min", -999.0)), float(meta.get("max", 999.0)))
            dspin.setSingleStep(meta.get("step", 0.1))
            dspin.setValue(float(default or 0.0))
            return dspin
        line = QLineEdit()
        if default is not None:
            line.setText(str(default))
        return line

    def _add_step(self) -> None:
        action_key = self.action_combo.currentData()
        label = self.action_combo.currentText()
        params: Dict[str, object] = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QComboBox):
                params[name] = widget.currentData() or widget.currentText()
            elif isinstance(widget, QSpinBox):
                params[name] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[name] = widget.value()
            else:
                params[name] = widget.text().strip()
        action = DesignAction(name=label, action_type=action_key, params=params)
        self._sequence.append(action)
        item = QListWidgetItem(f"{label} – {params}")
        self.sequence_list.addItem(item)

    def _remove_selected_step(self) -> None:
        row = self.sequence_list.currentRow()
        if row < 0:
            return
        self.sequence_list.takeItem(row)
        del self._sequence[row]

    def _clear_steps(self) -> None:
        self.sequence_list.clear()
        self._sequence.clear()

    def _accept(self) -> None:
        if not self._sequence:
            QMessageBox.warning(self, "No Steps", "Add at least one automation step.")
            return
        self._result_actions = list(self._sequence)
        self.accept()

    def built_actions(self) -> List[DesignAction]:
        return list(self._result_actions)

    @property
    def apply_fade_in(self) -> bool:
        return self.fade_in_checkbox.isChecked()

    @property
    def apply_fade_out(self) -> bool:
        return self.fade_out_checkbox.isChecked()

    @property
    def duplicate_layer(self) -> bool:
        return self.layer_checkbox.isChecked()

