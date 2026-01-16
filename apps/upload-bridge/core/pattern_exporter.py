"""
Pattern Exporter - Export patterns to various formats
"""

from typing import Optional

from core.pattern import Pattern
from core.export_options import ExportOptions
from core.export.encoders import (
    build_binary_payload,
    build_dat_payload,
    build_intel_hex,
    build_c_header,
    encode_frame_bytes,
    bytes_per_pixel,
)


class PatternExporter:
    """Export Pattern objects to various file formats"""
    
    @staticmethod
    def export_binary(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export pattern to standard binary format (.bin)
        
        Format:
        - Header: num_leds (2 bytes) + num_frames (2 bytes)
        - For each frame: delay_ms (2 bytes) + RGB data (3 * led_count bytes)
        """
        try:
            payload = build_binary_payload(pattern, options)
            with open(filepath, "wb") as f:
                f.write(payload)
            return True
        except Exception as e:
            raise Exception(f"Failed to export binary: {e}")
    
    @staticmethod
    def export_hex(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export pattern to Intel HEX format (.hex)
        """
        try:
            payload = build_intel_hex(pattern, options)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(payload)
            return True
        except Exception as e:
            raise Exception(f"Failed to export HEX: {e}")

    @staticmethod
    def export_dat(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export pattern to Upload Bridge DAT format (.dat) with metadata header.
        """
        try:
            payload = build_dat_payload(pattern, options)
            with open(filepath, "wb") as f:
                f.write(payload)
            return True
        except Exception as e:
            raise Exception(f"Failed to export DAT: {e}")
    
    @staticmethod
    def export_leds(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export pattern to LEDS text format (.leds)
        """
        opts = options or ExportOptions()
        
        try:
            with open(filepath, 'w') as f:
                # Write header comment
                f.write(f"# LEDS Pattern Export\n")
                f.write(f"# Name: {pattern.name}\n")
                f.write(f"# LEDs: {pattern.metadata.led_count}\n")
                f.write(f"# Frames: {len(pattern.frames)}\n")
                f.write(f"# Dimensions: {pattern.metadata.width}x{pattern.metadata.height}\n")
                f.write(f"# Export Options: RGB={opts.rgb_order}, ColorSpace={opts.color_space}\n")
                f.write("\n")
                
                bpp = bytes_per_pixel(opts)
                expected_leds = pattern.metadata.width * pattern.metadata.height

                # Write frames
                for frame_idx, frame in enumerate(pattern.frames):
                    f.write(f"FRAME {frame_idx}\n")
                    f.write(f"DELAY {frame.duration_ms}\n")

                    encoded = encode_frame_bytes(pattern, frame, opts)
                    for led_idx in range(expected_leds):
                        start = led_idx * bpp
                        chunk = encoded[start:start + bpp]
                        if len(chunk) < bpp:
                            chunk = chunk + bytes([0] * (bpp - len(chunk)))

                        if opts.color_space == "RGB565":
                            value = chunk[0] | (chunk[1] << 8)
                            f.write(f"LED {led_idx} {opts.format_number(value, 2)}\n")
                        else:  # RGB888 or trimmed variants
                            values = " ".join(str(byte) for byte in chunk)
                            f.write(f"LED {led_idx} {values}\n")

                    f.write("\n")
            
            return True
        except Exception as e:
            raise Exception(f"Failed to export LEDS: {e}")

    @staticmethod
    def export_header(
        pattern: Pattern,
        filepath: str,
        options: Optional[ExportOptions] = None,
        array_basename: Optional[str] = None,
    ) -> bool:
        """
        Export pattern as a C header (.h) with PROGMEM frame arrays.
        """
        try:
            base = array_basename or pattern.name or "Pattern"
            sanitized = "".join(ch if ch.isalnum() else "_" for ch in base)
            if not sanitized:
                sanitized = "Pattern"
            header_text = build_c_header(pattern, options, array_basename=sanitized)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header_text)
            return True
        except Exception as e:
            raise Exception(f"Failed to export header: {e}")
    
    @staticmethod
    def export_json(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """
        Export pattern to JSON format (.json)
        """
        if options is None:
            options = ExportOptions()
        
        try:
            import json
            # Note: JSON export doesn't apply advanced options, but we include them in metadata
            pattern_dict = pattern.to_dict()
            pattern_dict["export_options"] = {
                "rgb_order": options.rgb_order,
                "color_space": options.color_space,
                "scan_direction": options.scan_direction,
                "serpentine": options.serpentine
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pattern_dict, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise Exception(f"Failed to export JSON: {e}")
    
    @staticmethod
    def export_project(pattern: Pattern, filepath: str, options: Optional[ExportOptions] = None) -> bool:
        """Export pattern to project format (.ledproj)"""
        # Project format doesn't use advanced options
        try:
            pattern.save_to_file(filepath)
            return True
        except Exception as e:
            raise Exception(f"Failed to export project: {e}")
    
    @staticmethod
    def get_export_formats() -> list:
        """Get list of supported export formats"""
        return [
            ("Binary Format", "*.bin", PatternExporter.export_binary),
            ("DAT Format", "*.dat", PatternExporter.export_dat),
            ("Intel HEX Format", "*.hex", PatternExporter.export_hex),
            ("C Header (PROGMEM)", "*.h", PatternExporter.export_header),
            ("LEDS Text Format", "*.leds", PatternExporter.export_leds),
            ("JSON Format", "*.json", PatternExporter.export_json),
            ("Project Format", "*.ledproj", PatternExporter.export_project),
        ]

