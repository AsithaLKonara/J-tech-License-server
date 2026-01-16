#!/usr/bin/env python3
"""
Coverage Gate Script

Enforces minimum coverage threshold (85%) and blocks merge if not met.
"""

import sys
import subprocess
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_THRESHOLD = 85.0
COVERAGE_JSON = PROJECT_ROOT / "coverage.json"


def run_coverage():
    """Run pytest with coverage"""
    print("Running tests with coverage...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=ui.tabs.design_tools_tab",
        "--cov=domain",
        "--cov=core",
        "--cov-report=json:coverage.json",
        "--cov-report=term-missing",
        "-q"
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Tests failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    
    return True


def check_coverage():
    """Check if coverage meets threshold"""
    if not COVERAGE_JSON.exists():
        print(f"ERROR: Coverage file not found: {COVERAGE_JSON}")
        return False
    
    with open(COVERAGE_JSON) as f:
        data = json.load(f)
    
    total_coverage = data['totals']['percent_covered']
    
    print(f"\nCoverage: {total_coverage:.2f}% (Threshold: {COVERAGE_THRESHOLD}%)")
    
    if total_coverage < COVERAGE_THRESHOLD:
        print(f"\n❌ FAIL: Coverage {total_coverage:.2f}% is below threshold {COVERAGE_THRESHOLD}%")
        print("\nModules below threshold:")
        
        for file_path, file_data in data['files'].items():
            file_coverage = file_data['summary']['percent_covered']
            if file_coverage < COVERAGE_THRESHOLD:
                print(f"  {file_path}: {file_coverage:.2f}%")
        
        return False
    else:
        print(f"\n✅ PASS: Coverage {total_coverage:.2f}% meets threshold {COVERAGE_THRESHOLD}%")
        return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("Coverage Gate")
    print("=" * 60)
    
    # Run coverage
    if not run_coverage():
        sys.exit(1)
    
    # Check coverage
    if not check_coverage():
        sys.exit(1)
    
    print("\n✅ Coverage gate passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()

