"""
Test Execution Script - Runs all test suites
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0


def main():
    """Run all test suites."""
    print("="*70)
    print("Upload Bridge - Complete Test Suite Execution")
    print("="*70)
    
    results = {}
    
    # Phase 1: Unit Tests
    print("\n[Phase 1] Unit Testing")
    results['unit'] = run_command(
        ['python', '-m', 'pytest', 'tests/unit/', '-v', '--tb=short'],
        "Unit Tests"
    )
    
    # Phase 2: Integration Tests
    print("\n[Phase 2] Integration Testing")
    results['integration'] = run_command(
        ['python', '-m', 'pytest', 'tests/integration/', '-v', '--tb=short'],
        "Integration Tests"
    )
    
    # Phase 3: Comprehensive Tests
    print("\n[Phase 3] Comprehensive System Tests")
    results['comprehensive'] = run_command(
        ['python', '-m', 'pytest', 'tests/comprehensive/', '-v', '--tb=short'],
        "Comprehensive Tests"
    )
    
    # Phase 4: Circular Layout Tests
    print("\n[Phase 4] Circular Layout Tests")
    results['circular'] = run_command(
        ['python', '-m', 'pytest', 'tests/test_budurasmala_*.py', '-v', '--tb=short'],
        "Circular Layout Tests"
    )
    
    # Phase 5: Export/Import Tests
    print("\n[Phase 5] Export/Import Tests")
    results['export'] = run_command(
        ['python', '-m', 'pytest', 'tests/test_budurasmala_export.py', '-v', '--tb=short'],
        "Export/Import Tests"
    )
    
    # Summary
    print("\n" + "="*70)
    print("Test Execution Summary")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {name:20s}: {status}")
    
    print(f"\nTotal: {total}, Passed: {passed}, Failed: {failed}")
    
    if failed > 0:
        print("\n⚠️  Some test suites failed. Review output above.")
        sys.exit(1)
    else:
        print("\n✅ All test suites passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

