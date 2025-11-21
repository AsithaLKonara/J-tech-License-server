"""
Filename Hints - Extract wiring/format hints from filenames

This module extracts detection hints from filenames to improve auto-detection accuracy.
For example, "alternate up down" suggests column-serpentine wiring.
"""

from typing import Optional, Tuple
import re


def extract_wiring_hints(filename: str) -> Tuple[Optional[str], Optional[str], float]:
    """
    Extract wiring mode and data-in corner hints from filename.
    
    Args:
        filename: Filename (with or without path/extension)
        
    Returns:
        Tuple of (wiring_mode_hint, data_in_corner_hint, confidence)
        confidence: 0.0-1.0, 0.9+ = strong hint from explicit keywords
        
    Examples:
        "alternate up down" -> ("Column-serpentine", None, 0.85)
        "alternate down up" -> ("Column-serpentine", None, 0.85)
        "serpentine left top" -> ("Serpentine", "LT", 0.9)
        "column-major right bottom" -> ("Column-major", "RB", 0.9)
    """
    # Normalize filename: remove path and extension, lowercase
    name = filename.lower()
    if '/' in name or '\\' in name:
        name = name.split('/')[-1].split('\\')[-1]
    if '.' in name:
        name = name.rsplit('.', 1)[0]
    
    wiring_hint = None
    corner_hint = None
    confidence = 0.0
    search_name = re.sub(r'[_\-]+', ' ', name)
    
    # Strong hints: explicit wiring mode keywords (high confidence)
    explicit_wiring_patterns = [
        (r'\brow[_\s-]?major\b', 'Row-major', 0.9),
        (r'\bcolumn[_\s-]?major\b', 'Column-major', 0.9),
        (r'\bcolumn[_\s-]?serpentine\b', 'Column-serpentine', 0.9),
        (r'\brow[_\s-]?serpentine\b', 'Serpentine', 0.9),
        (r'\bserpentine\b', 'Serpentine', 0.9),
    ]
    
    for pattern, mode, conf in explicit_wiring_patterns:
        if re.search(pattern, search_name):
            wiring_hint = mode
            confidence = max(confidence, conf)
            break
    
    # Medium hints: descriptive patterns (medium confidence)
    # "alternate up down" or "alternate down up" -> column-serpentine
    if not wiring_hint:
        if re.search(r'\balternate.*(?:up.*down|down.*up)\b', search_name):
            wiring_hint = 'Column-serpentine'
            confidence = 0.85
        elif re.search(r'\bzigzag\b', search_name) or re.search(r'\bsnake\b', search_name):
            # Could be row or column, but common in column patterns
            wiring_hint = 'Column-serpentine'
            confidence = 0.65
    
    # Corner hints: explicit corner keywords
    corner_patterns = [
        (r'\b(?:left|lt)[_\s-]?(?:top|upper)\b', 'LT', 0.9),
        (r'\b(?:left|lt)[_\s-]?(?:bottom|lower|down)\b', 'LB', 0.9),
        (r'\b(?:right|rt)[_\s-]?(?:top|upper)\b', 'RT', 0.9),
        (r'\b(?:right|rt)[_\s-]?(?:bottom|lower|down)\b', 'RB', 0.9),
        (r'\btop[_\s-]?(?:left|lt)\b', 'LT', 0.9),
        (r'\btop[_\s-]?(?:right|rt)\b', 'RT', 0.9),
        (r'\bbottom[_\s-]?(?:left|lt)\b', 'LB', 0.9),
        (r'\bbottom[_\s-]?(?:right|rt)\b', 'RB', 0.9),
    ]
    
    for pattern, corner, conf in corner_patterns:
        if re.search(pattern, search_name):
            corner_hint = corner
            confidence = max(confidence, conf)
            break
    
    # Weak hints: directional keywords (low confidence, but useful when combined)
    if not corner_hint:
        if 'left' in name and ('top' in name or 'upper' in name or 'up' in name):
            corner_hint = 'LT'
            confidence = max(confidence, 0.6)
        elif 'left' in name and ('bottom' in name or 'lower' in name or 'down' in name):
            corner_hint = 'LB'
            confidence = max(confidence, 0.6)
        elif 'right' in name and ('top' in name or 'upper' in name or 'up' in name):
            corner_hint = 'RT'
            confidence = max(confidence, 0.6)
        elif 'right' in name and ('bottom' in name or 'lower' in name or 'down' in name):
            corner_hint = 'RB'
            confidence = max(confidence, 0.6)
    
    # Directional hints for column-serpentine:
    # "up down" or "down up" in alternate context suggests column direction
    if wiring_hint == 'Column-serpentine' and not corner_hint:
        if re.search(r'\bup.*down\b', name) or re.search(r'\bdown.*up\b', name):
            # "up down" typically means top-to-bottom then bottom-to-top = LT or RT
            # "down up" typically means bottom-to-top then top-to-bottom = LB or RB
            if 'down up' in name or 'down-up' in name:
                # Starting from bottom suggests LB or RB
                # We can't determine without more context, but LB is common
                corner_hint = 'LB'
                confidence = max(confidence, 0.7)
            elif 'up down' in name or 'up-down' in name:
                # Starting from top suggests LT or RT
                # LT is common default
                corner_hint = 'LT'
                confidence = max(confidence, 0.7)
    
    return wiring_hint, corner_hint, confidence


