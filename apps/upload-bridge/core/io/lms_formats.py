from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from core.dimension_scorer import score_dimensions

from core.automation import LayerBinding, LMSInstruction, PatternInstruction, PatternInstructionSequence


class LMSFormatError(RuntimeError):
    """Raised when an LMS import/export operation fails."""


# ---------------------------------------------------------------------------
# DAT helpers
# ---------------------------------------------------------------------------

def detect_dat_header(lines: Iterable[str]) -> Tuple[int, int, int]:
    """
    Parse the DAT header (width, height, frame count).
    """
    cleaned = [line.strip() for line in lines if line.strip()]
    if len(cleaned) < 2:
        raise LMSFormatError("DAT file missing header rows")
    try:
        width_str, height_str = cleaned[0].split()
        width = int(width_str)
        height = int(height_str)
        frame_count = int(cleaned[1])
    except ValueError as exc:
        raise LMSFormatError(f"Invalid DAT header: {cleaned[:2]}") from exc
    if width <= 0 or height <= 0 or frame_count <= 0:
        raise LMSFormatError("DAT header values must be greater than zero")
    return width, height, frame_count


def parse_dat_file(path: Path) -> Dict[str, object]:
    """
    Read LMS DAT export, returning metadata plus raw hex rows.
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    width, height, frame_count = detect_dat_header(lines)
    data_rows = [line.strip() for line in lines[2:] if line.strip()]
    return {
        "format": "DAT",
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "color_space": "RGB32",
        # DAT exports from LED Matrix Studio do not encode wiring or color order explicitly.
        # We leave these as generic/unknown so downstream detectors or user inputs can refine them.
        "color_order": "RGB",
        "bit_packing": "8-bit",
        "serpentine": None,
        "orientation": None,
        "metadata_source": "dat_header",
        "rows": data_rows,
    }


# ---------------------------------------------------------------------------
# HEX helpers
# ---------------------------------------------------------------------------

def _parse_hex_record(line: str) -> Tuple[int, int, int, bytes]:
    if not line.startswith(":"):
        raise LMSFormatError("Invalid HEX line (missing colon)")
    line = line.strip()
    try:
        byte_count = int(line[1:3], 16)
        address = int(line[3:7], 16)
        record_type = int(line[7:9], 16)
        data = bytes.fromhex(line[9:-2])
    except ValueError as exc:
        raise LMSFormatError(f"Malformed HEX row: {line}") from exc
    checksum = int(line[-2:], 16)
    computed = ((byte_count + (address >> 8) + (address & 0xFF) + record_type + sum(data)) & 0xFF)
    computed = ((~computed + 1) & 0xFF)
    if checksum != computed:
        raise LMSFormatError(f"Checksum mismatch for HEX row {line}")
    return byte_count, address, record_type, data


def detect_hex_layout(lines: Iterable[str], guess_bytes_per_pixel: Optional[int] = None) -> Dict[str, object]:
    """
    Inspect Intel HEX lines to infer byte packing, width, and approximate height.
    """
    record_lengths: List[int] = []
    total_payload_bytes = 0
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        byte_count, _, record_type, data = _parse_hex_record(line)
        if record_type != 0:
            continue
        record_lengths.append(byte_count)
        total_payload_bytes += len(data)

    if not record_lengths:
        raise LMSFormatError("HEX file contained no data records")

    most_common_len = Counter(record_lengths).most_common(1)[0][0]
    bytes_per_pixel = guess_bytes_per_pixel
    if bytes_per_pixel is None:
        if most_common_len % 3 == 0:
            bytes_per_pixel = 3
            color_space = "RGB32"
        elif most_common_len % 2 == 0:
            bytes_per_pixel = 2
            color_space = "RGB565"
        else:
            bytes_per_pixel = 1
            color_space = "RGB3"
    else:
        color_space = "RGB32" if bytes_per_pixel == 3 else "RGB565"

    width = max(1, most_common_len // bytes_per_pixel)
    total_pixels = total_payload_bytes // bytes_per_pixel
    height = 1
    frame_count = total_pixels // width if width else total_pixels
    if frame_count == 0:
        frame_count = 1

    return {
        "format": "HEX",
        "bytes_per_pixel": bytes_per_pixel,
        "color_space": color_space,
        "width": width,
        "height": height,
        "frame_count": frame_count,
        # HEX payloads do not encode wiring or color order; we treat them as unknown and rely
        # on higher-level detectors (e.g. file_format_detector) plus user presets.
        "color_order": "RGB",
        "bit_packing": f"{bytes_per_pixel * 8}-bit",
        "serpentine": None,
        "orientation": None,
        "metadata_source": "hex_layout_inference",
    }


def parse_hex_file(path: Path, guess_bytes_per_pixel: Optional[int] = None) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    layout = detect_hex_layout(lines, guess_bytes_per_pixel)
    layout["raw_lines"] = [line.strip() for line in lines if line.strip()]
    return layout


# ---------------------------------------------------------------------------
# BIN helpers
# ---------------------------------------------------------------------------

def parse_bin_stream(data: bytes, width: Optional[int] = None, height: Optional[int] = None, bytes_per_pixel: int = 3) -> Dict[str, object]:
    layout_confidence: Optional[float] = None
    if width is None or height is None:
        # Use shared dimension scorer so BIN inference stays consistent with the rest of
        # the system (file_open → auto-detect → preview flows).
        inferred_w, inferred_h, inferred_frames, confidence = score_dimensions(
            data,
            bytes_per_pixel=bytes_per_pixel,
            include_strips=True,
            preferred_led_counts=None,
        )
        width = width or inferred_w
        height = height or inferred_h
        layout_confidence = confidence
    else:
        # When explicit dimensions are provided, we can still compute an approximate
        # confidence for diagnostics if desired.
        total_pixels = len(data) // bytes_per_pixel
        if total_pixels > 0:
            _, _, _, confidence = score_dimensions(
                data,
                bytes_per_pixel=bytes_per_pixel,
                include_strips=True,
                preferred_led_counts=None,
            )
            layout_confidence = confidence

    frame_size = width * height * bytes_per_pixel  # type: ignore[arg-type]
    if frame_size == 0:
        raise LMSFormatError("BIN frame size resolved to zero")
    frame_count = len(data) // frame_size
    return {
        "format": "BIN",
        "width": width,
        "height": height,
        "frame_count": frame_count,
        "bytes_per_pixel": bytes_per_pixel,
        "color_space": "RGB32" if bytes_per_pixel == 3 else "RGB565",
        # BIN blobs similarly lack explicit wiring/color metadata; treat these as unknown
        # so callers know further detection or manual confirmation is required.
        "color_order": "RGB",
        "bit_packing": f"{bytes_per_pixel * 8}-bit",
        "serpentine": None,
        "orientation": None,
        "metadata_source": "bin_layout_inference",
        "layout_confidence": layout_confidence,
        "payload": data,
    }


# ---------------------------------------------------------------------------
# LEDS helpers
# ---------------------------------------------------------------------------

_METADATA_PATTERN = re.compile(r"#\s*(?P<key>[\w\s]+):\s*(?P<value>.+)")


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "on"}


def _normalize_slot(token: str) -> str:
    token = token.strip()
    return token if token and token.upper() != "NULL" else "NULL"


def parse_leds_file(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    metadata: Dict[str, object] = {}
    data_section: List[str] = []
    instructions: List[PatternInstruction] = []
    in_data = False
    pattern_index = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            match = _METADATA_PATTERN.match(line)
            if match:
                key = match.group("key").strip().lower()
                value = match.group("value").strip()
                metadata[key] = value
            continue
        if line.lower().startswith("data:"):
            in_data = True
            continue
        if in_data:
            data_section.append(line)
            continue
        if line.lower().startswith("pattern"):
            pattern_index += 1
            _, payload = line.split(":", 1)
            parts = [part.strip() for part in payload.split(",")]
            if len(parts) < 5:
                raise LMSFormatError(f"Invalid pattern instruction line: {line}")
            source = _normalize_slot(parts[0])
            code = parts[1]
            layer2 = _normalize_slot(parts[2])
            mask = _normalize_slot(parts[3])
            try:
                repeat = int(parts[4])
            except ValueError as exc:
                raise LMSFormatError(f"Invalid repeat count in line: {line}") from exc

            # Optional extended metadata for gap/parameters, stored as comment keys:
            #   # pattern1_gap: 4
            #   # pattern1_params: {"speed": 2, "direction": "reverse"}
            gap_key = f"pattern{pattern_index}_gap"
            params_key = f"pattern{pattern_index}_params"
            gap = 0
            params: Dict[str, object] = {}
            if gap_key in metadata:
                try:
                    gap = int(metadata[gap_key])
                except (TypeError, ValueError):
                    gap = 0
            if params_key in metadata:
                try:
                    raw_params = metadata[params_key]
                    if isinstance(raw_params, str):
                        params = json.loads(raw_params)
                    elif isinstance(raw_params, dict):
                        params = raw_params
                except (json.JSONDecodeError, TypeError, ValueError):
                    params = {}

            binding = LayerBinding(slot=source, frame_index=None)
            layer2_binding = LayerBinding(slot=layer2, frame_index=None) if layer2 != "NULL" else None
            mask_binding = LayerBinding(slot=mask, frame_index=None) if mask != "NULL" else None
            instruction = LMSInstruction(code=code, repeat=repeat, parameters=params, gap=gap)
            instructions.append(
                PatternInstruction(
                    source=binding,
                    instruction=instruction,
                    layer2=layer2_binding,
                    mask=mask_binding,
                )
            )

    sequence = PatternInstructionSequence(instructions)
    return {
        "format": "LEDS",
        "metadata": metadata,
        "sequence": sequence,
        "data": data_section,
    }


def write_leds_file(
    path: Path,
    pattern_metadata: Dict[str, object],
    sequence: PatternInstructionSequence,
    frame_data: Optional[Iterable[str]] = None,
) -> None:
    lines: List[str] = []
    lines.append("# LED Matrix Studio Export")

    def _write_meta(key: str, value: object) -> None:
        lines.append(f"# {key}: {value}")

    _write_meta("Width", pattern_metadata.get("width"))
    _write_meta("Height", pattern_metadata.get("height"))
    _write_meta("Frames", pattern_metadata.get("frames"))
    _write_meta("Format", pattern_metadata.get("format", "RGB32"))
    _write_meta("Serpentine", pattern_metadata.get("serpentine", False))
    _write_meta("Orientation", pattern_metadata.get("orientation", "RowLeftToRight"))
    _write_meta("Color Order", pattern_metadata.get("color_order", "RGB"))

    # Persist optional per-instruction gap and parameters in comment metadata so that
    # Upload Bridge can round-trip them without breaking LED Matrix Studio compatibility.
    for idx, instruction in enumerate(sequence, start=1):
        if instruction.instruction.gap:
            _write_meta(f"pattern{idx}_gap", instruction.instruction.gap)
        if instruction.instruction.parameters:
            try:
                params_json = json.dumps(instruction.instruction.parameters)
            except TypeError:
                # Fallback: string representation if parameters are not fully JSON-serializable
                params_json = str(instruction.instruction.parameters)
            _write_meta(f"pattern{idx}_params", params_json)

    for idx, instruction in enumerate(sequence, start=1):
        source = instruction.source.slot
        layer2 = instruction.layer2.slot if instruction.layer2 else "NULL"
        mask = instruction.mask.slot if instruction.mask else "NULL"
        repeat = instruction.instruction.repeat
        code = instruction.instruction.code
        lines.append(f"Pattern{idx}: {source}, {code}, {layer2}, {mask}, {repeat}")

    lines.append("Data:")
    if frame_data:
        lines.extend(frame_data)
    else:
        lines.append("# (frame data omitted)")

    path.write_text("\n".join(lines), encoding="utf-8")


