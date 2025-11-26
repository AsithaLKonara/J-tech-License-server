#!/usr/bin/env python3
"""
Test Application Launch and Runtime Errors
Simulates actual app opening and checks for runtime errors
"""
import sys
import os
import traceback
from pathlib import Path
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal

sys.path.insert(0, os.path.dirname(__file__))

class AppLaunchTester(QObject):
    """Test app launch and capture runtime errors"""
    test_complete = Signal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.errors = []
        self.warnings = []
        self.stage = ""
    
    def test_launch(self):
        """Test launching the application"""
        try:
            self.stage = "Creating QApplication"
            print(f"[RUNTIME] {self.stage}...")
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            app.setApplicationName("Upload Bridge Test")
            app.setOrganizationName("Upload Bridge Project")
            app.setStyle("Fusion")
            
            print(f"[RUNTIME] ✓ QApplication created")
            
            self.stage = "Importing main window"
            print(f"[RUNTIME] {self.stage}...")
            
            from ui.main_window import UploadBridgeMainWindow
            print(f"[RUNTIME] ✓ Main window module imported")
            
            self.stage = "Creating main window instance"
            print(f"[RUNTIME] {self.stage}...")
            
            window = UploadBridgeMainWindow()
            print(f"[RUNTIME] ✓ Main window instance created")
            
            self.stage = "Checking window properties"
            print(f"[RUNTIME] {self.stage}...")
            
            # Check that window has expected properties
            checks = []
            
            # Check tabs exist
            if hasattr(window, 'tabs') or hasattr(window, 'tab_widget'):
                checks.append("Has tabs/widget structure")
            
            # Check for common UI elements
            if hasattr(window, 'setWindowTitle'):
                checks.append("Has window methods")
            
            print(f"[RUNTIME] ✓ Window properties: {', '.join(checks)}")
            
            self.stage = "Showing window (briefly)"
            print(f"[RUNTIME] {self.stage}...")
            
            window.show()
            print(f"[RUNTIME] ✓ Window shown")
            
            # Process events to ensure everything renders
            app.processEvents()
            time.sleep(0.5)  # Brief delay to see if anything crashes
            app.processEvents()
            
            self.stage = "Checking for runtime errors"
            print(f"[RUNTIME] {self.stage}...")
            
            # Check if window is still valid
            try:
                is_visible = window.isVisible()
                title = window.windowTitle()
                print(f"[RUNTIME] ✓ Window is valid (visible={is_visible}, title={title})")
            except Exception as e:
                self.errors.append(f"Window validation failed: {e}")
            
            # Test tab switching if possible
            try:
                if hasattr(window, 'tab_widget'):
                    tab_count = window.tab_widget.count()
                    print(f"[RUNTIME] ✓ Found {tab_count} tabs")
            except Exception as e:
                self.warnings.append(f"Tab check failed: {e}")
            
            self.stage = "Cleanup"
            print(f"[RUNTIME] {self.stage}...")
            
            window.close()
            app.quit()
            
            print(f"[RUNTIME] ✓ Cleanup complete")
            
            if self.errors:
                return False, f"Errors during launch: {'; '.join(self.errors)}"
            else:
                return True, "Launch successful"
                
        except Exception as e:
            error_msg = f"Failed at stage '{self.stage}': {str(e)}\n{traceback.format_exc()}"
            self.errors.append(error_msg)
            return False, error_msg

def main():
    """Run runtime launch test"""
    print("="*70)
    print("RUNTIME TEST: Application Launch and Runtime Error Check")
    print("="*70)
    print()
    
    tester = AppLaunchTester()
    success, message = tester.test_launch()
    
    print()
    print("="*70)
    if success:
        print("✓ RUNTIME TEST PASSED")
        print("="*70)
        print(f"Result: {message}")
        if tester.warnings:
            print(f"\nWarnings: {len(tester.warnings)}")
            for w in tester.warnings:
                print(f"  - {w}")
        return 0
    else:
        print("✗ RUNTIME TEST FAILED")
        print("="*70)
        print(f"Error: {message}")
        if tester.errors:
            print(f"\nErrors ({len(tester.errors)}):")
            for e in tester.errors:
                print(f"  - {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

