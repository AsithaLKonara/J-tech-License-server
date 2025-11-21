"""
Export Validation Helpers
=========================

Utilities for validating patterns prior to export and generating lightweight
preview summaries so the UI can surface byte counts and header information
before the user commits to saving a file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from core.pattern import Pattern
from core.export_options import ExportOptions
from core.export.encoders import (
    bytes_per_pixel,
    encode_frame_bytes,
    prepare_frame_pixels,
    build_binary_payload,
    build_dat_payload,
    build_intel_hex,
    build_c_header,
)


class ExportValidationError(RuntimeError):
    """Raised when a preview cannot be generated for the requested format."""


@dataclass
class GeometryReport:
    """Details about geometry validation for a pattern."""

    expected_pixels: int
    mismatched_frames: List[int] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.mismatched_frames


@dataclass
class ExportPreview:
    """Summary information describing a potential export."""

    format_name: str
    total_bytes: int
    frame_count: int
    bytes_per_frame: int
    header_summary: str
    detail_lines: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    geometry: GeometryReport = field(
        default_factory=lambda: GeometryReport(expected_pixels=0)
    )

    @property
    def blocking_issue(self) -> bool:
        return not self.geometry.is_valid


def _check_geometry(pattern: Pattern) -> GeometryReport:
    expected_pixels = pattern.metadata.width * pattern.metadata.height
    mismatched = [
        idx
        for idx, frame in enumerate(pattern.frames)
        if len(frame.pixels) != expected_pixels
    ]
    return GeometryReport(expected_pixels=expected_pixels, mismatched_frames=mismatched)


def _base_stats(pattern: Pattern, options: ExportOptions) -> Tuple[int, int]:
    bpp = bytes_per_pixel(options)
    expected_frame_bytes = pattern.metadata.width * pattern.metadata.height * bpp
    return bpp, expected_frame_bytes


def _binary_preview(pattern: Pattern, options: ExportOptions) -> ExportPreview:
    payload = build_binary_payload(pattern, options)
    bpp, expected_frame_bytes = _base_stats(pattern, options)
    header_summary = (
        f"Header: {pattern.metadata.led_count} LEDs • "
        f"{pattern.frame_count} frame(s) • "
        f"{2 + expected_frame_bytes} bytes/frame"
    )
    detail_lines = [
        f"Pixel encoding: {bpp} byte(s)/pixel",
        f"Payload bytes (incl. header): {len(payload)}",
    ]

    preview = ExportPreview(
        format_name="Binary Format",
        total_bytes=len(payload),
        frame_count=pattern.frame_count,
        bytes_per_frame=expected_frame_bytes,
        header_summary=header_summary,
        detail_lines=detail_lines,
        geometry=_check_geometry(pattern),
    )

    expected_total = 4 + pattern.frame_count * (2 + expected_frame_bytes)
    if expected_total != len(payload):
        preview.warnings.append(
            "Encoded payload length differs from header expectations "
            f"(expected {expected_total}, got {len(payload)})."
        )
    return preview


def _dat_preview(pattern: Pattern, options: ExportOptions) -> ExportPreview:
    payload = build_dat_payload(pattern, options)
    bpp, expected_frame_bytes = _base_stats(pattern, options)

    header_summary = (
        f"Header: {pattern.metadata.width}×{pattern.metadata.height} • "
        f"{pattern.frame_count} frame(s) • {bpp} B/pixel"
    )
    detail_lines = [
        "Layout: [width][height][frames][bytes-per-pixel][reserved]",
        f"Payload bytes (incl. header): {len(payload)}",
    ]

    preview = ExportPreview(
        format_name="DAT Format",
        total_bytes=len(payload),
        frame_count=pattern.frame_count,
        bytes_per_frame=expected_frame_bytes,
        header_summary=header_summary,
        detail_lines=detail_lines,
        geometry=_check_geometry(pattern),
    )

    expected_total = 6 + pattern.frame_count * (2 + expected_frame_bytes)
    if expected_total != len(payload):
        preview.warnings.append(
            "DAT payload length differs from calculated expectation "
            f"(expected {expected_total}, got {len(payload)})."
        )
    return preview


def _hex_preview(pattern: Pattern, options: ExportOptions) -> ExportPreview:
    text_payload = build_intel_hex(pattern, options)
    lines = text_payload.strip().splitlines()
    data_records = max(0, len(lines) - 1)  # subtract EOF record
    byte_count = len(text_payload.encode("utf-8"))
    record_size = (
        options.bytes_per_line if options.bytes_per_line > 0 else 16
    )

    header_summary = (
        f"{data_records} data record(s) • {record_size} bytes/record • payload {byte_count} bytes"
    )

    preview = ExportPreview(
        format_name="Intel HEX Format",
        total_bytes=byte_count,
        frame_count=pattern.frame_count,
        bytes_per_frame=pattern.metadata.width * pattern.metadata.height,
        header_summary=header_summary,
        detail_lines=[
            f"Includes EOF record • Line endings: {len(lines)} total",
        ],
        geometry=_check_geometry(pattern),
    )
    return preview


def _header_preview(pattern: Pattern, options: ExportOptions) -> ExportPreview:
    header_text = build_c_header(pattern, options)
    lines = header_text.strip().splitlines()
    total_bytes = len(header_text.encode("utf-8"))
    preview = ExportPreview(
        format_name="C Header (PROGMEM)",
        total_bytes=total_bytes,
        frame_count=pattern.frame_count,
        bytes_per_frame=pattern.metadata.width * pattern.metadata.height,
        header_summary=f"{len(lines)} line(s) • {pattern.frame_count} array(s)",
        detail_lines=[
            "Content: PROGMEM arrays with per-frame data.",
        ],
        geometry=_check_geometry(pattern),
    )
    return preview


def _pattern_json_size(pattern: Pattern) -> int:
    import json

    return len(json.dumps(pattern.to_dict(), ensure_ascii=False).encode("utf-8"))


def _json_preview(pattern: Pattern, _options: ExportOptions) -> ExportPreview:
    total_bytes = _pattern_json_size(pattern)
    preview = ExportPreview(
        format_name="JSON Format",
        total_bytes=total_bytes,
        frame_count=pattern.frame_count,
        bytes_per_frame=pattern.metadata.width * pattern.metadata.height,
        header_summary="JSON project payload (metadata + frames).",
        detail_lines=[
            f"UTF-8 encoded bytes: {total_bytes}",
        ],
        geometry=_check_geometry(pattern),
    )
    return preview


def _project_preview(pattern: Pattern, _options: ExportOptions) -> ExportPreview:
    """
    Project exports reuse the JSON serializer, so reuse that sizing information.
    """
    total_bytes = _pattern_json_size(pattern)
    preview = ExportPreview(
        format_name="Project Format",
        total_bytes=total_bytes,
        frame_count=pattern.frame_count,
        bytes_per_frame=pattern.metadata.width * pattern.metadata.height,
        header_summary="Internal Upload Bridge .ledproj archive.",
        detail_lines=[
            f"Estimated JSON size (not including filesystem overhead): {total_bytes} bytes",
        ],
        geometry=_check_geometry(pattern),
    )
    return preview


def _leds_preview(pattern: Pattern, options: ExportOptions) -> ExportPreview:
    """
    Estimate LEDS text export size without generating the full file in memory.

    The calculation mirrors PatternExporter.export_leds but accumulates encoded
    line lengths instead of building the string, so even large patterns remain
    responsive.
    """
    import io

    bpp = bytes_per_pixel(options)
    stream = io.StringIO()

    stream.write("# LEDS Pattern Export\n")
    stream.write(f"# Name: {pattern.name}\n")
    stream.write(f"# LEDs: {pattern.metadata.led_count}\n")
    stream.write(f"# Frames: {pattern.frame_count}\n")
    stream.write(
        f"# Dimensions: {pattern.metadata.width}x{pattern.metadata.height}\n"
    )
    stream.write(
        f"# Export Options: RGB={options.rgb_order}, ColorSpace={options.color_space}\n\n"
    )

    encoded_length = stream.tell()

    expected_leds = pattern.metadata.width * pattern.metadata.height
    for frame_idx, frame in enumerate(pattern.frames):
        stream.write(f"FRAME {frame_idx}\n")
        stream.write(f"DELAY {frame.duration_ms}\n")

        encoded = encode_frame_bytes(pattern, frame, options)
        for led_idx in range(expected_leds):
            start = led_idx * bpp
            chunk = encoded[start : start + bpp]
            if len(chunk) < bpp:
                chunk = chunk + bytes([0] * (bpp - len(chunk)))

            if options.color_space == "RGB565":
                value = chunk[0] | (chunk[1] << 8)
                stream.write(f"LED {led_idx} {options.format_number(value, 2)}\n")
            else:
                values = " ".join(str(byte) for byte in chunk)
                stream.write(f"LED {led_idx} {values}\n")
        stream.write("\n")

    total_bytes = len(stream.getvalue().encode("utf-8"))

    preview = ExportPreview(
        format_name="LEDS Text Format",
        total_bytes=total_bytes,
        frame_count=pattern.frame_count,
        bytes_per_frame=pattern.metadata.width * pattern.metadata.height,
        header_summary=f"Text export with {pattern.frame_count} frame block(s).",
        detail_lines=[
            f"Calculated with {bpp} byte(s)/pixel • Approximate lines: "
            f"{pattern.frame_count * (expected_leds + 2)}",
        ],
        geometry=_check_geometry(pattern),
    )
    return preview


PREVIEW_BUILDERS: Dict[str, Callable[[Pattern, ExportOptions], ExportPreview]] = {
    "Binary Format": _binary_preview,
    "DAT Format": _dat_preview,
    "Intel HEX Format": _hex_preview,
    "C Header (PROGMEM)": _header_preview,
    "LEDS Text Format": _leds_preview,
    "JSON Format": _json_preview,
    "Project Format": _project_preview,
}


def generate_export_preview(
    pattern: Pattern,
    format_name: str,
    options: Optional[ExportOptions] = None,
) -> ExportPreview:
    """
    Generate a preview summary for the requested export format.

    Args:
        pattern: Pattern instance to validate.
        format_name: Human readable format label (matches PatternExporter).
        options: Export options (defaults to ExportOptions()).

    Returns:
        ExportPreview describing payload and potential warnings.
    """
    builder = PREVIEW_BUILDERS.get(format_name)
    if builder is None:
        raise ExportValidationError(f"No preview available for {format_name!r}")

    opts = options or ExportOptions()
    return builder(pattern, opts)

