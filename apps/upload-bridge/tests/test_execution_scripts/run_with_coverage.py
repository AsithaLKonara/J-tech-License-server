"""
Test Execution with Coverage Report
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run tests with coverage reporting."""
    print("="*70)
    print("Upload Bridge - Test Coverage Report")
    print("="*70)
    
    # Run tests with coverage
    cmd = [
        'python', '-m', 'pytest',
        'tests/unit/',
        'tests/integration/',
        '--cov=core',
        '--cov=ui',
        '--cov=domain',
        '--cov-report=html',
        '--cov-report=term',
        '--cov-report=json',
        '-v'
    ]
    
    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        print("\n✅ Coverage report generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - JSON: coverage.json")
        print("  - Terminal: See above")
    else:
        print("\n⚠️  Tests failed. Check output above.")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

