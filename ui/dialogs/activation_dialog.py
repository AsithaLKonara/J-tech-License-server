"""
Offline Activation Dialog (PySide6)

Drop-in dialog that reads license keys from LICENSE_KEYS.txt next to the
installed executable and stores activation at %APPDATA%\UploadBridge\activation.json.

Usage:
    from ui.dialogs.activation_dialog import ensure_activation_or_exit
    ensure_activation_or_exit(parent=None)

Notes:
    - Case-insensitive key match
    - Keys format: ULBP-XXXX-XXXX-XXXX (but also accepts any non-empty line)
    - No network calls; purely offline
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Set

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)


APPDATA_DIR = Path(os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))) / "UploadBridge"
ACTIVATION_FILE = APPDATA_DIR / "activation.json"
KEY_PATTERN = re.compile(r"ULBP-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}")


def _app_dir() -> Path:
    """Return directory where the app is running from (works in PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parent.parent.parent


def _normalize_key(s: str) -> str:
    return re.sub(r"\s+", "", s).upper()


def _read_license_keys() -> Set[str]:
    keys: Set[str] = set()
    candidates = [
        _app_dir() / "LICENSE_KEYS.txt",
        _app_dir() / "config" / "license_keys.yaml",
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            content = candidate.read_text(encoding="utf-8", errors="ignore")
            # Match strict pattern
            for m in KEY_PATTERN.findall(content.upper()):
                keys.add(_normalize_key(m))
            # Fallback: accept non-empty lines
            for line in content.splitlines():
                s = line.strip().strip('"\'')
                if not s or s.startswith("#"):
                    continue
                if len(s) >= 6:
                    keys.add(_normalize_key(s))
        except Exception:
            pass
    return keys


def is_activated() -> bool:
    if not ACTIVATION_FILE.exists():
        return False
    try:
        data = json.loads(ACTIVATION_FILE.read_text(encoding="utf-8"))
        return bool(data.get("activated")) and bool(data.get("key"))
    except Exception:
        return False


def write_activation(key: str) -> None:
    ACTIVATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "activated": True,
        "key": key,
    }
    ACTIVATION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


class ActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Activation Required")
        self._valid_keys = _read_license_keys()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Enter your license key (see LICENSE_KEYS.txt):"))
        self.input = QLineEdit(self)
        self.input.setPlaceholderText("ULBP-XXXX-XXXX-XXXX")
        layout.addWidget(self.input)

        btns = QHBoxLayout()
        self.btn_activate = QPushButton("Activate")
        self.btn_cancel = QPushButton("Cancel")
        btns.addWidget(self.btn_activate)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.btn_activate.clicked.connect(self.on_activate)
        self.btn_cancel.clicked.connect(self.reject)

    def on_activate(self) -> None:
        key = _normalize_key(self.input.text())
        if not key:
            QMessageBox.warning(self, "Activation", "Please enter a license key.")
            return
        if key in self._valid_keys:
            write_activation(key)
            QMessageBox.information(self, "Activation", "Activation successful. Thank you!")
            self.accept()
        else:
            QMessageBox.critical(self, "Invalid Key", "That license key is not valid. Please check LICENSE_KEYS.txt.")


def ensure_activation_or_exit(parent=None) -> None:
    """Show activation dialog if not already activated. Exit on cancel."""
    if is_activated():
        return
    dlg = ActivationDialog(parent)
    if dlg.exec() != QDialog.Accepted:
        # Graceful exit when user cancels activation
        sys.exit(0)


