from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from domain.effects import EffectDefinition, generate_effect_preview
from ui.icons import get_icon


class EffectsLibraryWidget(QWidget):
    """Scrollable effect browser with preview/apply actions."""

    effectSelected = Signal(object)
    previewRequested = Signal(object, float)
    applyRequested = Signal(object, float)
    refreshRequested = Signal()
    openFolderRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._effects: List[EffectDefinition] = []
        self._filtered: List[EffectDefinition] = []
        self._thumbnails: Dict[str, QPixmap] = {}
        self._selected_id: Optional[str] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_effects(self, effects: Iterable[EffectDefinition], categories: Iterable[str]) -> None:
        self._effects = list(effects)
        self._effects.sort(key=lambda eff: (eff.category.lower(), eff.name.lower()))
        self._populate_category_combo(categories)
        self._refresh_effect_grid()

    def intensity(self) -> float:
        return self.intensity_slider.value() / 100.0

    def selected_effect(self) -> Optional[EffectDefinition]:
        if not self._selected_id:
            return None
        for effect in self._effects:
            if effect.identifier == self._selected_id:
                return effect
        return None

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All categories", userData="__all__")
        self.category_combo.currentIndexChanged.connect(self._refresh_effect_grid)
        header.addWidget(QLabel("Category:"))
        header.addWidget(self.category_combo, 1)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search effects…")
        self.search_edit.textChanged.connect(self._refresh_effect_grid)
        header.addWidget(self.search_edit, 1)

        refresh_btn = QToolButton()
        refresh_btn.setIcon(get_icon("refresh"))
        refresh_btn.setToolTip("Rescan effects folder")
        refresh_btn.clicked.connect(self.refreshRequested)
        header.addWidget(refresh_btn)

        open_btn = QToolButton()
        open_btn.setIcon(get_icon("export"))
        open_btn.setToolTip("Open effects folder")
        open_btn.clicked.connect(self.openFolderRequested)
        header.addWidget(open_btn)

        layout.addLayout(header)

        intensity_row = QHBoxLayout()
        intensity_row.setSpacing(6)
        intensity_row.addWidget(QLabel("Intensity:"))
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(10, 100)
        self.intensity_slider.setValue(60)
        intensity_row.addWidget(self.intensity_slider, 1)
        self.intensity_label = QLabel("60%")
        intensity_row.addWidget(self.intensity_label)
        self.intensity_slider.valueChanged.connect(
            lambda value: self.intensity_label.setText(f"{value}%")
        )
        layout.addLayout(intensity_row)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.scroll_area, 1)

        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_area.setWidget(container)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        self.preview_button = QPushButton("Preview on current frame")
        self.preview_button.setEnabled(False)
        self.preview_button.clicked.connect(self._emit_preview)
        actions_row.addWidget(self.preview_button)

        self.apply_button = QPushButton("Apply to selected frames")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self._emit_apply)
        actions_row.addWidget(self.apply_button)

        layout.addLayout(actions_row)

        self.info_label = QLabel(
            "Drop new effect files into the effects folder and press refresh \n"
            "to load them here."
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.info_label)

        self.card_group = QButtonGroup(self)
        self.card_group.setExclusive(True)
        self.card_group.idClicked.connect(self._on_card_clicked)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _populate_category_combo(self, categories: Iterable[str]) -> None:
        current = self.category_combo.currentData()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All categories", userData="__all__")
        for category in sorted(categories, key=lambda c: c.lower()):
            self.category_combo.addItem(category, userData=category)
        self.category_combo.blockSignals(False)
        if current is not None:
            idx = self.category_combo.findData(current)
            if idx != -1:
                self.category_combo.setCurrentIndex(idx)

    def _refresh_effect_grid(self) -> None:
        # Clear previous cards
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.card_group = QButtonGroup(self)
        self.card_group.setExclusive(True)
        self.card_group.idClicked.connect(self._on_card_clicked)

        category_filter = self.category_combo.currentData()
        search = self.search_edit.text().strip().lower()
        self._filtered = []
        row = col = 0
        max_columns = 2
        for effect in self._effects:
            if category_filter and category_filter != "__all__" and effect.category != category_filter:
                continue
            if search and search not in effect.name.lower() and search not in effect.identifier.lower():
                continue
            self._filtered.append(effect)
            card = _EffectCard(effect, self._thumbnail_for(effect))
            self.grid_layout.addWidget(card, row, col)
            self.card_group.addButton(card, len(self._filtered) - 1)
            col += 1
            if col >= max_columns:
                col = 0
                row += 1

        if self._selected_id:
            for idx, effect in enumerate(self._filtered):
                if effect.identifier == self._selected_id:
                    button = self.card_group.button(idx)
                    if button:
                        button.setChecked(True)
                        break
        self._update_action_state()

    def _thumbnail_for(self, effect: EffectDefinition) -> QPixmap:
        if effect.identifier in self._thumbnails:
            return self._thumbnails[effect.identifier]

        pixmap: QPixmap
        if effect.preview_path and Path(effect.preview_path).exists():
            pixmap = QPixmap(str(effect.preview_path))
        else:
            pixels = generate_effect_preview(effect)
            size = int(math.sqrt(len(pixels)))
            image = QImage(size, size, QImage.Format_RGB32)
            for y in range(size):
                for x in range(size):
                    r, g, b = pixels[y * size + x]
                    image.setPixel(x, y, QColor(r, g, b).rgb())
            pixmap = QPixmap.fromImage(image).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._thumbnails[effect.identifier] = pixmap
        return pixmap

    def _on_card_clicked(self, index: int) -> None:
        if 0 <= index < len(self._filtered):
            effect = self._filtered[index]
            self._selected_id = effect.identifier
            self.effectSelected.emit(effect)
        else:
            self._selected_id = None
        self._update_action_state()

    def _update_action_state(self) -> None:
        enabled = self._selected_id is not None
        self.preview_button.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)

    def _emit_preview(self) -> None:
        effect = self.selected_effect()
        if effect is None:
            return
        self.previewRequested.emit(effect, self.intensity())

    def _emit_apply(self) -> None:
        effect = self.selected_effect()
        if effect is None:
            return
        self.applyRequested.emit(effect, self.intensity())


class _EffectCard(QToolButton):
    """Compact button displaying effect thumbnail and metadata."""

    def __init__(self, effect: EffectDefinition, thumbnail: QPixmap, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.effect = effect
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setIconSize(thumbnail.size())
        self.setIcon(thumbnail)
        self.setStyleSheet(
            "QToolButton { border: 1px solid rgba(255,255,255,40); border-radius: 6px; padding: 4px; }"
            "QToolButton:checked { border: 1px solid #4C8BF5; background-color: rgba(76,139,245,40); }"
        )
        self.setAutoRaise(False)
        self._build_overlay()

    def _build_overlay(self) -> None:
        overlay = QFrame(self)
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents)
        overlay.setStyleSheet(
            "background: rgba(0, 0, 0, 120); color: white; border-radius: 6px;"
        )
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(6, 6, 6, 6)
        overlay_layout.addStretch(1)
        name_label = QLabel(self.effect.name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-weight: 600; font-size: 11px; color: white;")
        overlay_layout.addWidget(name_label)
        category = QLabel(self.effect.category)
        category.setStyleSheet("font-size: 9px; color: #DDDDDD;")
        overlay_layout.addWidget(category)
        overlay.resize(self.size())
        overlay.lower()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for child in self.children():
            if isinstance(child, QFrame):
                child.resize(self.size())
