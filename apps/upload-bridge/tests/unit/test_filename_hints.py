"""Tests for filename hint extraction"""
import pytest
from core.filename_hints import extract_wiring_hints


def test_extract_alternate_up_down():
    """Test that 'alternate up down' extracts column-serpentine hint"""
    wiring, corner, confidence = extract_wiring_hints("alternate up down 33 frames.bin")
    assert wiring == "Column-serpentine"
    assert confidence >= 0.7
    # Corner may or may not be detected based on pattern


def test_extract_alternate_down_up():
    """Test that 'alternate down up' extracts column-serpentine hint"""
    wiring, corner, confidence = extract_wiring_hints("alternate down up 33 frames.bin")
    assert wiring == "Column-serpentine"
    assert confidence >= 0.7


def test_extract_explicit_wiring():
    """Test that explicit wiring mode keywords are detected"""
    wiring, corner, confidence = extract_wiring_hints("pattern_column-serpentine_left-top.bin")
    assert wiring == "Column-serpentine"
    assert corner == "LT"
    assert confidence >= 0.9


def test_extract_row_serpentine():
    """Test that row serpentine is detected"""
    wiring, corner, confidence = extract_wiring_hints("pattern_serpentine_right-bottom.bin")
    assert wiring == "Serpentine"
    assert corner == "RB"
    assert confidence >= 0.9


def test_extract_corner_hints():
    """Test that corner hints are extracted correctly"""
    test_cases = [
        ("left_top_pattern.bin", "LT"),
        ("right_bottom_pattern.bin", "RB"),
        ("bottom_left_pattern.bin", "LB"),
        ("top_right_pattern.bin", "RT"),
    ]
    for filename, expected_corner in test_cases:
        _, corner, confidence = extract_wiring_hints(filename)
        assert corner == expected_corner
        assert confidence >= 0.6


def test_no_hints():
    """Test that files without hints return None"""
    wiring, corner, confidence = extract_wiring_hints("pattern.bin")
    assert wiring is None
    assert corner is None
    assert confidence == 0.0


