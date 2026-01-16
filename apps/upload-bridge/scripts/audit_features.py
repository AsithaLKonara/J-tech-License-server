#!/usr/bin/env python3
"""
Feature Implementation Audit Script
Verifies that features listed in FEATURE_INVENTORY.md have implementation files
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

def parse_feature_inventory():
    """Parse FEATURE_INVENTORY.md and extract features"""
    inventory_path = Path("docs/FEATURE_INVENTORY.md")
    features = []
    
    with open(inventory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse table rows
    # Format: | 1.1 | Feature Name | ✅ | `file.py` | Notes |
    pattern = r'^\|\s*(\d+\.\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|'
    
    for line in content.split('\n'):
        match = re.match(pattern, line)
        if match:
            feature_id, feature_name, status, impl_file, notes = match.groups()
            features.append({
                'id': feature_id.strip(),
                'name': feature_name.strip(),
                'status': status.strip(),
                'file': impl_file.strip(),
                'notes': notes.strip()
            })
    
    return features

def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """Check if implementation file exists"""
    path = Path(file_path)
    if path.exists():
        return True, "Exists"
    else:
        # Check if it's a directory reference
        if '/' in file_path or '\\' in file_path:
            parts = file_path.replace('\\', '/').split('/')
            # Try to find the file in the codebase
            for part in parts:
                if part.endswith('.py'):
                    # Search for the file
                    found = list(Path('.').rglob(part))
                    if found:
                        return True, f"Found at {found[0]}"
        return False, "Not found"

def main():
    print("=" * 80)
    print("Feature Implementation Audit")
    print("=" * 80)
    
    features = parse_feature_inventory()
    print(f"\n📊 Total Features Found: {len(features)}")
    
    # Categorize by status
    status_counts = {}
    file_exists = 0
    file_missing = 0
    
    results = []
    
    for feature in features:
        status = feature['status']
        status_counts[status] = status_counts.get(status, 0) + 1
        
        file_path = feature['file']
        exists, reason = check_file_exists(file_path)
        
        if exists:
            file_exists += 1
        else:
            file_missing += 1
        
        results.append({
            'feature': feature,
            'file_exists': exists,
            'reason': reason
        })
    
    print(f"\n📈 Status Breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    print(f"\n📁 File Verification:")
    print(f"  ✅ Files exist: {file_exists}")
    print(f"  ❌ Files missing: {file_missing}")
    
    # Show missing files
    if file_missing > 0:
        print(f"\n⚠️  Missing Implementation Files:")
        for result in results:
            if not result['file_exists']:
                feature = result['feature']
                print(f"    {feature['id']}: {feature['name']}")
                print(f"      File: {feature['file']}")
                print(f"      Status: {feature['status']}")
    
    # Show features with ✅ but missing files
    print(f"\n⚠️  Features Marked ✅ but File Missing:")
    count = 0
    for result in results:
        if result['feature']['status'] == '✅' and not result['file_exists']:
            feature = result['feature']
            print(f"    {feature['id']}: {feature['name']} - {feature['file']}")
            count += 1
    if count == 0:
        print("    None")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

