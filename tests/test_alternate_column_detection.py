"""
Test alternate column detection for LED Matrix Studio patterns.

Tests that patterns exported with "Alternate (Down/Up)" and "Alternate (Up/Down)"
settings are correctly detected as Column-serpentine wiring.
"""

import pytest
from pathlib import Path

from parsers.parser_registry import parse_pattern_file
from core.file_format_detector import detect_file_format


# Test patterns directory
PATTERNS_DIR = Path("patterns/12x6 patterns")


@pytest.mark.skipif(not PATTERNS_DIR.exists(), reason="Patterns directory not found")
def test_alternate_column_down_up_detection():
    """Test that 'columns down up' pattern is detected as Column-serpentine."""
    pattern_path = PATTERNS_DIR / "12.6 columns down up.bin"
    if not pattern_path.exists():
        pytest.skip(f"Test pattern not found: {pattern_path}")
    
    pattern = parse_pattern_file(str(pattern_path))
    wiring, corner = detect_file_format(pattern)
    
    assert wiring == "Column-serpentine", (
        f"Expected Column-serpentine, got {wiring}. "
        f"Pattern: {pattern_path.name}, "
        f"Dimensions: {pattern.metadata.width}×{pattern.metadata.height}"
    )
    assert corner in ("LT", "LB", "RT", "RB"), f"Invalid corner: {corner}"


@pytest.mark.skipif(not PATTERNS_DIR.exists(), reason="Patterns directory not found")
def test_alternate_column_up_down_detection():
    """Test that 'columns up down' pattern is detected as Column-serpentine."""
    pattern_path = PATTERNS_DIR / "12.6 columns up down.dat..dat"
    if not pattern_path.exists():
        pytest.skip(f"Test pattern not found: {pattern_path}")
    
    pattern = parse_pattern_file(str(pattern_path))
    wiring, corner = detect_file_format(pattern)
    
    assert wiring == "Column-serpentine", (
        f"Expected Column-serpentine, got {wiring}. "
        f"Pattern: {pattern_path.name}, "
        f"Dimensions: {pattern.metadata.width}×{pattern.metadata.height}"
    )
    assert corner in ("LT", "LB", "RT", "RB"), f"Invalid corner: {corner}"


@pytest.mark.skipif(not PATTERNS_DIR.exists(), reason="Patterns directory not found")
def test_row_major_pattern_not_detected_as_column():
    """Test that row-major patterns are not incorrectly detected as column-serpentine."""
    pattern_path = PATTERNS_DIR / "test_row_major_12x6.bin"
    if not pattern_path.exists():
        pytest.skip(f"Test pattern not found: {pattern_path}")
    
    pattern = parse_pattern_file(str(pattern_path))
    wiring, corner = detect_file_format(pattern)
    
    # Should be row-based, not column-based
    assert wiring in ("Row-major", "Serpentine"), (
        f"Expected row-based wiring (Row-major or Serpentine), got {wiring}. "
        f"Pattern: {pattern_path.name}"
    )
    assert corner in ("LT", "LB", "RT", "RB"), f"Invalid corner: {corner}"


@pytest.mark.skipif(not PATTERNS_DIR.exists(), reason="Patterns directory not found")
def test_row_serpentine_pattern_detection():
    """Test that row serpentine patterns are correctly detected."""
    pattern_path = PATTERNS_DIR / "12.6 rows left right bin.bin"
    if not pattern_path.exists():
        pytest.skip(f"Test pattern not found: {pattern_path}")
    
    pattern = parse_pattern_file(str(pattern_path))
    wiring, corner = detect_file_format(pattern)
    
    # Should be row-based serpentine
    assert wiring in ("Row-major", "Serpentine"), (
        f"Expected row-based wiring, got {wiring}. "
        f"Pattern: {pattern_path.name}"
    )
    assert corner in ("LT", "LB", "RT", "RB"), f"Invalid corner: {corner}"


def test_detection_handles_missing_patterns_gracefully():
    """Test that detection returns defaults for invalid patterns."""
    from core.pattern import Pattern, Frame, PatternMetadata
    
    # Empty pattern
    empty_pattern = Pattern(
        name="Empty",
        metadata=PatternMetadata(width=12, height=6),
        frames=[]
    )
    wiring, corner = detect_file_format(empty_pattern)
    assert wiring == "Row-major"
    assert corner == "LT"
    
    # Pattern with wrong pixel count (manually tamper after validation)
    wrong_pattern = Pattern(
        name="Wrong",
        metadata=PatternMetadata(width=12, height=6),
        frames=[Frame(pixels=[(0, 0, 0)] * 72, duration_ms=20)]
    )
    wrong_pattern.frames[0].pixels = [(0, 0, 0)] * 10  # Force mismatch
    wiring, corner = detect_file_format(wrong_pattern)
    assert wiring == "Row-major"
    assert corner == "LT"

