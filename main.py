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

# Initialize enterprise logging and configuration early
try:
    # Initialize configuration first
    from core.config import get_config
    from core.logging import setup_logging, get_logger, LogLevel
    from pathlib import Path
    
    config = get_config()
    
    # Setup enterprise logging with configuration
    log_level_str = config.get('log_level', 'INFO').upper()
    try:
        log_level = LogLevel[log_level_str]
    except KeyError:
        log_level = LogLevel.INFO
    
    setup_logging(
        level=log_level,
        log_to_file=config.get('log_to_file', True),
        log_to_console=config.get('log_to_console', True),
        json_format=config.get('log_json', False),
        log_dir=Path(config.get('log_dir', 'logs'))
    )
    
    logger = get_logger(__name__)
    logger.info("Enterprise logging initialized", extra={
        'log_level': log_level_str,
        'log_to_file': config.get('log_to_file'),
        'log_to_console': config.get('log_to_console'),
        'environment': config.environment.value
    })
except Exception as e:
    # Fallback to basic logging if enterprise logging fails
    try:
        from core.logging_config import setup_logging
        log_to_file = bool(os.environ.get("UPLOADBRIDGE_LOG_FILE"))
        setup_logging(log_to_file=log_to_file)
        import logging as _logging
        _logging.getLogger(__name__).warning("Enterprise logging failed, using fallback: %s", e)
    except Exception:
        pass

def _startup_health_check() -> None:
    """Run comprehensive health check and log results."""
    try:
        from core.health import get_health_checker
        from core.logging import get_logger
        import os as _os
        import sys as _sys
        from pathlib import Path as _Path

        logger = get_logger(__name__)
        logger.info("Starting comprehensive health check")
        
        # Run enterprise health check
        try:
            health_checker = get_health_checker()
            health_status = health_checker.check_health()
            logger.info("Health check completed", extra={
                'overall_status': health_status['status'],
                'checks': health_status['checks']
            })
        except Exception as e:
            logger.warning("Enterprise health check failed, running basic checks: %s", e)
        
        # Basic environment checks
        logger.info("Environment check", extra={
            'QT_PLUGIN_PATH': _os.environ.get("QT_PLUGIN_PATH", ""),
            'QT_QPA_PLATFORM_PLUGIN_PATH': _os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", ""),
            'python_version': _sys.version
        })
        
        # Firmware template resolution probe (esp8266 as representative)
        try:
            from firmware.builder import FirmwareBuilder  # type: ignore
            fb = FirmwareBuilder()
            tpl = fb._resolve_template_dir("esp8266")
            logger.info("Firmware template (esp8266) path: %s", tpl)
        except Exception as e:
            logger.error("Firmware template resolution failed: %s", e, exc_info=True)
        
        # Write access probe
        try:
            appdata = _Path(_os.environ.get("APPDATA", str(_Path.home())))/"UploadBridge"
            appdata.mkdir(parents=True, exist_ok=True)
            probe = appdata/"write_test.tmp"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            logger.info("Write-access OK: %s", appdata)
        except Exception as e:
            logger.error("Write-access check failed: %s", e, exc_info=True)
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
    # Get logger for main function
    try:
        from core.logging import get_logger
        logger = get_logger(__name__)
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
    
    # Log application startup
    try:
        from core.config import get_config
        config = get_config()
        logger.info("Application starting", extra={
            'app_name': config.get('app_name'),
            'app_version': config.get('app_version'),
            'environment': config.environment.value,
            'debug': config.get('debug', False)
        })
    except Exception:
        logger.info("Application starting")
    
    # Crash handler to surface errors in GUI
    def _excepthook(exc_type, exc, tb):
        import traceback
        tb_text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))
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
    try:
        logger.info("Creating main window")
        window = UploadBridgeMainWindow()
        try:
            if 'icon_path' in locals() and icon_path:
                window.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        # Log audit event for application start
        try:
            from core.logging import EnterpriseLogger
            enterprise_logger = EnterpriseLogger.instance()
            enterprise_logger.log_audit("application_started", details={
                'version': config.get('app_version') if 'config' in locals() else 'unknown'
            })
        except Exception:
            pass
        
        # Open file passed via file association (if any)
        try:
            file_to_open = sys.argv[1] if len(sys.argv) > 1 else None
            if file_to_open and hasattr(window, 'load_file'):
                logger.info("Opening file from command line", extra={'file': file_to_open})
                window.load_file(file_to_open)
        except Exception as e:
            logger.error("Failed to open file from command line: %s", e, exc_info=True)
        
        window.show()
        logger.info("Main window shown, entering event loop")
    except Exception as e:
        logger.critical("Failed to create main window: %s", e, exc_info=True)
        QMessageBox.critical(None, "Upload Bridge - Fatal Error", 
                           f"Failed to start application:\n{str(e)}")
        sys.exit(1)
    
    # Run application
    try:
        exit_code = app.exec()
        logger.info("Application exiting", extra={'exit_code': exit_code})
        sys.exit(exit_code)
    except Exception as e:
        logger.critical("Fatal error during application execution: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

