#!/usr/bin/env python3
"""
Upload Bridge Launcher Script
Quick start without complex setup
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print(" 🚀 Upload Bridge v3.0 - Universal LED Pattern Flasher")
print("="*70)
print()

# Check dependencies
print("Checking dependencies...")

try:
    import PySide6
    print("✅ PySide6 installed")
except ImportError:
    print("❌ PySide6 not found")
    print("   Install: pip install PySide6")
    sys.exit(1)

try:
    import serial
    print("✅ pyserial installed")
except ImportError:
    print("⚠️  pyserial not found (needed for port detection)")
    print("   Install: pip install pyserial")

try:
    import yaml
    print("✅ PyYAML installed")
except ImportError:
    print("❌ PyYAML not found")
    print("   Install: pip install PyYAML")
    sys.exit(1)

print()
print("Launching Upload Bridge...")
print()

# Import and run
try:
    from main import main
    main()
except Exception as e:
    print(f"❌ Error launching: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

