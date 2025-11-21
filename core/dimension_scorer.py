"""
Dimension Scorer - shared heuristics for non-square layout detection.

This module factors LED counts, evaluates plausible (width, height) pairs,
and optionally infers LED+frame combinations for raw RGB payloads.
All parsers and the MatrixDetector rely on the same scoring so results stay
consistent across the app.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import math
from typing import Iterable, Iterator, List, Optional, Tuple

RGBPixel = Tuple[int, int, int]

# Common matrix layouts observed in real hardware (width, height)
COMMON_LAYOUTS = {
    (8, 8),
    (12, 6),
    (15, 6),
    (12, 8),
    (12, 12),
    (16, 8),
    (16, 9),
    (16, 10),
    (16, 16),
    (20, 10),
    (20, 12),
    (24, 12),
    (24, 16),
    (17, 5),
    (32, 8),
    (32, 12),
    (32, 16),
    (32, 32),
    (40, 6),
    (40, 10),
    (48, 12),
    (48, 24),
    (64, 16),
    (64, 32),
}

# Popular LED counts (strips + matrices)
COMMON_LED_COUNTS = {
    16,
    24,
    30,
    32,
    36,
    40,
    48,
    50,
    54,
    60,
    64,
    72,
    76,
    80,
    84,
    85,
    90,
    96,
    100,
    108,
    120,
    128,
    144,
    150,
    160,
    176,
    192,
    200,
    224,
    240,
    256,
    288,
    300,
    320,
    360,
    384,
    400,
    432,
    448,
    480,
    512,
    576,
    600,
    640,
    720,
    768,
    800,
    900,
    960,
    1024,
    1152,
    1200,
    1280,
    1536,
    1600,
    1920,
    2048,
    2304,
}

# Aspect ratios that should receive a boost (width / height)
PREFERRED_ASPECT_RATIOS = [
    1.0,  # square
    16 / 9,
    4 / 3,
    3 / 2,
    2.0,
    8 / 3,
    3.0,
    4.0,
    0.5,  # tall orientation
    0.75,
]


@dataclass
class DimensionCandidate:
    width: int
    height: int
    confidence: float


@dataclass
class DimensionResolution:
    led_count: int
    width: int
    height: int
    frames: int
    confidence: float


def _abs_ratio_difference(a: float, b: float) -> float:
    return abs(a - b) / (b or 1.0)


def _factor_pairs(count: int, include_strips: bool) -> Iterator[Tuple[int, int]]:
    if count <= 0:
        return iter(())
    sqrt_n = int(math.sqrt(count))
    pairs: List[Tuple[int, int]] = []
    for factor in range(1, sqrt_n + 1):
        if count % factor != 0:
            continue
        height = factor
        width = count // factor
        if width < height:
            width, height = height, width
        if height == 1 and not include_strips and width != 1:
            continue
        pairs.append((width, height))
    return iter(pairs)


def factor_pairs(count: int, include_strips: bool = True) -> List[Tuple[int, int]]:
    """Public helper returning factor pairs (width >= height)."""
    return list(_factor_pairs(count, include_strips=include_strips))


def _base_layout_score(width: int, height: int) -> float:
    if height <= 0 or width <= 0:
        return 0.0
    aspect = width / height
    score = 0.25  # baseline

    # Common layout boost
    if (width, height) in COMMON_LAYOUTS or (height, width) in COMMON_LAYOUTS:
        score += 0.25

    # Aspect ratio closeness
    best_aspect_bonus = 0.0
    for preferred in PREFERRED_ASPECT_RATIOS:
        diff = _abs_ratio_difference(aspect, preferred)
        if diff <= 0.05:
            best_aspect_bonus = max(best_aspect_bonus, 0.22)
        elif diff <= 0.12:
            best_aspect_bonus = max(best_aspect_bonus, 0.18)
        elif diff <= 0.20:
            best_aspect_bonus = max(best_aspect_bonus, 0.12)
    score += best_aspect_bonus

    # Even dimensions are easier to wire
    if width % 2 == 0 and height % 2 == 0:
        score += 0.05

    # Penalise extremely skewed layouts
    skew = max(aspect, 1 / aspect if aspect else 0)
    if skew > 6.0:
        score -= 0.05

    return max(0.05, min(score, 0.95))


def layout_score(width: int, height: int, total_pixels: Optional[int] = None) -> float:
    """Public helper returning base layout score."""
    _ = total_pixels  # reserved for future weighting
    return _base_layout_score(width, height)


def _pixel_alignment_bonus(frame: Iterable[RGBPixel], width: int) -> float:
    frame_list = list(frame) if frame is not None else []
    if width <= 1 or len(frame_list) < width + 1:
        return 0.0

    wrap_diffs: List[int] = []
    inline_diffs: List[int] = []
    for idx in range(len(frame_list) - 1):
        diff = sum(abs(frame_list[idx][channel] - frame_list[idx + 1][channel]) for channel in range(3))
        if (idx + 1) % width == 0:
            wrap_diffs.append(diff)
        else:
            inline_diffs.append(diff)

    if not inline_diffs or not wrap_diffs:
        return 0.0

    avg_inline = sum(inline_diffs) / len(inline_diffs)
    avg_wrap = sum(wrap_diffs) / len(wrap_diffs)
    if avg_wrap <= avg_inline:
        return 0.0

    gain = (avg_wrap - avg_inline) / (avg_inline + 1e-6)
    return min(0.2, max(0.0, gain * 0.1))


def generate_layout_candidates(
    led_count: int,
    first_frame: Optional[Iterable[RGBPixel]] = None,
    include_strips: bool = False,
    limit: Optional[int] = 8,
) -> List[Tuple[int, int, float]]:
    """Return sorted layout candidates (width, height, confidence)."""
    candidates: List[Tuple[int, int, float]] = []
    for width, height in _factor_pairs(led_count, include_strips=include_strips):
        score = _base_layout_score(width, height)
        if first_frame:
            score += _pixel_alignment_bonus(first_frame, width)
        score = max(0.05, min(score, 0.99))
        candidates.append((width, height, score))

    candidates.sort(key=lambda item: item[2], reverse=True)
    if limit is not None:
        candidates = candidates[:limit]
    return candidates


def pick_best_layout(
    led_count: int,
    first_frame: Optional[Iterable[RGBPixel]] = None,
    include_strips: bool = False,
) -> Optional[Tuple[int, int, float]]:
    candidates = generate_layout_candidates(
        led_count,
        first_frame=first_frame,
        include_strips=include_strips,
        limit=1,
    )
    return candidates[0] if candidates else None


def _frame_score(frames: int, dimension_source: Optional[str] = None) -> float:
    """
    Score frame count for dimension detection confidence.
    
    Args:
        frames: Number of frames in the pattern
        dimension_source: Source of dimensions ('header', 'detector', 'fallback', etc.)
                         If 'header', returns full confidence regardless of frame count
    
    Returns:
        Confidence score (0.0 to 1.0) for frame count
    """
    # If dimensions come from header, trust them completely
    if dimension_source == "header":
        return 1.0
    
    if frames <= 1:
        return 0.0
    if frames <= 4:
        return 0.7
    if frames <= 12:
        return 0.7
    if frames <= 60:
        return 0.85
    if frames <= 240:
        return 0.75
    if frames <= 600:
        return 0.55
    if frames <= 1200:
        return 0.35
    # Reduced penalty for 2000-5000 frame range (common for long animations)
    if frames <= 2000:
        return 0.3
    if frames <= 5000:
        return 0.25  # Increased from 0.2
    return 0.15  # Increased from 0.1


def infer_leds_and_frames(
    total_pixels: int,
    include_strips: bool = True,
    preferred_led_counts: Optional[Iterable[int]] = None,
    pixel_bytes: Optional[bytes] = None,
    dimension_source: Optional[str] = None,
) -> Optional[DimensionResolution]:
    """Infer LED count, width, height, and frame count from total pixel count."""
    if total_pixels <= 0:
        return None

    divisors: List[int] = []
    sqrt_total = int(math.sqrt(total_pixels))
    for value in range(1, sqrt_total + 1):
        if total_pixels % value != 0:
            continue
        divisors.append(value)
        complement = total_pixels // value
        if complement != value:
            divisors.append(complement)

    if preferred_led_counts:
        for led_count in preferred_led_counts:
            if led_count > 0 and total_pixels % led_count == 0:
                divisors.append(led_count)

    divisors = sorted(set(filter(lambda n: 1 < n <= 10000, divisors)))

    best_resolution: Optional[DimensionResolution] = None
    best_score = -1.0

    for led_count in divisors:
        frames = total_pixels // led_count
        if frames <= 0:
            continue

        first_frame_pixels: Optional[List[RGBPixel]] = None
        if pixel_bytes and len(pixel_bytes) >= led_count * 3:
            raw = pixel_bytes[: led_count * 3]
            first_frame_pixels = [
                (raw[i], raw[i + 1], raw[i + 2])
                for i in range(0, led_count * 3, 3)
            ]

        layout = pick_best_layout(
            led_count,
            first_frame=first_frame_pixels,
            include_strips=include_strips,
        )
        if not layout:
            continue
        width, height, layout_score = layout
        frame_conf = _frame_score(frames, dimension_source=dimension_source)
        if preferred_led_counts and led_count in preferred_led_counts:
            layout_score = min(0.99, layout_score + 0.05)
        if not include_strips and min(width, height) < 3:
            continue

        total_score = layout_score * 0.8 + frame_conf * 0.2

        if total_score > best_score:
            best_resolution = DimensionResolution(
                led_count=led_count,
                width=width,
                height=height,
                frames=frames,
                confidence=min(0.99, total_score),
            )
            best_score = total_score

    return best_resolution


def score_dimensions(
    data: bytes,
    bytes_per_pixel: int = 3,
    include_strips: bool = True,
    preferred_led_counts: Optional[Iterable[int]] = None,
    dimension_source: Optional[str] = None,
) -> Tuple[int, int, int, float]:
    """
    Convenience helper that infers width, height, frame count, and confidence
    directly from raw pixel bytes.
    """
    if bytes_per_pixel <= 0:
        raise ValueError("bytes_per_pixel must be positive")

    total_pixels = len(data) // bytes_per_pixel
    if total_pixels <= 0:
        return (1, 1, 1, 0.0)

    resolution = infer_leds_and_frames(
        total_pixels,
        include_strips=include_strips,
        preferred_led_counts=preferred_led_counts,
        pixel_bytes=data,
        dimension_source=dimension_source,
    )
    if resolution:
        return (
            resolution.width,
            resolution.height,
            resolution.frames,
            min(1.0, max(0.0, resolution.confidence)),
        )

    width = total_pixels
    height = 1
    confidence = 0.2
    if not include_strips:
        width = height = int(math.sqrt(total_pixels)) or 1
        confidence = 0.1
    return (width, height, 1, confidence)


