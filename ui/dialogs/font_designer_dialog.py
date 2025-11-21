from __future__ import annotations

from typing import List

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QLabel,
    QMessageBox,
    QInputDialog,
)
from PySide6.QtCore import Qt

from domain.text.bitmap_font import BitmapFont, BitmapFontRepository


class FontDesignerDialog(QDialog):
    """Lightweight bitmap font editor."""

    AVAILABLE_CHARS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?.,:;#&-+/<>\"'")

    def __init__(self, repository: BitmapFontRepository, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Font Designer")
        self.resize(640, 520)
        self.repo = repository

        self.current_font: BitmapFont = BitmapFont("Custom Font")
        self._grid_state: List[List[bool]] = []

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Font:"))
        self.font_combo = QComboBox()
        self.font_combo.currentTextChanged.connect(self._on_font_changed)
        header_row.addWidget(self.font_combo, 1)

        new_btn = QPushButton("New Font…")
        new_btn.clicked.connect(self._create_new_font)
        header_row.addWidget(new_btn)

        save_btn = QPushButton("Save Font")
        save_btn.clicked.connect(self._save_font)
        header_row.addWidget(save_btn)
        layout.addLayout(header_row)

        metric_row = QHBoxLayout()
        metric_row.addWidget(QLabel("Width:"))
        self.font_width_spin = QSpinBox()
        self.font_width_spin.setRange(3, 16)
        self.font_width_spin.setValue(self.current_font.width)
        self.font_width_spin.valueChanged.connect(self._on_font_metrics_changed)
        metric_row.addWidget(self.font_width_spin)

        metric_row.addWidget(QLabel("Height:"))
        self.font_height_spin = QSpinBox()
        self.font_height_spin.setRange(3, 24)
        self.font_height_spin.setValue(self.current_font.height)
        self.font_height_spin.valueChanged.connect(self._on_font_metrics_changed)
        metric_row.addWidget(self.font_height_spin)
        layout.addLayout(metric_row)

        char_row = QHBoxLayout()
        char_row.addWidget(QLabel("Character:"))
        self.char_combo = QComboBox()
        self.char_combo.addItems(self.AVAILABLE_CHARS)
        self.char_combo.currentTextChanged.connect(self._load_glyph)
        char_row.addWidget(self.char_combo)

        apply_btn = QPushButton("Save Glyph")
        apply_btn.clicked.connect(self._save_glyph)
        char_row.addWidget(apply_btn)

        clear_btn = QPushButton("Clear Glyph")
        clear_btn.clicked.connect(self._clear_glyph)
        char_row.addWidget(clear_btn)
        layout.addLayout(char_row)

        self.grid = QTableWidget()
        self.grid.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.grid.horizontalHeader().setVisible(False)
        self.grid.verticalHeader().setVisible(False)
        self.grid.setSelectionMode(QAbstractItemView.NoSelection)
        self.grid.cellClicked.connect(self._toggle_cell)
        layout.addWidget(self.grid, 1)

        self._load_fonts()

    def _load_fonts(self) -> None:
        names = self.repo.list_fonts()
        self.font_combo.blockSignals(True)
        self.font_combo.clear()
        if names:
            for name in names:
                self.font_combo.addItem(name)
            try:
                self.current_font = self.repo.load_font(names[0])
            except Exception:
                self.current_font = BitmapFont(names[0])
            self.font_combo.setCurrentIndex(0)
        else:
            self.current_font = BitmapFont("Custom Font")
            self.font_combo.addItem(self.current_font.name)
        self.font_combo.blockSignals(False)
        self._apply_font_to_ui()

    def _apply_font_to_ui(self) -> None:
        self.font_width_spin.blockSignals(True)
        self.font_height_spin.blockSignals(True)
        self.font_width_spin.setValue(self.current_font.width)
        self.font_height_spin.setValue(self.current_font.height)
        self.font_width_spin.blockSignals(False)
        self.font_height_spin.blockSignals(False)
        self._load_glyph(self.char_combo.currentText())

    def _load_glyph(self, char: str) -> None:
        if not char:
            char = self.AVAILABLE_CHARS[0]
        glyph = self.current_font.glyph(char)
        self.grid.setRowCount(self.current_font.height)
        self.grid.setColumnCount(self.current_font.width)
        self._grid_state = [[False for _ in range(self.current_font.width)] for _ in range(self.current_font.height)]
        for row in range(self.current_font.height):
            for col in range(self.current_font.width):
                item = QTableWidgetItem("")
                item.setFlags(Qt.ItemIsEnabled)
                self.grid.setItem(row, col, item)
                state = glyph[row][col]
                self._grid_state[row][col] = state
                self._apply_cell_style(row, col, state)
        self.grid.resizeColumnsToContents()
        self.grid.resizeRowsToContents()

    def _toggle_cell(self, row: int, col: int) -> None:
        self._grid_state[row][col] = not self._grid_state[row][col]
        self._apply_cell_style(row, col, self._grid_state[row][col])

    def _apply_cell_style(self, row: int, col: int, state: bool) -> None:
        item = self.grid.item(row, col)
        if not item:
            return
        color = QColor("#4CAF50") if state else QColor("#202020")
        item.setBackground(color)
        item.setData(Qt.UserRole, state)
        item.setToolTip("Filled" if state else "Empty")

    def _save_glyph(self) -> None:
        char = self.char_combo.currentText()
        self.current_font.update_glyph(char, self._grid_state)
        QMessageBox.information(self, "Glyph Saved", f"Saved glyph for '{char}'.")

    def _clear_glyph(self) -> None:
        for row in range(self.current_font.height):
            for col in range(self.current_font.width):
                self._grid_state[row][col] = False
                self._apply_cell_style(row, col, False)

    def _on_font_changed(self, name: str) -> None:
        if not name:
            return
        try:
            self.current_font = self.repo.load_font(name)
        except FileNotFoundError:
            self.current_font = BitmapFont(name)
        self._apply_font_to_ui()

    def _create_new_font(self) -> None:
        name, ok = QInputDialog.getText(self, "New Font", "Font name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self.current_font = BitmapFont(name, self.font_width_spin.value(), self.font_height_spin.value())
        self.font_combo.blockSignals(True)
        if self.font_combo.findText(name) == -1:
            self.font_combo.addItem(name)
        self.font_combo.setCurrentText(name)
        self.font_combo.blockSignals(False)
        self._apply_font_to_ui()

    def _save_font(self) -> None:
        try:
            path = self.repo.save_font(self.current_font)
        except Exception as exc:  # pragma: no cover - best effort dialog
            QMessageBox.critical(self, "Save Failed", f"Unable to save font:\n{exc}")
            return
        QMessageBox.information(self, "Font Saved", f"Saved font to {path.name}.")
        self._load_fonts()

    def _on_font_metrics_changed(self) -> None:
        self.current_font.width = self.font_width_spin.value()
        self.current_font.height = self.font_height_spin.value()
        self._load_glyph(self.char_combo.currentText())

