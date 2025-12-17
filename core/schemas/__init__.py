"""
Canonical Pattern Schema System

Provides JSON schema validation and conversion utilities for LED patterns.
"""

# Gracefully handle missing jsonschema dependency
try:
    from .pattern_schema_v1 import (
        PATTERN_SCHEMA_V1,
        validate_pattern_json,
        PatternSchemaError,
    )
except ImportError as e:
    # If jsonschema is missing, create stubs
    PATTERN_SCHEMA_V1 = {}
    
    class PatternSchemaError(Exception):
        """Raised when pattern JSON validation fails"""
        pass
    
    def validate_pattern_json(*args, **kwargs):
        """Stub function when jsonschema is not available"""
        raise ImportError(
            "jsonschema is required for pattern validation. "
            "Install it with: pip install jsonschema>=4.0.0"
        ) from e

from .pattern_converter import (
    PatternConverter,
    encode_pixels_rle,
    decode_pixels_rle,
)
from .migration import (
    SchemaMigrator,
    migrate_pattern_json,
    get_schema_version,
)

__all__ = [
    'PATTERN_SCHEMA_V1',
    'validate_pattern_json',
    'PatternSchemaError',
    'PatternConverter',
    'encode_pixels_rle',
    'decode_pixels_rle',
    'SchemaMigrator',
    'migrate_pattern_json',
    'get_schema_version',
]

