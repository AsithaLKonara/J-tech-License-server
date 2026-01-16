#!/usr/bin/env python3
"""
Upload Bridge - Main Application Entry Point
Universal LED Pattern Flasher
"""

import sys
import os
from pathlib import Path
import logging

# Ensure app root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def setup_initial_logger() -> logging.Logger:
    """Create a temporary logger for early startup messages."""
    logger = logging.getLogger("startup_logger")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def configure_environment(logger: logging.Logger) -> None:
    """Set environment variables for Qt and PyInstaller plugins."""
    if os.environ.get("UPLOADBRIDGE_DEBUG"):
        os.environ.setdefault("QT_DEBUG_PLUGINS", "1")
        os.environ.setdefault("QT_OPENGL", "software")

    meipass = getattr(sys, "_MEIPASS", None)
    candidates = []
    if meipass:
        candidates += [
            os.path.join(meipass, "PySide6", "plugins"),
            os.path.join(meipass, "PySide6", "Qt", "plugins"),
            os.path.join(meipass, "qt6_plugins"),
        ]

    base_dir = Path(__file__).parent
    candidates += [
        base_dir / "PySide6" / "plugins",
        base_dir / "PySide6" / "Qt" / "plugins",
        base_dir / "qt6_plugins",
    ]

    plugin_path = next((p for p in candidates if p.is_dir()), None)
    if plugin_path:
        os.environ["QT_PLUGIN_PATH"] = str(plugin_path)
        platforms_path = plugin_path / "platforms"
        if platforms_path.is_dir():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_path)
        logger.info("Qt plugin path set: %s", plugin_path)


def hide_windows_console():
    """Hide console window on Windows in production mode."""
    if os.name == "nt" and not os.environ.get("UPLOADBRIDGE_DEBUG"):
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass


def run_health_checks(logger: logging.Logger):
    """Perform environment, file system, and firmware template health checks."""
    try:
        from core.health import get_health_checker
        from core.logging import get_logger

        health_logger = get_logger(__name__)
        health_logger.info("Starting comprehensive health check")

        try:
            health_checker = get_health_checker()
            status = health_checker.check_health()
            health_logger.info(
                "Health check results",
                extra={"overall_status": status["status"], "checks": status["checks"]},
            )
        except Exception as e:
            health_logger.warning("Enterprise health check failed, basic checks only: %s", e)

        # Environment info
        import sys as _sys

        health_logger.info(
            "Environment check",
            extra={
                "QT_PLUGIN_PATH": os.environ.get("QT_PLUGIN_PATH", ""),
                "QT_QPA_PLATFORM_PLUGIN_PATH": os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", ""),
                "python_version": _sys.version,
            },
        )

        # Firmware template test
        try:
            from firmware.builder import FirmwareBuilder

            fb = FirmwareBuilder()
            tpl = fb._resolve_template_dir("esp8266")
            health_logger.info("Firmware template path (esp8266): %s", tpl)
        except Exception as e:
            health_logger.error("Firmware template resolution failed: %s", e, exc_info=True)

        # Write-access test
        try:
            appdata = Path(os.environ.get("APPDATA", str(Path.home()))) / "UploadBridge"
            appdata.mkdir(parents=True, exist_ok=True)
            test_file = appdata / "write_test.tmp"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            health_logger.info("Write-access OK: %s", appdata)
        except Exception as e:
            health_logger.error("Write-access check failed: %s", e, exc_info=True)

    except Exception as e:
        logger.warning("Health checks failed: %s", e)


def setup_qt_app() -> "QApplication":
    """Initialize QApplication and set application attributes."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QCoreApplication

    app = QApplication(sys.argv)
    app.setApplicationName("Upload Bridge")
    app.setOrganizationName("Upload Bridge Project")
    app.setStyle("Fusion")

    if os.environ.get("QT_OPENGL", "").lower() == "software" or os.environ.get("UPLOADBRIDGE_DEBUG"):
        try:
            QCoreApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        except Exception:
            pass

    # Set app icon
    from PySide6.QtGui import QIcon

    base_dir = Path(__file__).parent
    candidate_icons = [
        base_dir / "LEDMatrixStudio_icon.ico",
        base_dir / "resources/icons/LEDMatrixStudio_icon.ico",
        base_dir / "assets/icons/LEDMatrixStudio_icon.ico",
    ]
    icon_path = next((p for p in candidate_icons if p.exists()), None)
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def setup_exception_hook(logger: logging.Logger):
    """Catch unhandled exceptions and display an error dialog."""
    import traceback
    from PySide6.QtWidgets import QMessageBox

    def excepthook(exc_type, exc_value, exc_traceback):
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        if not QApplication.instance():
            print(tb_text, file=sys.stderr)
            return

        try:
            QMessageBox.critical(None, "Upload Bridge - Error", tb_text[:4000])
        except Exception:
            pass

    sys.excepthook = excepthook


def run_app():
    logger = setup_initial_logger()
    logger.info("Starting Upload Bridge")

    configure_environment(logger)
    hide_windows_console()

    # Run early health checks
    run_health_checks(logger)

    try:
        from core.config import get_config
        from core.logging import setup_logging, get_logger, LogLevel

        config = get_config()
        log_level_str = config.get("log_level", "INFO").upper()
        log_level = LogLevel.__members__.get(log_level_str, LogLevel.INFO)

        setup_logging(
            level=log_level,
            log_to_file=config.get("log_to_file", True),
            log_to_console=config.get("log_to_console", True),
            json_format=config.get("log_json", False),
            log_dir=Path(config.get("log_dir", "logs")),
        )
        logger = get_logger(__name__)
        logger.info(
            "Enterprise logging initialized",
            extra={
                "log_level": log_level_str,
                "log_to_console": config.get("log_to_console"),
                "environment": getattr(config, "environment", None),
            },
        )

    except Exception as e:
        logger.warning("Failed to initialize enterprise logging: %s", e)

    setup_exception_hook(logger)

    app = setup_qt_app()

    # Authentication / License verification - MANDATORY
    # User must login and have ACTIVE license before app opens
    try:
        from core.auth_manager import AuthManager
        from core.license_manager import LicenseManager
        from ui.dialogs.login_dialog import ensure_authenticated_or_exit
        from PySide6.QtWidgets import QMessageBox, QDialog

        auth_manager = AuthManager(server_url=config.get("auth_server_url", "http://localhost:8000"))
        license_manager = LicenseManager(server_url=config.get("auth_server_url", "http://localhost:8000"))
        
        # Step 1: Check if user is authenticated
        if not auth_manager.has_valid_token():
            logger.info("No valid authentication token found - showing login dialog")
            ensure_authenticated_or_exit(None, auth_manager, config)
        
        # Step 2: Verify license is ACTIVE (respects grace period for offline use)
        logger.info("Verifying license status...")
        # Don't force online - allows grace period for offline operation
        is_valid, message, license_info = license_manager.validate_license(force_online=False)
        
        # Check if license status is ACTIVE
        license_status = license_info.get('status', '').upper() if license_info else ''
        
        if not is_valid or license_status != 'ACTIVE':
            logger.warning("License validation failed or not ACTIVE. Status: %s, Message: %s", license_status, message)
            
            # Show license activation dialog instead of just exiting
            from ui.dialogs.license_activation_dialog import LicenseActivationDialog
            from PySide6.QtWidgets import QApplication
            
            logger.info("Showing license activation dialog...")
            activation_dialog = LicenseActivationDialog(
                None,
                auth_manager=auth_manager,
                license_manager=license_manager,
                config=config
            )
            
            # Ensure dialog is visible and on top
            activation_dialog.raise_()
            activation_dialog.activateWindow()
            
            # Show activation dialog - it will validate license internally before accepting
            # Dialog will only accept if license is ACTIVE
            result = activation_dialog.exec()
            
            # If dialog was cancelled, closed, or activation failed
            if result != QDialog.Accepted:
                logger.warning("License activation dialog was cancelled or closed without successful activation")
                QMessageBox.warning(
                    None,
                    "License Required",
                    "License activation is required to use Upload Bridge.\n\nApplication will now exit."
                )
                sys.exit(1)
            
            # Dialog was accepted, which means license was successfully activated and validated as ACTIVE
            # Re-check license one final time to ensure it's ACTIVE before continuing
            logger.info("License activation dialog accepted - performing final license verification...")
            is_valid_final, message_final, license_info_final = license_manager.validate_license(force_online=True)
            license_status_final = license_info_final.get('status', '').upper() if license_info_final else ''
            
            if not is_valid_final or license_status_final != 'ACTIVE':
                logger.error("License still not ACTIVE after activation dialog accepted. Status: %s, Message: %s", license_status_final, message_final)
                QMessageBox.critical(
                    None,
                    "License Not Active",
                    f"License activation dialog was accepted, but license verification failed.\n\n"
                    f"Status: {license_status_final or 'UNKNOWN'}\n"
                    f"Message: {message_final}\n\n"
                    f"Please contact support."
                )
                sys.exit(1)
            
            logger.info("License verified successfully after activation. Status: ACTIVE")
        else:
            logger.info("License verified successfully. Status: ACTIVE")

    except ImportError as e:
        logger.critical("Failed to import required modules: %s", e, exc_info=True)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"Failed to load license system:\n\n{e}\n\nApplication cannot start."
        )
        sys.exit(1)
    except Exception as e:
        logger.critical("License verification failed: %s", e, exc_info=True)
        QMessageBox.critical(
            None,
            "License Verification Failed",
            f"Failed to verify license:\n\n{e}\n\nApplication cannot start."
        )
        sys.exit(1)

    # Create main controller
    try:
        from ui.factory import create_editor_controller

        controller = create_editor_controller()
        controller.show()

        # Open file from command line if provided
        if len(sys.argv) > 1 and hasattr(controller, "load_file"):
            file_to_open = sys.argv[1]
            logger.info("Opening file from command line: %s", file_to_open)
            try:
                controller.load_file(file_to_open)
            except Exception as e:
                logger.error("Failed to open file: %s", e, exc_info=True)

        exit_code = app.exec()
        logger.info("Application exiting", extra={"exit_code": exit_code})
        sys.exit(exit_code)

    except Exception as e:
        logger.critical("Failed to create EditorController: %s", e, exc_info=True)
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(None, "Upload Bridge - Fatal Error", f"Failed to start application:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    run_app()
