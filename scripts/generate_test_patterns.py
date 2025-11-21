"""
Utility script to produce a suite of synthetic pattern files with varied
dimensions, frame counts, and wiring metadata for regression testing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.pattern import Frame, Pattern, PatternMetadata
from core.pattern_exporter import PatternExporter
from core.export_options import ExportOptions


@dataclass
class PatternSpec:
    filename: str
    name: str
    width: int
    height: int
    frames: int
    wiring_mode: str
    data_in_corner: str
    style: str
    description: str


OUTPUT_DIR = Path("patterns/generated")
DOC_PATH = OUTPUT_DIR / "generated_patterns_overview.md"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for existing in OUTPUT_DIR.glob("*"):
        if existing.is_file() and existing.suffix.lower() in {".bin", ".dat", ".leds"}:
            existing.unlink()


def build_frames(
    width: int,
    height: int,
    frame_count: int,
    style: str,
) -> List[Frame]:
    frames: List[Frame] = []
    for frame_idx in range(frame_count):
        pixels: List[Tuple[int, int, int]] = []
        for y in range(height):
            for x in range(width):
                pixels.append(_colour_for(style, x, y, width, height, frame_idx))
        duration = 80 + (frame_idx % 4) * 20
        frames.append(Frame(pixels=pixels, duration_ms=duration))
    return frames


def _colour_for(
    style: str,
    x: int,
    y: int,
    width: int,
    height: int,
    frame: int,
) -> Tuple[int, int, int]:
    if style == "gradient_horizontal":
        ratio = x / max(1, width - 1)
        r = int(255 * ratio)
        g = (frame * 25) % 256
        b = 60
    elif style == "gradient_vertical":
        ratio = y / max(1, height - 1)
        r = (frame * 30) % 256
        g = int(255 * ratio)
        b = 120
    elif style == "diagonal_wave":
        angle = (x + y + frame) * math.pi / 8.0
        r = int(128 + 127 * math.sin(angle))
        g = int(128 + 127 * math.sin(angle + math.pi / 2))
        b = int(128 + 127 * math.sin(angle + math.pi))
    elif style == "center_pulse":
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0
        dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        pulse = max(0.0, 1.0 - (dist / max(width, height)))
        intensity = int(255 * abs(math.sin(frame / 3 + pulse * math.pi)))
        r, g, b = intensity, int(intensity * 0.6), int(intensity * 0.2)
    elif style == "vertical_stripes":
        stripe = (x + frame) % 4
        colours = [
            (255, 80, 0),
            (0, 160, 255),
            (50, 255, 120),
            (200, 50, 255),
        ]
        r, g, b = colours[stripe]
    elif style == "horizontal_stripes":
        stripe = (y + frame) % 4
        colours = [
            (255, 200, 40),
            (40, 80, 255),
            (255, 40, 160),
            (40, 255, 200),
        ]
        r, g, b = colours[stripe]
    elif style == "swirl":
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0
        angle = math.atan2(y - cy, x - cx) + frame * 0.3
        radius = math.hypot(x - cx, y - cy)
        r = int((math.sin(angle) * 0.5 + 0.5) * 255)
        g = int((math.sin(radius / 2 + frame * 0.2) * 0.5 + 0.5) * 255)
        b = int((math.cos(angle) * 0.5 + 0.5) * 255)
    elif style == "sparkle":
        seed = (x * 31 + y * 17 + frame * 13) % 256
        r = (seed * 53) % 256
        g = (seed * 97) % 256
        b = (seed * 191) % 256
    elif style == "fire_fall":
        intensity = max(0, 255 - int(((y + frame) % height) * (255 / max(1, height - 1))))
        r = min(255, intensity * 2)
        g = min(255, int(intensity * 0.6))
        b = int(intensity * 0.1)
    elif style == "ocean_current":
        wave = math.sin((x / max(1, width - 1) + frame * 0.2) * math.pi * 2)
        r = int(30 + 40 * wave)
        g = int(100 + 80 * wave)
        b = int(180 + 60 * wave)
    else:
        # Fallback rainbow
        base = (x + y + frame) % 256
        r = base
        g = (base + 85) % 256
        b = (base + 170) % 256

    return (
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b))),
    )


def build_pattern(spec: PatternSpec) -> Pattern:
    frames = build_frames(spec.width, spec.height, spec.frames, spec.style)
    metadata = PatternMetadata(
        width=spec.width,
        height=spec.height,
        wiring_mode=spec.wiring_mode,
        data_in_corner=spec.data_in_corner,
        dimension_source="manual",
        dimension_confidence=1.0,
        source_format=Path(spec.filename).suffix.lstrip("."),
    )
    return Pattern(name=spec.name, metadata=metadata, frames=frames)


def export_pattern(pattern: Pattern, target_path: Path) -> None:
    exporter = PatternExporter()
    ext = target_path.suffix.lower()
    options = ExportOptions()

    wiring = pattern.metadata.wiring_mode
    if wiring in {"Serpentine", "Column-serpentine"}:
        options.serpentine = True
    options.scan_direction = "Rows" if wiring in {"Row-major", "Serpentine"} else "Columns"

    corner = pattern.metadata.data_in_corner
    if options.scan_direction == "Rows":
        if corner in {"RT", "RB"}:
            options.scan_order = "RightToLeft"
        elif corner in {"LB", "RB"}:
            options.scan_order = "BottomToTop"
        else:
            options.scan_order = "LeftToRight"
    else:
        if corner in {"LB", "RB"}:
            options.scan_order = "BottomToTop"
        else:
            options.scan_order = "TopToBottom"

    if ext == ".bin":
        exporter.export_binary(pattern, str(target_path), options)
    elif ext == ".dat":
        exporter.export_dat(pattern, str(target_path), options)
    elif ext == ".leds":
        exporter.export_leds(pattern, str(target_path), options)
    else:
        raise ValueError(f"Unsupported export extension: {ext}")


def write_doc(specs: List[PatternSpec]) -> None:
    lines = [
        "# Generated Test Patterns",
        "",
        "The following assets were generated automatically for metadata detection tests.",
        "",
        "| File | Format | Dimensions (W×H) | Frames | Wiring | Data-In Corner | Description |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for spec in specs:
        ext = Path(spec.filename).suffix.lstrip(".")
        lines.append(
            f"| `{spec.filename}` | `{ext}` | {spec.width}×{spec.height} | "
            f"{spec.frames} | {spec.wiring_mode} | {spec.data_in_corner} | {spec.description} |"
        )

    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


PATTERN_SPECS: List[PatternSpec] = [
    PatternSpec(
            filename="aurora_strip.bin",
            name="Aurora Strip",
            width=8,
            height=1,
            frames=6,
            wiring_mode="Row-major",
            data_in_corner="LT",
            style="gradient_horizontal",
            description="8 LED strip with a moving horizontal gradient pulse.",
        ),
    PatternSpec(
            filename="sunrise_matrix.bin",
            name="Sunrise Matrix",
            width=8,
            height=8,
            frames=10,
            wiring_mode="Serpentine",
            data_in_corner="LT",
            style="gradient_vertical",
            description="8×8 matrix using serpentine wiring with a vertical sunrise fade.",
        ),
    PatternSpec(
            filename="ocean_columns.bin",
            name="Ocean Columns",
            width=12,
            height=6,
            frames=8,
            wiring_mode="Column-major",
            data_in_corner="LB",
            style="ocean_current",
            description="Column-scanned 12×6 matrix with flowing cyan ocean currents.",
        ),
    PatternSpec(
            filename="meteor_curtain.bin",
            name="Meteor Curtain",
            width=16,
            height=9,
            frames=12,
            wiring_mode="Column-serpentine",
            data_in_corner="RT",
            style="vertical_stripes",
            description="16×9 display with column serpentine wiring and meteor streak stripes.",
        ),
    PatternSpec(
            filename="pulse_square.bin",
            name="Pulse Square",
            width=10,
            height=10,
            frames=5,
            wiring_mode="Row-major",
            data_in_corner="RB",
            style="center_pulse",
            description="Square panel pulsing from the centre outward, bottom-right data in.",
        ),
    PatternSpec(
            filename="sparkle_band.bin",
            name="Sparkle Band",
            width=20,
            height=5,
            frames=7,
            wiring_mode="Row-major",
            data_in_corner="RT",
            style="sparkle",
            description="Wide band with randomised sparkle pattern starting top-right.",
        ),
    PatternSpec(
            filename="swirl_matrix.bin",
            name="Swirl Matrix",
            width=6,
            height=6,
            frames=9,
            wiring_mode="Column-major",
            data_in_corner="LT",
            style="swirl",
            description="6×6 column-major panel with swirling hues for layout diagnostics.",
        ),
    PatternSpec(
            filename="cascade_tower.bin",
            name="Cascade Tower",
            width=4,
            height=16,
            frames=6,
            wiring_mode="Serpentine",
            data_in_corner="LB",
            style="fire_fall",
            description="Tall 4×16 serpentine tower featuring a cascading fire effect.",
        ),
    PatternSpec(
            filename="nebula_grid.bin",
            name="Nebula Grid",
            width=14,
            height=7,
            frames=11,
            wiring_mode="Row-major",
            data_in_corner="LB",
            style="diagonal_wave",
            description="Nebula-inspired diagonal wave across a 14×7 grid, bottom-left feed.",
        ),
    PatternSpec(
            filename="vortex_banner.bin",
            name="Vortex Banner",
            width=32,
            height=8,
            frames=16,
            wiring_mode="Column-serpentine",
            data_in_corner="RB",
            style="horizontal_stripes",
            description="Ultra-wide banner with alternating colour bands and RB entry point.",
    ),
]


def main() -> None:
    ensure_output_dir()

    for spec in PATTERN_SPECS:
        pattern = build_pattern(spec)
        target_path = OUTPUT_DIR / spec.filename
        export_pattern(pattern, target_path)

    write_doc(PATTERN_SPECS)
    print(f"Generated {len(PATTERN_SPECS)} pattern files in {OUTPUT_DIR}")
    print(f"Documentation written to {DOC_PATH}")


if __name__ == "__main__":
    main()

