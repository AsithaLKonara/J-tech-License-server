"""
Utility script: inspect BIN pattern files for inferred dimensions.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.dimension_scorer import score_dimensions
from core.io.lms_formats import parse_bin_stream


def inspect(path: Path) -> None:
    data = path.read_bytes()
    size = len(data)
    width, height, frames, conf = score_dimensions(data)
    meta = parse_bin_stream(data)

    print(f"File: {path}")
    print(f"  Size: {size} bytes")
    print(f"  score_dimensions -> {width}x{height}, frames={frames}, confidence={conf:.2f}")
    print(f"  parse_bin_stream -> {meta['width']}x{meta['height']}, frames={meta['frame_count']}")
    print(f"  Bytes per frame (score_dimensions): {size // max(frames, 1)}")
    print()


if __name__ == "__main__":
    files = [
        Path("patterns/alternate/up down.bin"),
        Path("patterns/alternate/down up.bin"),
        Path("patterns/alternate/12x6 left to right alternate up down 33 frames.bin"),
        Path("patterns/alternate/12x6 left to right alternate down up 33 frames.bin"),
    ]
    for path in files:
        if path.exists():
            inspect(path)
        else:
            print(f"File not found: {path}")

