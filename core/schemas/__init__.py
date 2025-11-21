"""
Canonical Pattern Schema System

Provides JSON schema validation and conversion utilities for LED patterns.
"""

from .pattern_schema_v1 import (
    PATTERN_SCHEMA_V1,
    validate_pattern_json,
    PatternSchemaError,
)
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

