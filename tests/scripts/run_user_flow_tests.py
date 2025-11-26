#!/usr/bin/env python3
"""
Automated User Flow Testing Runner

This script runs automated tests that simulate real user interactions with the application.
It opens the application and tests all user flows as a real user would.

Usage:
    python run_user_flow_tests.py
    python run_user_flow_tests.py --verbose
    python run_user_flow_tests.py --specific TestUserFlow_PatternCreation
"""

import sys
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run automated user flow tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_user_flow_tests.py
  
  # Run with verbose output
  python run_user_flow_tests.py --verbose
  
  # Run specific test class
  python run_user_flow_tests.py --specific TestUserFlow_PatternCreation
  
  # Run specific test method
  python run_user_flow_tests.py --specific TestUserFlow_PatternCreation::test_create_new_pattern
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--specific", "-s",
        type=str,
        help="Run specific test class or method"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Run with coverage reporting"
    )
    
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    test_file = Path(__file__).parent / "tests" / "e2e" / "test_user_flows_automated.py"
    
    if not test_file.exists():
        print(f"Error: Test file not found: {test_file}")
        sys.exit(1)
    
    cmd = ["python", "-m", "pytest", str(test_file)]
    
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if args.specific:
        # Add specific test to run
        cmd.append("-k")
        cmd.append(args.specific)
    
    if args.coverage:
        cmd.extend(["--cov=ui", "--cov=core", "--cov-report=term-missing"])
    
    if args.html_report:
        cmd.extend(["--html=test_report.html", "--self-contained-html"])
    
    # Add standard options
    cmd.extend(["--tb=short", "--color=yes"])
    
    print("=" * 70)
    print("Running Automated User Flow Tests")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}")
    print("=" * 70)
    print()
    
    # Run tests
    result = subprocess.run(cmd)
    
    print()
    print("=" * 70)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

