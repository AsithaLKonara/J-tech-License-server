#!/usr/bin/env python3
"""
Check Version Consistency Script

This script checks that version numbers are consistent across:
- setup.py / pyproject.toml
- Application metadata
- Documentation files

Usage:
    python scripts/tools/check_version_consistency.py
    python scripts/tools/check_version_consistency.py --fix  # Auto-fix inconsistencies
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

# Expected version (update this when releasing)
EXPECTED_VERSION = "3.0.0"

# Files to check for version
VERSION_FILES = [
    # Python package files
    ("apps/upload-bridge/setup.py", [
        (r'version\s*=\s*["\'](\d+\.\d+\.\d+)["\']', 'version = "{}"'),
    ]),
    # Config files
    ("apps/upload-bridge/core/config/config_manager.py", [
        (r"'app_version':\s*os\.getenv\('APP_VERSION',\s*['\"](\d+\.\d+\.\d+)['\"])", "'app_version': os.getenv('APP_VERSION', '{}')"),
        (r"'app_version':\s*['\"](\d+\.\d+\.\d+)['\"]", "'app_version': '{}'"),
    ]),
    # Documentation files (check for version references)
    ("README.md", [
        (r'v(\d+\.\d+\.\d+)', 'v{}'),  # v3.0.0
        (r'Version\s+(\d+\.\d+\.\d+)', 'Version {}'),  # Version 3.0.0
    ]),
]

# Documentation files to check (informational only, won't auto-fix)
DOC_FILES = [
    "docs/FINAL_STATUS_REPORT.md",
    "docs/RELEASE_NOTES.md",
    "docs/CHANGELOG.md",
    "docs/PACKAGE_README.md",
]


def find_version_in_file(file_path: Path, patterns: List[Tuple[str, str]]) -> List[Tuple[int, str, str]]:
    """
    Find version strings in a file.
    
    Returns:
        List of (line_number, found_version, pattern) tuples
    """
    if not file_path.exists():
        return []
    
    versions = []
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, _ in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    version = match.group(1)
                    versions.append((line_num, version, pattern))
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
    
    return versions


def fix_version_in_file(file_path: Path, patterns: List[Tuple[str, str]], dry_run: bool = False) -> bool:
    """
    Fix version strings in a file.
    
    Returns:
        True if file was modified
    """
    if not file_path.exists():
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original_content = content
        lines = content.split('\n')
        modified = False
        
        for line_num, line in enumerate(lines):
            for pattern, replacement_template in patterns:
                def replace_match(match):
                    nonlocal modified
                    found_version = match.group(1)
                    if found_version != EXPECTED_VERSION:
                        modified = True
                        return replacement_template.format(EXPECTED_VERSION)
                    return match.group(0)
                
                new_line = re.sub(pattern, replace_match, line, flags=re.IGNORECASE)
                if new_line != line:
                    lines[line_num] = new_line
        
        if modified and not dry_run:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
        elif modified:
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False


def check_version_consistency(fix: bool = False, dry_run: bool = False) -> Tuple[bool, List[str]]:
    """
    Check version consistency across all files.
    
    Returns:
        (is_consistent, list_of_issues)
    """
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    issues = []
    files_to_fix = []
    
    # Check version files
    for rel_path, patterns in VERSION_FILES:
        file_path = root_dir / rel_path
        if not file_path.exists():
            issues.append(f"File not found: {rel_path}")
            continue
        
        versions = find_version_in_file(file_path, patterns)
        for line_num, found_version, pattern in versions:
            if found_version != EXPECTED_VERSION:
                issue = f"{rel_path}:{line_num}: Found version '{found_version}', expected '{EXPECTED_VERSION}'"
                issues.append(issue)
                files_to_fix.append((file_path, patterns))
    
    # Check documentation files (informational)
    for rel_path in DOC_FILES:
        file_path = root_dir / rel_path
        if file_path.exists():
            # Simple check for version mentions
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            version_matches = re.findall(r'\b(\d+\.\d+\.\d+)\b', content)
            for version in set(version_matches):
                if version != EXPECTED_VERSION and version.count('.') == 2:
                    issues.append(f"{rel_path}: Mentions version '{version}' (informational)")
    
    # Fix if requested
    if fix and files_to_fix:
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Fixing version inconsistencies...")
        for file_path, patterns in files_to_fix:
            if fix_version_in_file(file_path, patterns, dry_run=dry_run):
                status = "Would fix" if dry_run else "Fixed"
                print(f"  {status}: {file_path.relative_to(root_dir)}")
        
        # Re-check after fixing
        if not dry_run:
            return check_version_consistency(fix=False, dry_run=False)
    
    return len(issues) == 0, issues


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Check version consistency across codebase")
    parser.add_argument('--fix', action='store_true', help='Auto-fix version inconsistencies')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    args = parser.parse_args()
    
    print(f"Checking version consistency (expecting {EXPECTED_VERSION})...")
    print()
    
    is_consistent, issues = check_version_consistency(fix=args.fix, dry_run=args.dry_run)
    
    if is_consistent:
        print(f"✅ All version strings match {EXPECTED_VERSION}")
        return 0
    else:
        print(f"❌ Found {len(issues)} version inconsistency(ies):\n")
        for issue in issues:
            print(f"  {issue}")
        
        if not args.fix:
            print("\n💡 Tip: Use --fix to automatically fix inconsistencies")
            print("💡 Tip: Use --dry-run to see what would be fixed")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
