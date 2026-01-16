def energy_vectors(design_pixels, width, height):
    brightness = [r + g + b for (r, g, b) in design_pixels]
    row_energy = [
        sum(brightness[row * width : (row + 1) * width]) for row in range(height)
    ]
    col_energy = [sum(brightness[col::width]) for col in range(width)]
    return row_energy, col_energy

import os
import sys

sys.path.insert(0, os.path.abspath("."))

from core.file_format_detector import _score_orientation, detect_file_format, _contiguity_bonus, _average_neighbor_diff
from core.pattern import Frame, Pattern, PatternMetadata
from core.wiring_mapper import WiringMapper


def generate_test_pixels(width, height, wiring_mode):
    pixels = []
    column_emphasis = "Column" in wiring_mode
    for y in range(height):
        for x in range(width):
            base = x if column_emphasis else y
            r = (base * 70) % 256
            g = (x * 31 + y * 17) % 256
            b = (base * 90 + x * 11 + y * 5) % 256
            pixels.append((r, g, b))
    return pixels
from core.matrix_mapper import MatrixMappingOptions, unwrap_pixels_to_design_order


def build_pattern(width, height, wiring, corner):
    design_pixels = generate_test_pixels(width, height, wiring)
    mapper = WiringMapper(width, height, wiring, corner)
    hardware = mapper.design_to_hardware(design_pixels)
    metadata = PatternMetadata(width=width, height=height)
    frame = Frame(pixels=hardware, duration_ms=20)
    return Pattern(name="debug", metadata=metadata, frames=[frame])


PATTERN_WIRING = os.environ.get("DEBUG_WIRING", "Row-major")
pattern = build_pattern(5, 4, PATTERN_WIRING, "LT")
frames = [list(frame.pixels) for frame in pattern.frames[:1]]
width = pattern.metadata.width
height = pattern.metadata.height
raw_pixels = frames[0]
adjacent_diff = _average_neighbor_diff(raw_pixels, 1)
row_step_diff = _average_neighbor_diff(raw_pixels, width)
col_step_diff = _average_neighbor_diff(raw_pixels, height)
print("adjacent", adjacent_diff, "row_step", row_step_diff, "col_step", col_step_diff)

for order in ("row", "column"):
    for serp in (False, True):
        scores = _score_orientation(frames, width, height, order, serp)
        print(order, "serp" if serp else "straight", scores)

options_row = MatrixMappingOptions(width, height, "row", False, "top_left")
design_row = unwrap_pixels_to_design_order(raw_pixels, options_row)
options_col = MatrixMappingOptions(width, height, "column", False, "top_left")
design_col = unwrap_pixels_to_design_order(raw_pixels, options_col)
print("contiguity row", _contiguity_bonus(design_row, width, height, "row"))
print("contiguity col", _contiguity_bonus(design_col, width, height, "column"))

print("detected:", detect_file_format(pattern))

