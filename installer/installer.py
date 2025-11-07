#!/usr/bin/env python3
"""
Upload Bridge - Simple GUI Installer

User flow: Install → Activate → Launch
- Copies UploadBridge.exe to install directory with progress bar
- Prompts for license key (offline, pre-made keys)
- Activates on this machine (first time only)
- Launches the app
"""

import os
import sys
import shutil
import json
import logging
import traceback
from pathlib import Path
import re

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QPlainTextEdit,
    QCheckBox,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon
import subprocess


def default_install_dir() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "UploadBridge"
    return Path.home() / ".uploadbridge"


def get_package_dir() -> Path:
    # Directory where Installer is running
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) if hasattr(sys, "_MEIPASS") else Path(os.path.dirname(sys.executable))
    return Path(__file__).resolve().parent.parent


def find_source_app() -> Path:
    # Prefer local folder's UploadBridge.exe (next to installer)
    candidates = [
        Path(os.path.dirname(sys.executable)) / "UploadBridge.exe" if getattr(sys, "frozen", False) else get_package_dir() / "dist" / "UploadBridge.exe",
        get_package_dir() / "UploadBridge.exe",
        # Embedded payload inside one-file installer (PyInstaller MEIPASS)
        (get_package_dir() / "payload" / "UploadBridge.exe") if getattr(sys, "frozen", False) else Path(),
    ]
    for c in candidates:
        if c.exists():
            return c
    return Path()


def copy_launchers_to(target_dir: Path) -> None:
    """Copy launcher .bat and .vbs from packaged resources to target directory."""
    try:
        src_dir = get_package_dir() / "windows"
        candidates = [
            (src_dir / "LAUNCH_UPLOAD_BRIDGE.bat", target_dir / "LAUNCH_UPLOAD_BRIDGE.bat"),
            (src_dir / "LAUNCH_UPLOAD_BRIDGE.vbs", target_dir / "LAUNCH_UPLOAD_BRIDGE.vbs"),
            (src_dir / "LAUNCH_UPLOAD_BRIDGE_DEBUG.bat", target_dir / "LAUNCH_UPLOAD_BRIDGE_DEBUG.bat"),
        ]
        for src, dst in candidates:
            if src.exists():
                try:
                    dst.write_bytes(src.read_bytes())
                except Exception:
                    pass
    except Exception:
        pass


def get_desktop_dir() -> Path:
    # Try common desktop locations
    candidates = []
    if os.name == "nt":
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            candidates.append(Path(userprofile) / "Desktop")
        one_drive = os.environ.get("OneDrive")
        if one_drive:
            candidates.append(Path(one_drive) / "Desktop")
        public = os.environ.get("PUBLIC")
        if public:
            candidates.append(Path(public) / "Desktop")
    # Fallback to home Desktop
    candidates.append(Path.home() / "Desktop")
    for c in candidates:
        if c and c.exists():
            return c
    # Last resort, default install dir
    return default_install_dir()


def create_windows_shortcut(target_exe: Path, name: str, icon: Path | None = None) -> bool:
    """Create a .lnk shortcut on the user's Desktop using PowerShell COM.
    Returns True on success, False otherwise.
    """
    try:
        desktop = get_desktop_dir()
        desktop.mkdir(parents=True, exist_ok=True)
        lnk = desktop / f"{name}.lnk"
        ps_code = (
            "& {param($t,$d,$i,$l) "
            "$W=New-Object -ComObject WScript.Shell;"
            "$S=$W.CreateShortcut($l);"
            "$S.TargetPath=$t;"
            "$S.WorkingDirectory=$d;"
            "if($i){$S.IconLocation=$i};"
            "$S.Save()}"
        )
        args = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            ps_code,
            "-args",
            str(target_exe),
            str(target_exe.parent),
            str(icon) if icon else "",
            str(lnk),
        ]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return lnk.exists()
    except Exception:
        return False


KEY_PATTERN = re.compile(r"ULBP-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}")


def _normalize_key(s: str) -> str:
    # Uppercase, collapse spaces, keep dashes
    return re.sub(r"\s+", "", s).upper()


def read_license_keys() -> set[str]:
    keys: set[str] = set()
    # LICENSE_KEYS.txt in package directory
    for candidate in [
        get_package_dir() / "LICENSE_KEYS.txt",
        get_package_dir() / "config" / "license_keys.yaml",
        Path(__file__).resolve().parent.parent / "config" / "license_keys.yaml",
    ]:
        if candidate.exists():
            try:
                content = candidate.read_text(encoding="utf-8", errors="ignore")
                # Try strict pattern first
                for m in KEY_PATTERN.findall(content.upper()):
                    keys.add(_normalize_key(m))
                # For YAML list items without the ULBP- prefix pattern captured above
                for line in content.splitlines():
                    line = line.strip().lstrip("- ").strip().strip('"\'')
                    if not line:
                        continue
                    if KEY_PATTERN.fullmatch(line.upper()):
                        keys.add(_normalize_key(line))
            except Exception:
                # Ignore read errors, continue
                pass
    return keys


def activation_store_path() -> Path:
    base = Path(os.environ.get("APPDATA", str(default_install_dir())))
    return base / "UploadBridge" / "activation.json"


def write_activation(key: str) -> None:
    path = activation_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"activated": True, "key": key}
    path.write_text(json.dumps(data), encoding="utf-8")


def is_activated() -> bool:
    path = activation_store_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("activated"))
    except Exception:
        return False


class CopyWorker(QThread):
    progress = Signal(int)
    message = Signal(str)
    finished_ok = Signal(Path)
    failed = Signal(str)

    def __init__(self, src: Path, dst_dir: Path):
        super().__init__()
        self.src = src
        self.dst_dir = dst_dir

    def run(self):
        try:
            self.message.emit("Preparing installation directory...")
            self.dst_dir.mkdir(parents=True, exist_ok=True)
            target = self.dst_dir / self.src.name

            # Copy in chunks to report progress
            total = self.src.stat().st_size
            copied = 0
            buf_size = 1024 * 1024
            self.message.emit(f"Copying {self.src.name}...")
            with open(self.src, "rb") as rf, open(target, "wb") as wf:
                while True:
                    chunk = rf.read(buf_size)
                    if not chunk:
                        break
                    wf.write(chunk)
                    copied += len(chunk)
                    pct = int(min(100, (copied / max(1, total)) * 100))
                    self.progress.emit(pct)
            # Ensure executable bit on Unix
            try:
                os.chmod(target, 0o755)
            except Exception:
                pass
            self.progress.emit(100)
            self.message.emit("Copy complete.")
            self.finished_ok.emit(target)
        except Exception as e:
            self.failed.emit(str(e))


class InstallerDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Upload Bridge Installer")
        # Try set icon from package
        for icon_candidate in [
            get_package_dir() / "LEDMatrixStudio_icon.ico",
            Path(__file__).resolve().parent.parent / "LEDMatrixStudio_icon.ico",
        ]:
            if icon_candidate.exists():
                self.setWindowIcon(QIcon(str(icon_candidate)))
                break

        self.source_app = find_source_app()
        self.install_dir = default_install_dir()
        self.valid_keys = read_license_keys()

        self.install_log_path = self._default_log_path()
        self._init_logging(self.install_log_path)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Install location group
        loc_group = QGroupBox("Installation Location")
        loc_layout = QHBoxLayout()
        self.path_edit = QLineEdit(str(self.install_dir))
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.on_browse)
        loc_layout.addWidget(self.path_edit)
        loc_layout.addWidget(browse_btn)
        loc_group.setLayout(loc_layout)
        layout.addWidget(loc_group)

        # Progress group
        prog_group = QGroupBox("Installation Progress")
        prog_v = QVBoxLayout()
        self.status_label = QLabel("Ready to install.")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        prog_v.addWidget(self.status_label)
        prog_v.addWidget(self.progress)
        prog_group.setLayout(prog_v)
        layout.addWidget(prog_group)

        # License group
        lic_group = QGroupBox("Activation")
        lic_h = QHBoxLayout()
        self.license_edit = QLineEdit()
        self.license_edit.setPlaceholderText("Enter license key (from LICENSE_KEYS.txt)")
        self.activate_btn = QPushButton("Activate")
        self.activate_btn.clicked.connect(self.on_activate_clicked)
        lic_h.addWidget(self.license_edit)
        lic_h.addWidget(self.activate_btn)
        lic_group.setLayout(lic_h)
        layout.addWidget(lic_group)

        # Action buttons
        btns = QHBoxLayout()
        self.install_btn = QPushButton("Install")
        self.install_btn.clicked.connect(self.on_install_clicked)
        self.launch_btn = QPushButton("Launch Upload Bridge")
        self.launch_btn.setEnabled(False)
        self.launch_btn.clicked.connect(self.on_launch_clicked)
        btns.addWidget(self.install_btn)
        btns.addStretch()
        btns.addWidget(self.launch_btn)
        layout.addLayout(btns)

        # Log view (collapsible)
        self.log_toggle = QCheckBox("Show installation log")
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setVisible(False)
        self.log_toggle.toggled.connect(self.log_view.setVisible)
        layout.addWidget(self.log_toggle)
        layout.addWidget(self.log_view)

        # Tail timer
        self._tail_pos = 0
        self._tail_timer = QTimer(self)
        self._tail_timer.timeout.connect(self._tail_log)
        self._tail_timer.start(400)

        # If already activated, hint it
        if is_activated():
            self.status_label.setText("Detected previous activation on this device.")

        # Disable activation until installed
        self.activate_btn.setEnabled(False)
        self.license_edit.setEnabled(False)

    def on_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select Install Folder", str(self.install_dir))
        if d:
            self.path_edit.setText(d)
            # Switch logging to chosen folder early
            try:
                self._switch_log_to_target(Path(d))
            except Exception:
                pass

    def on_install_clicked(self):
        if not self.source_app.exists():
            QMessageBox.critical(self, "Missing App", "UploadBridge.exe not found in the package folder.")
            return
        target_dir = Path(self.path_edit.text()).expanduser()
        # Switch logging to target dir
        self._switch_log_to_target(target_dir)
        try:
            logging.info("Install requested. Target=%s, Source=%s", target_dir, self.source_app)
        except Exception:
            pass
        self.install_btn.setEnabled(False)
        self.copy_worker = CopyWorker(self.source_app, target_dir)
        self.copy_worker.progress.connect(self.progress.setValue)
        self.copy_worker.message.connect(self._on_status_message)
        self.copy_worker.failed.connect(self.on_copy_failed)
        self.copy_worker.finished_ok.connect(self.on_copy_finished)
        self.copy_worker.start()

    def _on_status_message(self, msg: str):
        try:
            logging.info("%s", msg)
        except Exception:
            pass
        self.status_label.setText(msg)

    def on_copy_failed(self, err: str):
        self.install_btn.setEnabled(True)
        try:
            logging.error("Copy failed: %s\n%s", err, traceback.format_exc())
        except Exception:
            pass
        QMessageBox.critical(self, "Install Failed", f"Error copying files:\n{err}")

    def on_copy_finished(self, target: Path):
        try:
            logging.info("Copy finished to %s", target.parent)
        except Exception:
            pass
        self.status_label.setText(f"Installed to: {target.parent}")
        # Ensure launcher scripts are present
        try:
            logging.info("Copying launcher scripts...")
            copy_launchers_to(target.parent)
        except Exception as e:
            try:
                logging.warning("Launcher copy warning: %s", e)
            except Exception:
                pass
        # Try to create desktop shortcut
        icon_candidate = None
        for icon_path in [
            get_package_dir() / "LEDMatrixStudio_icon.ico",
            Path(__file__).resolve().parent.parent / "LEDMatrixStudio_icon.ico",
        ]:
            if icon_path.exists():
                icon_candidate = icon_path
                break
        created = False
        if os.name == "nt":
            vbs = target.parent / "LAUNCH_UPLOAD_BRIDGE.vbs"
            if vbs.exists():
                created = create_windows_shortcut(vbs, "Upload Bridge", icon_candidate)
            else:
                created = create_windows_shortcut(target, "Upload Bridge", icon_candidate)
        if created:
            self.status_label.setText(self.status_label.text() + "  (Desktop shortcut created)")
        # Verify critical files
        try:
            self._verify_post_copy(target.parent)
            logging.info("Post-copy verification OK")
        except Exception as e:
            try:
                logging.error("Verification failed: %s", e)
            except Exception:
                pass
            QMessageBox.critical(self, "Install Verification Failed", str(e))
        self.activate_btn.setEnabled(True)
        self.license_edit.setEnabled(True)
        QMessageBox.information(self, "Installed", "Installation completed. Please enter your license key to activate.")

    def on_activate_clicked(self):
        key = self.license_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Activation", "Please enter a license key.")
            return
        norm = _normalize_key(key)
        if norm in self.valid_keys:
            write_activation(key)
            self.status_label.setText("Activated successfully.")
            QMessageBox.information(self, "Activation", "Product activated. You can now launch Upload Bridge.")
            self.launch_btn.setEnabled(True)
            self.activate_btn.setEnabled(False)
            self.license_edit.setEnabled(False)
        else:
            QMessageBox.critical(self, "Invalid Key", "The license key you entered is invalid. Please check LICENSE_KEYS.txt and try again.")

    def on_launch_clicked(self):
        # Launch installed app with working directory to avoid resource path issues
        target_dir = Path(self.path_edit.text()).expanduser()
        vbs = target_dir / "LAUNCH_UPLOAD_BRIDGE.vbs"
        bat = target_dir / "LAUNCH_UPLOAD_BRIDGE.bat"
        exe = target_dir / "UploadBridge.exe"
        launch_target = vbs if vbs.exists() else (bat if bat.exists() else exe)
        if not launch_target.exists():
            QMessageBox.critical(self, "Not Found", f"{launch_target} not found.")
            return
        try:
            # Ensure app writes logs for troubleshooting
            env = os.environ.copy()
            env.setdefault("UPLOADBRIDGE_LOG_LEVEL", "INFO")
            env.setdefault("UPLOADBRIDGE_LOG_FILE", str(target_dir / "UploadBridge.log"))
            if os.name == "nt":
                # Enable debug on first launch to help diagnose issues
                env.setdefault("UPLOADBRIDGE_DEBUG", "1")
                subprocess.Popen([str(launch_target)], cwd=str(target_dir), env=env)
            else:
                subprocess.Popen([str(launch_target)], cwd=str(target_dir), env=env)
            try:
                logging.info("Launched: %s", launch_target)
            except Exception:
                pass
            self.accept()
        except Exception as e:
            # Fallback to startfile
            try:
                if os.name == "nt":
                    os.startfile(str(launch_target))  # type: ignore[attr-defined]
                    self.accept()
                    return
            except Exception:
                pass
            try:
                logging.error("Launch failed: %s\n%s", e, traceback.format_exc())
            except Exception:
                pass
            QMessageBox.critical(self, "Launch Failed", str(e))

    # --- Logging and verification helpers ---
    def _default_log_path(self) -> Path:
        return Path(os.environ.get("TEMP", str(Path.home()))) / "UploadBridge_Install.log"

    def _init_logging(self, log_path: Path) -> None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                handlers=[logging.FileHandler(str(log_path), encoding="utf-8"),]
            )
            logging.info("=== Installer started ===")
            logging.info("Using log file: %s", log_path)
        except Exception:
            pass

    def _tail_log(self) -> None:
        try:
            p = Path(self.install_log_path)
            if not p.exists():
                return
            data = p.read_bytes()
            if len(data) > self._tail_pos:
                chunk = data[self._tail_pos:]
                self._tail_pos = len(data)
                self.log_view.appendPlainText(chunk.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def _switch_log_to_target(self, target_dir: Path) -> None:
        try:
            new_log = target_dir / "Install.log"
            if new_log == self.install_log_path:
                return
            # Replace root logger handlers with new file
            root = logging.getLogger()
            for h in list(root.handlers):
                root.removeHandler(h)
            self.install_log_path = new_log
            fh = logging.FileHandler(str(self.install_log_path), encoding="utf-8")
            fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            fh.setFormatter(fmt)
            root.addHandler(fh)
            root.setLevel(logging.INFO)
            logging.info("Switched logging to %s", self.install_log_path)
            # Reset tail position to re-read file in UI
            self._tail_pos = 0
        except Exception:
            pass

    def _verify_post_copy(self, target_dir: Path) -> None:
        required = [
            target_dir / "UploadBridge.exe",
            target_dir / "LAUNCH_UPLOAD_BRIDGE.vbs",
            target_dir / "LICENSE_KEYS.txt",
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise RuntimeError(f"Missing required files after copy: {missing}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Upload Bridge Installer")
    # Try set app icon
    for icon_candidate in [
        get_package_dir() / "LEDMatrixStudio_icon.ico",
        Path(__file__).resolve().parent.parent / "LEDMatrixStudio_icon.ico",
    ]:
        if icon_candidate.exists():
            app.setWindowIcon(QIcon(str(icon_candidate)))
            break
    dlg = InstallerDialog()
    dlg.resize(640, 320)
    dlg.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


