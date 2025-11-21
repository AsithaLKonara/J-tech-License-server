"""
Compare how a binary pattern looks under two different (width, height, frames) assumptions.
"""

from pathlib import Path


def load_frames(data: bytes, width: int, height: int):
    bpf = width * height * 3
    frames = []
    for offset in range(0, len(data), bpf):
        chunk = data[offset : offset + bpf]
        if len(chunk) != bpf:
            break
        pixels = [
            tuple(chunk[i : i + 3]) for i in range(0, bpf, 3)
        ]
        frames.append(pixels)
    return frames


def to_grid(pixels, width, height):
    chars = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b = pixels[y * width + x]
            if r > 200 and g < 60 and b < 60:
                row.append("R")
            elif g > 200 and r < 60:
                row.append("G")
            elif b > 200 and r < 60:
                row.append("B")
            elif r > 200 and g > 200 and b < 80:
                row.append("Y")
            elif r > 230 and g > 230 and b > 230:
                row.append("W")
            else:
                row.append(".")
        chars.append("".join(row))
    return "\n".join(chars)


def compare(path: Path, layouts):
    print(f"File: {path}")
    data = path.read_bytes()
    for width, height in layouts:
        frames = load_frames(data, width, height)
        print(f"  Layout {width}x{height}, frames={len(frames)}")
        if frames:
            print(to_grid(frames[0], width, height))
        print()


if __name__ == "__main__":
    files = [
        Path("patterns/alternate/up down.bin"),
        Path("patterns/alternate/down up.bin"),
        Path("patterns/alternate/12x6 left to right alternate up down 33 frames.bin"),
        Path("patterns/alternate/12x6 left to right alternate down up 33 frames.bin"),
    ]
    for fp in files:
        if fp.exists():
            compare(fp, [(16, 9), (12, 6)])
        else:
            print(f"File not found: {fp}")

