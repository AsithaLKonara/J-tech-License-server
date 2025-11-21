"""
Pattern JSON Converter - Converts between Pattern objects and JSON schema format

Provides conversion utilities for the canonical pattern JSON schema v1.0,
including RLE compression for pixel data.
"""

import base64
import json
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from core.pattern import Pattern, Frame, PatternMetadata
from core.schemas.pattern_schema_v1 import (
    PATTERN_SCHEMA_V1,
    validate_pattern_json,
    PatternSchemaError,
)


class PatternConverter:
    """Converts Pattern objects to/from canonical JSON schema format"""
    
    @staticmethod
    def encode_pixels_rle(pixels: List[Tuple[int, int, int]]) -> str:
        """
        Encode pixel array using Run-Length Encoding (RLE) with base64.
        
        Format: [run_length, r, g, b, run_length, r, g, b, ...]
        
        Args:
            pixels: List of RGB tuples [(R, G, B), ...]
            
        Returns:
            Base64-encoded RLE compressed string
        """
        if not pixels:
            return ""
        
        encoded = bytearray()
        current_pixel = pixels[0]
        run_length = 1
        
        for pixel in pixels[1:]:
            if pixel == current_pixel and run_length < 255:
                run_length += 1
            else:
                # Write run
                encoded.append(min(run_length, 255))
                encoded.extend(current_pixel)
                # Start new run
                current_pixel = pixel
                run_length = 1
        
        # Write final run
        encoded.append(min(run_length, 255))
        encoded.extend(current_pixel)
        
        return base64.b64encode(encoded).decode('ascii')
    
    @staticmethod
    def decode_pixels_rle(encoded: str, pixel_count: int) -> List[Tuple[int, int, int]]:
        """
        Decode base64 RLE-encoded pixel data.
        
        Args:
            encoded: Base64-encoded RLE string
            pixel_count: Expected number of pixels
            
        Returns:
            List of RGB tuples
        """
        if not encoded:
            return [(0, 0, 0)] * pixel_count
        
        decoded = base64.b64decode(encoded)
        pixels = []
        i = 0
        
        while i < len(decoded) and len(pixels) < pixel_count:
            run_length = decoded[i]
            if i + 4 > len(decoded):
                break
            r, g, b = decoded[i + 1], decoded[i + 2], decoded[i + 3]
            pixels.extend([(r, g, b)] * run_length)
            i += 4
        
        # Pad if necessary
        while len(pixels) < pixel_count:
            pixels.append((0, 0, 0))
        
        return pixels[:pixel_count]
    
    @staticmethod
    def pattern_to_json(pattern: Pattern, use_rle: bool = True) -> Dict[str, Any]:
        """
        Convert Pattern object to canonical JSON schema format.
        
        Args:
            pattern: Pattern object to convert
            use_rle: Whether to use RLE compression for pixels
            
        Returns:
            Pattern JSON dictionary
        """
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Convert frames with layers
        frames_json = []
        for idx, frame in enumerate(pattern.frames):
            # Get composite pixels (from layer manager if available, else frame pixels)
            pixels = frame.pixels
            
            # Create default layer
            layer_data = {
                "id": str(uuid.uuid4()),
                "name": "base",
                "opacity": 1.0,
                "blend_mode": "normal",
                "visible": True,
                "encoding": "rle+rgba8" if use_rle else "raw+rgb8"
            }
            
            if use_rle:
                layer_data["pixels"] = PatternConverter.encode_pixels_rle(pixels)
            else:
                layer_data["pixels"] = [[int(r), int(g), int(b)] for r, g, b in pixels]
            
            frame_data = {
                "index": idx,
                "duration_ms": frame.duration_ms,
                "layers": [layer_data]
            }
            frames_json.append(frame_data)
        
        # Convert effects from LMS instructions if available
        effects_json = []
        if hasattr(pattern, 'lms_pattern_instructions') and pattern.lms_pattern_instructions:
            for instruction in pattern.lms_pattern_instructions:
                effect_type = instruction.get('action', 'scroll')
                effects_json.append({
                    "id": str(uuid.uuid4()),
                    "type": effect_type,
                    "parameters": instruction.get('params', {}),
                    "frame_range": instruction.get('frame_range')
                })
        
        # Build JSON structure
        pattern_json = {
            "schema_version": "1.0",
            "id": pattern.id,
            "name": pattern.name,
            "description": "",
            "tags": [],
            "created_at": now,
            "modified_at": now,
            "matrix": {
                "width": pattern.metadata.width,
                "height": pattern.metadata.height,
                "layout": "row_major" if pattern.metadata.wiring_mode == "Row-major" else "column_major",
                "wiring": "zigzag" if "Serpentine" in pattern.metadata.wiring_mode else "linear",
                "default_color_order": pattern.metadata.color_order
            },
            "frames": frames_json,
            "effects": effects_json,
            "metadata": {
                "author": "",
                "source_file": pattern.metadata.source_path or "",
                "approx_memory_bytes": pattern.metadata.led_count * 3 * len(pattern.frames),
                "export_formats": ["bin", "leds", "json", "hex", "dat", "h", "ledproj"]
            }
        }
        
        # Validate before returning
        try:
            validate_pattern_json(pattern_json)
        except PatternSchemaError as e:
            raise ValueError(f"Generated JSON does not validate: {e}") from e
        
        return pattern_json
    
    @staticmethod
    def pattern_from_json(data: Dict[str, Any]) -> Pattern:
        """
        Convert canonical JSON schema format to Pattern object.
        
        Args:
            data: Pattern JSON dictionary
            
        Returns:
            Pattern object
        """
        # Validate JSON first
        try:
            validate_pattern_json(data)
        except PatternSchemaError as e:
            raise ValueError(f"Invalid pattern JSON: {e}") from e
        
        # Extract matrix info
        matrix = data["matrix"]
        metadata = PatternMetadata(
            width=matrix["width"],
            height=matrix["height"],
            color_order=matrix.get("default_color_order", "RGB"),
            wiring_mode=matrix.get("layout", "row_major").replace("_", "-").title(),
        )
        
        # Extract frames
        frames = []
        pixel_count = matrix["width"] * matrix["height"]
        
        for frame_data in data["frames"]:
            # Get first layer's pixels (or composite all visible layers)
            layers = frame_data.get("layers", [])
            if not layers:
                pixels = [(0, 0, 0)] * pixel_count
            else:
                # For now, use first layer (can be enhanced to composite all layers)
                layer = layers[0]
                pixels_data = layer["pixels"]
                encoding = layer.get("encoding", "rle+rgba8")
                
                if encoding.startswith("rle"):
                    if isinstance(pixels_data, str):
                        pixels = PatternConverter.decode_pixels_rle(pixels_data, pixel_count)
                    else:
                        # Fallback: raw array
                        pixels = [tuple(p[:3]) for p in pixels_data]
                else:
                    # Raw encoding
                    if isinstance(pixels_data, str):
                        # Decode base64
                        decoded = base64.b64decode(pixels_data)
                        pixels = [
                            (decoded[i], decoded[i+1], decoded[i+2])
                            for i in range(0, len(decoded), 3)
                        ]
                    else:
                        pixels = [tuple(p[:3]) for p in pixels_data]
                
                # Ensure correct length
                while len(pixels) < pixel_count:
                    pixels.append((0, 0, 0))
                pixels = pixels[:pixel_count]
            
            frame = Frame(
                pixels=pixels,
                duration_ms=frame_data["duration_ms"]
            )
            frames.append(frame)
        
        # Create Pattern
        pattern = Pattern(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Untitled Pattern"),
            metadata=metadata,
            frames=frames
        )
        
        return pattern
    
    @staticmethod
    def save_pattern_json(pattern: Pattern, file_path: Path, use_rle: bool = True) -> None:
        """
        Save pattern to JSON file.
        
        Args:
            pattern: Pattern object
            file_path: Path to save JSON file
            use_rle: Whether to use RLE compression
        """
        json_data = PatternConverter.pattern_to_json(pattern, use_rle=use_rle)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_pattern_json(file_path: Path) -> Pattern:
        """
        Load pattern from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Pattern object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return PatternConverter.pattern_from_json(data)


# Convenience aliases for backward compatibility
encode_pixels_rle = PatternConverter.encode_pixels_rle
decode_pixels_rle = PatternConverter.decode_pixels_rle

