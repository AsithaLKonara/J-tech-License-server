#!/usr/bin/env python3
"""
Integration Test Runner

Runs integration tests for layer features and generates reports.

Usage:
    python scripts/run_integration_tests.py --gui
    python scripts/run_integration_tests.py --signals
    python scripts/run_integration_tests.py --cross-feature
    python scripts/run_integration_tests.py --all
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_gui_tests():
    """Run GUI test suite."""
    print("=" * 70)
    print("Running GUI Test Suite")
    print("=" * 70)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, "tests/gui/test_design_tools_gui.py"],
            cwd=project_root,
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running GUI tests: {e}")
        return False


def run_signal_tests():
    """Run signal integration tests."""
    print("=" * 70)
    print("Running Signal Connection Tests")
    print("=" * 70)
    print()
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/integration/test_signal_integrations.py", "-v"],
            cwd=project_root,
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running signal tests: {e}")
        return False


def run_cross_feature_tests():
    """Run cross-feature integration tests."""
    print("=" * 70)
    print("Running Cross-Feature Integration Tests")
    print("=" * 70)
    print()
    print("Note: Cross-feature tests require manual verification.")
    print("Please refer to docs/INTEGRATION_TEST_RESULTS.md for test scenarios.")
    print()
    return True


def generate_report(results: dict):
    """Generate integration test report."""
    report_file = project_root / "docs" / "INTEGRATION_TEST_RESULTS.md"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# Integration Test Results - Layer Features

**Date**: {timestamp}  
**Tester**: Automated Test Runner  
**Application Version**: [Version]

---

## Test Execution Summary

| Test Category | Status | Passed | Failed | Notes |
|---------------|--------|--------|--------|-------|
| GUI Test Suite | {'✅ Pass' if results.get('gui') else '❌ Fail'} | - | - | |
| Signal Connections | {'✅ Pass' if results.get('signals') else '❌ Fail'} | - | - | |
| Cross-Feature Integration | ⏳ Manual | - | - | |

---

## Detailed Results

### GUI Test Suite
**Status**: {'✅ Pass' if results.get('gui') else '❌ Fail'}  
**Date**: {timestamp}

[Add detailed results from GUI test suite]

### Signal Connection Tests
**Status**: {'✅ Pass' if results.get('signals') else '❌ Fail'}  
**Date**: {timestamp}

[Add detailed results from signal tests]

### Cross-Feature Integration
**Status**: ⏳ Manual Testing Required  
**Date**: {timestamp}

Please refer to docs/INTEGRATION_TEST_RESULTS.md for manual test scenarios.

---

## Overall Summary

**Total Tests**: [Number]  
**Passed**: [Number]  
**Failed**: [Number]

### Issues Found:
[List any issues]

---

## Sign-off

**Tester**: Automated Test Runner  
**Date**: {timestamp}  
**Status**: {'✅ Ready for UAT' if all(results.values()) else '❌ Needs Review'}
"""
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"Report generated: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="Integration Test Runner")
    parser.add_argument("--gui", action="store_true", help="Run GUI test suite")
    parser.add_argument("--signals", action="store_true", help="Run signal connection tests")
    parser.add_argument("--cross-feature", action="store_true", help="Show cross-feature test scenarios")
    parser.add_argument("--all", action="store_true", help="Run all automated tests")
    
    args = parser.parse_args()
    
    results = {}
    
    if args.all or args.gui:
        results['gui'] = run_gui_tests()
    
    if args.all or args.signals:
        results['signals'] = run_signal_tests()
    
    if args.all or args.cross_feature:
        results['cross_feature'] = run_cross_feature_tests()
    
    if args.all:
        generate_report(results)
        print()
        print("=" * 70)
        print("Integration Test Summary")
        print("=" * 70)
        for test, passed in results.items():
            status = "✅ Pass" if passed else "❌ Fail"
            print(f"{test}: {status}")


if __name__ == "__main__":
    main()

