from __future__ import annotations

from pathlib import Path

from core.io import (
    LMSFormatError,
    detect_dat_header,
    parse_bin_stream,
    parse_dat_file,
    parse_hex_file,
    parse_leds_file,
)


def test_detect_dat_header_and_parse(tmp_path: Path) -> None:
    content = "4 2\n3\nFF0000 FF0000 FF0000 FF0000\n00FF00 00FF00 00FF00 00FF00\n"
    dat_path = tmp_path / "sample.dat"
    dat_path.write_text(content)

    width, height, frame_count = detect_dat_header(content.splitlines())
    assert (width, height, frame_count) == (4, 2, 3)

    parsed = parse_dat_file(dat_path)
    assert parsed["format"] == "DAT"
    assert parsed["rows"]


def test_parse_hex_file(tmp_path: Path) -> None:
    # Simple Intel HEX payload with 4 bytes (record length 04)
    # :04 0000 00 01020304  F2  (valid checksum)
    hex_content = ":0400000001020304F2\n:00000001FF\n"
    hex_path = tmp_path / "pattern.hex"
    hex_path.write_text(hex_content)

    parsed = parse_hex_file(hex_path)
    assert parsed["format"] == "HEX"
    assert parsed["width"] >= 1
    assert parsed["frame_count"] >= 1


def test_parse_leds_file(tmp_path: Path) -> None:
    leds_payload = """# LED Matrix Studio Export
# Width: 4
# Height: 4
# Frames: 2
# Format: RGB32
Pattern1: Frame1, moveLeft1, NULL, NULL, 5
Data:
FF0000 FF0000 FF0000 FF0000
"""
    leds_path = tmp_path / "pattern.leds"
    leds_path.write_text(leds_payload)

    parsed = parse_leds_file(leds_path)
    assert parsed["format"] == "LEDS"
    assert parsed["sequence"].summarize()["instruction_count"] == 1


def test_parse_bin_stream_infers_dimensions() -> None:
    payload = bytes([255, 0, 0] * 4)  # 4 RGB pixels (12 bytes)
    parsed = parse_bin_stream(payload)
    assert parsed["format"] == "BIN"
    # With 4 pixels, dimension scorer may infer 2x1 strip (2 frames) or other valid layouts
    # The important thing is that it returns valid dimensions and frame count
    assert parsed["frame_count"] > 0
    assert parsed["width"] > 0
    assert parsed["height"] > 0
    assert parsed["width"] * parsed["height"] * parsed["frame_count"] == 4  # 4 total pixels


def test_hex_parser_invalid_checksum(tmp_path: Path) -> None:
    bad_hex = ":0400000001020304F5\n"  # bad checksum
    hex_path = tmp_path / "bad.hex"
    hex_path.write_text(bad_hex)

    try:
        parse_hex_file(hex_path)
    except LMSFormatError:
        pass
    else:
        raise AssertionError("Expected LMSFormatError for invalid checksum")

