"""
Test helpers for generating synthetic LED pattern binaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple
import struct


RGB = Tuple[int, int, int]


def _pattern_pixels(width: int, height: int, frame_index: int) -> List[RGB]:
    pixels: List[RGB] = []
    led_count = width * height
    for idx in range(led_count):
        base = (frame_index * 17 + idx * 11) % 256
        pixels.append((base, (base + 40) % 256, (base + 80) % 256))
    return pixels


def make_raw_rgb_payload(width: int, height: int, frames: int = 1) -> bytes:
    payload = bytearray()
    for frame_index in range(frames):
        for pixel in _pattern_pixels(width, height, frame_index):
            payload.extend(pixel)
    return bytes(payload)


def make_standard_binary(width: int, height: int, frames: int = 1, delay_ms: int = 40) -> bytes:
    led_count = width * height
    header = struct.pack("<HH", led_count, frames)
    body = bytearray()
    for frame_index in range(frames):
        body.extend(struct.pack("<H", delay_ms))
        for pixel in _pattern_pixels(width, height, frame_index):
            body.extend(pixel)
    return header + bytes(body)


def make_dimension_header_binary(width: int, height: int, frames: int = 1, duration_ms: int = 100) -> bytes:
    led_count = width * height
    header = struct.pack("<HHH", width, height, frames)
    body = bytearray()
    for frame_index in range(frames):
        body.extend(struct.pack("<H", duration_ms))
        for pixel in _pattern_pixels(width, height, frame_index):
            body.extend(pixel)
    return header + bytes(body)


def write_fixture(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

