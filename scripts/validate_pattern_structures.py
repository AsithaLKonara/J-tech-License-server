"""
Validate legacy and newly generated pattern files to ensure metadata detection
remains consistent across formats.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parsers.parser_registry import parse_pattern_file
from scripts.generate_test_patterns import PATTERN_SPECS, OUTPUT_DIR


ALLOWED_EXTS = {".bin", ".dat", ".leds", ".hex", ".json", ".ledproj"}


@dataclass
class PatternReport:
    path: Path
    width: int
    height: int
    frames: int
    wiring_mode: str
    data_in_corner: str
    confidence: float
    source_format: str


def inspect_pattern(path: Path) -> PatternReport:
    pattern = parse_pattern_file(str(path))
    metadata = pattern.metadata
    return PatternReport(
        path=path,
        width=metadata.width,
        height=metadata.height,
        frames=pattern.frame_count,
        wiring_mode=getattr(metadata, "wiring_mode", "unknown"),
        data_in_corner=getattr(metadata, "data_in_corner", "unknown"),
        confidence=float(getattr(metadata, "dimension_confidence", 0.0) or 0.0),
        source_format=getattr(metadata, "source_format", path.suffix.lstrip(".")),
    )


def gather_legacy_patterns() -> List[PatternReport]:
    legacy_dir = Path("patterns")
    reports: List[PatternReport] = []
    for item in sorted(legacy_dir.iterdir()):
        if not item.is_file() or item.parent.name == OUTPUT_DIR.name:
            continue
        if item.suffix.lower() not in ALLOWED_EXTS:
            continue
        reports.append(inspect_pattern(item))
    return reports


def validate_generated_patterns() -> Tuple[List[PatternReport], List[str]]:
    reports: List[PatternReport] = []
    mismatches: List[str] = []
    for spec in PATTERN_SPECS:
        target = OUTPUT_DIR / spec.filename
        if not target.exists():
            mismatches.append(f"Missing generated file: {target}")
            continue
        report = inspect_pattern(target)
        reports.append(report)

        expected_leds = spec.width * spec.height
        detected_leds = report.width * report.height
        if detected_leds != expected_leds:
            mismatches.append(
                f"{spec.filename}: expected {expected_leds} LEDs "
                f"({spec.width}×{spec.height}), detected "
                f"{detected_leds} LEDs ({report.width}×{report.height})"
            )
        if report.frames != spec.frames:
            mismatches.append(
                f"{spec.filename}: expected {spec.frames} frames, detected {report.frames}"
            )
    return reports, mismatches


def print_report(title: str, reports: List[PatternReport]) -> None:
    if not reports:
        print(f"{title}: none found")
        return
    print(f"\n{title}:")
    print("-" * len(title))
    for report in reports:
        print(
            f"{report.path.name:>20} | {report.width:>4}×{report.height:<4} | "
            f"frames={report.frames:<5} | wiring={report.wiring_mode:<17} | "
            f"corner={report.data_in_corner:<2} | confidence={report.confidence:0.2f}"
        )


def main() -> None:
    legacy_reports = gather_legacy_patterns()
    generated_reports, mismatches = validate_generated_patterns()

    print_report("Legacy Patterns", legacy_reports)
    print_report("Generated Patterns", generated_reports)

    if mismatches:
        print("\nMismatches detected:")
        for issue in mismatches:
            print(f" - {issue}")
        raise SystemExit(1)

    print("\nAll generated patterns matched expected dimensions and frame counts.")


if __name__ == "__main__":
    main()

