#!/usr/bin/env python3
"""
Verify Version Consistency Script

Checks that all version strings in the codebase match the expected version.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Expected version
EXPECTED_VERSION = "3.0.0"

# Directories to check
CHECK_DIRS = [
    "apps/upload-bridge",
]

# File patterns to check
INCLUDE_PATTERNS = [
    "*.py",
    "*.md",
    "*.txt",
    "*.spec",
    "*.iss",
    "*.wxs",
    "*.yml",
    "*.yaml",
]

# Patterns to find version strings
VERSION_PATTERNS = [
    r'version\s*[:=]\s*["\'](\d+\.\d+\.\d+)["\']',  # version = "3.0.0"
    r'Version\s*[:=]\s*["\'](\d+\.\d+\.\d+)["\']',  # Version = "3.0.0"
    r'VERSION\s*[:=]\s*["\'](\d+\.\d+\.\d+)["\']',  # VERSION = "3.0.0"
    r'__version__\s*=\s*["\'](\d+\.\d+\.\d+)["\']',  # __version__ = "3.0.0"
    r'AppVersion\s*=\s*["\'](\d+\.\d+\.\d+)["\']',  # AppVersion = "3.0.0"
    r'#define AppVersion "(\d+\.\d+\.\d+)"',  # #define AppVersion "3.0.0"
    r'Version="(\d+\.\d+\.\d+)"',  # Version="3.0.0" (XML)
    r'version\s+"(\d+\.\d+\.\d+)"',  # version "3.0.0"
]

# Patterns to exclude (documentation, examples, test data)
EXCLUDE_PATTERNS = [
    r'.*\.pyc$',
    r'.*__pycache__.*',
    r'.*\.git.*',
    r'.*test.*data.*',
    r'.*example.*',
]


def find_version_strings(file_path: Path) -> List[Tuple[int, str]]:
    """Find all version strings in a file."""
    versions = []
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern in VERSION_PATTERNS:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    version = match.group(1)
                    versions.append((line_num, version))
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    return versions


def should_check_file(file_path: Path) -> bool:
    """Check if file should be checked."""
    # Check exclude patterns
    file_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if re.match(pattern, file_str, re.IGNORECASE):
            return False
    
    # Check include patterns
    for pattern in INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True
    
    return False


def verify_version_consistency(root_dir: Path) -> Tuple[bool, List[str]]:
    """Verify version consistency across codebase."""
    issues = []
    total_files = 0
    files_with_versions = 0
    
    root_path = Path(root_dir)
    if not root_path.exists():
        return False, [f"Root directory not found: {root_dir}"]
    
    # Walk through all files
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        
        if not should_check_file(file_path):
            continue
        
        total_files += 1
        versions = find_version_strings(file_path)
        
        if versions:
            files_with_versions += 1
            for line_num, version in versions:
                if version != EXPECTED_VERSION:
                    rel_path = file_path.relative_to(root_path)
                    issues.append(f"{rel_path}:{line_num}: Found version '{version}', expected '{EXPECTED_VERSION}'")
    
    return len(issues) == 0, issues


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        root_dir = Path(sys.argv[1])
    else:
        # Default to project root
        script_dir = Path(__file__).resolve().parent
        root_dir = script_dir.parent.parent.parent / "apps" / "upload-bridge"
    
    print(f"Verifying version consistency (expecting {EXPECTED_VERSION})...")
    print(f"Checking directory: {root_dir}\n")
    
    is_consistent, issues = verify_version_consistency(root_dir)
    
    if is_consistent:
        print(f"✅ All version strings match {EXPECTED_VERSION}")
        return 0
    else:
        print(f"❌ Found {len(issues)} version inconsistency(ies):\n")
        for issue in issues:
            print(f"  {issue}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

