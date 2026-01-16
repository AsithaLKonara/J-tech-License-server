#!/usr/bin/env python3
"""
Test Runner for Comprehensive Deep Testing Suite

Runs all test suites in the comprehensive testing package.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


def run_tests():
    """Run all comprehensive tests"""
    
    # Set environment for headless Qt
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    
    # Test suite files
    test_suites = [
        "tests/comprehensive/test_suite_1_design_tools_core.py",
        "tests/comprehensive/test_suite_2_feature_overview.py",
        "tests/comprehensive/test_suite_3_all_tabs_integration.py",
        "tests/comprehensive/test_suite_4_signal_connections.py",
        "tests/comprehensive/test_suite_5_error_handling.py",
        "tests/comprehensive/test_suite_6_ui_components.py",
        "tests/comprehensive/test_suite_7_manager_interactions.py",
        "tests/comprehensive/test_suite_8_file_io.py",
    ]
    
    # Run pytest on all suites
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ] + test_suites
    
    print("Running comprehensive test suites...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

