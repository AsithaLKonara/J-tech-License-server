"""
Comprehensive verification of all 16 wiring/corner combinations
Tests wiring_mapper.py logic for correctness
"""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from core.wiring_mapper import WiringMapper


WIRING_MODES: Tuple[str, ...] = (
    "Row-major",
    "Serpentine",
    "Column-major",
    "Column-serpentine",
)
DATA_CORNERS: Tuple[str, ...] = ("LT", "LB", "RT", "RB")


@dataclass(frozen=True)
class MappingResult:
    """Container for a single wiring+corner verification outcome."""

    width: int
    height: int
    wiring_mode: str
    data_corner: str
    checksum: str

    @property
    def key(self) -> str:
        return f"{self.wiring_mode}_{self.data_corner}"


def _generate_design_pixels(width: int, height: int) -> List[Tuple[int, int, int]]:
    """
    Create a deterministic set of RGB tuples where each LED position maps to a
    unique color. We encode the LED index directly in the RGB components so that
    even very large matrices remain collision-free.
    """
    total_leds = width * height
    pixels: List[Tuple[int, int, int]] = []
    for idx in range(total_leds):
        r = (idx >> 16) & 0xFF
        g = (idx >> 8) & 0xFF
        b = idx & 0xFF
        pixels.append((r, g, b))
    return pixels


def _validate_mapping(
    width: int,
    height: int,
    wiring_mode: str,
    data_corner: str,
    design_pixels: List[Tuple[int, int, int]],
    verbose: bool = False,
) -> MappingResult:
    """
    Validate a single wiring/corner combination and return the deterministic
    checksum. Raises ValueError if the mapping is invalid.
    """
    mapper = WiringMapper(width, height, wiring_mode, data_corner)
    hardware_pixels = mapper.design_to_hardware(design_pixels)

    total_leds = width * height
    if len(hardware_pixels) != total_leds:
        raise ValueError(
            f"{wiring_mode} + {data_corner}: expected {total_leds} pixels, "
            f"got {len(hardware_pixels)}"
        )

    mapping = mapper._build_mapping_table()
    if len(mapping) != total_leds:
        raise ValueError(
            f"{wiring_mode} + {data_corner}: mapping table incorrect length "
            f"{len(mapping)} (expected {total_leds})"
        )

    if sorted(mapping) != list(range(total_leds)):
        raise ValueError(
            f"{wiring_mode} + {data_corner}: mapping table is not a permutation "
            f"of 0..{total_leds-1}"
        )

    # Confirm the hardware pixels align with the mapping table
    for hw_idx, design_idx in enumerate(mapping):
        expected_pixel = design_pixels[design_idx]
        actual_pixel = hardware_pixels[hw_idx]
        if expected_pixel != actual_pixel:
            raise ValueError(
                f"{wiring_mode} + {data_corner}: mismatch at hardware index "
                f"{hw_idx} (design idx {design_idx})"
            )

    flat_bytes = bytes([c for rgb in hardware_pixels for c in rgb])
    checksum = hashlib.sha256(flat_bytes).hexdigest()[:16]

    if verbose:
        print(f"  ✓ {wiring_mode:20s} + {data_corner:2s} → checksum {checksum}")

    return MappingResult(width, height, wiring_mode, data_corner, checksum)


def verify_matrix_size(
    width: int,
    height: int,
    wiring_modes: Iterable[str] = WIRING_MODES,
    data_corners: Iterable[str] = DATA_CORNERS,
    verbose: bool = False,
) -> Dict[str, MappingResult]:
    """
    Verify every wiring/data-corner combination for the specified matrix size.
    Returns a dictionary of MappingResult keyed by "<wiring>_<corner>".
    """
    if width < 1 or height < 1:
        raise ValueError(f"Invalid matrix size: {width}x{height}")

    design_pixels = _generate_design_pixels(width, height)
    results: Dict[str, MappingResult] = {}

    if verbose:
        print("=" * 80)
        print(f"Matrix {width}×{height} → {width * height} LEDs")
        print("=" * 80)

    for wiring_mode in wiring_modes:
        for data_corner in data_corners:
            result = _validate_mapping(
                width,
                height,
                wiring_mode,
                data_corner,
                design_pixels,
                verbose=verbose,
            )
            results[result.key] = result

    checksums = [result.checksum for result in results.values()]
    if len(checksums) != len(set(checksums)):
        message = (
            f"{width}x{height}: duplicate checksums detected across wiring combinations"
        )
        if width * height > 1:
            raise ValueError(message)
        if verbose:
            print(f"  ⚠ {message} (expected for single-LED matrices)")

    return results


def sweep_square_sizes(
    min_size: int,
    max_size: int,
    verbose: bool = False,
) -> Dict[Tuple[int, int], Dict[str, MappingResult]]:
    """
    Sweep square matrices from min_size×min_size through max_size×max_size.
    Returns nested dictionaries keyed by (width, height) then "<wiring>_<corner>".
    """
    if min_size > max_size:
        raise ValueError(f"min_size ({min_size}) cannot be greater than max_size ({max_size})")

    all_results: Dict[Tuple[int, int], Dict[str, MappingResult]] = {}
    total_combinations = (max_size - min_size + 1) * len(WIRING_MODES) * len(DATA_CORNERS)

    print("=" * 80)
    print(
        f"SWEEPING MATRIX SIZES {min_size}×{min_size} → {max_size}×{max_size} "
        f"({total_combinations} combinations)"
    )
    print("=" * 80)

    failures: List[Tuple[int, int, str]] = []

    for size in range(min_size, max_size + 1):
        try:
            results = verify_matrix_size(size, size, verbose=verbose)
            all_results[(size, size)] = results
            print(f"✓ {size:2d}×{size:2d}: all 16 wiring combinations validated")
        except Exception as exc:  # pragma: no cover - diagnostic output path
            print(f"❌ {size:2d}×{size:2d}: {exc}")
            failures.append((size, size, str(exc)))

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    tested = (max_size - min_size + 1)
    print(f"Matrix sizes tested: {tested}")
    print(f"Total combinations: {total_combinations}")
    print(f"Failures: {len(failures)}")

    if failures:
        print("\nFailure details:")
        for width, height, message in failures:
            print(f"  - {width}×{height}: {message}")
    else:
        print("\nAll wiring/corner combinations passed for every matrix size.")

    return all_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify wiring mapper logic across all 16 wiring combinations.",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Width of the matrix to test (requires --height).",
    )
    parser.add_argument(
        "--height",
        type=int,
        help="Height of the matrix to test (requires --width).",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=None,
        help="Minimum square size to sweep (e.g., 1 for 1×1).",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=None,
        help="Maximum square size to sweep (e.g., 50 for 50×50).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output for every wiring/corner combination.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if (args.width is None) ^ (args.height is None):
        raise SystemExit("Both --width and --height must be provided together.")

    if args.width and args.height:
        verify_matrix_size(args.width, args.height, verbose=args.verbose)
        return

    min_size = args.min_size if args.min_size is not None else 4
    max_size = args.max_size if args.max_size is not None else 4

    sweep_square_sizes(min_size, max_size, verbose=args.verbose)


if __name__ == "__main__":
    main()

