"""
File Format Detector - Auto-detect wiring mode and data-in corner from pattern data

This module analyzes pattern pixel data to determine the most likely wiring format.
It uses heuristics based on pixel patterns and corner/edge analysis.
"""

from typing import Tuple, Optional, List
from .pattern import Pattern
import logging

logger = logging.getLogger(__name__)


def detect_file_format(pattern: Pattern) -> Tuple[str, str]:
    """
    Auto-detect the most likely file format (wiring mode + data-in corner).
    
    Returns:
        Tuple of (wiring_mode, data_in_corner)
        e.g., ("Serpentine", "LT")
    
    Strategy:
    1. Analyze corner pixels to identify data-in corner
    2. Analyze row/column patterns to identify wiring mode
    3. Return best match with confidence score
    """
    if not pattern or not pattern.frames or len(pattern.frames) == 0:
        return ("Row-major", "LT")  # Default fallback
    
    width = pattern.metadata.width
    height = pattern.metadata.height
    
    if height <= 1:
        # Strip pattern - no wiring mode matters
        return ("Row-major", "LT")
    
    if width * height != len(pattern.frames[0].pixels):
        logger.warning(f"Pixel count mismatch: expected {width * height}, got {len(pattern.frames[0].pixels)}")
        return ("Row-major", "LT")
    
    # Use first frame for analysis
    pixels = list(pattern.frames[0].pixels)
    
    # Step 1: Detect data-in corner by analyzing corner pixels
    # We look for patterns that suggest where data starts
    corner_scores = {
        "LT": 0,  # Top-left
        "LB": 0,  # Bottom-left
        "RT": 0,  # Top-right
        "RB": 0,  # Bottom-right
    }
    
    # Analyze first few pixels to guess starting corner
    # If first pixel is at a corner, that's likely the data-in corner
    first_pixel = pixels[0]
    
    # Check if first pixel matches any corner
    top_left = pixels[0]  # Design order (0,0)
    top_right = pixels[width - 1]  # Design order (width-1, 0)
    bottom_left = pixels[(height - 1) * width]  # Design order (0, height-1)
    bottom_right = pixels[height * width - 1]  # Design order (width-1, height-1)
    
    # If first pixel matches a corner, that corner is likely data-in
    if first_pixel == top_left:
        corner_scores["LT"] += 10
    if first_pixel == top_right:
        corner_scores["RT"] += 10
    if first_pixel == bottom_left:
        corner_scores["LB"] += 10
    if first_pixel == bottom_right:
        corner_scores["RB"] += 10
    
    # Step 2: Detect wiring mode by analyzing row/column patterns
    # Check if rows alternate direction (Serpentine)
    # Check if columns alternate direction (Column-serpentine)
    # Check if it's sequential (Row-major or Column-major)
    
    wiring_scores = {
        "Row-major": 0,
        "Serpentine": 0,
        "Column-major": 0,
        "Column-serpentine": 0,
    }
    
    # Analyze first few rows to detect serpentine pattern
    # In serpentine, odd rows should be reversed
    # We check if row 1 looks like reversed row 0
    
    # Extract first two rows
    row0 = pixels[0:width]
    row1 = pixels[width:width * 2] if height > 1 else []
    
    if len(row1) == width:
        # Check if row1 is reversed row0 (serpentine indicator)
        row0_reversed = list(reversed(row0))
        similarity = sum(1 for i in range(width) if row0_reversed[i] == row1[i])
        if similarity > width * 0.7:  # 70% match suggests serpentine
            wiring_scores["Serpentine"] += 10
        
        # Check if row1 is same as row0 (row-major indicator)
        similarity = sum(1 for i in range(width) if row0[i] == row1[i])
        if similarity > width * 0.7:
            wiring_scores["Row-major"] += 5
    
    # Analyze first two columns for column-based patterns
    col0 = [pixels[i * width] for i in range(height)]
    col1 = [pixels[i * width + 1] for i in range(height)] if width > 1 else []
    
    if len(col1) == height:
        # Check if col1 is reversed col0 (column-serpentine indicator)
        col0_reversed = list(reversed(col0))
        similarity = sum(1 for i in range(height) if col0_reversed[i] == col1[i])
        if similarity > height * 0.7:
            wiring_scores["Column-serpentine"] += 10
        
        # Check if col1 is same as col0 (column-major indicator)
        similarity = sum(1 for i in range(height) if col0[i] == col1[i])
        if similarity > height * 0.7:
            wiring_scores["Column-major"] += 5
    
    # Default: Row-major is most common
    wiring_scores["Row-major"] += 3
    
    # Find best matches
    best_wiring = max(wiring_scores.items(), key=lambda x: x[1])[0]
    best_corner = max(corner_scores.items(), key=lambda x: x[1])[0]
    
    # If no strong signal, default to common LED Matrix Studio format
    if wiring_scores[best_wiring] < 5:
        best_wiring = "Serpentine"  # LED Matrix Studio default
    
    if corner_scores[best_corner] < 5:
        best_corner = "LT"  # Left Top is most common
    
    logger.info(f"🔍 Auto-detected file format: {best_wiring} {best_corner}")
    logger.info(f"   Wiring scores: {wiring_scores}")
    logger.info(f"   Corner scores: {corner_scores}")
    
    return (best_wiring, best_corner)


def detect_file_format_with_confidence(pattern: Pattern) -> Tuple[str, str, float]:
    """
    Auto-detect file format with confidence score (0.0-1.0).
    
    Returns:
        Tuple of (wiring_mode, data_in_corner, confidence)
    """
    wiring, corner = detect_file_format(pattern)
    
    # Calculate confidence based on pattern analysis
    # For now, return medium confidence (0.6) since detection is heuristic
    # User should verify the detection
    confidence = 0.6
    
    return (wiring, corner, confidence)

