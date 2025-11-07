#!/usr/bin/env python3
"""
Safe Launcher for Upload Bridge
Handles errors gracefully and provides helpful messages
"""

import sys
import os
import traceback

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        print(f"Current version: {sys.version}")
        print("Please install Python 3.8+ from: https://python.org")
        return False
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import PySide6
    except ImportError:
        missing.append("PySide6")
    
    try:
        import serial
    except ImportError:
        missing.append("pyserial")
    
    try:
        import yaml
    except ImportError:
        missing.append("pyyaml")
    
    try:
        import colorama
    except ImportError:
        missing.append("colorama")
    
    try:
        import tqdm
    except ImportError:
        missing.append("tqdm")
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nTo install missing dependencies:")
        print("pip install -r requirements_simple.txt")
        print("Or run: install_simple.bat")
        return False
    
    return True

def launch_application():
    """Launch the main application"""
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import and run main application
        from main import main
        main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nPossible solutions:")
        print("1. Run: install_simple.bat")
        print("2. Check that all files are present")
        print("3. Make sure you're in the correct directory")
        
    except Exception as e:
        print(f"❌ Application error: {e}")
        print("\nFull error details:")
        traceback.print_exc()
        
        print("\nPossible solutions:")
        print("1. Run: test_installation.py")
        print("2. Check Python version (needs 3.8+)")
        print("3. Reinstall dependencies")

def main():
    """Main launcher function"""
    print("=" * 60)
    print("Upload Bridge - Safe Launcher")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        input("\nPress Enter to exit...")
        return
    
    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        return
    
    print("✅ All checks passed!")
    print("🚀 Starting Upload Bridge...")
    print()
    
    # Launch application
    launch_application()

if __name__ == "__main__":
    main()










