#!/usr/bin/env python3
"""
Check GUI Test Status

Checks if the automated GUI test is running or has completed.

Usage:
    python scripts/check_gui_test_status.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_test_status():
    """Check the status of GUI test execution."""
    results_file = project_root / "docs" / "GUI_TEST_RESULTS_AUTOMATED.md"
    
    print("=" * 70)
    print("GUI Test Status Check")
    print("=" * 70)
    print()
    
    # Check if results file exists
    if results_file.exists():
        print("✅ Test Results File Found!")
        print(f"   Location: {results_file}")
        print()
        print("Reading results...")
        print()
        
        with open(results_file, 'r') as f:
            content = f.read()
            print(content[:1000])  # First 1000 chars
            if len(content) > 1000:
                print("\n... (truncated)")
        
        return True
    else:
        print("⏳ Test Results File Not Found")
        print(f"   Expected: {results_file}")
        print()
        print("This means:")
        print("  - Test may still be running")
        print("  - Test may not have started yet")
        print("  - Test may have encountered an error")
        print()
        print("To check:")
        print("  1. Look for GUI test window (should be visible)")
        print("  2. Check console for error messages")
        print("  3. Wait a few more minutes for completion")
        print()
        print("To run the test:")
        print("  python tests/gui/run_gui_tests_automated.py")
        
        return False

if __name__ == "__main__":
    check_test_status()








