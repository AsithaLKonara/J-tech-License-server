#!/usr/bin/env python3
"""
Test Directory Script
Verifies that the script is running from the correct directory
"""

import os
import sys

def main():
    print("=" * 50)
    print("Directory Test")
    print("=" * 50)
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Python executable: {sys.executable}")
    
    # Check if main.py exists in current directory
    main_py_path = os.path.join(os.getcwd(), "main.py")
    if os.path.exists(main_py_path):
        print("✅ main.py found in current directory")
    else:
        print("❌ main.py NOT found in current directory")
        print("Available files:")
        for file in os.listdir("."):
            if file.endswith(".py"):
                print(f"  - {file}")
    
    # Check if we're in the upload_bridge directory
    if "upload_bridge" in os.getcwd().lower():
        print("✅ Running from upload_bridge directory")
    else:
        print("❌ NOT running from upload_bridge directory")
        print("Please run this script from the upload_bridge directory")
    
    print("=" * 50)

if __name__ == "__main__":
    main()










