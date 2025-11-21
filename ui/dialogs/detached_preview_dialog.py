from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox
from PySide6.QtCore import Qt

from core.pattern import Pattern
from ui.widgets.enhanced_led_simulator import EnhancedLEDSimulatorWidget


class DetachedPreviewDialog(QDialog):
    """Floating preview window that mirrors the design canvas output."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detached Preview")
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.resize(640, 520)

        self._last_pattern: Optional[Pattern] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.preview_widget = EnhancedLEDSimulatorWidget(self)
        layout.addWidget(self.preview_widget, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def load_pattern(self, pattern: Optional[Pattern]) -> None:
        """Push the latest pattern into the preview widget."""
        self._last_pattern = pattern
        if pattern:
            self.preview_widget.load_pattern(pattern)
        else:
            self.preview_widget.clear()

    def refresh(self) -> None:
        """Reload the preview using the last-seen pattern."""
        self.load_pattern(self._last_pattern)

