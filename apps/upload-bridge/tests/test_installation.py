#!/usr/bin/env python3
"""
Test Installation Script
Verifies that Upload Bridge can be installed and run properly
"""

import sys
import os

def test_python_version():
    """Test Python version"""
    print("Testing Python version...")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ required")
        return False
    else:
        print("✅ Python version OK")
        return True

def test_imports():
    """Test critical imports"""
    print("\nTesting imports...")
    
    # Test PySide6
    try:
        from PySide6.QtWidgets import QApplication
        print("✅ PySide6 imported successfully")
    except ImportError as e:
        print(f"❌ PySide6 import failed: {e}")
        return False
    
    # Test other dependencies
    dependencies = [
        ('serial', 'pyserial'),
        ('yaml', 'pyyaml'),
        ('colorama', 'colorama'),
        ('tqdm', 'tqdm')
    ]
    
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            return False
    
    return True

def test_application_imports():
    """Test application-specific imports"""
    print("\nTesting application imports...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from main import main
        print("✅ Main application imported successfully")
    except ImportError as e:
        print(f"❌ Main application import failed: {e}")
        return False
    
    try:
        from ui.main_window import UploadBridgeMainWindow
        print("✅ Main window imported successfully")
    except ImportError as e:
        print(f"❌ Main window import failed: {e}")
        return False
    
    return True

def test_gui_creation():
    """Test GUI creation without showing"""
    print("\nTesting GUI creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import UploadBridgeMainWindow
        
        # Create application (but don't show)
        app = QApplication(sys.argv)
        window = UploadBridgeMainWindow()
        
        print("✅ GUI created successfully")
        return True
    except Exception as e:
        print(f"❌ GUI creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Upload Bridge - Installation Test")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_imports,
        test_application_imports,
        test_gui_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Upload Bridge is ready to use.")
        print("\nTo run Upload Bridge:")
        print("1. Double-click RUN_SIMPLE.bat")
        print("2. Or run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTo fix issues:")
        print("1. Run: install_simple.bat")
        print("2. Make sure Python 3.10+ is installed")
        print("3. Check that all dependencies are installed")
    
    print("=" * 50)

if __name__ == "__main__":
    main()










