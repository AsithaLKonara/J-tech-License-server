"""
Matrix Mapper - Remap pattern pixels for different matrix wiring orders
Supports row/column major, serpentine, and origin selection
"""

from dataclasses import dataclass
from typing import List, Tuple

from .pattern import Pattern, Frame, PatternMetadata


@dataclass
class MatrixMappingOptions:
    """Mapping options describing how the physical matrix is wired."""
    width: int
    height: int
    order: str = "row"  # "row" or "column"
    serpentine: bool = True
    origin: str = "top_left"  # top_left, top_right, bottom_left, bottom_right


def _normalize_origin(x: int, y: int, width: int, height: int, origin: str) -> Tuple[int, int]:
    """Transform (x, y) from design top-left origin to the physical origin."""
    if origin == "top_left":
        return x, y
    elif origin == "top_right":
        return (width - 1 - x), y
    elif origin == "bottom_left":
        return x, (height - 1 - y)
    elif origin == "bottom_right":
        return (width - 1 - x), (height - 1 - y)
    else:
        return x, y


def _linear_index_for_mapping(x: int, y: int, options: MatrixMappingOptions) -> int:
    """Compute linear LED index for given (x, y) under mapping options."""
    # First apply origin normalization to convert provided coordinates into top-left logical space
    nx, ny = _normalize_origin(x, y, options.width, options.height, options.origin)

    if options.order == "row":
        # Row-major wiring
        if options.serpentine and (ny % 2 == 1):
            nx = (options.width - 1) - nx
        return ny * options.width + nx

    # Column-major wiring
    if options.serpentine and (nx % 2 == 1):
        ny = (options.height - 1) - ny
    return nx * options.height + ny


def get_linear_index(x: int, y: int, options: MatrixMappingOptions) -> int:
    """Public helper to compute linear index for given design coordinate."""
    return _linear_index_for_mapping(x, y, options)


def unwrap_pixels_to_design_order(
    pixels: List[Tuple[int, int, int]],
    options: MatrixMappingOptions,
) -> List[Tuple[int, int, int]]:
    """
    Convert physical wiring order pixels into design (row-major top-left) order.
    """
    led_count = options.width * options.height
    if len(pixels) != led_count:
        return list(pixels)

    decoded: List[Tuple[int, int, int]] = [(0, 0, 0)] * led_count

    for y in range(options.height):
        for x in range(options.width):
            physical_index = _linear_index_for_mapping(x, y, options)
            decoded[y * options.width + x] = pixels[physical_index]

    return decoded


def remap_pattern(pattern: Pattern, options: MatrixMappingOptions) -> Pattern:
    """
    Remap a pattern's frames from logical matrix order to physical wiring order.

    Assumes incoming frame pixel list is row-major top-left order by default.
    """
    if options.width * options.height != pattern.led_count:
        # Dimension mismatch; do not remap
        return pattern

    remapped_frames: List[Frame] = []

    for frame in pattern.frames:
        if len(frame.pixels) != pattern.led_count:
            remapped_frames.append(frame)
            continue

        # Build target pixel list
        target: List[Tuple[int, int, int]] = [(0, 0, 0)] * pattern.led_count

        # Source is assumed row-major top-left: idx = y * width + x
        for y in range(options.height):
            for x in range(options.width):
                src_idx = y * options.width + x
                dst_idx = _linear_index_for_mapping(x, y, options)
                target[dst_idx] = frame.pixels[src_idx]

        remapped_frames.append(Frame(pixels=target, duration_ms=frame.duration_ms))

    # Copy pattern with updated metadata width/height if needed
    new_meta = PatternMetadata(
        width=options.width,
        height=options.height,
        color_order=pattern.metadata.color_order,
        fps=pattern.metadata.fps,
        total_ms=pattern.metadata.total_ms,
        brightness=pattern.metadata.brightness,
    )

    return Pattern(name=pattern.name, metadata=new_meta, frames=remapped_frames)


