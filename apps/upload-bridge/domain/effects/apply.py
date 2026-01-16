from __future__ import annotations

import math
import random
from typing import Iterable, List, Sequence, Tuple, Callable, Optional

from core.pattern import Frame, Pattern

from .models import EffectDefinition

Color = Tuple[int, int, int]

# Canonical colour palette lookup used to infer gradients from effect names.
_BASE_COLOURS = {
    "red": (252, 92, 92),
    "green": (54, 179, 126),
    "blue": (77, 136, 255),
    "cyan": (64, 224, 208),
    "yellow": (255, 214, 102),
    "purple": (177, 132, 255),
    "magenta": (255, 105, 180),
    "white": (250, 250, 250),
    "orange": (255, 163, 72),
    "pink": (255, 142, 170),
    "teal": (64, 200, 180),
    "gold": (255, 215, 128),
}
_DEFAULT_PALETTE = [(255, 148, 114), (93, 109, 255), (140, 255, 235)]


def apply_effect_to_frames(
    pattern: Pattern,
    effect: EffectDefinition,
    frame_indices: Iterable[int],
    intensity: float,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> None:
    """Apply the procedural effect to the provided frames.

    The implementation purposefully produces visually pleasing (yet lightweight)
    overlays so we can honour legacy effect names without depending on SWF
    parsing.  The behaviour is deterministic for a given effect identifier.
    
    Args:
        pattern: Pattern to apply effect to
        effect: Effect definition
        frame_indices: Frames to apply effect to
        intensity: Effect intensity (0.0-1.0)
        progress_callback: Optional callback(completed, total) for progress updates
    """

    frames = list(frame_indices)
    if not frames:
        return

    total = len(frames)
    width = max(1, pattern.metadata.width)
    height = max(1, pattern.metadata.height)
    palette = _build_palette(effect)
    style = _derive_style(effect)
    rng = random.Random(effect.identifier)
    speed = 0.05 + intensity * 0.45

    processed_count = 0
    skipped_count = 0
    
    for step, frame_index in enumerate(frames):
        if not (0 <= frame_index < len(pattern.frames)):
            skipped_count += 1
            import logging
            logging.warning(f"Effect application: Skipping invalid frame index {frame_index} (pattern has {len(pattern.frames)} frames)")
            continue
        frame = pattern.frames[frame_index]
        pixels = list(frame.pixels)
        if len(pixels) != width * height:
            pixels = _pad_or_trim_pixels(pixels, width * height)

        offset = step * speed
        transformed = _apply_style_to_pixels(pixels, width, height, palette, style, offset, intensity, rng)
        frame.pixels = transformed
        processed_count += 1
        
        # Call progress callback and check if canceled
        if progress_callback:
            should_continue = progress_callback(step + 1, total)
            if not should_continue:
                # User canceled - stop processing remaining frames
                import logging
                logging.info(f"Effect application canceled by user after processing {processed_count} of {total} frames")
                break
    
    # Log completion statistics
    if skipped_count > 0:
        import logging
        logging.warning(f"Effect application: Processed {processed_count} frames, skipped {skipped_count} invalid frames")


def generate_effect_preview(
    effect: EffectDefinition,
    size: int = 64,
    intensity: float = 0.6,
) -> List[Color]:
    """Generate a small preview pixel buffer for UI thumbnails."""

    width = height = max(4, min(16, size // 8))
    palette = _build_palette(effect)
    style = _derive_style(effect)
    rng = random.Random(effect.identifier)
    pixels = [(0, 0, 0)] * (width * height)
    return _apply_style_to_pixels(pixels, width, height, palette, style, offset=0.0, intensity=intensity, rng=rng)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _apply_style_to_pixels(
    pixels: Sequence[Color],
    width: int,
    height: int,
    palette: Sequence[Color],
    style: str,
    offset: float,
    intensity: float,
    rng: random.Random,
) -> List[Color]:
    blended: List[Color] = []
    total_frames = 1.0  # used for wave calculations

    for idx in range(width * height):
        x = idx % width
        y = idx // width
        base = pixels[idx] if idx < len(pixels) else (0, 0, 0)
        t = _sample_position(style, x, y, width, height, offset, total_frames, rng)
        colour = _sample_palette(palette, t)
        blended.append(_blend(base, colour, intensity))
    return blended


def _build_palette(effect: EffectDefinition) -> List[Color]:
    tokens = effect.keywords
    colours: List[Color] = []
    for token in tokens:
        if token in _BASE_COLOURS and _BASE_COLOURS[token] not in colours:
            colours.append(_BASE_COLOURS[token])
        elif token.endswith("ish"):
            root = token[:-3]
            if root in _BASE_COLOURS and _BASE_COLOURS[root] not in colours:
                colours.append(_BASE_COLOURS[root])
    if not colours:
        colours = list(_DEFAULT_PALETTE)
    elif len(colours) == 1:
        # Add complementary colour for smoother gradients
        comp = _complementary_colour(colours[0])
        colours.append(comp)
    return colours[:5]


def _derive_style(effect: EffectDefinition) -> str:
    tokens = effect.keywords
    if any(token in {"radial", "proliferation", "burst", "oval", "ellipse"} for token in tokens):
        return "radial"
    if any(token in {"symmetrical", "mirror", "double"} for token in tokens):
        return "mirrored"
    if any(token in {"down", "up", "over"} for token in tokens):
        return "vertical"
    if any(token in {"left", "right", "linear"} for token in tokens):
        return "horizontal"
    if any(token in {"color", "colour", "gradient", "change"} for token in tokens):
        return "gradient"
    return "horizontal"


def _sample_position(
    style: str,
    x: int,
    y: int,
    width: int,
    height: int,
    offset: float,
    total_frames: float,
    rng: random.Random,
) -> float:
    if style == "vertical":
        return (y / max(1, height - 1) + offset) % 1.0
    if style == "radial":
        cx = (width - 1) / 2
        cy = (height - 1) / 2
        dist = math.hypot(x - cx, y - cy)
        max_dist = math.hypot(cx, cy)
        return min(1.0, (dist / max_dist) + offset)
    if style == "mirrored":
        centre = (width - 1) / 2
        dist = abs(x - centre) / max(centre, 1)
        return (dist + offset) % 1.0
    if style == "gradient":
        return (x + y) / max(1, width + height - 2)
    # default horizontal wave
    return (x / max(1, width - 1) + offset) % 1.0


def _sample_palette(palette: Sequence[Color], position: float) -> Color:
    if not palette:
        return (0, 0, 0)
    if len(palette) == 1:
        return palette[0]
    position = position % 1.0
    scaled = position * (len(palette) - 1)
    index = int(math.floor(scaled))
    frac = scaled - index
    c1 = palette[index]
    c2 = palette[min(index + 1, len(palette) - 1)]
    return _lerp_colour(c1, c2, frac)


def _blend(base: Color, overlay: Color, intensity: float) -> Color:
    mix = max(0.0, min(1.0, intensity))
    r = int(base[0] * (1 - mix) + overlay[0] * mix)
    g = int(base[1] * (1 - mix) + overlay[1] * mix)
    b = int(base[2] * (1 - mix) + overlay[2] * mix)
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def _lerp_colour(c1: Color, c2: Color, t: float) -> Color:
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _complementary_colour(colour: Color) -> Color:
    return (255 - colour[0], 255 - colour[1], 255 - colour[2])


def _pad_or_trim_pixels(pixels: Sequence[Color], size: int) -> List[Color]:
    if len(pixels) >= size:
        return list(pixels[:size])
    padded = list(pixels)
    padded.extend([(0, 0, 0)] * (size - len(pixels)))
    return padded


__all__ = ["apply_effect_to_frames", "generate_effect_preview"]
