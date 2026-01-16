#!/usr/bin/env python3
"""
Standalone Design Tools Tab Launcher
Runs only the Design Tools tab without the full application or other tabs.
"""

import sys
import os
from pathlib import Path

# Ensure app root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QIcon

# Configure Qt environment
def setup_qt_environment():
    """Set up Qt plugin paths."""
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


def main():
    """Main entry point for standalone design tools tab."""
    setup_qt_environment()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Design Tools")
    app.setOrganizationName("Upload Bridge Project")
    app.setStyle("Fusion")
    
    # Set app icon if available
    base_dir = Path(__file__).parent
    candidate_icons = [
        base_dir / "LEDMatrixStudio_icon.ico",
        base_dir / "resources/icons/LEDMatrixStudio_icon.ico",
        base_dir / "assets/icons/LEDMatrixStudio_icon.ico",
    ]
    icon_path = next((p for p in candidate_icons if p.exists()), None)
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create minimal main window
    window = QMainWindow()
    window.setWindowTitle("Design Tools - LED Matrix Pattern Editor")
    window.setMinimumSize(1200, 800)
    
    try:
        # Import and create design tools tab
        from ui.tabs.design_tools_tab import DesignToolsTab
        
        design_tab = DesignToolsTab()
        window.setCentralWidget(design_tab)
        
        window.show()
        
        print("Design Tools Tab launched successfully!")
        print("Close the window to exit.")
        
        exit_code = app.exec()
        sys.exit(exit_code)
        
    except ImportError as e:
        print(f"Error importing DesignToolsTab: {e}")
        print("Make sure you're running from the correct directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching Design Tools Tab: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

