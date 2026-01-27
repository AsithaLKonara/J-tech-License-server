"""
Enhanced Text Tool - Widget for advanced text rendering with live preview.

Delivers live preview, multiple font sizes (3×5, 5×7, 7×9, custom bitmap),
text effects (outline, shadow, gradient), character spacing, auto-scroll
preview, alignment controls, and multi-line support. The widget exposes
render/scroll options so the main design tab can generate frames using
the shared TextRenderer pipeline.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QImage, QPixmap, qRgb
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QFontComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QColor, QFont, QImage, QPixmap, qRgb

from domain.text.bitmap_font import BitmapFont
from domain.text.text_renderer import TextRenderer, TextRenderOptions, TextScrollOptions

RGB = Tuple[int, int, int]


class EnhancedTextToolWidget(QWidget):
    text_changed = Signal(str)
    font_changed = Signal(str)
    effects_changed = Signal()
    alignment_changed = Signal(str)
    spacing_changed = Signal(int)
    scroll_settings_changed = Signal()
    generate_requested = Signal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        font_repo=None,
        dimension_provider: Optional[Callable[[], Tuple[int, int]]] = None,
    ):
        super().__init__(parent)
        self.font_repo = font_repo
        self._dimension_provider = dimension_provider or (lambda: (64, 32))
        self._font_designer_callback: Optional[Callable[[], None]] = None

        self._text = ""
        self._font_type = "bitmap"  # "bitmap" or "system"
        self._system_font_name = "Arial"
        self._system_font_size = 12
        self._alignment = "center"
        self._spacing = 0
        self._multi_line = True
        self._selected_font_data: Optional[Tuple[str, ...]] = None
        self._active_bitmap_font: Optional[BitmapFont] = None

        self._primary_color: RGB = (255, 255, 255)
        self._outline_enabled = False
        self._outline_color: RGB = (255, 255, 255)
        self._shadow_enabled = False
        self._shadow_color: RGB = (20, 20, 20)
        self._shadow_offset: Tuple[int, int] = (1, 1)
        self._gradient_enabled = False
        self._gradient_start: RGB = (255, 255, 255)
        self._gradient_end: RGB = (255, 128, 0)
        self._gradient_orientation = "vertical"

        self._renderer = TextRenderer()
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._update_preview)

        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._advance_scroll_frame)
        self._scroll_frames: List[List[RGB]] = []
        self._scroll_frame_index = 0

        self._setup_ui()
        self.refresh_font_list()
        self._update_preview()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_primary_color(self, color: RGB) -> None:
        self._primary_color = color
        self._schedule_preview()

    def set_dimension_provider(self, provider: Callable[[], Tuple[int, int]]) -> None:
        self._dimension_provider = provider
        self._schedule_preview()

    def set_font_designer_callback(self, callback: Callable[[], None]) -> None:
        self._font_designer_callback = callback

    def refresh_font_list(self) -> None:
        if not hasattr(self, "font_combo"):
            return
        current_data = self.font_combo.currentData()
        self.font_combo.blockSignals(True)
        self.font_combo.clear()
        # Built-in presets
        self.font_combo.addItem("3×5 (Mini)", ("builtin", 3, 5))
        self.font_combo.addItem("5×7 (Classic)", ("builtin", 5, 7))
        self.font_combo.addItem("7×9 (Large)", ("builtin", 7, 9))
        if self.font_repo:
            for name in sorted(self.font_repo.list_fonts()):
                self.font_combo.addItem(f"{name} (Custom)", ("custom", name))
        self.font_combo.blockSignals(False)
        if current_data:
            idx = self.font_combo.findData(current_data)
            if idx >= 0:
                self.font_combo.setCurrentIndex(idx)
        if self.font_combo.count() > 1 and self.font_combo.currentIndex() < 0:
            self.font_combo.setCurrentIndex(1)
        self._on_font_changed(self.font_combo.currentIndex())

    def get_text(self) -> str:
        return self._text

    def build_render_options(self, width: int, height: int, color: RGB) -> TextRenderOptions:
        font_size = self._active_bitmap_font.height if self._active_bitmap_font else self._font_height_from_combo()
        return TextRenderOptions(
            width=width,
            height=height,
            color=color,
            background=(0, 0, 0),
            alignment=self._alignment,
            spacing=self._spacing,
            line_spacing=1,
            multiline=self._multi_line,
            font_size=self._system_font_size if self._font_type == "system" else font_size,
            font_name=self._system_font_name if self._font_type == "system" else None,
            bitmap_font=None if self._font_type == "system" else self._active_bitmap_font,
            outline=self._outline_enabled,
            outline_color=self._outline_color if self._outline_enabled else None,
            outline_thickness=1,
            shadow=self._shadow_enabled,
            shadow_color=self._shadow_color if self._shadow_enabled else None,
            shadow_offset=self._shadow_offset,
            gradient=self._gradient_enabled,
            gradient_start=self._gradient_start if self._gradient_enabled else None,
            gradient_end=self._gradient_end if self._gradient_enabled else None,
            gradient_orientation=self._gradient_orientation,
        )

    def get_scroll_options(self, fallback_direction: str) -> TextScrollOptions:
        direction = fallback_direction
        if self.scroll_preview_checkbox.isChecked():
            direction = self.scroll_direction_combo.currentText().lower()
        elif hasattr(self, "anim_type_combo"):
             # Use the global setting if preview is off
             text = self.anim_type_combo.currentText()
             if "Scrolling" in text:
                 direction = text.split()[-1].lower()
        
        step = max(1, self.scroll_speed_slider.value() // 2)
        padding = 4
        return TextScrollOptions(direction=direction, step=step, padding=padding)

    def get_animation_type(self) -> str:
        return self.anim_type_combo.currentText()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addWidget(self._build_text_group())
        root.addWidget(self._build_font_group())
        root.addWidget(self._build_animation_settings_group())
        root.addWidget(self._build_layout_group())
        root.addWidget(self._build_spacing_group())
        root.addWidget(self._build_effects_group())
        root.addWidget(self._build_alignment_group())
        root.addWidget(self._build_scroll_group())
        root.addWidget(self._build_preview_group(), stretch=1)

        generate_btn = QPushButton("Generate Text Animation")
        generate_btn.clicked.connect(self.generate_requested.emit)
        root.addWidget(generate_btn)

    def _build_text_group(self) -> QGroupBox:
        group = QGroupBox("Text Input")
        layout = QVBoxLayout(group)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Enter text… (multi-line supported)")
        self.text_input.setMaximumHeight(120)
        self.text_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.text_input)
        return group

    def _build_font_group(self) -> QGroupBox:
        group = QGroupBox("Font")
        layout = QVBoxLayout(group)
        
        # Font Type Toggle
        type_row = QHBoxLayout()
        self.font_type_group = QButtonGroup(self)
        self.bitmap_radio = QRadioButton("Bitmap Font")
        self.system_radio = QRadioButton("System Font")
        self.bitmap_radio.setChecked(True)
        self.font_type_group.addButton(self.bitmap_radio, 0)
        self.font_type_group.addButton(self.system_radio, 1)
        type_row.addWidget(self.bitmap_radio)
        type_row.addWidget(self.system_radio)
        type_row.addStretch()
        layout.addLayout(type_row)
        
        # Bitmap Font Section
        self.bitmap_section = QWidget()
        bitmap_layout = QHBoxLayout(self.bitmap_section)
        bitmap_layout.setContentsMargins(0, 0, 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.currentIndexChanged.connect(self._on_font_changed)
        bitmap_layout.addWidget(QLabel("Preset:"))
        bitmap_layout.addWidget(self.font_combo, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Refresh custom bitmap font list")
        refresh_btn.clicked.connect(self.refresh_font_list)
        bitmap_layout.addWidget(refresh_btn)

        designer_btn = QPushButton("Font Designer…")
        designer_btn.clicked.connect(self._on_font_designer_requested)
        bitmap_layout.addWidget(designer_btn)
        layout.addWidget(self.bitmap_section)
        
        # System Font Section
        self.system_section = QWidget()
        system_layout = QVBoxLayout(self.system_section)
        system_layout.setContentsMargins(0, 0, 0, 0)
        
        font_name_row = QHBoxLayout()
        self.system_font_combo = QFontComboBox()
        self.system_font_combo.currentFontChanged.connect(self._on_system_font_changed)
        font_name_row.addWidget(QLabel("Family:"))
        font_name_row.addWidget(self.system_font_combo, 1)
        system_layout.addLayout(font_name_row)
        
        font_size_row = QHBoxLayout()
        self.system_size_spin = QSlider(Qt.Horizontal)
        self.system_size_spin.setRange(4, 64)
        self.system_size_spin.setValue(12)
        self.system_size_spin.valueChanged.connect(self._on_system_font_changed)
        self.system_size_label = QLabel("12 px")
        font_size_row.addWidget(QLabel("Size:"))
        font_size_row.addWidget(self.system_size_spin, 1)
        font_size_row.addWidget(self.system_size_label)
        system_layout.addLayout(font_size_row)
        
        layout.addWidget(self.system_section)
        self.system_section.setVisible(False)
        
        # Connect toggles
        self.bitmap_radio.toggled.connect(self._on_font_type_toggled)
        self.system_radio.toggled.connect(self._on_font_type_toggled)
        
        return group

    def _build_animation_settings_group(self) -> QGroupBox:
        group = QGroupBox("Animation Settings")
        layout = QVBoxLayout(group)
        
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Type:"))
        self.anim_type_combo = QComboBox()
        self.anim_type_combo.addItems([
            "Typed (Character by Character)", 
            "Scrolling Left", 
            "Scrolling Right", 
            "Scrolling Up", 
            "Scrolling Down"
        ])
        type_row.addWidget(self.anim_type_combo, 1)
        layout.addLayout(type_row)
        
        # Frames per character (for typing)
        self.typing_speed_row = QHBoxLayout()
        self.typing_speed_row.addWidget(QLabel("Frames/Char:"))
        self.frames_per_char_spin = QSlider(Qt.Horizontal)
        self.frames_per_char_spin.setRange(1, 10)
        self.frames_per_char_spin.setValue(2)
        self.frames_per_char_label = QLabel("2")
        self.frames_per_char_spin.valueChanged.connect(lambda v: self.frames_per_char_label.setText(str(v)))
        self.typing_speed_row.addWidget(self.frames_per_char_spin, 1)
        self.typing_speed_row.addWidget(self.frames_per_char_label)
        layout.addLayout(self.typing_speed_row)
        
        def on_type_changed(text):
            is_typing = "Typed" in text
            self.typing_speed_row.setEnabled(is_typing)
            
        self.anim_type_combo.currentTextChanged.connect(on_type_changed)
        on_type_changed(self.anim_type_combo.currentText())
        
        return group

    def _build_layout_group(self) -> QGroupBox:
        group = QGroupBox("Layout & Flow")
        layout = QVBoxLayout(group)
        self.multi_line_checkbox = QCheckBox("Enable multi-line layout")
        self.multi_line_checkbox.setChecked(True)
        self.multi_line_checkbox.toggled.connect(self._on_layout_changed)
        layout.addWidget(self.multi_line_checkbox)
        return group

    def _build_spacing_group(self) -> QGroupBox:
        group = QGroupBox("Character Spacing")
        layout = QVBoxLayout(group)
        row = QHBoxLayout()
        row.addWidget(QLabel("Spacing:"))
        self.spacing_label = QLabel("0 px")
        row.addWidget(self.spacing_label)
        row.addStretch()
        layout.addLayout(row)

        self.spacing_slider = QSlider(Qt.Horizontal)
        self.spacing_slider.setRange(0, 10)
        self.spacing_slider.valueChanged.connect(self._on_spacing_changed)
        layout.addWidget(self.spacing_slider)
        return group

    def _build_effects_group(self) -> QGroupBox:
        group = QGroupBox("Text Effects")
        layout = QVBoxLayout(group)

        self.outline_checkbox = QCheckBox("Outline")
        self.outline_checkbox.toggled.connect(self._on_effects_changed)
        layout.addWidget(self.outline_checkbox)

        outline_row = QHBoxLayout()
        outline_row.addWidget(QLabel("Outline Color:"))
        self.outline_color_btn = QPushButton("Select…")
        self.outline_color_btn.clicked.connect(lambda: self._choose_effect_color("outline"))
        outline_row.addWidget(self.outline_color_btn)
        outline_row.addStretch()
        layout.addLayout(outline_row)

        self.shadow_checkbox = QCheckBox("Shadow")
        self.shadow_checkbox.toggled.connect(self._on_effects_changed)
        layout.addWidget(self.shadow_checkbox)

        shadow_row = QHBoxLayout()
        shadow_row.addWidget(QLabel("Shadow Color:"))
        self.shadow_color_btn = QPushButton("Select…")
        self.shadow_color_btn.clicked.connect(lambda: self._choose_effect_color("shadow"))
        shadow_row.addWidget(self.shadow_color_btn)
        shadow_row.addStretch()
        layout.addLayout(shadow_row)

        self.gradient_checkbox = QCheckBox("Gradient Fill")
        self.gradient_checkbox.toggled.connect(self._on_effects_changed)
        layout.addWidget(self.gradient_checkbox)

        gradient_row = QHBoxLayout()
        self.gradient_start_btn = QPushButton("Start…")
        self.gradient_start_btn.clicked.connect(lambda: self._choose_effect_color("gradient_start"))
        self.gradient_end_btn = QPushButton("End…")
        self.gradient_end_btn.clicked.connect(lambda: self._choose_effect_color("gradient_end"))
        gradient_row.addWidget(QLabel("Gradient Colors:"))
        gradient_row.addWidget(self.gradient_start_btn)
        gradient_row.addWidget(self.gradient_end_btn)
        gradient_row.addStretch()
        layout.addLayout(gradient_row)

        orientation_row = QHBoxLayout()
        orientation_row.addWidget(QLabel("Gradient Axis:"))
        self.gradient_orientation_combo = QComboBox()
        self.gradient_orientation_combo.addItems(["Vertical", "Horizontal"])
        self.gradient_orientation_combo.currentTextChanged.connect(self._on_gradient_orientation_changed)
        orientation_row.addWidget(self.gradient_orientation_combo)
        orientation_row.addStretch()
        layout.addLayout(orientation_row)
        return group

    def _build_alignment_group(self) -> QGroupBox:
        group = QGroupBox("Alignment")
        layout = QHBoxLayout(group)
        self.align_group = QButtonGroup(self)
        self.align_left = QRadioButton("Left")
        self.align_center = QRadioButton("Center")
        self.align_right = QRadioButton("Right")
        self.align_center.setChecked(True)
        for idx, btn in enumerate((self.align_left, self.align_center, self.align_right)):
            self.align_group.addButton(btn, idx)
            layout.addWidget(btn)
        self.align_left.toggled.connect(lambda checked: checked and self._on_alignment_changed("left"))
        self.align_center.toggled.connect(lambda checked: checked and self._on_alignment_changed("center"))
        self.align_right.toggled.connect(lambda checked: checked and self._on_alignment_changed("right"))
        layout.addStretch()
        return group

    def _build_scroll_group(self) -> QGroupBox:
        group = QGroupBox("Auto-Scroll Preview")
        layout = QVBoxLayout(group)
        self.scroll_preview_checkbox = QCheckBox("Animate preview using scroll settings")
        self.scroll_preview_checkbox.toggled.connect(self._on_scroll_settings_changed)
        layout.addWidget(self.scroll_preview_checkbox)

        row = QHBoxLayout()
        row.addWidget(QLabel("Direction:"))
        self.scroll_direction_combo = QComboBox()
        self.scroll_direction_combo.addItems(["Left", "Right", "Up", "Down"])
        self.scroll_direction_combo.currentTextChanged.connect(self._on_scroll_settings_changed)
        row.addWidget(self.scroll_direction_combo)

        row.addWidget(QLabel("Speed:"))
        self.scroll_speed_slider = QSlider(Qt.Horizontal)
        self.scroll_speed_slider.setRange(1, 10)
        self.scroll_speed_slider.setValue(4)
        self.scroll_speed_slider.valueChanged.connect(self._on_scroll_settings_changed)
        row.addWidget(self.scroll_speed_slider, 1)
        layout.addLayout(row)
        return group

    def _build_preview_group(self) -> QGroupBox:
        group = QGroupBox("Live Preview")
        layout = QVBoxLayout(group)
        self.preview_label = QLabel("Preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(140)
        self.preview_label.setStyleSheet("background-color: #222; border: 1px solid #555;")
        layout.addWidget(self.preview_label)
        return group

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_text_changed(self) -> None:
        self._text = self.text_input.toPlainText()
        self.text_changed.emit(self._text)
        self._schedule_preview()

    def _on_font_changed(self, index: int) -> None:
        data = self.font_combo.itemData(index)
        self._selected_font_data = data
        self._active_bitmap_font = None
        if not data:
            return
        mode = data[0]
        if mode == "custom" and self.font_repo:
            try:
                self._active_bitmap_font = self.font_repo.load_font(data[1])
            except FileNotFoundError:
                self._active_bitmap_font = None
        self.font_changed.emit(self.font_combo.currentText())
        self._schedule_preview()

    def _on_system_font_changed(self) -> None:
        self._system_font_name = self.system_font_combo.currentFont().family()
        self._system_font_size = self.system_size_spin.value()
        self.system_size_label.setText(f"{self._system_font_size} px")
        self.font_changed.emit(self._system_font_name)
        self._schedule_preview()

    def _on_font_type_toggled(self) -> None:
        if self.bitmap_radio.isChecked():
            self._font_type = "bitmap"
            self.bitmap_section.setVisible(True)
            self.system_section.setVisible(False)
        else:
            self._font_type = "system"
            self.bitmap_section.setVisible(False)
            self.system_section.setVisible(True)
        self._schedule_preview()

    def _on_font_designer_requested(self) -> None:
        if self._font_designer_callback:
            self._font_designer_callback()
            self.refresh_font_list()

    def _on_layout_changed(self, checked: bool) -> None:
        self._multi_line = checked
        self._schedule_preview()

    def _on_effects_changed(self) -> None:
        self._outline_enabled = self.outline_checkbox.isChecked()
        self._shadow_enabled = self.shadow_checkbox.isChecked()
        self._gradient_enabled = self.gradient_checkbox.isChecked()
        self.effects_changed.emit()
        self._schedule_preview()

    def _on_alignment_changed(self, alignment: str) -> None:
        self._alignment = alignment
        self.alignment_changed.emit(alignment)
        self._schedule_preview()

    def _on_spacing_changed(self, value: int) -> None:
        self._spacing = value
        self.spacing_label.setText(f"{value} px")
        self.spacing_changed.emit(value)
        self._schedule_preview()

    def _on_gradient_orientation_changed(self, _: str) -> None:
        self._gradient_orientation = self.gradient_orientation_combo.currentText().lower()
        self._schedule_preview()

    def _on_scroll_settings_changed(self, *_) -> None:
        if not self.scroll_preview_checkbox.isChecked():
            self._scroll_timer.stop()
        self.scroll_settings_changed.emit()
        self._schedule_preview()

    def _choose_effect_color(self, effect: str) -> None:
        current = {
            "outline": self._outline_color,
            "shadow": self._shadow_color,
            "gradient_start": self._gradient_start,
            "gradient_end": self._gradient_end,
        }.get(effect, self._primary_color)
        color = QColorDialog.getColor(QColor(*current), self, "Select colour")
        if not color.isValid():
            return
        new_rgb = (color.red(), color.green(), color.blue())
        if effect == "outline":
            self._outline_color = new_rgb
        elif effect == "shadow":
            self._shadow_color = new_rgb
        elif effect == "gradient_start":
            self._gradient_start = new_rgb
        elif effect == "gradient_end":
            self._gradient_end = new_rgb
        self._schedule_preview()

    # ------------------------------------------------------------------
    # Preview rendering
    # ------------------------------------------------------------------
    def _schedule_preview(self) -> None:
        self._preview_timer.start(200)

    def _update_preview(self) -> None:
        text = self._text.strip("\n")
        if not text:
            self._scroll_timer.stop()
            self.preview_label.setText("Preview will appear here")
            self.preview_label.setPixmap(QPixmap())
            return

        width, height = self._dimension_provider()
        render_opts = self.build_render_options(width, height, self._primary_color)

        if self.scroll_preview_checkbox.isChecked():
            scroll_opts = self.get_scroll_options(self.scroll_direction_combo.currentText().lower())
            self._scroll_frames = self._renderer.render_scroll_frames(text, render_opts, scroll_opts)
            self._scroll_frame_index = 0
            self._scroll_timer.start(self._scroll_interval_ms())
            self._display_pixels(self._scroll_frames[0], width, height)
        else:
            self._scroll_timer.stop()
            pixels = self._renderer.render_pixels(text, render_opts)
            self._display_pixels(pixels, width, height)

    def _scroll_interval_ms(self) -> int:
        speed = self.scroll_speed_slider.value()
        return max(40, 240 - speed * 20)

    def _advance_scroll_frame(self) -> None:
        if not self._scroll_frames:
            return
        width, height = self._dimension_provider()
        self._scroll_frame_index = (self._scroll_frame_index + 1) % len(self._scroll_frames)
        self._display_pixels(self._scroll_frames[self._scroll_frame_index], width, height)

    def _display_pixels(self, pixels: List[RGB], width: int, height: int) -> None:
        image = QImage(width, height, QImage.Format_RGB888)
        for idx, (r, g, b) in enumerate(pixels):
            x = idx % width
            y = idx // width
            image.setPixel(x, y, qRgb(r, g, b))
        pixmap = QPixmap.fromImage(image).scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        self.preview_label.setPixmap(pixmap)
        self.preview_label.setText("")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _font_height_from_combo(self) -> int:
        if not self._selected_font_data:
            return 7
        data = self._selected_font_data
        if data[0] == "builtin":
            return int(data[2])
        if self._active_bitmap_font:
            return self._active_bitmap_font.height
        return 7

