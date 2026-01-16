#!/usr/bin/env python3
"""
E2E Test Runner
Main script to run all E2E tests with proper setup and teardown
"""

import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def run_tests(test_path: str = "tests/e2e", verbose: bool = True, markers: list = None):
    """Run E2E tests"""
    cmd = ["pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])
    
    logger.info(f"Running tests: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode == 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run E2E tests")
    parser.add_argument("--category", choices=[
        "license", "auth", "user", "pattern", "journey", 
        "integration", "error", "performance", "all"
    ], default="all", help="Test category to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel")
    
    args = parser.parse_args()
    
    markers = None
    if args.category != "all":
        markers = [args.category]
    
    cmd = ["pytest", "tests/e2e"]
    
    if args.verbose:
        cmd.append("-v")
    
    if markers:
        cmd.extend(["-m", " or ".join(markers)])
    
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
