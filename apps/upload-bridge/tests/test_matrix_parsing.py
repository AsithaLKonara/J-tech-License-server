import struct

from core.matrix_detector import MatrixDetector
from core.dimension_scorer import infer_leds_and_frames
from parsers.enhanced_binary_parser import EnhancedBinaryParser
from parsers.raw_rgb_parser import RawRGBParser
from parsers.standard_format_parser import StandardFormatParser


def _build_rectangular_frame(width: int, height: int) -> list[tuple[int, int, int]]:
    frame = []
    for y in range(height):
        for x in range(width):
            value = (y * width + x) % 256
            frame.append((value, (value + 85) % 256, (value + 170) % 256))
    return frame


def _build_rgb_payload(led_count: int, frame_index: int) -> bytes:
    payload = bytearray()
    for led_idx in range(led_count):
        value = (frame_index * 7 + led_idx * 3) % 256
        payload.extend(((value) & 0xFF, (value + 40) % 256, (value + 80) % 256))
    return bytes(payload)


def test_matrix_detector_prefers_rectangular_layout_with_frame_data():
    frame = _build_rectangular_frame(12, 6)
    best = MatrixDetector.pick_best_dimensions(len(frame), frame)
    assert best is not None
    width, height, score = best
    assert (width, height) == (12, 6)
    assert score > 0.6


def test_enhanced_binary_parser_handles_per_frame_headers():
    frame_count = 2
    led_count = 72
    header_len = 4

    frames = []
    for idx in range(frame_count):
        header = bytes([0xAA + idx] * header_len)
        payload = _build_rgb_payload(led_count, idx)
        frames.append(header + payload)

    data = struct.pack("<H", frame_count) + b"".join(frames)

    parser = EnhancedBinaryParser()
    pattern = parser.parse(data)

    assert pattern.frame_count == frame_count
    assert pattern.metadata.width == 12
    assert pattern.metadata.height == 6
    assert pattern.metadata.dimension_source == "detector"
    assert pattern.metadata.dimension_confidence > 0.3
    assert pattern.frames[0].led_count == led_count


def test_raw_rgb_parser_infers_rectangular_matrix():
    led_count = 72
    frame_count = 5

    payload = bytearray()
    for frame_idx in range(frame_count):
        payload.extend(_build_rgb_payload(led_count, frame_idx))

    parser = RawRGBParser()
    pattern = parser.parse(bytes(payload))

    assert pattern.frame_count == frame_count
    assert pattern.metadata.width == 12
    assert pattern.metadata.height == 6
    assert pattern.metadata.dimension_source in {"detector", "fallback"}
    assert pattern.metadata.dimension_confidence > 0.0


def test_standard_parser_uses_matrix_detector_for_dimensions():
    led_count = 72
    frame_count = 3
    delay_ms = 40

    header = struct.pack("<HH", led_count, frame_count)
    frames = []
    for idx in range(frame_count):
        frame_payload = struct.pack("<H", delay_ms) + _build_rgb_payload(led_count, idx)
        frames.append(frame_payload)

    data = header + b"".join(frames)

    parser = StandardFormatParser()
    pattern = parser.parse(data)

    assert pattern.frame_count == frame_count
    assert pattern.metadata.width == 12
    assert pattern.metadata.height == 6
    assert pattern.metadata.dimension_source in {"detector", "fallback"}
    assert pattern.metadata.dimension_confidence >= 0.0


def test_dimension_header_parser_trusts_header():
    width = 12
    height = 6
    frame_count = 2
    duration = 200
    led_count = width * height

    frames = []
    for frame_idx in range(frame_count):
        frames.append(struct.pack("<H", duration) + bytes([
            (frame_idx * 5 + i) % 256
            for i in range(led_count * 3)
        ]))

    payload = struct.pack("<HHH", width, height, frame_count) + b"".join(frames)

    parser = EnhancedBinaryParser()
    pattern = parser.parse(payload)

    assert pattern.metadata.width == width
    assert pattern.metadata.height == height
    assert pattern.metadata.dimension_source == "header"
    assert pattern.metadata.dimension_confidence == 1.0


def test_raw_rgb_parser_detects_wide_matrix():
    width, height = 20, 10
    led_count = width * height
    frame_count = 4

    payload = bytearray()
    for frame_idx in range(frame_count):
        payload.extend(_build_rgb_payload(led_count, frame_idx))

    parser = RawRGBParser()
    pattern = parser.parse(bytes(payload))

    dims = {pattern.metadata.width, pattern.metadata.height}
    assert {width, height} == dims
    assert pattern.frame_count == frame_count
    assert pattern.metadata.dimension_confidence > 0.5


def test_dimension_scorer_infers_leds_and_frames():
    width, height, frames = 5, 17, 6
    total_pixels = width * height * frames

    pixel_bytes = b"".join(_build_rgb_payload(width * height, frame_idx) for frame_idx in range(frames))
    from core.dimension_scorer import COMMON_LED_COUNTS

    resolution = infer_leds_and_frames(
        total_pixels,
        include_strips=False,
        pixel_bytes=pixel_bytes,
        preferred_led_counts=COMMON_LED_COUNTS,
    )

    assert resolution is not None
    assert {resolution.width, resolution.height} == {width, height}
    assert resolution.frames == frames
    assert resolution.confidence > 0.4

