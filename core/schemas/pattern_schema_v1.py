"""
Pattern JSON Schema v1.0 - Canonical pattern format definition and validation

This module defines the JSON Schema Draft 7 schema for LED patterns and provides
validation utilities.
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError


# JSON Schema Draft 7 definition for pattern v1.0
PATTERN_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": [
        "schema_version",
        "id",
        "name",
        "matrix",
        "frames"
    ],
    "properties": {
        "schema_version": {
            "type": "string",
            "pattern": "^1\\.0$",
            "description": "Schema version (must be '1.0')"
        },
        "id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique pattern identifier (UUID v4)"
        },
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256,
            "description": "Pattern name"
        },
        "description": {
            "type": "string",
            "maxLength": 4096,
            "default": "",
            "description": "Optional pattern description"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1,
                "maxLength": 64
            },
            "uniqueItems": True,
            "default": [],
            "description": "Pattern tags for categorization"
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of creation"
        },
        "modified_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 timestamp of last modification"
        },
        "matrix": {
            "type": "object",
            "required": ["width", "height"],
            "properties": {
                "width": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 256,
                    "description": "Matrix width (LEDs)"
                },
                "height": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 256,
                    "description": "Matrix height (LEDs)"
                },
                "layout": {
                    "type": "string",
                    "enum": ["row_major", "column_major"],
                    "default": "row_major",
                    "description": "Pixel layout order"
                },
                "wiring": {
                    "type": "string",
                    "enum": ["linear", "zigzag", "serpentine"],
                    "default": "linear",
                    "description": "Wiring pattern"
                },
                "default_color_order": {
                    "type": "string",
                    "enum": ["RGB", "GRB", "BRG", "BGR", "RBG", "GBR"],
                    "default": "RGB",
                    "description": "Default color channel order"
                },
                # Circular layout support
                "layout_type": {
                    "type": "string",
                    "enum": ["rectangular", "circle", "ring", "arc", "radial", "multi_ring", "radial_rays", "custom_positions"],
                    "default": "rectangular",
                    "description": "Layout type (rectangular or circular variants)"
                },
                "circular_led_count": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "maximum": 1024,
                    "description": "Number of LEDs in circular layout"
                },
                "circular_radius": {
                    "type": ["number", "null"],
                    "minimum": 0.0,
                    "description": "Outer radius for circular layout"
                },
                "circular_inner_radius": {
                    "type": ["number", "null"],
                    "minimum": 0.0,
                    "description": "Inner radius for ring layouts"
                },
                "circular_start_angle": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 360.0,
                    "default": 0.0,
                    "description": "Start angle in degrees (for arc layouts)"
                },
                "circular_end_angle": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 360.0,
                    "default": 360.0,
                    "description": "End angle in degrees (for arc layouts)"
                },
                "circular_led_spacing": {
                    "type": ["number", "null"],
                    "minimum": 0.0,
                    "description": "Optional custom LED spacing"
                },
                "circular_mapping_table": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {
                            "type": "integer",
                            "minimum": 0
                        },
                        "description": "LED index to grid (x, y) mapping"
                    },
                    "description": "Precomputed mapping table: LED index -> (grid_x, grid_y)"
                },
                # Multi-ring layout support (Budurasmala)
                "multi_ring_count": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Number of concentric rings"
                },
                "ring_led_counts": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 512
                    },
                    "description": "LEDs per ring"
                },
                "ring_radii": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "number",
                        "minimum": 0.0
                    },
                    "description": "Radius for each ring"
                },
                "ring_spacing": {
                    "type": ["number", "null"],
                    "minimum": 0.0,
                    "description": "Spacing between rings"
                },
                # Radial ray support (Budurasmala)
                "ray_count": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "maximum": 64,
                    "description": "Number of rays extending from center"
                },
                "leds_per_ray": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "maximum": 100,
                    "description": "LEDs along each ray"
                },
                "ray_spacing_angle": {
                    "type": ["number", "null"],
                    "minimum": 0.0,
                    "maximum": 360.0,
                    "description": "Angle between rays in degrees"
                },
                # Custom LED positions (for custom PCBs - Budurasmala)
                "custom_led_positions": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {
                            "type": "number"
                        },
                        "description": "LED position (x, y) in mm or units"
                    },
                    "description": "Custom LED positions for custom PCBs"
                },
                "led_position_units": {
                    "type": "string",
                    "enum": ["grid", "mm", "inches"],
                    "default": "grid",
                    "description": "Units for LED positions"
                },
                "custom_position_center_x": {
                    "type": ["number", "null"],
                    "description": "Center X for custom positions"
                },
                "custom_position_center_y": {
                    "type": ["number", "null"],
                    "description": "Center Y for custom positions"
                },
                # Matrix-style Budurasmala (curved matrix, text rendering)
                "matrix_style": {
                    "type": ["string", "null"],
                    "enum": ["curved", "hybrid_ring_matrix", None],
                    "description": "Matrix style for Budurasmala layouts"
                },
                "text_content": {
                    "type": ["string", "null"],
                    "maxLength": 256,
                    "description": "Text to render on circular matrix"
                },
                "text_font_size": {
                    "type": ["integer", "null"],
                    "minimum": 1,
                    "maximum": 128,
                    "description": "Font size for text rendering"
                },
                "text_color": {
                    "type": ["array", "null"],
                    "items": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 255
                    },
                    "minItems": 3,
                    "maxItems": 3,
                    "description": "RGB color for text"
                }
            },
            "additionalProperties": False
        },
        "frames": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["index", "duration_ms", "layers"],
                "properties": {
                    "index": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Frame index (0-based)"
                    },
                    "duration_ms": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10000,
                        "description": "Frame duration in milliseconds"
                    },
                    "layers": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["id", "name", "opacity", "blend_mode", "pixels", "encoding"],
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "format": "uuid",
                                    "description": "Layer identifier (UUID)"
                                },
                                "name": {
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 128,
                                    "description": "Layer name"
                                },
                                "opacity": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "description": "Layer opacity (0.0-1.0)"
                                },
                                "blend_mode": {
                                    "type": "string",
                                    "enum": ["normal", "add", "multiply", "screen"],
                                    "default": "normal",
                                    "description": "Layer blend mode"
                                },
                                "visible": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Layer visibility"
                                },
                                "pixels": {
                                    "oneOf": [
                                        {
                                            "type": "string",
                                            "description": "Base64-encoded RLE compressed pixel data"
                                        },
                                        {
                                            "type": "array",
                                            "items": {
                                                "type": "array",
                                                "minItems": 3,
                                                "maxItems": 3,
                                                "items": {
                                                    "type": "integer",
                                                    "minimum": 0,
                                                    "maximum": 255
                                                }
                                            },
                                            "description": "Uncompressed RGB pixel array"
                                        }
                                    ],
                                    "description": "Pixel data (compressed or uncompressed)"
                                },
                                "encoding": {
                                    "type": "string",
                                    "enum": ["rle+rgba8", "raw+rgba8", "raw+rgb8"],
                                    "default": "rle+rgba8",
                                    "description": "Pixel data encoding format"
                                }
                            },
                            "additionalProperties": False
                        },
                        "description": "Frame layers (composited bottom-to-top)"
                    }
                },
                "additionalProperties": False
            },
            "description": "Animation frames"
        },
        "effects": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "type"],
                "properties": {
                    "id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "Effect identifier"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["scroll", "rotate", "mirror", "flip", "invert", "wipe", "reveal", "bounce"],
                        "description": "Effect type"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Effect-specific parameters"
                    },
                    "frame_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "integer", "minimum": 0},
                            "end": {"type": "integer", "minimum": 0}
                        },
                        "description": "Frame range for effect application"
                    }
                },
                "additionalProperties": False
            },
            "default": [],
            "description": "Applied effects (non-destructive)"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "author": {
                    "type": "string",
                    "maxLength": 256,
                    "description": "Pattern author"
                },
                "source_file": {
                    "type": "string",
                    "description": "Original source file path"
                },
                "approx_memory_bytes": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Approximate memory usage in bytes"
                },
                "export_formats": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["bin", "leds", "json", "hex", "dat", "h", "ledproj"]
                    },
                    "description": "Supported export formats"
                }
            },
            "additionalProperties": True,
            "description": "Additional metadata"
        }
    },
    "additionalProperties": False
}


class PatternSchemaError(Exception):
    """Raised when pattern JSON validation fails"""
    pass


def validate_pattern_json(data: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate pattern JSON data against schema.
    
    Args:
        data: Pattern JSON data (dict)
        schema: Optional schema to use (defaults to PATTERN_SCHEMA_V1)
        
    Returns:
        True if valid
        
    Raises:
        PatternSchemaError: If validation fails
    """
    if schema is None:
        schema = PATTERN_SCHEMA_V1
    
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        raise PatternSchemaError(f"Pattern JSON validation failed: {e.message}") from e


def load_schema_from_file(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON schema from file.
    
    Args:
        file_path: Path to schema JSON file
        
    Returns:
        Schema dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_schema_to_file(schema: Dict[str, Any], file_path: Path) -> None:
    """
    Save JSON schema to file.
    
    Args:
        schema: Schema dictionary
        file_path: Path to save schema
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

