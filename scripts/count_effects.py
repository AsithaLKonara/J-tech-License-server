#!/usr/bin/env python3
"""Count effects in effects directory"""

from pathlib import Path

def count_effects():
    """Count effects in Res/effects directory"""
    effects_dir = Path("Res/effects")
    
    if not effects_dir.exists():
        print(f"Effects directory not found: {effects_dir}")
        return 0
    
    # Count effect files (SWF, JSON, YAML)
    supported_extensions = {".swf", ".json", ".yaml", ".yml"}
    count = 0
    
    for path in effects_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in supported_extensions:
            count += 1
    
    return count

if __name__ == "__main__":
    count = count_effects()
    print(f"Total effects found: {count}")

