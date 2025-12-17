#!/usr/bin/env python3
"""
Upload Bridge - Main Application Entry Point
Universal LED Pattern Flasher
"""

import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# #region agent log
try:
    from core.debug_logger import debug_log
    debug_log("main.py:11", "Application startup - Python path initialized", {"python_path": sys.path[:3], "script_path": __file__}, hypothesis_id="A", run_id="run1")
except Exception:
    pass
# #endregion

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication, Qt

# Initialize enterprise logging and configuration early
# #region agent log
try:
    from core.debug_logger import debug_log, debug_log_error
    debug_log("main.py:18", "Starting logging initialization", {}, hypothesis_id="A")
except Exception:
    pass
# #endregion
try:
    # Initialize configuration first
    from core.config import get_config
    from core.logging import setup_logging, get_logger, LogLevel
    from pathlib import Path
    
    # #region agent log
    try:
        debug_log("main.py:25", "Before get_config() call", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    config = get_config()
    
    # #region agent log
    try:
        debug_log("main.py:30", "Config retrieved successfully", {"log_level": config.get('log_level', 'INFO')}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    # Setup enterprise logging with configuration
    log_level_str = config.get('log_level', 'INFO').upper()
    try:
        log_level = LogLevel[log_level_str]
    except KeyError:
        log_level = LogLevel.INFO
    
    # #region agent log
    try:
        debug_log("main.py:38", "Before setup_logging call", {"log_level": log_level_str, "log_to_file": config.get('log_to_file', True)}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    setup_logging(
        level=log_level,
        log_to_file=config.get('log_to_file', True),
        log_to_console=config.get('log_to_console', True),
        json_format=config.get('log_json', False),
        log_dir=Path(config.get('log_dir', 'logs'))
    )
    
    # #region agent log
    try:
        debug_log("main.py:48", "Enterprise logging setup completed", {"log_level": log_level_str}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    logger = get_logger(__name__)
    logger.info("Enterprise logging initialized", extra={
        'log_level': log_level_str,
        'log_to_file': config.get('log_to_file'),
        'log_to_console': config.get('log_to_console'),
        'environment': config.environment.value
    })
    # #region agent log
    try:
        debug_log("main.py:90", "After logger.info call, logging block complete", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
except Exception as e:
    # #region agent log
    try:
        debug_log_error("main.py:56", e, {"fallback": True}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    # Fallback to basic logging if enterprise logging fails
    try:
        from core.logging_config import setup_logging
        log_to_file = bool(os.environ.get("UPLOADBRIDGE_LOG_FILE"))
        setup_logging(log_to_file=log_to_file)
        import logging as _logging
        _logging.getLogger(__name__).warning("Enterprise logging failed, using fallback: %s", e)
        # #region agent log
        try:
            debug_log("main.py:63", "Fallback logging setup completed", {"log_to_file": log_to_file}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    except Exception as e2:
        # #region agent log
        try:
            debug_log_error("main.py:68", e2, {"fallback_failed": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        pass

def _startup_health_check() -> None:
    """Run comprehensive health check and log results."""
    # #region agent log
    try:
        from core.debug_logger import debug_log, debug_log_error
        debug_log("main.py:59", "Health check function entry", {}, hypothesis_id="B")
    except Exception:
        pass
    # #endregion
    try:
        from core.health import get_health_checker
        from core.logging import get_logger
        import os as _os
        import sys as _sys
        from pathlib import Path as _Path

        logger = get_logger(__name__)
        logger.info("Starting comprehensive health check")
        
        # #region agent log
        try:
            debug_log("main.py:72", "Before enterprise health check", {}, hypothesis_id="B")
        except Exception:
            pass
        # #endregion
        
        # Run enterprise health check
        try:
            health_checker = get_health_checker()
            health_status = health_checker.check_health()
            # #region agent log
            try:
                debug_log("main.py:78", "Enterprise health check completed", {"status": health_status.get('status')}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.info("Health check completed", extra={
                'overall_status': health_status['status'],
                'checks': health_status['checks']
            })
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("main.py:85", e, {"health_check_failed": True}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.warning("Enterprise health check failed, running basic checks: %s", e)
        
        # Basic environment checks
        # #region agent log
        try:
            debug_log("main.py:91", "Environment check", {"qt_plugin_path": _os.environ.get("QT_PLUGIN_PATH", "")}, hypothesis_id="B")
        except Exception:
            pass
        # #endregion
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
            # #region agent log
            try:
                debug_log("main.py:100", "Firmware template resolved", {"template_path": str(tpl)}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.info("Firmware template (esp8266) path: %s", tpl)
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("main.py:106", e, {"firmware_template_failed": True}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.error("Firmware template resolution failed: %s", e, exc_info=True)
        
        # Write access probe
        try:
            appdata = _Path(_os.environ.get("APPDATA", str(_Path.home())))/"UploadBridge"
            appdata.mkdir(parents=True, exist_ok=True)
            probe = appdata/"write_test.tmp"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            # #region agent log
            try:
                debug_log("main.py:115", "Write access check passed", {"appdata_path": str(appdata)}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.info("Write-access OK: %s", appdata)
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("main.py:120", e, {"write_access_failed": True}, hypothesis_id="B")
            except Exception:
                pass
            # #endregion
            logger.error("Write-access check failed: %s", e, exc_info=True)
    except Exception as e:
        # #region agent log
        try:
            debug_log_error("main.py:125", e, {"health_check_exception": True}, hypothesis_id="B")
        except Exception:
            pass
        # #endregion
        # Do not raise; this is diagnostic-only
        pass

# Optional debug mode for diagnosing startup issues
# #region agent log
try:
    debug_log("main.py:235", "Before debug mode check", {}, hypothesis_id="A")
except Exception:
    pass
# #endregion
if os.environ.get('UPLOADBRIDGE_DEBUG'):
    os.environ.setdefault('QT_DEBUG_PLUGINS', '1')
    # Prefer software OpenGL in debug to avoid driver issues
    os.environ.setdefault('QT_OPENGL', 'software')
    # #region agent log
    try:
        debug_log("main.py:240", "Debug mode enabled", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion

# Ensure Qt plugin paths resolve correctly in packaged mode (onefile/onedir)
# #region agent log
try:
    debug_log("main.py:245", "Before Qt plugin path setup", {}, hypothesis_id="A")
except Exception:
    pass
# #endregion
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
        # #region agent log
        try:
            debug_log("main.py:263", "Qt plugin path set", {"plugin_path": plugin_path}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    else:
        # #region agent log
        try:
            debug_log("main.py:269", "No Qt plugin path found", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
except Exception as e:
    # #region agent log
    try:
        debug_log_error("main.py:274", e, {"qt_plugin_setup_failed": True}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    pass

# Hide console window on Windows if present (skip in debug mode)
# #region agent log
try:
    debug_log("main.py:282", "Before console window hiding check", {"os_name": os.name}, hypothesis_id="A")
except Exception:
    pass
# #endregion
if os.name == 'nt' and not os.environ.get('UPLOADBRIDGE_DEBUG'):
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
            # #region agent log
            try:
                debug_log("main.py:276", "Console window hidden", {}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
    except Exception as e:
        # #region agent log
        try:
            debug_log_error("main.py:283", e, {"console_hide_failed": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        pass

# #region agent log
try:
    debug_log("main.py:290", "Before UploadBridgeMainWindow import", {}, hypothesis_id="A")
except Exception:
    pass
# #endregion
try:
    from ui.main_window import UploadBridgeMainWindow
    # #region agent log
    try:
        debug_log("main.py:295", "UploadBridgeMainWindow imported successfully", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
except Exception as e:
    # Fallback: extend sys.path for PyInstaller layouts and retry
    # #region agent log
    try:
        debug_log_error("main.py:302", e, {"import_failed_retrying": True}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
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
        # #region agent log
        try:
            debug_log("main.py:315", "Retrying import after path extension", {"candidates": candidates}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        from ui.main_window import UploadBridgeMainWindow  # type: ignore
        # #region agent log
        try:
            debug_log("main.py:320", "Retry import successful", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    except Exception as e2:
        # #region agent log
        try:
            debug_log_error("main.py:325", e2, {"retry_import_failed_exiting": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.error("Import error: %s", e2)
        logger.error("Make sure all dependencies are installed: pip install -r requirements_simple.txt")
        
        # Show user-friendly error message before exiting
        try:
            # Try to show error in GUI if Qt is available
            from PySide6.QtWidgets import QApplication, QMessageBox
            import sys as _sys
            if not QApplication.instance():
                app = QApplication(_sys.argv)
            error_msg = (
                f"Missing Required Dependency\n\n"
                f"Error: {str(e2)}\n\n"
                f"The application requires the 'jsonschema' module to run.\n\n"
                f"To install it, run:\n"
                f"  pip install jsonschema>=4.0.0\n\n"
                f"Or install all dependencies:\n"
                f"  pip install -r requirements.txt"
            )
            QMessageBox.critical(None, "Upload Bridge - Missing Dependency", error_msg)
        except Exception:
            # Fallback to console output if GUI not available
            print("\n" + "="*60)
            print("ERROR: Missing Required Dependency")
            print("="*60)
            print(f"\nError: {e2}")
            print("\nThe application requires the 'jsonschema' module to run.")
            print("\nTo install it, run:")
            print("  pip install jsonschema>=4.0.0")
            print("\nOr install all dependencies:")
            print("  pip install -r requirements.txt")
            print("="*60 + "\n")
        sys.exit(1)


def main():
    """Main application entry point"""
    # #region agent log
    try:
        from core.debug_logger import debug_log, debug_log_error, debug_log_function_entry
        debug_log_function_entry("main", "main.py:178", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    # Get logger for main function
    try:
        from core.logging import get_logger
        logger = get_logger(__name__)
        # #region agent log
        try:
            debug_log("main.py:186", "Logger obtained successfully", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    except Exception:
        import logging
        logger = logging.getLogger(__name__)
        # #region agent log
        try:
            debug_log("main.py:193", "Using fallback logging", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    
    # Log application startup
    try:
        from core.config import get_config
        config = get_config()
        # #region agent log
        try:
            debug_log("main.py:200", "Config loaded in main", {"app_name": config.get('app_name')}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.info("Application starting", extra={
            'app_name': config.get('app_name'),
            'app_version': config.get('app_version'),
            'environment': config.environment.value,
            'debug': config.get('debug', False)
        })
    except Exception:
        logger.info("Application starting")
        # #region agent log
        try:
            debug_log("main.py:208", "Config load failed, using default", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
    
    # Crash handler to surface errors in GUI
    def _excepthook(exc_type, exc, tb):
        import traceback
        tb_text = "".join(traceback.format_exception(exc_type, exc, tb))
        # #region agent log
        try:
            debug_log_error("main.py:214", exc, {"unhandled_exception": True, "exception_type": exc_type.__name__}, hypothesis_id="C")
        except Exception:
            pass
        # #endregion
        try:
            logger.error("Unhandled exception", exc_info=(exc_type, exc, tb))
        except Exception:
            pass
        try:
            QMessageBox.critical(None, "Upload Bridge - Error", tb_text[:4000])
        except Exception:
            pass
    sys.excepthook = _excepthook
    # #region agent log
    try:
        debug_log("main.py:222", "Exception hook installed", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    # Create Qt application
    # #region agent log
    try:
        debug_log("main.py:225", "Before QApplication creation", {"argv_count": len(sys.argv)}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    app = QApplication(sys.argv)
    app.setApplicationName("Upload Bridge")
    app.setOrganizationName("Upload Bridge Project")
    # #region agent log
    try:
        debug_log("main.py:230", "QApplication created", {"app_name": app.applicationName()}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    
    # Set application style
    app.setStyle("Fusion")
    # #region agent log
    try:
        debug_log("main.py:236", "Application style set to Fusion", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion

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
    
    # Authentication check before showing UI
    # #region agent log
    try:
        debug_log("main.py:250", "Before authentication check", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    try:
        # Try new account-based authentication first
        try:
            from core.auth_manager import AuthManager
            from ui.dialogs.login_dialog import ensure_authenticated_or_exit
            from core.config import get_config
            
            config = get_config()
            auth_server_url = config.get('auth_server_url', 'http://localhost:3000')
            
            auth_manager = AuthManager(server_url=auth_server_url)
            
            # Check if authenticated
            if not auth_manager.has_valid_token():
                ensure_authenticated_or_exit(None, auth_manager, auth_server_url)
            
            # #region agent log
            try:
                debug_log("main.py:254", "Account authentication check completed", {}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
        except ImportError:
            # Fall back to file-based activation for backward compatibility
            # #region agent log
            try:
                debug_log("main.py:260", "Falling back to file-based activation", {}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
            from ui.dialogs.activation_dialog import ensure_activation_or_exit
            ensure_activation_or_exit(None)
            # #region agent log
            try:
                debug_log("main.py:264", "File-based activation check completed", {}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
    except Exception as e:
        # #region agent log
        try:
            debug_log_error("main.py:269", e, {"authentication_check_failed": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        # Don't exit on error - allow app to continue (user can retry login later)
        logger.warning("Authentication check failed: %s", e)
        pass

    # Create and show main window
    # #region agent log
    try:
        debug_log("main.py:265", "Before main window creation", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    try:
        logger.info("Creating main window")
        window = UploadBridgeMainWindow()
        # #region agent log
        try:
            debug_log("main.py:270", "Main window created successfully", {"window_type": type(window).__name__}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
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
            # #region agent log
            try:
                debug_log("main.py:290", "Checking for command line file", {"file_to_open": file_to_open}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
            if file_to_open and hasattr(window, 'load_file'):
                logger.info("Opening file from command line", extra={'file': file_to_open})
                # #region agent log
                try:
                    debug_log("main.py:295", "Loading file from command line", {"file": file_to_open}, hypothesis_id="A")
                except Exception:
                    pass
                # #endregion
                window.load_file(file_to_open)
                # #region agent log
                try:
                    debug_log("main.py:299", "File loaded from command line", {"file": file_to_open}, hypothesis_id="A")
                except Exception:
                    pass
                # #endregion
        except Exception as e:
            # #region agent log
            try:
                debug_log_error("main.py:304", e, {"file_load_failed": True}, hypothesis_id="A")
            except Exception:
                pass
            # #endregion
            logger.error("Failed to open file from command line: %s", e, exc_info=True)
        
        window.show()
        # #region agent log
        try:
            debug_log("main.py:310", "Main window shown, entering event loop", {}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.info("Main window shown, entering event loop")
    except Exception as e:
        # #region agent log
        try:
            debug_log_error("main.py:316", e, {"main_window_creation_failed": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.critical("Failed to create main window: %s", e, exc_info=True)
        QMessageBox.critical(None, "Upload Bridge - Fatal Error", 
                           f"Failed to start application:\n{str(e)}")
        sys.exit(1)
    
    # Run application
    # #region agent log
    try:
        debug_log("main.py:320", "Starting Qt event loop", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    try:
        exit_code = app.exec()
        # #region agent log
        try:
            debug_log("main.py:324", "Event loop exited", {"exit_code": exit_code}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.info("Application exiting", extra={'exit_code': exit_code})
        sys.exit(exit_code)
    except Exception as e:
        # #region agent log
        try:
            debug_log_error("main.py:330", e, {"event_loop_failed": True}, hypothesis_id="A")
        except Exception:
            pass
        # #endregion
        logger.critical("Fatal error during application execution: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # #region agent log
    try:
        from core.debug_logger import debug_log
        debug_log("main.py:669", "Main entry point reached - calling main()", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion
    main()
    # #region agent log
    try:
        from core.debug_logger import debug_log
        debug_log("main.py:676", "main() function returned", {}, hypothesis_id="A")
    except Exception:
        pass
    # #endregion

