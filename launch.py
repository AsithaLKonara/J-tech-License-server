#!/usr/bin/env python3
"""
Upload Bridge Launcher with Error Handling
"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print(" 🚀 Launching Upload Bridge v3.0...")
print("="*70)
print()

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from ui.main_window import UploadBridgeMainWindow
    
    print("✅ Modules imported successfully")
    print("✅ Creating Qt application...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Upload Bridge")
    app.setOrganizationName("Upload Bridge Project")
    app.setStyle("Fusion")
    
    print("✅ Creating main window...")
    
    window = UploadBridgeMainWindow()
    
    print("✅ Showing window...")
    
    window.show()
    
    print()
    print("="*70)
    print(" ✅ Upload Bridge v3.0 is NOW RUNNING!")
    print("="*70)
    print()
    print(" The application window should be visible on your screen.")
    print(" If you don't see it, check your taskbar or Alt+Tab.")
    print()
    print(" Press Ctrl+C here to close the application.")
    print("="*70)
    print()
    
    sys.exit(app.exec())

except Exception as e:
    print()
    print("="*70)
    print(" ❌ ERROR LAUNCHING APPLICATION")
    print("="*70)
    print()
    print(f"Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("Please report this error.")
    sys.exit(1)

