#!/usr/bin/env python3
"""
Deep Integration Test Runner

Runs comprehensive integration tests covering all component integrations.

Usage:
    python run_deep_integration_tests.py
    python run_deep_integration_tests.py --verbose
    python run_deep_integration_tests.py --specific TestTabToTabIntegrations
"""

import sys
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run deep integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all integration tests
  python run_deep_integration_tests.py
  
  # Run with verbose output
  python run_deep_integration_tests.py --verbose
  
  # Run specific test class
  python run_deep_integration_tests.py --specific TestTabToTabIntegrations
  
  # Run with coverage
  python run_deep_integration_tests.py --coverage
        """
    )
    
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--specific", "-s", type=str, help="Run specific test class")
    parser.add_argument("--coverage", "-c", action="store_true", help="Run with coverage")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML report")
    
    args = parser.parse_args()
    
    # Build pytest command
    test_dir = Path(__file__).parent / "tests" / "integration"
    
    if not test_dir.exists():
        print(f"Error: Test directory not found: {test_dir}")
        sys.exit(1)
    
    cmd = ["python", "-m", "pytest", str(test_dir)]
    
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if args.specific:
        cmd.append("-k")
        cmd.append(args.specific)
    
    if args.coverage:
        cmd.extend(["--cov=ui", "--cov=core", "--cov-report=term-missing"])
    
    if args.html_report:
        cmd.extend(["--html=integration_test_report.html", "--self-contained-html"])
    
    cmd.extend(["--tb=short", "--color=yes"])
    
    print("=" * 70)
    print("Running Deep Integration Tests")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}")
    print("=" * 70)
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

