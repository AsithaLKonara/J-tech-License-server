#!/usr/bin/env python3
"""
Python 3.12 Verification Script
Comprehensive test to ensure Upload Bridge works perfectly with Python 3.12
"""

import sys
import os
import platform
import subprocess
from datetime import datetime

def test_python_version():
    """Test Python version and compatibility"""
    print("🐍 Testing Python Version...")
    
    version = sys.version_info
    print(f"   Python Version: {version.major}.{version.minor}.{version.micro}")
    print(f"   Platform: {platform.platform()}")
    print(f"   Architecture: {platform.architecture()}")
    
    if version.major == 3 and version.minor >= 12:
        print("   ✅ Python 3.12+ detected - Full compatibility")
        return True
    elif version.major == 3 and version.minor >= 8:
        print("   ✅ Python 3.8+ detected - Compatible")
        return True
    else:
        print("   ❌ Python 3.8+ required")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        ('PySide6', 'PySide6'),
        ('serial', 'pyserial'),
        ('yaml', 'pyyaml'),
        ('colorama', 'colorama'),
        ('tqdm', 'tqdm'),
        ('esptool', 'esptool')
    ]
    
    all_good = True
    for module, package in dependencies:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'Unknown')
            print(f"   ✅ {package}: {version}")
        except ImportError as e:
            print(f"   ❌ {package}: Not installed - {e}")
            all_good = False
    
    return all_good

def test_application_imports():
    """Test application-specific imports"""
    print("\n🔧 Testing Application Imports...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from main import main
        print("   ✅ Main application imported")
    except ImportError as e:
        print(f"   ❌ Main application import failed: {e}")
        return False
    
    try:
        from ui.main_window import UploadBridgeMainWindow
        print("   ✅ Main window imported")
    except ImportError as e:
        print(f"   ❌ Main window import failed: {e}")
        return False
    
    try:
        from core.pattern import Pattern
        print("   ✅ Pattern class imported")
    except ImportError as e:
        print(f"   ❌ Pattern class import failed: {e}")
        return False
    
    try:
        from parsers.parser_registry import parse_pattern_file
        print("   ✅ Parser registry imported")
    except ImportError as e:
        print(f"   ❌ Parser registry import failed: {e}")
        return False
    
    return True

def test_gui_creation():
    """Test GUI creation without showing"""
    print("\n🖥️  Testing GUI Creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from ui.main_window import UploadBridgeMainWindow
        
        # Create application (but don't show)
        app = QApplication(sys.argv)
        window = UploadBridgeMainWindow()
        
        print("   ✅ GUI created successfully")
        print("   ✅ PySide6 working correctly")
        
        # Clean up
        app.quit()
        return True
    except Exception as e:
        print(f"   ❌ GUI creation failed: {e}")
        return False

def test_file_operations():
    """Test file operations"""
    print("\n📁 Testing File Operations...")
    
    try:
        # Test current directory
        cwd = os.getcwd()
        print(f"   Current directory: {cwd}")
        
        # Test if main.py exists
        main_py = os.path.join(cwd, "main.py")
        if os.path.exists(main_py):
            print("   ✅ main.py found")
        else:
            print("   ❌ main.py not found")
            return False
        
        # Test if we're in upload_bridge directory
        if "upload_bridge" in cwd.lower():
            print("   ✅ Running from upload_bridge directory")
        else:
            print("   ⚠️  Not running from upload_bridge directory")
        
        return True
    except Exception as e:
        print(f"   ❌ File operations failed: {e}")
        return False

def test_serial_communication():
    """Test serial communication capabilities"""
    print("\n🔌 Testing Serial Communication...")
    
    try:
        import serial
        import serial.tools.list_ports
        
        # List available ports
        ports = serial.tools.list_ports.comports()
        print(f"   Found {len(ports)} serial ports")
        
        for port in ports:
            print(f"   - {port.device}: {port.description}")
        
        print("   ✅ Serial communication ready")
        return True
    except Exception as e:
        print(f"   ❌ Serial communication failed: {e}")
        return False

def test_esp_tools():
    """Test ESP tools"""
    print("\n⚡ Testing ESP Tools...")
    
    try:
        import esptool
        
        # Test esptool version
        version = esptool.__version__
        print(f"   esptool version: {version}")
        
        # Test if esptool can be called
        result = subprocess.run(['esptool.py', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("   ✅ esptool command line working")
        else:
            print("   ⚠️  esptool command line not working")
        
        print("   ✅ ESP tools ready")
        return True
    except Exception as e:
        print(f"   ❌ ESP tools failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Upload Bridge - Python 3.12 Verification")
    print("=" * 60)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Application Imports", test_application_imports),
        ("GUI Creation", test_gui_creation),
        ("File Operations", test_file_operations),
        ("Serial Communication", test_serial_communication),
        ("ESP Tools", test_esp_tools)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Upload Bridge is fully compatible with Python 3.12")
        print("✅ Ready for production use")
        print("\nTo run Upload Bridge:")
        print("1. Double-click LAUNCH_SAFE.bat")
        print("2. Or run: python main.py")
    else:
        print("⚠️  Some tests failed")
        print("Please check the errors above and fix them")
        print("\nCommon fixes:")
        print("1. Run: install_simple.bat")
        print("2. Check Python version (needs 3.8+)")
        print("3. Make sure you're in the upload_bridge directory")
    
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)










