"""
Export Package - Export encoders, validators, exporters, and build manifests

Provides complete export pipeline for LED patterns.
"""

from .encoders import (
    build_binary_payload,
    build_dat_payload,
    build_intel_hex,
    build_c_header,
    encode_frame_bytes,
    bytes_per_pixel,
    prepare_frame_pixels,
)
from .validator import (
    ExportPreview,
    ExportValidationError,
    generate_export_preview,
)
from .build_manifest import (
    BuildManifest,
    generate_build_manifest,
)
from .exporters import (
    PatternExporter,
    export_pattern,
)

__all__ = [
    # Encoders
    'build_binary_payload',
    'build_dat_payload',
    'build_intel_hex',
    'build_c_header',
    'encode_frame_bytes',
    'bytes_per_pixel',
    'prepare_frame_pixels',
    # Validator
    'ExportPreview',
    'ExportValidationError',
    'generate_export_preview',
    # Build Manifest
    'BuildManifest',
    'generate_build_manifest',
    # Exporters
    'PatternExporter',
    'export_pattern',
]
