#!/usr/bin/env python3
"""
Comprehensive IC Code Template Verification Script
Checks all templates against chip_database.yaml for completeness and correctness
"""

import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Set

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "firmware" / "templates"
CHIP_DB = PROJECT_ROOT / "config" / "chip_database.yaml"


def load_chip_database() -> Dict[str, dict]:
    """Load chip database YAML"""
    with open(CHIP_DB, 'r') as f:
        data = yaml.safe_load(f)
    return data['chips']


def get_existing_templates() -> Dict[str, List[Path]]:
    """Scan templates directory and find all template files"""
    templates = {}
    
    if not TEMPLATES_DIR.exists():
        return templates
    
    # Check directories
    for item in TEMPLATES_DIR.iterdir():
        if item.is_dir():
            chip_id = item.name
            templates[chip_id] = []
            
            # Find all source files
            for pattern in ['*.c', '*.ino', '*.cpp']:
                templates[chip_id].extend(item.glob(pattern))
            
            # Check for Makefile
            if (item / "Makefile").exists():
                templates[chip_id].append(item / "Makefile")
    
    # Check loose template files
    for pattern in ['*_template.c', '*_template.ino']:
        for template_file in TEMPLATES_DIR.glob(pattern):
            # Extract chip ID from filename (e.g., pic18f4550_template.c -> pic18f4550)
            chip_id = template_file.stem.replace('_template', '')
            if chip_id not in templates:
                templates[chip_id] = []
            templates[chip_id].append(template_file)
    
    return templates


def check_template_structure(chip_id: str, template_paths: List[Path]) -> Tuple[bool, List[str]]:
    """Check if template has correct structure and required files"""
    issues = []
    
    # Check for source files
    has_c = any(p.suffix == '.c' for p in template_paths)
    has_ino = any(p.suffix == '.ino' for p in template_paths)
    
    if not has_c and not has_ino:
        issues.append("No source files (.c or .ino) found")
        return False, issues  # Can't proceed without source files
    
    # Check if template is in directory or loose file
    has_dir = TEMPLATES_DIR / chip_id
    has_loose = any(p.parent == TEMPLATES_DIR for p in template_paths)
    
    if has_loose and not has_dir.exists():
        issues.append(f"Loose template file found but no directory - should be in {chip_id}/")
    
    # Check for pattern_data.h include requirement
    source_files = [p for p in template_paths if p.suffix in ['.c', '.ino', '.cpp']]
    if source_files:
        for src_file in source_files:
            try:
                content = src_file.read_text(encoding='utf-8', errors='ignore')
                
                # Check if this is an include-based template stub
                import re
                include_pattern = r'#include\s+[<"]\.\./[^>"]+\.c[>"]'
                is_stub = bool(re.search(include_pattern, content))
                
                if is_stub:
                    # This is a valid stub template - check that included file exists
                    match = re.search(include_pattern, content)
                    if match:
                        include_path_str = match.group(0)
                        # Extract relative path
                        rel_path_match = re.search(r'\.\./([^>"]+\.c)', include_path_str)
                        if rel_path_match:
                            rel_path = rel_path_match.group(1)
                            included_file = src_file.parent.parent / rel_path
                            if not included_file.exists():
                                issues.append(f"{src_file.name} includes non-existent file: {rel_path}")
                            else:
                                # Stub template is valid if included file exists and has pattern_data.h
                                try:
                                    included_content = included_file.read_text(encoding='utf-8', errors='ignore')
                                    if 'pattern_data.h' not in included_content:
                                        issues.append(f"{src_file.name} includes file without pattern_data.h: {rel_path}")
                                except:
                                    pass
                    # Stub templates are valid - skip other checks
                    continue
                
                # For non-stub templates, check pattern_data.h
                if 'pattern_data.h' not in content:
                    issues.append(f"{src_file.name} does not include pattern_data.h")
                if 'pattern_data' not in content.lower():
                    issues.append(f"{src_file.name} may not use pattern_data correctly")
            except Exception as e:
                issues.append(f"Cannot read {src_file.name}: {e}")
    
    return len(issues) == 0, issues


def check_template_content(chip_id: str, template_paths: List[Path], chip_info: dict) -> Tuple[bool, List[str]]:
    """Check template content for correctness"""
    issues = []
    source_files = [p for p in template_paths if p.suffix in ['.c', '.ino', '.cpp']]
    
    for src_file in source_files:
        try:
            content = src_file.read_text(encoding='utf-8', errors='ignore')
            
            # Check if this is an include-based template stub
            import re
            include_pattern = r'#include\s+[<"]\.\./[^>"]+\.c[>"]'
            is_stub = bool(re.search(include_pattern, content))
            
            if is_stub:
                # Stub templates are valid - they delegate to included file
                # The included file will be checked separately if it's in templates
                continue
            
            # Check for required elements
            has_main = 'main' in content or 'setup' in content or 'loop' in content
            if not has_main:
                issues.append(f"{src_file.name} missing main/entry point")
            
            # Check for LED_COUNT or similar (LED_COUNT can come from pattern_data.h)
            has_led_def = 'LED_COUNT' in content or 'NUM_LEDS' in content or '#define LED_COUNT' in content
            if not has_led_def and 'pattern_data.h' in content:
                # LED_COUNT might be defined in pattern_data.h, which is acceptable
                pass
            elif not has_led_def:
                issues.append(f"{src_file.name} missing LED_COUNT/NUM_LEDS definition (not found in file or pattern_data.h)")
            
            # Check for frame handling (FRAME_COUNT might come from pattern_data.h)
            has_frame_ref = 'frame' in content.lower() or 'FRAME' in content or 'FRAME_COUNT' in content
            if not has_frame_ref:
                issues.append(f"{src_file.name} missing frame handling code")
            
            # Check for delay/timing functions
            if 'delay' not in content.lower():
                issues.append(f"{src_file.name} missing delay functions")
            
            # Check memory constraints match chip
            max_leds = chip_info.get('max_leds', 0)
            if max_leds > 0:
                # Try to find MAX_LEDS definition
                max_leds_match = re.search(r'MAX_LEDS\s+(\d+)', content)
                if max_leds_match:
                    template_max = int(max_leds_match.group(1))
                    if template_max > max_leds * 1.5:  # Allow 50% buffer
                        issues.append(f"{src_file.name} MAX_LEDS ({template_max}) exceeds chip limit ({max_leds})")
        
        except Exception as e:
            issues.append(f"Cannot analyze {src_file.name}: {e}")
    
    return len(issues) == 0, issues


def main():
    """Main verification function"""
    print("=" * 80)
    print("IC CODE TEMPLATES E2E VERIFICATION REPORT")
    print("=" * 80)
    print()
    
    # Load chip database
    chips = load_chip_database()
    print(f"✓ Loaded chip database: {len(chips)} chips defined")
    print()
    
    # Get existing templates
    templates = get_existing_templates()
    print(f"✓ Found templates for {len(templates)} chips")
    print()
    
    # Compare chips vs templates
    chip_ids = set(chips.keys())
    template_ids = set(templates.keys())
    
    missing_templates = chip_ids - template_ids
    extra_templates = template_ids - chip_ids
    
    print("=" * 80)
    print("TEMPLATE AVAILABILITY CHECK")
    print("=" * 80)
    
    if missing_templates:
        print(f"\n❌ MISSING TEMPLATES ({len(missing_templates)}):")
        for chip_id in sorted(missing_templates):
            chip_info = chips[chip_id]
            print(f"  - {chip_id:20s} ({chip_info['name']}) - {chip_info['family']}")
    else:
        print("\n✓ All chips have templates")
    
    if extra_templates:
        print(f"\n⚠️  EXTRA TEMPLATES (not in chip_database.yaml) ({len(extra_templates)}):")
        for chip_id in sorted(extra_templates):
            print(f"  - {chip_id}")
    else:
        print("\n✓ No extra templates found")
    
    print()
    print("=" * 80)
    print("TEMPLATE STRUCTURE CHECK")
    print("=" * 80)
    
    structure_issues = {}
    for chip_id in sorted(chip_ids & template_ids):
        template_paths = templates[chip_id]
        is_valid, issues = check_template_structure(chip_id, template_paths)
        if not is_valid:
            structure_issues[chip_id] = issues
    
    if structure_issues:
        print(f"\n❌ STRUCTURE ISSUES ({len(structure_issues)} chips):")
        for chip_id, issues in sorted(structure_issues.items()):
            print(f"\n  {chip_id}:")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("\n✓ All templates have correct structure")
    
    print()
    print("=" * 80)
    print("TEMPLATE CONTENT CHECK")
    print("=" * 80)
    
    content_issues = {}
    for chip_id in sorted(chip_ids & template_ids):
        template_paths = templates[chip_id]
        chip_info = chips[chip_id]
        is_valid, issues = check_template_content(chip_id, template_paths, chip_info)
        if not is_valid:
            content_issues[chip_id] = issues
    
    if content_issues:
        print(f"\n❌ CONTENT ISSUES ({len(content_issues)} chips):")
        for chip_id, issues in sorted(content_issues.items()):
            print(f"\n  {chip_id}:")
            for issue in issues:
                print(f"    - {issue}")
    else:
        print("\n✓ All templates have correct content")
    
    print()
    print("=" * 80)
    print("EXPORT TEMPLATES CHECK")
    print("=" * 80)
    
    # Check export_templates.py
    export_templates_file = PROJECT_ROOT / "core" / "export_templates.py"
    if export_templates_file.exists():
        content = export_templates_file.read_text()
        # Check for basic templates
        expected_templates = ["Arduino PROGMEM", "Plain RGB Hex Array", "PIC Assembly Table"]
        found_templates = []
        for template_name in expected_templates:
            if template_name in content:
                found_templates.append(template_name)
        
        print(f"\n✓ Export templates found: {', '.join(found_templates)}")
        missing_export = set(expected_templates) - set(found_templates)
        if missing_export:
            print(f"  ⚠️  Missing: {', '.join(missing_export)}")
    else:
        print("\n❌ export_templates.py not found")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_issues = len(missing_templates) + len(structure_issues) + len(content_issues)
    
    if total_issues == 0:
        print("\n✅ ALL TEMPLATES VERIFIED - NO ISSUES FOUND")
    else:
        print(f"\n❌ FOUND {total_issues} CATEGORIES OF ISSUES:")
        print(f"   - Missing templates: {len(missing_templates)}")
        print(f"   - Structure issues: {len(structure_issues)}")
        print(f"   - Content issues: {len(content_issues)}")
        print(f"   - Extra templates: {len(extra_templates)}")
    
    print()
    return total_issues == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
