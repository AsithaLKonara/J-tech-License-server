#!/usr/bin/env python3
"""
Chip Support Audit Script
Counts chips in database, profiles, and uploaders
"""

import yaml
import json
from pathlib import Path
from collections import defaultdict

def count_chips_in_database():
    """Count chips in chip_database.yaml"""
    db_path = Path("config/chip_database.yaml")
    with open(db_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    chips = data.get('chips', {})
    return chips

def count_profile_json():
    """Count profile JSON files"""
    profiles_dir = Path("uploaders/profiles")
    profiles = {}
    for json_file in profiles_dir.glob("*.json"):
        if json_file.name == "template.json":
            continue
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chip_id = data.get('chip_id', json_file.stem)
            profiles[chip_id] = json_file.name
    return profiles

def count_uploader_files():
    """Count uploader Python files"""
    uploaders_dir = Path("uploaders")
    uploaders = {}
    for py_file in uploaders_dir.glob("*_uploader.py"):
        # Extract chip name from filename
        name = py_file.stem.replace('_uploader', '')
        uploaders[name] = py_file.name
    return uploaders

def main():
    print("=" * 60)
    print("Chip Support Audit")
    print("=" * 60)
    
    # Count chips in database
    db_chips = count_chips_in_database()
    print(f"\n📊 Database Chips: {len(db_chips)}")
    print("\nChips by family:")
    families = defaultdict(list)
    for chip_id, spec in db_chips.items():
        family = spec.get('family', 'unknown')
        families[family].append(chip_id)
    
    for family, chips in sorted(families.items()):
        print(f"  {family}: {len(chips)} chips")
        for chip_id in sorted(chips):
            uploader = db_chips[chip_id].get('uploader', 'N/A')
            print(f"    - {chip_id} (uploader: {uploader})")
    
    # Count profile JSONs
    profiles = count_profile_json()
    print(f"\n📄 Profile JSONs: {len(profiles)}")
    for chip_id, filename in sorted(profiles.items()):
        print(f"  - {chip_id} ({filename})")
    
    # Count uploader files
    uploaders = count_uploader_files()
    print(f"\n🔧 Uploader Files: {len(uploaders)}")
    for name, filename in sorted(uploaders.items()):
        print(f"  - {name} ({filename})")
    
    # Analysis
    print("\n" + "=" * 60)
    print("Analysis")
    print("=" * 60)
    
    # Chips in database but no profile
    db_chip_ids = set(db_chips.keys())
    profile_chip_ids = set(profiles.keys())
    missing_profiles = db_chip_ids - profile_chip_ids
    
    print(f"\n⚠️  Chips in database without profile JSON: {len(missing_profiles)}")
    if missing_profiles:
        for chip_id in sorted(missing_profiles):
            print(f"    - {chip_id}")
    
    # Profiles that don't match database
    extra_profiles = profile_chip_ids - db_chip_ids
    print(f"\n⚠️  Profile JSONs not in database: {len(extra_profiles)}")
    if extra_profiles:
        for chip_id in sorted(extra_profiles):
            print(f"    - {chip_id}")
    
    # Check esp32s.json chip_id
    esp32s_profile = Path("uploaders/profiles/esp32s.json")
    if esp32s_profile.exists():
        with open(esp32s_profile, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chip_id = data.get('chip_id')
            if chip_id != 'esp32s2':
                print(f"\n⚠️  esp32s.json has chip_id='{chip_id}' but should be 'esp32s2'")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

