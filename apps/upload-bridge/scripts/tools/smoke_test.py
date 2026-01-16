#!/usr/bin/env python3
"""
Smoke test: build minimal patterns, generate firmware headers (no compilation),
and validate WiFi binary conversion.
"""
from __future__ import annotations

import os
from pathlib import Path

import sys
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.pattern import create_solid_color_pattern, create_test_pattern
from firmware.builder import FirmwareBuilder
from wifi_upload.upload_bridge_wifi_uploader import UploadBridgeWiFiUploader


def assert_file_contains(path: Path, token: str):
    assert path.exists(), f"Missing file: {path}"
    text = path.read_text(encoding="utf-8", errors="ignore")
    assert token in text, f"'{token}' not found in {path}"


def test_universal_headers():
    # Create small patterns
    pattern_strip = create_solid_color_pattern(led_count=16, color=(255, 0, 0), duration_ms=50, name="Strip Red")
    pattern_matrix = create_test_pattern(led_count=64, frame_count=5)  # 8x8 assumption in preview

    fb = FirmwareBuilder()

    # Generate for esp8266 (arduino template)
    result_esp = fb.build_universal_firmware(pattern_strip, "esp8266")
    assert result_esp.success, f"ESP8266 universal build failed: {result_esp.error_message}"
    pd_esp = Path(result_esp.firmware_path).with_name("pattern_data.h")
    assert_file_contains(pd_esp, "#define LED_COUNT 16")
    assert_file_contains(pd_esp, "#define FRAME_COUNT 1")

    # Generate for atmega328p (C template)
    result_avr = fb.build_universal_firmware(pattern_matrix, "atmega328p")
    assert result_avr.success, f"AVR universal build failed: {result_avr.error_message}"
    pd_avr = Path(result_avr.firmware_path).with_name("pattern_data.h")
    assert_file_contains(pd_avr, "#define LED_COUNT 64")
    assert_file_contains(pd_avr, "#define FRAME_COUNT 5")


def test_wifi_binary_conversion():
    pattern = create_test_pattern(led_count=10, frame_count=3)
    uploader = UploadBridgeWiFiUploader()
    worker = uploader  # reuse conversion through UploadBridgeWiFiUploader by constructing WiFiUploadWorker indirectly

    # Use the same conversion logic as WiFi worker
    # We access the method via a temporary worker instance
    from wifi_upload.upload_bridge_wifi_uploader import WiFiUploadWorker

    w = WiFiUploadWorker(pattern, esp_ip="192.168.4.1")
    data = w.convert_pattern_to_binary()
    assert data is not None and len(data) > 0, "WiFi binary conversion returned empty"

    # Validate header (LEDs, frames as little-endian)
    num_leds = int.from_bytes(data[0:2], "little")
    num_frames = int.from_bytes(data[2:4], "little")
    assert num_leds == 10, f"Header LED count mismatch: {num_leds}"
    assert num_frames == 3, f"Header frame count mismatch: {num_frames}"


def main():
    test_universal_headers()
    test_wifi_binary_conversion()
    print("Smoke tests passed.")


if __name__ == "__main__":
    main()


