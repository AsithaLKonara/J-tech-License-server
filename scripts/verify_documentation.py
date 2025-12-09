#!/usr/bin/env python3
"""
Documentation Verification Script

Verifies that all documentation files are up to date, cross-references work,
and code examples are valid.

Usage:
    python scripts/verify_documentation.py
"""

import sys
import re
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def find_markdown_files(directory: Path) -> List[Path]:
    """Find all markdown files in directory."""
    return list(directory.rglob("*.md"))


def check_cross_references(file_path: Path) -> List[Tuple[str, str]]:
    """Check cross-references in markdown file."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all markdown links [text](path)
    link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = re.findall(link_pattern, content)
    
    for text, link in links:
        # Skip external links
        if link.startswith('http://') or link.startswith('https://'):
            continue
        
        # Skip anchor links
        if link.startswith('#'):
            continue
        
        # Resolve relative paths
        if link.startswith('/'):
            target = project_root / link[1:]
        else:
            target = file_path.parent / link
        
        # Check if file exists
        if not target.exists():
            issues.append((f"Broken link: [{text}]({link})", str(file_path)))
    
    return issues


def check_code_blocks(file_path: Path) -> List[Tuple[str, str]]:
    """Check code blocks for syntax issues."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find code blocks
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
    
    for lang, code in code_blocks:
        # Basic validation for Python code
        if lang == 'python' or (not lang and 'python' in code.lower()):
            # Check for common syntax issues
            if code.count('(') != code.count(')'):
                issues.append(("Unbalanced parentheses in code block", str(file_path)))
            if code.count('[') != code.count(']'):
                issues.append(("Unbalanced brackets in code block", str(file_path)))
            if code.count('{') != code.count('}'):
                issues.append(("Unbalanced braces in code block", str(file_path)))
    
    return issues


def check_file_structure(file_path: Path) -> List[Tuple[str, str]]:
    """Check basic file structure."""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check for title (first line should be # Title)
    if lines and not lines[0].startswith('#'):
        issues.append(("Missing title (first line should start with #)", str(file_path)))
    
    # Check for reasonable length
    if len(lines) < 5:
        issues.append(("File seems too short", str(file_path)))
    
    return issues


def verify_documentation():
    """Main verification function."""
    docs_dir = project_root / "docs"
    
    if not docs_dir.exists():
        print(f"Error: docs directory not found: {docs_dir}")
        return False
    
    print("=" * 70)
    print("Documentation Verification")
    print("=" * 70)
    print()
    
    md_files = find_markdown_files(docs_dir)
    print(f"Found {len(md_files)} markdown files")
    print()
    
    all_issues = []
    
    for file_path in md_files:
        print(f"Checking: {file_path.relative_to(project_root)}")
        
        # Check cross-references
        ref_issues = check_cross_references(file_path)
        all_issues.extend(ref_issues)
        
        # Check code blocks
        code_issues = check_code_blocks(file_path)
        all_issues.extend(code_issues)
        
        # Check file structure
        structure_issues = check_file_structure(file_path)
        all_issues.extend(structure_issues)
    
    print()
    print("=" * 70)
    print("Verification Results")
    print("=" * 70)
    print()
    
    if all_issues:
        print(f"Found {len(all_issues)} issues:")
        print()
        for issue, file_path in all_issues:
            print(f"  - {issue}")
            print(f"    File: {file_path}")
            print()
        return False
    else:
        print("✅ All checks passed!")
        return True


def main():
    """Main entry point."""
    success = verify_documentation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

