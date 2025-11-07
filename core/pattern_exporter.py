"""
Pattern Exporter - Export patterns to various formats
"""

import struct
from typing import TextIO
from core.pattern import Pattern, PatternMetadata, Frame


class PatternExporter:
    """Export Pattern objects to various file formats"""
    
    @staticmethod
    def export_binary(pattern: Pattern, filepath: str) -> bool:
        """
        Export pattern to standard binary format (.bin)
        
        Format:
        - Header: num_leds (2 bytes) + num_frames (2 bytes)
        - For each frame: delay_ms (2 bytes) + RGB data (3 * led_count bytes)
        """
        try:
            with open(filepath, 'wb') as f:
                # Write header
                num_leds = pattern.metadata.led_count
                num_frames = len(pattern.frames)
                
                f.write(struct.pack('<H', num_leds))  # LED count
                f.write(struct.pack('<H', num_frames))  # Frame count
                
                # Write frames
                for frame in pattern.frames:
                    # Write delay
                    delay_ms = max(1, min(frame.duration_ms, 65535))
                    f.write(struct.pack('<H', delay_ms))
                    
                    # Write RGB data
                    for pixel in frame.pixels:
                        r, g, b = pixel[0], pixel[1], pixel[2]
                        f.write(bytes([r, g, b]))
            
            return True
        except Exception as e:
            raise Exception(f"Failed to export binary: {e}")
    
    @staticmethod
    def export_hex(pattern: Pattern, filepath: str) -> bool:
        """
        Export pattern to Intel HEX format (.hex)
        """
        try:
            with open(filepath, 'w') as f:
                address = 0
                
                # Write header
                num_leds = pattern.metadata.led_count
                num_frames = len(pattern.frames)
                header_data = struct.pack('<HH', num_leds, num_frames)
                address = PatternExporter._write_hex_record(f, address, header_data)
                
                # Write frames
                for frame in pattern.frames:
                    # Write delay
                    delay_ms = max(1, min(frame.duration_ms, 65535))
                    delay_data = struct.pack('<H', delay_ms)
                    address = PatternExporter._write_hex_record(f, address, delay_data)
                    
                    # Write RGB data
                    for pixel in frame.pixels:
                        rgb_data = bytes([pixel[0], pixel[1], pixel[2]])
                        address = PatternExporter._write_hex_record(f, address, rgb_data)
                
                # Write end of file record
                f.write(':00000001FF\n')
            
            return True
        except Exception as e:
            raise Exception(f"Failed to export HEX: {e}")
    
    @staticmethod
    def _write_hex_record(f: TextIO, address: int, data: bytes) -> int:
        """Write a single Intel HEX record"""
        chunk_size = 16
        offset = 0
        
        while offset < len(data):
            chunk = data[offset:offset+chunk_size]
            byte_count = len(chunk)
            record_type = 0x00  # Data record
            
            # Calculate checksum
            checksum = byte_count
            checksum += (address >> 8) & 0xFF
            checksum += address & 0xFF
            checksum += record_type
            
            for byte in chunk:
                checksum += byte
            
            checksum = (~checksum + 1) & 0xFF
            
            # Write record
            f.write(f':{byte_count:02X}{address:04X}{record_type:02X}')
            for byte in chunk:
                f.write(f'{byte:02X}')
            f.write(f'{checksum:02X}\n')
            
            address += byte_count
            offset += chunk_size
        
        return address
    
    @staticmethod
    def export_leds(pattern: Pattern, filepath: str) -> bool:
        """
        Export pattern to LEDS text format (.leds)
        """
        try:
            with open(filepath, 'w') as f:
                # Write header comment
                f.write(f"# LEDS Pattern Export\n")
                f.write(f"# Name: {pattern.name}\n")
                f.write(f"# LEDs: {pattern.metadata.led_count}\n")
                f.write(f"# Frames: {len(pattern.frames)}\n")
                f.write(f"# Dimensions: {pattern.metadata.width}x{pattern.metadata.height}\n")
                f.write("\n")
                
                # Write frames
                for frame_idx, frame in enumerate(pattern.frames):
                    f.write(f"FRAME {frame_idx}\n")
                    f.write(f"DELAY {frame.duration_ms}\n")
                    
                    # Write pixels
                    for led_idx, pixel in enumerate(frame.pixels):
                        r, g, b = pixel[0], pixel[1], pixel[2]
                        f.write(f"LED {led_idx} {r} {g} {b}\n")
                    
                    f.write("\n")
            
            return True
        except Exception as e:
            raise Exception(f"Failed to export LEDS: {e}")
    
    @staticmethod
    def export_json(pattern: Pattern, filepath: str) -> bool:
        """
        Export pattern to JSON format (.json)
        """
        try:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise Exception(f"Failed to export JSON: {e}")
    
    @staticmethod
    def export_project(pattern: Pattern, filepath: str) -> bool:
        """Export pattern to project format (.ledproj)"""
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
            ("Intel HEX Format", "*.hex", PatternExporter.export_hex),
            ("LEDS Text Format", "*.leds", PatternExporter.export_leds),
            ("JSON Format", "*.json", PatternExporter.export_json),
            ("Project Format", "*.ledproj", PatternExporter.export_project),
        ]

