from __future__ import annotations

import os
import sys
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt, QThread, Signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.media_converter import MediaConverter


class _MediaImportWorker(QThread):
    progress = Signal(int)
    status = Signal(str)
    completed = Signal(object, str)  # pattern or None, error message

    def __init__(self, file_path: str, width: int, height: int, fps: float, brightness: float, color_order: str):
        super().__init__()
        self.file_path = file_path
        self.width = width
        self.height = height
        self.fps = fps
        self.brightness = brightness
        self.color_order = color_order
        self.converter = MediaConverter()

    def run(self):
        try:
            self.status.emit("Analyzing media...")
            self.progress.emit(5)
            pattern = self.converter.convert_to_pattern(
                self.file_path,
                self.width,
                self.height,
                self.fps,
                self.brightness,
                self.color_order,
            )
            self.progress.emit(95)
            self.status.emit("Finalizing...")
            self.completed.emit(pattern, "")
        except Exception as e:
            self.completed.emit(None, str(e))


class MediaImportDialog(QDialog):
    def __init__(self, parent, file_path: str, width: int = 64, height: int = 32, fps: float = 20.0,
                 brightness: float = 1.0, color_order: str = "RGB"):
        super().__init__(parent)
        self.setWindowTitle("Importing Media...")
        self.setModal(True)
        self.resize(420, 140)

        layout = QVBoxLayout(self)
        self.label = QLabel(f"Importing: {os.path.basename(file_path)}")
        self.label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.label)

        self.status_label = QLabel("Preparing...")
        self.status_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate by default
        layout.addWidget(self.progress)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)

        # Worker
        self.worker = _MediaImportWorker(file_path, width, height, fps, brightness, color_order)
        self.worker.progress.connect(self.on_progress)
        self.worker.status.connect(self.on_status)
        self.worker.completed.connect(self.on_completed)
        self._result = None
        self.worker.start()

    def on_progress(self, v: int):
        # Switch to determinate if we get explicit progress
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 100)
        self.progress.setValue(v)

    def on_status(self, msg: str):
        self.status_label.setText(msg)

    def on_completed(self, pattern, error: str):
        if pattern is not None:
            self._result = pattern
            self.accept()
        else:
            self._result = None
            self.status_label.setText(f"Failed: {error}")
            self.reject()

    def result_pattern(self):
        return self._result


