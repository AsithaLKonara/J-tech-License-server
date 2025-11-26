"""
Export Pipeline - High-level export interface

This module provides the main export interface that coordinates between
encoders, validators, and build manifest generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from core.pattern import Pattern
from core.export_options import ExportOptions

from .encoders import (
    build_binary_payload,
    build_dat_payload,
    build_intel_hex,
    build_c_header,
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


class PatternExporter:
    """
    High-level pattern exporter that handles all export formats.
    
    Features:
    - Multiple export formats (bin, dat, hex, header, json, leds, ledproj)
    - Export validation and preview
    - Build manifest generation
    - Deterministic, reproducible exports
    """
    
    def __init__(self, options: Optional[ExportOptions] = None):
        """
        Initialize exporter.
        
        Args:
            options: Export options (defaults to ExportOptions())
        """
        self.options = options or ExportOptions()
    
    def export_binary(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as binary file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        payload = build_binary_payload(pattern, self.options)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "bin", payload)
        
        return output_path
    
    def export_dat(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as .dat file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        payload = build_dat_payload(pattern, self.options)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "dat", payload)
        
        return output_path
    
    def export_hex(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as Intel HEX file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        hex_content = build_intel_hex(pattern, self.options)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(hex_content)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "hex", hex_content.encode())
        
        return output_path
    
    def export_sprite_sheet(
        self,
        pattern: Pattern,
        output_path: Path,
        orientation: str = "horizontal",
        spacing: int = 0,
        scale_factor: int = 1,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as PNG sprite sheet.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            orientation: "horizontal" or "vertical" layout
            spacing: Pixels spacing between frames
            scale_factor: Pixel scaling factor
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        from core.image_exporter import ImageExporter
        
        ImageExporter.export_sprite_sheet(
            pattern,
            str(output_path),
            orientation=orientation,
            spacing=spacing,
            scale_factor=scale_factor,
            format="PNG"
        )
        
        if generate_manifest:
            payload = output_path.read_bytes()
            self._generate_manifest(pattern, output_path, "png_sprite", payload)
        
        return output_path
    
    def export_gif(
        self,
        pattern: Pattern,
        output_path: Path,
        frame_delay_ms: int = 50,
        loop: bool = True,
        scale_factor: int = 1,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as animated GIF.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            frame_delay_ms: Frame delay in milliseconds (overrides frame durations if > 0)
            loop: Whether to loop animation
            scale_factor: Pixel scaling factor
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        from core.image_exporter import ImageExporter
        
        # If frame_delay_ms is specified, temporarily override frame durations
        if frame_delay_ms > 0:
            original_durations = [frame.duration_ms for frame in pattern.frames]
            for frame in pattern.frames:
                frame.duration_ms = frame_delay_ms
        
        try:
            loop_count = 0 if loop else 1
            ImageExporter.export_animation_as_gif(
                pattern,
                str(output_path),
                scale_factor=scale_factor,
                loop_count=loop_count
            )
        finally:
            # Restore original durations
            if frame_delay_ms > 0:
                for i, frame in enumerate(pattern.frames):
                    if i < len(original_durations):
                        frame.duration_ms = original_durations[i]
        
        if generate_manifest:
            payload = output_path.read_bytes()
            self._generate_manifest(pattern, output_path, "gif", payload)
        
        return output_path
    
    def export_header(
        self,
        pattern: Pattern,
        output_path: Path,
        array_basename: str = "Pattern",
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as C header file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            array_basename: Base name for C arrays
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        header_content = build_c_header(pattern, self.options, array_basename)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(header_content)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "h", header_content.encode())
        
        return output_path
    
    def export_json(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as canonical JSON.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        import json
        
        json_data = pattern.to_dict()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "json", json.dumps(json_data, sort_keys=True).encode())
        
        return output_path
    
    def export_leds(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as LEDS text format.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        # LEDS format is text-based, similar to .dat but with text encoding
        from core.export.encoders import encode_frame_bytes
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='ascii') as f:
            f.write("# LEDS Pattern Export\n")
            f.write(f"# Width: {pattern.metadata.width}, Height: {pattern.metadata.height}\n")
            f.write(f"# Frames: {len(pattern.frames)}\n")
            f.write(f"# Export Options: RGB={self.options.rgb_order}, ColorSpace={self.options.color_space}\n\n")
            
            for i, frame in enumerate(pattern.frames):
                f.write(f"# Frame {i+1} (duration: {frame.duration_ms}ms)\n")
                frame_bytes = encode_frame_bytes(pattern, frame, self.options)
                # Write as hex string
                hex_str = frame_bytes.hex().upper()
                f.write(hex_str)
                f.write("\n\n")
        
        if generate_manifest:
            payload = output_path.read_bytes()
            self._generate_manifest(pattern, output_path, "leds", payload)
        
        return output_path
    
    def export_project(
        self,
        pattern: Pattern,
        output_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as .ledproj project file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            metadata: Optional project metadata
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        from core.project import save_project, ProjectMetadata
        
        project_metadata = None
        if metadata:
            project_metadata = ProjectMetadata(**metadata)
        
        save_project(pattern, output_path, metadata=project_metadata)
        
        if generate_manifest:
            payload = output_path.read_bytes()
            self._generate_manifest(pattern, output_path, "ledproj", payload)
        
        return output_path
    
    def preview(self, pattern: Pattern, format_name: str) -> ExportPreview:
        """
        Generate export preview.
        
        Args:
            pattern: Pattern to preview
            format_name: Export format name
            
        Returns:
            ExportPreview with size and warnings
        """
        return generate_export_preview(pattern, format_name, self.options)
    
    def _generate_manifest(
        self,
        pattern: Pattern,
        output_path: Path,
        export_format: str,
        firmware_bytes: bytes
    ) -> None:
        """Generate build manifest for export."""
        manifest = generate_build_manifest(
            pattern=pattern,
            export_format=export_format,
            firmware_bytes=firmware_bytes
        )
        
        manifest_path = output_path.with_suffix('.manifest.json')
        manifest.save(manifest_path)


# Convenience functions
def export_pattern(
    pattern: Pattern,
    output_path: Path,
    format: str = "bin",
    options: Optional[ExportOptions] = None,
    **kwargs
) -> Path:
    """
    Export pattern in specified format.
    
    Args:
        pattern: Pattern to export
        output_path: Output file path
        format: Export format (bin, dat, hex, header, json, leds, ledproj)
        options: Optional export options
        **kwargs: Additional format-specific options
        
    Returns:
        Path to exported file
    """
    exporter = PatternExporter(options)
    
    format_lower = format.lower()
    if format_lower == "bin":
        return exporter.export_binary(pattern, output_path, **kwargs)
    elif format_lower == "dat":
        return exporter.export_dat(pattern, output_path, **kwargs)
    elif format_lower == "hex":
        return exporter.export_hex(pattern, output_path, **kwargs)
    elif format_lower in ("h", "header"):
        return exporter.export_header(pattern, output_path, kwargs.get('array_basename', 'Pattern'))
    elif format_lower == "json":
        return exporter.export_json(pattern, output_path, **kwargs)
    elif format_lower == "leds":
        return exporter.export_leds(pattern, output_path, **kwargs)
    elif format_lower in ("ledproj", "project"):
        return exporter.export_project(pattern, output_path, kwargs.get('metadata'))
    elif format_lower == "png_sprite":
        return exporter.export_sprite_sheet(
            pattern,
            output_path,
            orientation=kwargs.get('orientation', 'horizontal'),
            spacing=kwargs.get('spacing', 0),
            scale_factor=kwargs.get('scale_factor', 1)
        )
    elif format_lower == "gif":
        return exporter.export_gif(
            pattern,
            output_path,
            frame_delay_ms=kwargs.get('frame_delay_ms', 0),
            loop=kwargs.get('loop', True),
            scale_factor=kwargs.get('scale_factor', 1)
        )
    else:
        raise ValueError(f"Unknown export format: {format}")


__all__ = [
    'PatternExporter',
    'export_pattern',
    'ExportPreview',
    'ExportValidationError',
    'BuildManifest',
]

