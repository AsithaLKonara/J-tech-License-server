#!/usr/bin/env python3
"""
Upload Bridge - Main Application Entry Point
Universal LED Pattern Flasher
"""

import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication, Qt

# Initialize logging early (enable file logging in debug)
try:
    from core.logging_config import setup_logging
    log_to_file = bool(os.environ.get("UPLOADBRIDGE_LOG_FILE"))
    setup_logging(log_to_file=log_to_file)
    try:
        import logging as _logging
        _logging.getLogger(__name__).info("Logging initialized (log_to_file=%s)", log_to_file)
    except Exception:
        pass
except Exception:
    pass

def _startup_health_check() -> None:
    """Log key environment and resource checks to aid troubleshooting."""
    try:
        import logging as _logging
        import traceback as _tb
        import os as _os
        import sys as _sys
        from pathlib import Path as _Path

        log = _logging.getLogger(__name__)
        log.info("Health check: starting")
        # Qt plugin environment
        log.info("QT_PLUGIN_PATH=%s", _os.environ.get("QT_PLUGIN_PATH", ""))
        log.info("QT_QPA_PLATFORM_PLUGIN_PATH=%s", _os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", ""))
        # Firmware template resolution probe (esp8266 as representative)
        try:
            from firmware.builder import FirmwareBuilder  # type: ignore
            fb = FirmwareBuilder()
            tpl = fb._resolve_template_dir("esp8266")
            log.info("Firmware template (esp8266) path: %s", tpl)
        except Exception as e:
            log.error("Firmware template resolution failed: %s", e)
        # Write access probe
        try:
            appdata = _Path(_os.environ.get("APPDATA", str(_Path.home())))/"UploadBridge"
            appdata.mkdir(parents=True, exist_ok=True)
            probe = appdata/"write_test.tmp"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            log.info("Write-access OK: %s", appdata)
        except Exception as e:
            log.error("Write-access check failed: %s", e)
    except Exception:
        # Do not raise; this is diagnostic-only
        pass

# Optional debug mode for diagnosing startup issues
if os.environ.get('UPLOADBRIDGE_DEBUG'):
    os.environ.setdefault('QT_DEBUG_PLUGINS', '1')
    # Prefer software OpenGL in debug to avoid driver issues
    os.environ.setdefault('QT_OPENGL', 'software')

# Ensure Qt plugin paths resolve correctly in packaged mode (onefile/onedir)
try:
    meipass = getattr(sys, '_MEIPASS', None)
    candidates = []
    if meipass:
        candidates += [
            os.path.join(meipass, 'PySide6', 'plugins'),
            os.path.join(meipass, 'PySide6', 'Qt', 'plugins'),
            os.path.join(meipass, 'qt6_plugins'),
        ]
    # On onedir, search relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates += [
        os.path.join(base_dir, 'PySide6', 'plugins'),
        os.path.join(base_dir, 'PySide6', 'Qt', 'plugins'),
        os.path.join(base_dir, 'qt6_plugins'),
    ]
    plugin_path = next((p for p in candidates if os.path.isdir(p)), None)
    if plugin_path:
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        platforms_path = os.path.join(plugin_path, 'platforms')
        if os.path.isdir(platforms_path):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_path
except Exception:
    pass

# Hide console window on Windows if present (skip in debug mode)
if os.name == 'nt' and not os.environ.get('UPLOADBRIDGE_DEBUG'):
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

try:
    from ui.main_window import UploadBridgeMainWindow
except Exception as e:
    # Fallback: extend sys.path for PyInstaller layouts and retry
    import logging
    logger = logging.getLogger(__name__)
    candidates = []
    try:
        candidates += [
            os.path.dirname(sys.executable),
            getattr(sys, '_MEIPASS', ''),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui'),
        ]
        for p in candidates:
            if p and p not in sys.path and os.path.exists(p):
                sys.path.insert(0, p)
        # Retry import
        from ui.main_window import UploadBridgeMainWindow  # type: ignore
    except Exception as e2:
        logger.error("Import error: %s", e2)
        logger.error("Make sure all dependencies are installed: pip install -r requirements_simple.txt")
        sys.exit(1)


def main():
    """Main application entry point"""
    # Crash handler to surface errors in GUI
    def _excepthook(exc_type, exc, tb):
        import traceback
        tb_text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            import logging as _logging
            _logging.getLogger(__name__).error("Unhandled exception:\n%s", tb_text)
        except Exception:
            pass
        try:
            QMessageBox.critical(None, "Upload Bridge - Error", tb_text[:4000])
        except Exception:
            pass
    sys.excepthook = _excepthook
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Upload Bridge")
    app.setOrganizationName("Upload Bridge Project")
    
    # Set application style
    app.setStyle("Fusion")

    # If requested, force software OpenGL at the Qt attribute level
    try:
        if os.environ.get('QT_OPENGL', '').lower() == 'software' or os.environ.get('UPLOADBRIDGE_DEBUG'):
            QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
    except Exception:
        pass
    
    # Resolve and set application icon
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_icons = [
            os.path.join(base_dir, "LEDMatrixStudio_icon.ico"),
            os.path.join(base_dir, "resources", "icons", "LEDMatrixStudio_icon.ico"),
            os.path.join(base_dir, "assets", "icons", "LEDMatrixStudio_icon.ico"),
        ]
        icon_path = next((p for p in candidate_icons if os.path.exists(p)), None)
        if icon_path:
            app.setWindowIcon(QIcon(icon_path))
    except Exception:
        # Non-fatal if icon not found
        pass
    # Run diagnostic health check after logging init
    try:
        _startup_health_check()
    except Exception:
        pass
    
    # Activation check before showing UI
    try:
        from ui.dialogs.activation_dialog import ensure_activation_or_exit
        ensure_activation_or_exit(None)
    except Exception:
        pass

    # Create and show main window
    window = UploadBridgeMainWindow()
    try:
        if 'icon_path' in locals() and icon_path:
            window.setWindowIcon(QIcon(icon_path))
    except Exception:
        pass
    # Open file passed via file association (if any)
    try:
        file_to_open = sys.argv[1] if len(sys.argv) > 1 else None
        if file_to_open and hasattr(window, 'load_file'):
            window.load_file(file_to_open)
    except Exception:
        pass
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

