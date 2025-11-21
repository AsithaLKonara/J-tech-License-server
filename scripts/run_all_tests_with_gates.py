#!/usr/bin/env python3
"""
Enhanced Test Runner with Gates

Runs all tests with coverage and enforces quality gates.
"""

import sys
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Running All Test Suites")
    print("=" * 60)
    
    # L0: Structural tests
    print("\n[L0] Running structural tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/l0_structural/", "-v", "-q"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ L0 tests failed!")
        return False
    
    # L1: Unit tests
    print("\n[L1] Running unit tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/unit/", "-v", "-q"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ L1 tests failed!")
        return False
    
    # L2: Feature tests
    print("\n[L2] Running feature tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/comprehensive/", "-v", "-q"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ L2 tests failed!")
        return False
    
    # L3: Workflow tests
    print("\n[L3] Running workflow tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/l3_workflow/", "-v", "-q"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ L3 tests failed!")
        return False
    
    # L4: Non-functional tests (skip slow ones by default)
    print("\n[L4] Running non-functional tests (excluding slow)...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/l4_nonfunctional/", "-v", "-q", "-m", "not slow"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ L4 tests failed!")
        return False
    
    # Meta tests
    print("\n[Meta] Running meta tests...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/meta/", "-v", "-q"],
        cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print("❌ Meta tests failed!")
        return False
    
    print("\n✅ All test suites passed!")
    return True


def main():
    """Main entry point"""
    success = run_tests()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

