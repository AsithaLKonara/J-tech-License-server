import os
import sys
import itertools

sys.path.insert(0, os.path.abspath("."))

from tests.unit.test_file_format_detection import _build_pattern
from core.file_format_detector import _score_orientation, detect_file_format

wiring = os.environ.get("ORIENT_WIRING", "Column-major")
pattern = _build_pattern(5, 4, wiring, "LT")
frames = [list(pattern.frames[0].pixels)]
width = pattern.metadata.width
height = pattern.metadata.height

for order, serp in itertools.product(("row", "column"), (False, True)):
    score = _score_orientation(frames, width, height, order, serp)
    print(order, "serp" if serp else "straight", score)

print("detected", detect_file_format(pattern))

