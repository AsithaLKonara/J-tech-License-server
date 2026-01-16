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
                "default_color_order": pattern.metadata.color_order,
                # Circular layout support
                "layout_type": getattr(pattern.metadata, 'layout_type', 'rectangular'),
                "circular_led_count": getattr(pattern.metadata, 'circular_led_count', None),
                "circular_radius": getattr(pattern.metadata, 'circular_radius', None),
                "circular_inner_radius": getattr(pattern.metadata, 'circular_inner_radius', None),
                "circular_start_angle": getattr(pattern.metadata, 'circular_start_angle', 0.0),
                "circular_end_angle": getattr(pattern.metadata, 'circular_end_angle', 360.0),
                "circular_led_spacing": getattr(pattern.metadata, 'circular_led_spacing', None),
                "circular_mapping_table": (
                    [[int(x), int(y)] for x, y in mapping_table] 
                    if (mapping_table := getattr(pattern.metadata, 'circular_mapping_table', None))
                    else None
                ),
                # Multi-ring layout support (Budurasmala)
                "multi_ring_count": getattr(pattern.metadata, 'multi_ring_count', None),
                "ring_led_counts": getattr(pattern.metadata, 'ring_led_counts', None),
                "ring_radii": getattr(pattern.metadata, 'ring_radii', None),
                "ring_spacing": getattr(pattern.metadata, 'ring_spacing', None),
                # Radial ray support (Budurasmala)
                "ray_count": getattr(pattern.metadata, 'ray_count', None),
                "leds_per_ray": getattr(pattern.metadata, 'leds_per_ray', None),
                "ray_spacing_angle": getattr(pattern.metadata, 'ray_spacing_angle', None),
                # Custom LED positions (for custom PCBs - Budurasmala)
                "custom_led_positions": (
                    [[float(x), float(y)] for x, y in positions] 
                    if (positions := getattr(pattern.metadata, 'custom_led_positions', None))
                    else None
                ),
                "led_position_units": getattr(pattern.metadata, 'led_position_units', 'grid'),
                "custom_position_center_x": getattr(pattern.metadata, 'custom_position_center_x', None),
                "custom_position_center_y": getattr(pattern.metadata, 'custom_position_center_y', None),
                # Matrix-style Budurasmala (curved matrix, text rendering)
                "matrix_style": getattr(pattern.metadata, 'matrix_style', None),
                "text_content": getattr(pattern.metadata, 'text_content', None),
                "text_font_size": getattr(pattern.metadata, 'text_font_size', None),
                "text_color": getattr(pattern.metadata, 'text_color', None),
                # Irregular/custom shape support (LED Build-style)
                "irregular_shape_enabled": getattr(pattern.metadata, 'irregular_shape_enabled', False),
                "active_cell_coordinates": (
                    [[int(x), int(y)] for x, y in coords] 
                    if (coords := getattr(pattern.metadata, 'active_cell_coordinates', None))
                    else None
                ),
                "background_image_path": getattr(pattern.metadata, 'background_image_path', None),
                "background_image_scale": getattr(pattern.metadata, 'background_image_scale', 1.0),
                "background_image_offset_x": getattr(pattern.metadata, 'background_image_offset_x', 0.0),
                "background_image_offset_y": getattr(pattern.metadata, 'background_image_offset_y', 0.0),
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
            # Circular layout support
            layout_type=matrix.get("layout_type", "rectangular"),
            circular_led_count=matrix.get("circular_led_count"),
            circular_radius=matrix.get("circular_radius"),
            circular_inner_radius=matrix.get("circular_inner_radius"),
            circular_start_angle=matrix.get("circular_start_angle", 0.0),
            circular_end_angle=matrix.get("circular_end_angle", 360.0),
            circular_led_spacing=matrix.get("circular_led_spacing"),
            circular_mapping_table=(
                [tuple(map(int, pos)) for pos in mapping_table]
                if (mapping_table := matrix.get("circular_mapping_table"))
                else None
            ),
            # Multi-ring layout support (Budurasmala)
            multi_ring_count=matrix.get("multi_ring_count"),
            ring_led_counts=matrix.get("ring_led_counts"),
            ring_radii=matrix.get("ring_radii"),
            ring_spacing=matrix.get("ring_spacing"),
            # Radial ray support (Budurasmala)
            ray_count=matrix.get("ray_count"),
            leds_per_ray=matrix.get("leds_per_ray"),
            ray_spacing_angle=matrix.get("ray_spacing_angle"),
            # Custom LED positions (for custom PCBs - Budurasmala)
            custom_led_positions=(
                [tuple(map(float, pos)) for pos in positions]
                if (positions := matrix.get("custom_led_positions"))
                else None
            ),
            led_position_units=matrix.get("led_position_units", "grid"),
            custom_position_center_x=matrix.get("custom_position_center_x"),
            custom_position_center_y=matrix.get("custom_position_center_y"),
            # Matrix-style Budurasmala (curved matrix, text rendering)
            matrix_style=matrix.get("matrix_style"),
            text_content=matrix.get("text_content"),
            text_font_size=matrix.get("text_font_size"),
            text_color=matrix.get("text_color"),
            # Irregular/custom shape support (LED Build-style)
            irregular_shape_enabled=matrix.get("irregular_shape_enabled", False),
            active_cell_coordinates=(
                [tuple(map(int, pos)) for pos in coords]
                if (coords := matrix.get("active_cell_coordinates"))
                else None
            ),
            background_image_path=matrix.get("background_image_path"),
            background_image_scale=matrix.get("background_image_scale", 1.0),
            background_image_offset_x=matrix.get("background_image_offset_x", 0.0),
            background_image_offset_y=matrix.get("background_image_offset_y", 0.0),
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
    def _write_json_file(file_path: Path, data: dict) -> None:
        """Internal file write with retry."""
        from core.retry import retry_file_operations
        
        @retry_file_operations(max_attempts=3, delay=0.1, backoff=1.5)
        def _do_write():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        _do_write()
    
    @staticmethod
    def _read_json_file(file_path: Path) -> dict:
        """Internal file read with retry."""
        from core.retry import retry_file_operations
        
        @retry_file_operations(max_attempts=3, delay=0.1, backoff=1.5)
        def _do_read():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return _do_read()
    
    @staticmethod
    def save_pattern_json(pattern: Pattern, file_path: Path, use_rle: bool = True) -> None:
        """
        Save pattern to JSON file.
        
        Args:
            pattern: Pattern object
            file_path: Path to save JSON file
            use_rle: Whether to use RLE compression
        """
        from core.retry import retry_file_operations
        
        json_data = PatternConverter.pattern_to_json(pattern, use_rle=use_rle)
        PatternConverter._write_json_file(file_path, json_data)
    
    @staticmethod
    def load_pattern_json(file_path: Path) -> Pattern:
        """
        Load pattern from JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Pattern object
        """
        data = PatternConverter._read_json_file(file_path)
        return PatternConverter.pattern_from_json(data)


# Convenience aliases for backward compatibility
encode_pixels_rle = PatternConverter.encode_pixels_rle
decode_pixels_rle = PatternConverter.decode_pixels_rle

