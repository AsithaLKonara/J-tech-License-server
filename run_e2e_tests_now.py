#!/usr/bin/env python3
"""
E2E Test Runner - Direct Execution
Runs all E2E tests and saves output to file
"""

import sys
import subprocess
import os
from pathlib import Path

# Change to project root
os.chdir(Path(__file__).parent)

print("=" * 60)
print("Running E2E Test Suite")
print("=" * 60)
print()

# Check if pytest is available
try:
    import pytest
    print(f"✓ pytest {pytest.__version__} found")
except ImportError:
    print("✗ pytest not found. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-xdist", "pytest-cov", "requests", "mysql-connector-python"], check=True)
    import pytest
    print(f"✓ pytest {pytest.__version__} installed")

print()

# Check test directory
test_dir = Path("tests/e2e")
if not test_dir.exists():
    print(f"✗ Test directory not found: {test_dir}")
    sys.exit(1)

print(f"✓ Test directory found: {test_dir}")
print()

# Count test files
test_files = list(test_dir.rglob("test_*.py"))
print(f"Found {len(test_files)} test files")
print()

# Run tests
print("Starting test execution...")
print("=" * 60)
print()

try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/e2e/", "-v", "--tb=short"],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    
    # Save to file
    with open("e2e_test_output.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\n\nSTDERR:\n")
        f.write(result.stderr)
        f.write(f"\n\nExit code: {result.returncode}\n")
    
    print()
    print("=" * 60)
    print(f"Test execution complete. Exit code: {result.returncode}")
    print("Output saved to: e2e_test_output.txt")
    print("=" * 60)
    
    sys.exit(result.returncode)
    
except subprocess.TimeoutExpired:
    print("✗ Tests timed out after 10 minutes")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error running tests: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
