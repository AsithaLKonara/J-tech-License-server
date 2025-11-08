"""
Design Tools Tab - LED matrix pattern authoring environment.

This tab provides an interactive workspace for crafting LED matrix animations.
Users can paint frames, manage palettes, queue automation actions (scroll,
mirror, rotate, etc.), and preview the resulting animation.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
    QMessageBox,
    QScrollArea,
    QColorDialog,
    QSlider,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from core.pattern import Pattern, Frame, PatternMetadata  # noqa: E402
from ui.widgets.matrix_design_canvas import MatrixDesignCanvas  # noqa: E402
from ui.widgets.enhanced_led_simulator import EnhancedLEDSimulatorWidget  # noqa: E402


@dataclass
class DesignAction:
    name: str
    action_type: str
    params: Dict[str, object]


class DesignToolsTab(QWidget):
    """
    Comprehensive LED matrix design studio.

    Key capabilities:
        - Interactive matrix painting canvas
        - Palette-based color selection
        - Frame management (add, duplicate, delete, reorder)
        - Automation action queue (scroll, rotate, mirror, invert, etc.)
        - Live preview using Enhanced LED simulator
        - Pattern import/export with rest of application
    """

    pattern_modified = Signal()
    pattern_created = Signal(Pattern)

    DEFAULT_COLORS = [
        (0, 0, 0),
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (255, 128, 0),
        (255, 0, 128),
        (0, 128, 255),
        (128, 0, 255),
        (0, 255, 128),
        (128, 255, 0),
        (128, 128, 128),
        (64, 64, 64),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._pattern: Optional[Pattern] = None
        self._current_frame_index: int = 0
        self._frame_duration_ms: int = 50
        self._action_queue: List[DesignAction] = []

        self._setup_ui()
        self._create_default_pattern()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        # Left column: canvas + frames + preview
        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        canvas_group = QGroupBox("Matrix Designer")
        canvas_layout = QVBoxLayout()
        canvas_layout.setSpacing(8)

        self.canvas = MatrixDesignCanvas(width=12, height=6, pixel_size=28)
        self.canvas.pixel_updated.connect(self._on_canvas_pixel_updated)
        canvas_layout.addWidget(self.canvas, stretch=1)

        canvas_status = QLabel("Click to paint. Right-click to erase.")
        canvas_status.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        canvas_layout.addWidget(canvas_status)

        canvas_group.setLayout(canvas_layout)
        left_column.addWidget(canvas_group, stretch=3)

        # Frame management
        frame_group = QGroupBox("Frames")
        frame_layout = QVBoxLayout()
        frame_layout.setSpacing(6)

        self.frame_list = QListWidget()
        self.frame_list.currentRowChanged.connect(self._on_frame_selected)
        frame_layout.addWidget(self.frame_list, stretch=1)

        frame_button_row = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self._on_add_frame)
        frame_button_row.addWidget(add_btn)

        dup_btn = QPushButton("🧬 Duplicate")
        dup_btn.clicked.connect(self._on_duplicate_frame)
        frame_button_row.addWidget(dup_btn)

        del_btn = QPushButton("🗑 Delete")
        del_btn.clicked.connect(self._on_delete_frame)
        frame_button_row.addWidget(del_btn)

        frame_button_row.addStretch()
        frame_layout.addLayout(frame_button_row)

        frame_move_row = QHBoxLayout()
        up_btn = QPushButton("⬆ Move Up")
        up_btn.clicked.connect(lambda: self._on_move_frame(-1))
        frame_move_row.addWidget(up_btn)

        down_btn = QPushButton("⬇ Move Down")
        down_btn.clicked.connect(lambda: self._on_move_frame(1))
        frame_move_row.addWidget(down_btn)

        frame_move_row.addStretch()
        frame_layout.addLayout(frame_move_row)

        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Frame duration (ms):"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 2000)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch()
        frame_layout.addLayout(duration_row)

        frame_group.setLayout(frame_layout)
        left_column.addWidget(frame_group, stretch=2)

        # Live preview
        preview_group = QGroupBox("Live Preview")
        preview_layout = QVBoxLayout()
        self.preview_widget = EnhancedLEDSimulatorWidget()
        preview_layout.addWidget(self.preview_widget)

        sync_button = QPushButton("🔄 Sync Preview")
        sync_button.clicked.connect(self._refresh_preview)
        preview_layout.addWidget(sync_button)

        preview_group.setLayout(preview_layout)
        left_column.addWidget(preview_group, stretch=2)

        root_layout.addLayout(left_column, stretch=2)

        # Right column (scroll area for tools)
        tools_scroll = QScrollArea()
        tools_scroll.setWidgetResizable(True)
        tools_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tools_container = QWidget()
        tools_layout = QVBoxLayout(tools_container)
        tools_layout.setSpacing(12)

        # Palette section
        palette_group = QGroupBox("Palette")
        palette_layout = QVBoxLayout()
        palette_layout.setSpacing(6)

        palette_buttons_layout = QGridLayout()
        for idx, color in enumerate(self.DEFAULT_COLORS):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"background-color: rgb{color}; border: 1px solid #444;")
            btn.clicked.connect(lambda checked=False, c=color: self._on_palette_selected(c))
            row = idx // 4
            col = idx % 4
            palette_buttons_layout.addWidget(btn, row, col)
        palette_layout.addLayout(palette_buttons_layout)

        preview_row = QHBoxLayout()
        preview_row.addWidget(QLabel("Current colour:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid #666;")
        preview_row.addWidget(self.color_preview)
        preview_row.addStretch()
        palette_layout.addLayout(preview_row)

        self.channel_sliders: Dict[str, Tuple[QSlider, QSpinBox]] = {}
        for channel, idx in zip(("R", "G", "B"), range(3)):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{channel}:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setValue(self._current_color[idx])
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setValue(self._current_color[idx])
            slider.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="slider"))
            spin.valueChanged.connect(lambda val, ch=channel: self._on_channel_slider_changed(ch, val, source="spin"))
            row_layout.addWidget(slider)
            row_layout.addWidget(spin)
            palette_layout.addLayout(row_layout)
            self.channel_sliders[channel] = (slider, spin)

        gradient_group = QGroupBox("Gradient")
        gradient_layout = QVBoxLayout()
        gradient_button_row = QHBoxLayout()
        self.gradient_start_btn = QPushButton("Start colour")
        self.gradient_start_btn.clicked.connect(lambda: self._choose_gradient_colour("start"))
        gradient_button_row.addWidget(self.gradient_start_btn)
        self.gradient_end_btn = QPushButton("End colour")
        self.gradient_end_btn.clicked.connect(lambda: self._choose_gradient_colour("end"))
        gradient_button_row.addWidget(self.gradient_end_btn)
        gradient_layout.addLayout(gradient_button_row)

        gradient_config_row = QHBoxLayout()
        gradient_config_row.addWidget(QLabel("Steps:"))
        self.gradient_steps_spin = QSpinBox()
        self.gradient_steps_spin.setRange(1, 256)
        self.gradient_steps_spin.setValue(32)
        gradient_config_row.addWidget(self.gradient_steps_spin)

        gradient_config_row.addWidget(QLabel("Orientation:"))
        self.gradient_orientation_combo = QComboBox()
        self.gradient_orientation_combo.addItems(["Horizontal", "Vertical", "Radial"])
        gradient_config_row.addWidget(self.gradient_orientation_combo)
        gradient_config_row.addStretch()
        gradient_layout.addLayout(gradient_config_row)

        apply_gradient_btn = QPushButton("Apply Gradient To Frame")
        apply_gradient_btn.clicked.connect(self._apply_gradient_from_controls)
        gradient_layout.addWidget(apply_gradient_btn)

        gradient_group.setLayout(gradient_layout)
        palette_layout.addWidget(gradient_group)

        palette_group.setLayout(palette_layout)
        tools_layout.addWidget(palette_group)

        # Ensure UI reflects default colours
        self._sync_channel_controls(self._current_color)
        self.gradient_start_btn.setStyleSheet(f"background-color: rgb{self._start_gradient_color};")
        self.gradient_end_btn.setStyleSheet(f"background-color: rgb{self._end_gradient_color};")

        # Matrix configuration
        matrix_group = QGroupBox("Matrix Configuration")
        matrix_layout = QHBoxLayout()
        matrix_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 64)
        self.width_spin.setValue(12)
        self.width_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        matrix_layout.addWidget(self.width_spin)

        matrix_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 64)
        self.height_spin.setValue(6)
        self.height_spin.valueChanged.connect(self._on_matrix_dimension_changed)
        matrix_layout.addWidget(self.height_spin)
        matrix_group.setLayout(matrix_layout)
        tools_layout.addWidget(matrix_group)

        # Automation controls
        automation_group = QGroupBox("Automation Actions")
        automation_layout = QVBoxLayout()

        wipe_row = QHBoxLayout()
        wipe_row.addWidget(QLabel("Wipe:"))
        self.wipe_combo = QComboBox()
        self.wipe_combo.addItems(["Left to Right", "Right to Left", "Top to Bottom", "Bottom to Top"])
        wipe_row.addWidget(self.wipe_combo)
        wipe_add = QPushButton("Add")
        wipe_add.clicked.connect(lambda: self._queue_action("Wipe", "wipe", {"mode": self.wipe_combo.currentText()}))
        wipe_row.addWidget(wipe_add)
        automation_layout.addLayout(wipe_row)

        reveal_row = QHBoxLayout()
        reveal_row.addWidget(QLabel("Reveal:"))
        self.reveal_combo = QComboBox()
        self.reveal_combo.addItems(["Left", "Right", "Top", "Bottom"])
        reveal_row.addWidget(self.reveal_combo)
        reveal_add = QPushButton("Add")
        reveal_add.clicked.connect(lambda: self._queue_action("Reveal", "reveal", {"direction": self.reveal_combo.currentText()}))
        reveal_row.addWidget(reveal_add)
        automation_layout.addLayout(reveal_row)

        scroll_row = QHBoxLayout()
        scroll_row.addWidget(QLabel("Scroll:"))
        self.scroll_combo = QComboBox()
        self.scroll_combo.addItems(["Up", "Down", "Left", "Right"])
        scroll_row.addWidget(self.scroll_combo)
        scroll_add = QPushButton("Add")
        scroll_add.clicked.connect(lambda: self._queue_action("Scroll", "scroll", {"direction": self.scroll_combo.currentText()}))
        scroll_row.addWidget(scroll_add)
        automation_layout.addLayout(scroll_row)

        rotate_row = QHBoxLayout()
        rotate_row.addWidget(QLabel("Rotate:"))
        self.rotate_combo = QComboBox()
        self.rotate_combo.addItems(["90° Clockwise", "90° Counter-clockwise"])
        rotate_row.addWidget(self.rotate_combo)
        rotate_add = QPushButton("Add")
        rotate_add.clicked.connect(lambda: self._queue_action("Rotate", "rotate", {"mode": self.rotate_combo.currentText()}))
        rotate_row.addWidget(rotate_add)
        automation_layout.addLayout(rotate_row)

        mirror_row = QHBoxLayout()
        mirror_btn = QPushButton("Mirror Horizontal")
        mirror_btn.clicked.connect(lambda: self._queue_action("Mirror Horizontal", "mirror", {"axis": "horizontal"}))
        mirror_row.addWidget(mirror_btn)
        flip_btn = QPushButton("Flip Vertical")
        flip_btn.clicked.connect(lambda: self._queue_action("Flip Vertical", "flip", {"axis": "vertical"}))
        mirror_row.addWidget(flip_btn)
        invert_btn = QPushButton("Invert Colours")
        invert_btn.clicked.connect(lambda: self._queue_action("Invert Colours", "invert", {}))
        mirror_row.addWidget(invert_btn)
        automation_layout.addLayout(mirror_row)

        automation_group.setLayout(automation_layout)
        tools_layout.addWidget(automation_group)

        # Action list
        action_group = QGroupBox("Action Queue")
        action_layout = QVBoxLayout()
        self.action_list = QListWidget()
        action_layout.addWidget(self.action_list)

        action_button_row = QHBoxLayout()
        remove_action_btn = QPushButton("Remove Selected")
        remove_action_btn.clicked.connect(self._on_remove_action)
        action_button_row.addWidget(remove_action_btn)
        clear_actions_btn = QPushButton("Clear All")
        clear_actions_btn.clicked.connect(self._on_clear_actions)
        action_button_row.addWidget(clear_actions_btn)
        action_layout.addLayout(action_button_row)

        apply_actions_btn = QPushButton("▶ Apply Actions")
        apply_actions_btn.clicked.connect(self._apply_actions_to_frames)
        action_layout.addWidget(apply_actions_btn)

        action_group.setLayout(action_layout)
        tools_layout.addWidget(action_group)

        # Processing options
        processing_group = QGroupBox("Processing Range")
        processing_layout = QVBoxLayout()
        self.source_button_group = QButtonGroup(self)
        use_first = QRadioButton("Use first frame as source")
        each_frame = QRadioButton("Use each frame independently")
        increment_frame = QRadioButton("Increment parameters per frame")
        use_first.setChecked(True)

        self.source_button_group.addButton(use_first, 0)
        self.source_button_group.addButton(each_frame, 1)
        self.source_button_group.addButton(increment_frame, 2)

        processing_layout.addWidget(use_first)
        processing_layout.addWidget(each_frame)
        processing_layout.addWidget(increment_frame)

        range_row = QHBoxLayout()
        range_row.addWidget(QLabel("Frame start:"))
        self.frame_start_spin = QSpinBox()
        self.frame_start_spin.setMinimum(1)
        self.frame_start_spin.setValue(1)
        range_row.addWidget(self.frame_start_spin)

        range_row.addWidget(QLabel("Frame end:"))
        self.frame_end_spin = QSpinBox()
        self.frame_end_spin.setMinimum(1)
        self.frame_end_spin.setValue(1)
        range_row.addWidget(self.frame_end_spin)
        processing_layout.addLayout(range_row)

        tools_layout.addWidget(processing_group)

        # Export controls
        export_group = QGroupBox("Pattern Export")
        export_layout = QVBoxLayout()
        self.pattern_name_combo = QComboBox()
        self.pattern_name_combo.setEditable(True)
        self.pattern_name_combo.lineEdit().setPlaceholderText("Pattern name (optional)")
        export_layout.addWidget(self.pattern_name_combo)

        export_button = QPushButton("💾 Save Design to Pattern")
        export_button.clicked.connect(self._emit_pattern)
        export_layout.addWidget(export_button)

        tools_layout.addWidget(export_group)
        tools_layout.addStretch()

        tools_scroll.setWidget(tools_container)
        root_layout.addWidget(tools_scroll, stretch=1)

    # ------------------------------------------------------------------
    # Pattern management
    # ------------------------------------------------------------------
    def _create_default_pattern(self):
        width = self.width_spin.value()
        height = self.height_spin.value()
        blank_frame = self._create_blank_frame(width, height)
        metadata = PatternMetadata(width=width, height=height)
        self._pattern = Pattern(name="New Design", metadata=metadata, frames=[blank_frame])
        self._current_frame_index = 0
        self._refresh_frame_list()
        self.canvas.set_matrix_size(width, height)
        self.canvas.set_frame_pixels(blank_frame.pixels)
        self._refresh_preview(no_message=True)

    def _create_blank_frame(self, width: int, height: int) -> Frame:
        pixels = [(0, 0, 0)] * (width * height)
        return Frame(pixels=pixels, duration_ms=self._frame_duration_ms)

    def load_pattern(self, pattern: Pattern, file_path: Optional[str] = None):
        """Load external pattern into design tab."""
        try:
            pattern_copy = Pattern.from_dict(pattern.to_dict()) if hasattr(pattern, "to_dict") else pattern
        except Exception:
            pattern_copy = pattern

        self._pattern = pattern_copy
        width = pattern_copy.metadata.width
        height = pattern_copy.metadata.height
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)

        self.canvas.set_matrix_size(width, height)
        self._current_frame_index = 0
        self._frame_duration_ms = pattern_copy.frames[0].duration_ms if pattern_copy.frames else self._frame_duration_ms
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.blockSignals(False)
        self._refresh_frame_list()
        self._load_current_frame_into_canvas()
        self._refresh_preview(no_message=True)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
        if not self._pattern or not self._pattern.frames:
            return
        frame = self._pattern.frames[self._current_frame_index]
        width, height = self.canvas.matrix_size()
        idx = y * width + x
        if 0 <= idx < len(frame.pixels):
            frame.pixels[idx] = color
            self.pattern_modified.emit()
            self._refresh_preview(no_message=True)

    def _on_palette_selected(self, color: Tuple[int, int, int]):
        self._current_color = color
        self.canvas.set_current_color(color)
        self._sync_channel_controls(color)

    def _sync_channel_controls(self, color: Tuple[int, int, int]):
        r, g, b = color
        if hasattr(self, "color_preview"):
            self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #666;")
        for channel, value in zip(("R", "G", "B"), (r, g, b)):
            if channel not in getattr(self, "channel_sliders", {}):
                continue
            slider, spin = self.channel_sliders[channel]
            slider.blockSignals(True)
            spin.blockSignals(True)
            slider.setValue(value)
            spin.setValue(value)
            slider.blockSignals(False)
            spin.blockSignals(False)

    def _on_channel_slider_changed(self, channel: str, value: int, source: str):
        slider, spin = self.channel_sliders[channel]
        if source == "slider":
            spin.blockSignals(True)
            spin.setValue(value)
            spin.blockSignals(False)
        else:
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)

        r = self.channel_sliders["R"][0].value()
        g = self.channel_sliders["G"][0].value()
        b = self.channel_sliders["B"][0].value()
        self._current_color = (r, g, b)
        self._sync_channel_controls(self._current_color)
        self.canvas.set_current_color(self._current_color)

    def _on_matrix_dimension_changed(self):
        if not self._pattern:
            return
        width = self.width_spin.value()
        height = self.height_spin.value()
        metadata = self._pattern.metadata
        metadata.width = width
        metadata.height = height
        self.canvas.set_matrix_size(width, height)

        for i, frame in enumerate(self._pattern.frames):
            expected = width * height
            if frame.led_count != expected:
                pixels = frame.pixels[:expected]
                if len(pixels) < expected:
                    pixels += [(0, 0, 0)] * (expected - len(pixels))
                self._pattern.frames[i] = Frame(pixels=pixels, duration_ms=frame.duration_ms)

        self._load_current_frame_into_canvas()
        self._refresh_frame_list()
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_frame_selected(self, index: int):
        if index < 0 or not self._pattern or index >= len(self._pattern.frames):
            return
        self._current_frame_index = index
        self._frame_duration_ms = self._pattern.frames[index].duration_ms
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._frame_duration_ms)
        self.duration_spin.blockSignals(False)
        self._load_current_frame_into_canvas()

    def _on_add_frame(self):
        if not self._pattern:
            return
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        new_frame = self._create_blank_frame(width, height)
        insert_at = self._current_frame_index + 1
        self._pattern.frames.insert(insert_at, new_frame)
        self._refresh_frame_list()
        self.frame_list.setCurrentRow(insert_at)
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_duplicate_frame(self):
        if not self._pattern or not self._pattern.frames:
            return
        frame = self._pattern.frames[self._current_frame_index].copy()
        insert_at = self._current_frame_index + 1
        self._pattern.frames.insert(insert_at, frame)
        self._refresh_frame_list()
        self.frame_list.setCurrentRow(insert_at)
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_delete_frame(self):
        if not self._pattern or len(self._pattern.frames) <= 1:
            QMessageBox.information(self, "Cannot Delete Frame", "At least one frame is required.")
            return
        del self._pattern.frames[self._current_frame_index]
        self._current_frame_index = max(0, self._current_frame_index - 1)
        self._refresh_frame_list()
        self.frame_list.setCurrentRow(self._current_frame_index)
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_move_frame(self, delta: int):
        if not self._pattern:
            return
        new_index = self._current_frame_index + delta
        if not (0 <= new_index < len(self._pattern.frames)):
            return
        self._pattern.frames[self._current_frame_index], self._pattern.frames[new_index] = (
            self._pattern.frames[new_index],
            self._pattern.frames[self._current_frame_index],
        )
        self._current_frame_index = new_index
        self._refresh_frame_list()
        self.frame_list.setCurrentRow(new_index)
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_duration_changed(self, value: int):
        self._frame_duration_ms = value
        if not self._pattern or not self._pattern.frames:
            return
        self._pattern.frames[self._current_frame_index].duration_ms = value
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _on_remove_action(self):
        row = self.action_list.currentRow()
        if row < 0:
            return
        del self._action_queue[row]
        self.action_list.takeItem(row)

    def _on_clear_actions(self):
        self._action_queue.clear()
        self.action_list.clear()

    # ------------------------------------------------------------------
    # Action queue
    # ------------------------------------------------------------------
    def _queue_action(self, label: str, action_type: str, params: Dict[str, object]):
        action = DesignAction(name=label, action_type=action_type, params=params)
        self._action_queue.append(action)
        item = QListWidgetItem(f"{label} • {params if params else ''}")
        self.action_list.addItem(item)

    def _apply_actions_to_frames(self):
        if not self._pattern or not self._action_queue:
            QMessageBox.information(self, "No Actions", "Add actions to the queue first.")
            return

        start = self.frame_start_spin.value() - 1
        end = self.frame_end_spin.value() - 1
        if start < 0:
            start = 0
        if end >= len(self._pattern.frames):
            end = len(self._pattern.frames) - 1
        if end < start:
            QMessageBox.warning(self, "Invalid Range", "Frame end must be after frame start.")
            return

        updated_frames = 0
        for idx in range(start, end + 1):
            for action in self._action_queue:
                if self._perform_action(self._pattern.frames[idx], action):
                    updated_frames += 1

        if updated_frames == 0:
            QMessageBox.information(self, "Actions Applied", "Actions executed (no visible changes).")
        else:
            self.pattern_modified.emit()
            self._load_current_frame_into_canvas()
            self._refresh_preview(no_message=True)

    def _perform_action(self, frame: Frame, action: DesignAction) -> bool:
        handlers = {
            "scroll": lambda: self._apply_scroll(frame, action.params.get("direction", "Right")),
            "rotate": lambda: self._apply_rotate(frame, action.params.get("mode", "90° Clockwise")),
            "mirror": lambda: self._apply_mirror(frame, action.params.get("axis", "horizontal")),
            "flip": lambda: self._apply_flip(frame, action.params.get("axis", "vertical")),
            "invert": lambda: self._apply_invert(frame),
            "wipe": lambda: self._apply_wipe(frame, action.params.get("mode", "Left to Right")),
            "reveal": lambda: self._apply_reveal(frame, action.params.get("direction", "Left")),
        }

        handler = handlers.get(action.action_type)
        if not handler:
            self._show_not_implemented(action.name)
            return False
        return handler()

    def _show_not_implemented(self, feature_name: str):
        QMessageBox.information(
            self,
            "Coming Soon",
            f"The action '{feature_name}' is not implemented yet. "
            "It is queued here so workflow remains consistent, but no changes were applied.",
        )

    # ------------------------------------------------------------------
    # Frame transformation helpers
    # ------------------------------------------------------------------
    def _frame_to_grid(self, frame: Frame) -> List[List[Tuple[int, int, int]]]:
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        pixels = list(frame.pixels)
        grid = []
        idx = 0
        for _ in range(height):
            row = pixels[idx:idx + width]
            if len(row) < width:
                row += [(0, 0, 0)] * (width - len(row))
            grid.append(row)
            idx += width
        return grid

    def _grid_to_frame(self, grid: List[List[Tuple[int, int, int]]], frame: Frame):
        frame.pixels = [tuple(pixel) for row in grid for pixel in row]

    def _apply_scroll(self, frame: Frame, direction: str) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        new_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

        offsets = {
            "Up": (0, -1),
            "Down": (0, 1),
            "Left": (-1, 0),
            "Right": (1, 0),
        }
        dx, dy = offsets.get(direction, (1, 0))
        for y in range(height):
            for x in range(width):
                src_x = x - dx
                src_y = y - dy
                if 0 <= src_x < width and 0 <= src_y < height:
                    new_grid[y][x] = grid[src_y][src_x]
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_rotate(self, frame: Frame, mode: str) -> bool:
        grid = self._frame_to_grid(frame)
        orig_height = len(grid)
        orig_width = len(grid[0])
        clockwise = "clockwise" in mode.lower()

        rotated = []
        if clockwise:
            for x in range(orig_width):
                new_row = []
                for y in range(orig_height - 1, -1, -1):
                    new_row.append(grid[y][x])
                rotated.append(new_row)
        else:
            for x in range(orig_width - 1, -1, -1):
                new_row = []
                for y in range(orig_height):
                    new_row.append(grid[y][x])
                rotated.append(new_row)

        # After rotation, adjust metadata width/height
        self._pattern.metadata.width = orig_height
        self._pattern.metadata.height = orig_width
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(self._pattern.metadata.width)
        self.height_spin.setValue(self._pattern.metadata.height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self.canvas.set_matrix_size(self._pattern.metadata.width, self._pattern.metadata.height)
        self._grid_to_frame(rotated, frame)
        return True

    def _apply_mirror(self, frame: Frame, axis: str) -> bool:
        grid = self._frame_to_grid(frame)
        axis = axis.lower()
        if axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        elif axis == "vertical":
            new_grid = list(reversed(grid))
        else:
            return False
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_flip(self, frame: Frame, axis: str) -> bool:
        grid = self._frame_to_grid(frame)
        axis = axis.lower()
        if axis == "vertical":
            new_grid = list(reversed(grid))
        elif axis == "horizontal":
            new_grid = [list(reversed(row)) for row in grid]
        else:
            return False
        self._grid_to_frame(new_grid, frame)
        return True

    def _apply_invert(self, frame: Frame) -> bool:
        frame.pixels = [(255 - r, 255 - g, 255 - b) for r, g, b in frame.pixels]
        return True

    def _apply_wipe(self, frame: Frame, mode: str) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        mode = mode.lower()
        if "left" in mode and "right" in mode:
            direction = "horizontal"
            forward = "left" in mode.split("to")[0]
        elif "top" in mode or "bottom" in mode:
            direction = "vertical"
            forward = "top" in mode.split("to")[0]
        else:
            direction = "horizontal"
            forward = True

        if direction == "horizontal":
            for y in range(height):
                row = grid[y]
                ordered = row if forward else list(reversed(row))
                for x in range(width):
                    fade = x / max(1, width - 1)
                    r, g, b = ordered[x]
                    ordered[x] = (int(r * fade), int(g * fade), int(b * fade))
                if not forward:
                    ordered.reverse()
                grid[y] = ordered
        else:
            ordered_rows = grid if forward else list(reversed(grid))
            for idx, row in enumerate(ordered_rows):
                fade = idx / max(1, height - 1)
                ordered_rows[idx] = [(int(r * fade), int(g * fade), int(b * fade)) for r, g, b in row]
            if not forward:
                ordered_rows.reverse()
            grid = ordered_rows

        self._grid_to_frame(grid, frame)
        return True

    def _apply_reveal(self, frame: Frame, direction: str) -> bool:
        grid = self._frame_to_grid(frame)
        width = len(grid[0])
        height = len(grid)
        direction = direction.lower()

        mask_grid = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
        if direction == "left":
            for y in range(height):
                for x in range(width):
                    if x <= width // 2:
                        mask_grid[y][x] = grid[y][x]
        elif direction == "right":
            for y in range(height):
                for x in range(width):
                    if x >= width // 2:
                        mask_grid[y][x] = grid[y][x]
        elif direction == "top":
            for y in range(height):
                if y <= height // 2:
                    mask_grid[y] = list(grid[y])
        elif direction == "bottom":
            for y in range(height):
                if y >= height // 2:
                    mask_grid[y] = list(grid[y])
        else:
            return False

        self._grid_to_frame(mask_grid, frame)
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _refresh_frame_list(self):
        self.frame_list.blockSignals(True)
        self.frame_list.clear()
        if not self._pattern:
            self.frame_list.blockSignals(False)
            return
        for idx, frame in enumerate(self._pattern.frames):
            item = QListWidgetItem(f"Frame {idx + 1} ({frame.duration_ms} ms)")
            self.frame_list.addItem(item)
        self.frame_list.blockSignals(False)
        self.frame_list.setCurrentRow(self._current_frame_index)

        total_frames = len(self._pattern.frames) if self._pattern else 1
        self.frame_start_spin.setMaximum(total_frames)
        self.frame_end_spin.setMaximum(total_frames)
        self.frame_end_spin.setValue(total_frames)

    def _load_current_frame_into_canvas(self):
        if not self._pattern or not self._pattern.frames:
            return
        frame = self._pattern.frames[self._current_frame_index]
        self.canvas.set_frame_pixels(frame.pixels)
        if frame.pixels:
            self._current_color = tuple(frame.pixels[0])
            self.canvas.set_current_color(self._current_color)
            self._sync_channel_controls(self._current_color)

    def _refresh_preview(self, no_message: bool = False):
        if not self._pattern:
            return
        try:
            self.preview_widget.load_pattern(self._pattern)
            if not no_message:
                QMessageBox.information(self, "Preview Updated", "Live preview synced with current design.")
        except Exception as exc:
            if not no_message:
                QMessageBox.warning(self, "Preview Error", f"Failed to refresh preview: {exc}")

    def _emit_pattern(self):
        if not self._pattern:
            return
        name_text = self.pattern_name_combo.currentText().strip()
        if name_text:
            self._pattern.name = name_text
        self.pattern_created.emit(self._pattern)
        QMessageBox.information(self, "Pattern Saved", "Design exported to application. Check other tabs to use it.")

    def _choose_gradient_colour(self, target: str):
        initial = QColor(*self._start_gradient_color) if target == "start" else QColor(*self._end_gradient_color)
        color = QColorDialog.getColor(initial, self, "Select colour")
        if not color.isValid():
            return
        rgb = (color.red(), color.green(), color.blue())
        if target == "start":
            self._start_gradient_color = rgb
            self.gradient_start_btn.setStyleSheet(f"background-color: rgb{rgb};")
        else:
            self._end_gradient_color = rgb
            self.gradient_end_btn.setStyleSheet(f"background-color: rgb{rgb};")

    def _apply_gradient_from_controls(self):
        if not self._pattern or not self._pattern.frames:
            return
        orientation = self.gradient_orientation_combo.currentText()
        steps = self.gradient_steps_spin.value()
        frame = self._pattern.frames[self._current_frame_index]
        self._apply_gradient(frame, orientation, steps)
        self.canvas.set_frame_pixels(frame.pixels)
        self.pattern_modified.emit()
        self._refresh_preview(no_message=True)

    def _apply_gradient(self, frame: Frame, orientation: str, steps: int):
        width = self._pattern.metadata.width
        height = self._pattern.metadata.height
        start_r, start_g, start_b = self._start_gradient_color
        end_r, end_g, end_b = self._end_gradient_color
        gradient_pixels: List[Tuple[int, int, int]] = []

        def interpolate(t: float) -> Tuple[int, int, int]:
            r = int(start_r + (end_r - start_r) * t)
            g = int(start_g + (end_g - start_g) * t)
            b = int(start_b + (end_b - start_b) * t)
            return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        orientation = orientation.lower()
        if orientation == "horizontal":
            denom = max(1, min(steps - 1, width - 1))
            for y in range(height):
                for x in range(width):
                    t = x / denom
                    gradient_pixels.append(interpolate(min(1.0, t)))
        elif orientation == "vertical":
            denom = max(1, min(steps - 1, height - 1))
            for y in range(height):
                t = y / denom
                for x in range(width):
                    gradient_pixels.append(interpolate(min(1.0, t)))
        else:
            center_x = (width - 1) / 2.0
            center_y = (height - 1) / 2.0
            max_dist = ((center_x) ** 2 + (center_y) ** 2) ** 0.5
            denom = max(1e-6, min(max_dist, float(steps)))
            for y in range(height):
                for x in range(width):
                    dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    t = dist / denom
                    gradient_pixels.append(interpolate(min(1.0, t)))

        frame.pixels = gradient_pixels


