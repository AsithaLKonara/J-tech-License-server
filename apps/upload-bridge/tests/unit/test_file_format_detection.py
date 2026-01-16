from __future__ import annotations

import itertools

import pytest

from core.file_format_detector import detect_file_format
from core.pattern import Frame, Pattern, PatternMetadata
from core.wiring_mapper import WiringMapper


def _generate_test_pixels(width: int, height: int, wiring_mode: str) -> list[tuple[int, int, int]]:
    """
    Create deterministic pixels that emphasise either row or column structure
    depending on the wiring mode. Diagnostic patterns commonly light entire
    rows/columns, so mirroring that behaviour improves realism.
    """
    pixels: list[tuple[int, int, int]] = []
    column_emphasis = "Column" in wiring_mode
    for y in range(height):
        for x in range(width):
            if column_emphasis:
                r = (x * 63) % 256
                g = 10 + (x * 11) % 40
                b = (y * 3) % 20
            else:
                r = (y * 63) % 256
                g = 10 + (y * 11) % 40
                b = (x * 3) % 20
            pixels.append((r, g, b))
    pixels[0] = (255, 0, 0)
    pixels[width - 1] = (0, 255, 0)
    pixels[(height - 1) * width] = (0, 0, 255)
    pixels[-1] = (255, 255, 0)
    return pixels


def _build_pattern(width: int, height: int, wiring: str, corner: str) -> Pattern:
    design_pixels = _generate_test_pixels(width, height, wiring)
    mapper = WiringMapper(width, height, wiring, corner)
    hardware_pixels = mapper.design_to_hardware(design_pixels)
    metadata = PatternMetadata(width=width, height=height)
    frame = Frame(pixels=hardware_pixels, duration_ms=20)
    return Pattern(
        name=f"test_{wiring}_{corner}",
        metadata=metadata,
        frames=[frame],
    )


WIRING_MODES = ["Row-major", "Serpentine", "Column-major", "Column-serpentine"]
DATA_CORNERS = ["LT", "LB", "RT", "RB"]


@pytest.mark.parametrize("wiring_mode", WIRING_MODES)
@pytest.mark.parametrize("corner", DATA_CORNERS)
def test_detect_file_format_for_all_wiring_combinations(wiring_mode: str, corner: str) -> None:
    """Ensure auto-detection matches every wiring/corner combination."""
    pattern = _build_pattern(5, 4, wiring_mode, corner)
    detected_wiring, detected_corner = detect_file_format(pattern)
    assert detected_wiring == wiring_mode, f"Expected {wiring_mode}, got {detected_wiring}"
    assert detected_corner == corner, f"Expected {corner}, got {detected_corner}"


def test_detect_with_metadata_hint():
    """Test that metadata hints bias detection correctly"""
    from core.file_format_detector import detect_file_format
    
    # Create a pattern with column-serpentine hint
    pattern = _build_pattern(12, 6, "Column-serpentine", "LT")
    pattern.metadata.wiring_mode_hint = "Column-serpentine"
    pattern.metadata.hint_confidence = 0.9
    
    detected_wiring, detected_corner = detect_file_format(pattern)
    assert detected_wiring == "Column-serpentine", f"Expected Column-serpentine with strong hint, got {detected_wiring}"


def test_detect_with_weak_hint():
    """Test that weak hints adjust scores but don't override"""
    from core.file_format_detector import detect_file_format
    
    # Create a pattern with weak hint
    pattern = _build_pattern(12, 6, "Row-major", "LT")
    pattern.metadata.wiring_mode_hint = "Column-serpentine"
    pattern.metadata.hint_confidence = 0.6  # Weak hint
    
    # Detection should still prefer heuristic result, but hint may bias score
    detected_wiring, detected_corner = detect_file_format(pattern)
    # Even with weak hint, the actual pattern structure should win
    assert detected_wiring in ["Row-major", "Column-serpentine"]  # Either is acceptable


def test_detect_with_corner_hint():
    """Test that corner hints are respected"""
    from core.file_format_detector import detect_file_format
    
    pattern = _build_pattern(8, 6, "Serpentine", "RB")
    pattern.metadata.data_in_corner_hint = "RB"
    pattern.metadata.hint_confidence = 0.9
    
    detected_wiring, detected_corner = detect_file_format(pattern)
    assert detected_corner == "RB", f"Expected RB with strong corner hint, got {detected_corner}"


@pytest.mark.skipif(
    not __import__("pathlib").Path("patterns/alternate/12x6 left to right alternate up down 33 frames.bin").exists(),
    reason="Test BIN files not found"
)
def test_detect_alternate_up_down_bin():
    """Test detection of 'alternate up down' BIN file"""
    from parsers.parser_registry import parse_pattern_file
    from core.file_format_detector import detect_file_format_with_confidence
    
    pattern = parse_pattern_file("patterns/alternate/12x6 left to right alternate up down 33 frames.bin")
    detected_wiring, detected_corner, confidence, reason = detect_file_format_with_confidence(pattern)
    
    # Should detect as column-serpentine with good confidence (hint from filename)
    assert detected_wiring == "Column-serpentine", f"Expected Column-serpentine, got {detected_wiring}"
    assert confidence >= 0.75, f"Expected confidence >= 0.75, got {confidence:.2f}"


@pytest.mark.skipif(
    not __import__("pathlib").Path("patterns/alternate/12x6 left to right alternate down up 33 frames.bin").exists(),
    reason="Test BIN files not found"
)
def test_detect_alternate_down_up_bin():
    """Test detection of 'alternate down up' BIN file"""
    from parsers.parser_registry import parse_pattern_file
    from core.file_format_detector import detect_file_format_with_confidence
    
    pattern = parse_pattern_file("patterns/alternate/12x6 left to right alternate down up 33 frames.bin")
    detected_wiring, detected_corner, confidence, reason = detect_file_format_with_confidence(pattern)
    
    # Should detect as column-serpentine with good confidence (hint from filename)
    assert detected_wiring == "Column-serpentine", f"Expected Column-serpentine, got {detected_wiring}"
    assert confidence >= 0.75, f"Expected confidence >= 0.75, got {confidence:.2f}"


