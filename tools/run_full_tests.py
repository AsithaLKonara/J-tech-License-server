#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.media_converter import MediaConverter
from parsers.parser_registry import parse_pattern_file
from firmware.builder import FirmwareBuilder
from uploaders.uploader_registry import get_uploader


VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
PATTERN_EXT = {".bin", ".hex", ".dat", ".leds", ".ledproj"}


def scan_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in sorted(root.iterdir()):
        if not p.is_file():
            continue
        files.append(p)
    return files


def test_media_file(path: Path, width: int, height: int, fps: float) -> bool:
    mc = MediaConverter()
    t0 = time.time()
    pattern = mc.convert_to_pattern(str(path), target_width=width, target_height=height, fps=fps)
    dt = time.time() - t0
    print(f"[MEDIA] {path.name}: {pattern.frame_count} frames, {pattern.led_count} leds, {dt:.2f}s")
    ok, warns = pattern.validate()
    if not ok:
        print(f"  [WARN] Validation: {warns}")
    return True


def test_pattern_file(path: Path) -> bool:
    t0 = time.time()
    pattern = parse_pattern_file(str(path))
    dt = time.time() - t0
    print(f"[PATTERN] {path.name}: {pattern.frame_count} frames, {pattern.led_count} leds, {dt:.2f}s")
    ok, warns = pattern.validate()
    if not ok:
        print(f"  [WARN] Validation: {warns}")
    return True


def build_universal(pattern, chip: str) -> bool:
    fb = FirmwareBuilder()
    res = fb.build_universal_firmware(pattern, chip)
    if not res.success:
        print(f"  [ERROR] Universal build failed: {res.error_message}")
        return False
    print(f"  [OK] Universal firmware: {res.firmware_path} ({res.size_bytes} bytes)")
    return True


def try_upload(pattern, chip: str, port: str) -> bool:
    uploader = get_uploader(chip)
    if not uploader:
        print("  [SKIP] No uploader available for chip")
        return False
    # Build using uploader (may require external toolchains)
    try:
        build = uploader.build_firmware(pattern, {"output_dir": "build/test_upload", "gpio_pin": 2})
        if not build.success:
            print(f"  [ERROR] Build failed: {build.error_message}")
            return False
        print(f"  [OK] Build for upload: {build.firmware_path}")
        up = uploader.upload(build.firmware_path, {"port": port})
        if up.success:
            print(f"  [OK] Uploaded: {up.bytes_written} bytes")
            return True
        print(f"  [ERROR] Upload failed: {up.error_message}")
        return False
    except Exception as e:
        print(f"  [ERROR] Upload exception: {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns_dir", help="Path to patterns/media directory")
    ap.add_argument("--chip", default="esp8266", help="Chip id for build/upload (default: esp8266)")
    ap.add_argument("--port", default=None, help="Serial port for upload (e.g., COM3)")
    ap.add_argument("--width", type=int, default=64, help="Target width for media conversion")
    ap.add_argument("--height", type=int, default=32, help="Target height for media conversion")
    ap.add_argument("--fps", type=float, default=20.0, help="Target FPS for media conversion")
    ap.add_argument("--upload", action="store_true", help="Attempt upload after build (requires toolchains)")
    args = ap.parse_args()

    root = Path(args.patterns_dir)
    if not root.exists():
        print(f"[ERROR] Directory not found: {root}")
        sys.exit(1)

    files = scan_files(root)
    print(f"Testing {len(files)} file(s) in {root}")

    mc = MediaConverter()
    total_ok = 0
    total_err = 0

    for path in files:
        ext = path.suffix.lower()
        try:
            if ext in VIDEO_EXT or ext in IMAGE_EXT:
                # Convert media
                t0 = time.time()
                pattern = mc.convert_to_pattern(str(path), target_width=args.width, target_height=args.height, fps=args.fps)
                dt = time.time() - t0
                print(f"[MEDIA] {path.name}: {pattern.frame_count} frames, {pattern.led_count} leds, {dt:.2f}s")
            elif ext in PATTERN_EXT:
                t0 = time.time()
                pattern = parse_pattern_file(str(path))
                dt = time.time() - t0
                print(f"[PATTERN] {path.name}: {pattern.frame_count} frames, {pattern.led_count} leds, {dt:.2f}s")
            else:
                print(f"[SKIP] {path.name}")
                continue

            ok, warns = pattern.validate()
            if not ok:
                print(f"  [WARN] Validation: {warns}")

            # Build universal firmware always (toolchain-free)
            build_universal(pattern, args.chip)

            # Optional upload (requires Arduino CLI/esptool installed)
            if args.upload and args.port:
                try_upload(pattern, args.chip, args.port)

            total_ok += 1
        except Exception as e:
            print(f"[ERROR] {path.name}: {e}")
            total_err += 1

    print(f"Done. OK: {total_ok}, ERR: {total_err}")


if __name__ == "__main__":
    main()


