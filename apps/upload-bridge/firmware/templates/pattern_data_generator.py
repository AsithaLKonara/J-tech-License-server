"""
Pattern Data Generator - Generate pattern_data.h from Pattern objects

Converts Pattern objects to C header files for embedded firmware.
"""

from pathlib import Path
from typing import Optional

from core.pattern import Pattern


def generate_pattern_data_header(
    pattern: Pattern,
    output_path: Path,
    chip_id: Optional[str] = None
) -> None:
    """
    Generate pattern_data.h from Pattern object.
    
    Args:
        pattern: Pattern object
        output_path: Path to save pattern_data.h
        chip_id: Optional chip ID for chip-specific optimizations
    """
    width = pattern.metadata.width
    height = pattern.metadata.height
    led_count = width * height
    frame_count = len(pattern.frames)
    
    # Build header file content
    lines = [
        "/* Pattern Data Header - Auto-generated */",
        f"/* Pattern: {pattern.name} */",
        f"/* Dimensions: {width}x{height} ({led_count} LEDs) */",
        f"/* Frames: {frame_count} */",
        "",
        "#ifndef PATTERN_DATA_H",
        "#define PATTERN_DATA_H",
        "",
        "#include <stdint.h>",
        "#include <FastLED.h>",
        "",
        f"#define LED_COUNT {led_count}",
        f"#define FRAME_COUNT {frame_count}",
        f"#define MATRIX_WIDTH {width}",
        f"#define MATRIX_HEIGHT {height}",
        "",
        "// Frame durations (milliseconds)",
        f"static const uint16_t frame_durations[{frame_count}] PROGMEM = {{",
    ]
    
    # Add frame durations
    durations = [str(frame.duration_ms) for frame in pattern.frames]
    lines.append("    " + ", ".join(durations) + ",")
    lines.append("};")
    lines.append("")
    
    # Add frame pixel data
    lines.append("// Frame pixel data")
    for frame_idx, frame in enumerate(pattern.frames):
        lines.append(f"// Frame {frame_idx}")
        lines.append(f"static const CRGB frame_{frame_idx}[LED_COUNT] PROGMEM = {{")
        
        # Format pixels as CRGB values
        pixel_lines = []
        for i in range(0, len(frame.pixels), 8):  # 8 pixels per line
            pixel_chunk = frame.pixels[i:i+8]
            pixel_strs = [
                f"CRGB({p[0]}, {p[1]}, {p[2]})"
                for p in pixel_chunk
            ]
            pixel_lines.append("    " + ", ".join(pixel_strs) + ",")
        
        lines.extend(pixel_lines)
        lines.append("};")
        lines.append("")
    
    # Add frames array
    lines.append("// Frames array")
    lines.append("static const CRGB* const frames[FRAME_COUNT] PROGMEM = {")
    frame_refs = [f"frame_{i}" for i in range(frame_count)]
    lines.append("    " + ", ".join(frame_refs) + ",")
    lines.append("};")
    lines.append("")
    lines.append("#endif // PATTERN_DATA_H")
    
    # Write header file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

