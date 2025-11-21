"""
Encoders for exporting patterns into firmware-friendly formats.

Provides shared helpers so all writers (binary, dat, hex, header) use the
same pixel ordering, colour remapping, bit-depth trimming, and bit ordering.
"""

from __future__ import annotations

import struct
from typing import Iterable, List, Tuple

from core.pattern import Frame, Pattern
from core.export_options import ExportOptions, RGB


def _reverse_bits(value: int, bit_count: int = 8) -> int:
    result = 0
    for _ in range(bit_count):
        result = (result << 1) | (value & 0x1)
        value >>= 1
    mask = (1 << bit_count) - 1
    return result & mask


def _apply_bit_order(byte_value: int, options: ExportOptions) -> int:
    byte_value &= 0xFF
    if options.bit_order_msb_lsb.upper() == "LSB":
        return _reverse_bits(byte_value)
    return byte_value


def _encode_pixel_bytes(pixel: RGB, options: ExportOptions) -> List[int]:
    """Encode a single RGB pixel into a byte sequence according to options."""
    ordered = options.reorder_color_channels(pixel)
    if options.color_space == "RGB888":
        working = options.trim_to_bit_depth(ordered)
        color_data = options.convert_color_space(tuple(working))
    else:
        color_data = options.convert_color_space(ordered)

    # RGB565 returns a tuple with a single 16-bit value.
    if options.color_space == "RGB565":
        value = color_data[0]
        return [value & 0xFF, (value >> 8) & 0xFF]

    return [int(channel) & 0xFF for channel in color_data]


def _expected_pixel_count(pattern: Pattern) -> int:
    return pattern.metadata.width * pattern.metadata.height


def prepare_frame_pixels(pattern: Pattern, frame: Frame) -> List[RGB]:
    """Ensure a frame has exactly width*height pixels (pad or trim)."""
    expected = _expected_pixel_count(pattern)
    pixels = list(frame.pixels)
    if len(pixels) < expected:
        pixels.extend([(0, 0, 0)] * (expected - len(pixels)))
    elif len(pixels) > expected:
        pixels = pixels[:expected]
    return pixels


def encode_frame_bytes(pattern: Pattern, frame: Frame, options: ExportOptions) -> bytes:
    """Encode a single frame into bytes (pixel only, no duration header)."""
    ordered_pixels = options.reorder_pixels(
        prepare_frame_pixels(pattern, frame),
        pattern.metadata.width,
        pattern.metadata.height,
    )

    data = bytearray()
    for pixel in ordered_pixels:
        for byte in _encode_pixel_bytes(pixel, options):
            data.append(_apply_bit_order(byte, options))
    return bytes(data)


def bytes_per_pixel(options: ExportOptions) -> int:
    """Determine bytes per pixel after encoding."""
    return len(_encode_pixel_bytes((0, 0, 0), options))


def build_binary_payload(pattern: Pattern, options: ExportOptions | None = None) -> bytes:
    """Return full binary payload (with Upload Bridge header)."""
    opts = options or ExportOptions()
    payload = bytearray()
    payload.extend(struct.pack("<H", pattern.metadata.led_count))
    payload.extend(struct.pack("<H", pattern.frame_count))

    for frame in pattern.frames:
        delay_ms = max(1, min(frame.duration_ms, 65535))
        payload.extend(struct.pack("<H", delay_ms))
        payload.extend(encode_frame_bytes(pattern, frame, opts))

    return bytes(payload)


def build_dat_payload(pattern: Pattern, options: ExportOptions | None = None) -> bytes:
    """
    Build a data payload similar to LED Matrix Studio .dat exports.

    Header layout:
        [0] width  (uint8, clamped at 255)
        [1] height (uint8, clamped at 255)
        [2] frames (uint16 little-endian)
        [4] bytes per pixel
        [5] reserved (0)
    """
    opts = options or ExportOptions()
    payload = bytearray()
    width = min(pattern.metadata.width, 255)
    height = min(pattern.metadata.height, 255)
    frames = min(pattern.frame_count, 0xFFFF)
    payload.append(width)
    payload.append(height)
    payload.extend(struct.pack("<H", frames))
    payload.append(bytes_per_pixel(opts))
    payload.append(0x00)  # reserved for future metadata

    for frame in pattern.frames:
        delay_ms = max(1, min(frame.duration_ms, 65535))
        payload.extend(struct.pack("<H", delay_ms))
        payload.extend(encode_frame_bytes(pattern, frame, opts))
    return bytes(payload)


def _iter_hex_records(binary_payload: bytes, record_size: int = 16) -> Iterable[Tuple[int, bytes]]:
    address = 0
    for index in range(0, len(binary_payload), record_size):
        chunk = binary_payload[index:index + record_size]
        yield address, chunk
        address += len(chunk)


def _format_hex_record(address: int, data: bytes) -> str:
    byte_count = len(data)
    record_type = 0x00
    checksum = byte_count
    checksum += (address >> 8) & 0xFF
    checksum += address & 0xFF
    checksum += record_type
    for byte in data:
        checksum += byte
    checksum = ((~checksum) + 1) & 0xFF
    record = f":{byte_count:02X}{address:04X}{record_type:02X}"
    record += "".join(f"{byte:02X}" for byte in data)
    record += f"{checksum:02X}"
    return record


def build_intel_hex(pattern: Pattern, options: ExportOptions | None = None) -> str:
    """Generate Intel HEX string for the pattern data."""
    opts = options or ExportOptions()
    binary_payload = build_binary_payload(pattern, opts)
    record_size = opts.bytes_per_line if opts.bytes_per_line > 0 else 16
    lines = [
        _format_hex_record(address, chunk)
        for address, chunk in _iter_hex_records(binary_payload, record_size=record_size)
    ]
    lines.append(":00000001FF")  # EOF record
    return "\n".join(lines) + "\n"


def build_c_header(pattern: Pattern, options: ExportOptions | None = None, array_basename: str = "Pattern") -> str:
    """
    Generate a simple C header representation with frame arrays.
    Returns header text (caller writes to .h file).
    """
    opts = options or ExportOptions()
    lines: List[str] = [
        "#pragma once",
        "#include <stdint.h>",
        "",
        f"// Pattern exported by Upload Bridge",
        f"static const uint16_t {array_basename}_WIDTH = {pattern.metadata.width};",
        f"static const uint16_t {array_basename}_HEIGHT = {pattern.metadata.height};",
        f"static const uint16_t {array_basename}_FRAMES = {pattern.frame_count};",
        "",
    ]

    byte_width = bytes_per_pixel(opts)
    for index, frame in enumerate(pattern.frames):
        frame_bytes = encode_frame_bytes(pattern, frame, opts)
        array_name = f"{array_basename}_Frame{index}"

        if byte_width == 3:
            element_type = "uint32_t"
            step = 3
        elif byte_width == 2:
            element_type = "uint16_t"
            step = 2
        else:
            element_type = "uint8_t"
            step = 1

        lines.append(f"static const {element_type} {array_name}[] PROGMEM = {{")

        values: List[int] = []
        for offset in range(0, len(frame_bytes), step):
            chunk = frame_bytes[offset:offset + step]
            if len(chunk) < step:
                chunk = chunk + bytes([0] * (step - len(chunk)))
            if step == 3:
                value = (chunk[0] << 16) | (chunk[1] << 8) | chunk[2]
            else:
                value = 0
                for idx, byte in enumerate(chunk):
                    value |= byte << (idx * 8)
            values.append(value)

        hex_width = step * 2 if step != 3 else 6
        formatted = ", ".join(f"0x{value:0{hex_width}X}" for value in values)
        lines.append(f"    {formatted}")
        lines.append("};")
        lines.append("")

    return "\n".join(lines)


__all__ = [
    "encode_frame_bytes",
    "bytes_per_pixel",
    "prepare_frame_pixels",
    "build_binary_payload",
    "build_dat_payload",
    "build_intel_hex",
    "build_c_header",
]

