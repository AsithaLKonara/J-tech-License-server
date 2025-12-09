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
    
    def export_wled(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as WLED JSON format.
        
        WLED is a popular ESP32-based LED controller firmware.
        This export creates a JSON file compatible with WLED's custom effect format.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        import json
        from core.export.encoders import _expected_pixel_count, prepare_frame_pixels
        from core.mapping.circular_mapper import CircularMapper
        
        # Get expected LED count (physical LEDs, not grid size)
        led_count = _expected_pixel_count(pattern)
        
        # WLED JSON format structure
        wled_data = {
            "name": pattern.name or "LED Pattern",
            "leds": led_count,
            "frames": []
        }
        
        # Convert each frame to WLED format
        for frame_idx, frame in enumerate(pattern.frames):
            # Get pixels from frame
            pixels = prepare_frame_pixels(pattern, frame)
            
            # For circular layouts, reorder pixels using mapping table
            layout_type = getattr(pattern.metadata, 'layout_type', 'rectangular')
            if layout_type != "rectangular" and pattern.metadata.circular_mapping_table:
                # Reorder pixels according to LED wiring order
                reordered_pixels = []
                for led_idx in range(led_count):
                    if led_idx < len(pattern.metadata.circular_mapping_table):
                        grid_x, grid_y = pattern.metadata.circular_mapping_table[led_idx]
                        if 0 <= grid_y < pattern.metadata.height and 0 <= grid_x < pattern.metadata.width:
                            grid_idx = grid_y * pattern.metadata.width + grid_x
                            if grid_idx < len(pixels):
                                reordered_pixels.append(pixels[grid_idx])
                            else:
                                reordered_pixels.append((0, 0, 0))
                        else:
                            reordered_pixels.append((0, 0, 0))
                    else:
                        reordered_pixels.append((0, 0, 0))
                pixels = reordered_pixels
            
            # Convert pixels to RGB array for WLED
            # WLED expects array of [R, G, B] tuples
            rgb_array = []
            for pixel in pixels[:led_count]:  # Ensure we don't exceed LED count
                if isinstance(pixel, (list, tuple)) and len(pixel) >= 3:
                    rgb_array.append([int(pixel[0]), int(pixel[1]), int(pixel[2])])
                else:
                    rgb_array.append([0, 0, 0])
            
            # Pad or trim to exact LED count
            while len(rgb_array) < led_count:
                rgb_array.append([0, 0, 0])
            rgb_array = rgb_array[:led_count]
            
            # WLED frame format
            wled_frame = {
                "dur": frame.duration_ms,  # Duration in milliseconds
                "data": rgb_array  # RGB data array
            }
            wled_data["frames"].append(wled_frame)
        
        # Add metadata for Budurasmala layouts
        # This helps WLED or other players understand the physical LED arrangement
        if hasattr(pattern.metadata, 'layout_type') and pattern.metadata.layout_type != "rectangular":
            wled_data["layout"] = {
                "type": pattern.metadata.layout_type,
                "circular_led_count": getattr(pattern.metadata, 'circular_led_count', None),
            }
            
            # Add multi-ring metadata (Budurasmala)
            if pattern.metadata.layout_type == "multi_ring":
                wled_data["layout"]["multi_ring_count"] = getattr(pattern.metadata, 'multi_ring_count', None)
                wled_data["layout"]["ring_led_counts"] = getattr(pattern.metadata, 'ring_led_counts', None)
                wled_data["layout"]["ring_radii"] = getattr(pattern.metadata, 'ring_radii', None)
                wled_data["layout"]["ring_spacing"] = getattr(pattern.metadata, 'ring_spacing', None)
                wled_data["description"] = f"Budurasmala multi-ring pattern: {wled_data['layout']['multi_ring_count']} rings"
            
            # Add radial ray metadata (Budurasmala)
            elif pattern.metadata.layout_type == "radial_rays":
                wled_data["layout"]["ray_count"] = getattr(pattern.metadata, 'ray_count', None)
                wled_data["layout"]["leds_per_ray"] = getattr(pattern.metadata, 'leds_per_ray', None)
                wled_data["layout"]["ray_spacing_angle"] = getattr(pattern.metadata, 'ray_spacing_angle', None)
                wled_data["description"] = f"Budurasmala radial ray pattern: {wled_data['layout']['ray_count']} rays"
            
            # Add standard circular layout metadata
            else:
                wled_data["layout"]["circular_radius"] = getattr(pattern.metadata, 'circular_radius', None)
                wled_data["layout"]["circular_inner_radius"] = getattr(pattern.metadata, 'circular_inner_radius', None)
                wled_data["layout"]["circular_start_angle"] = getattr(pattern.metadata, 'circular_start_angle', None)
                wled_data["layout"]["circular_end_angle"] = getattr(pattern.metadata, 'circular_end_angle', None)
        
        # Add pattern metadata
        if not wled_data.get("description"):
            wled_data["description"] = f"LED pattern: {wled_data['leds']} LEDs, {len(wled_data['frames'])} frames"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(wled_data, f, indent=2, ensure_ascii=False)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "wled", json.dumps(wled_data, sort_keys=True).encode())
        
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
    
    def export_falcon_player(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as Falcon Player sequence format.
        
        Falcon Player uses a JSON format similar to WLED but with additional
        metadata for sequence timing and effects.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        import json
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Falcon Player sequence format
        falcon_data = {
            "name": pattern.name or "LED Pattern",
            "version": "1.0",
            "leds": pattern.metadata.width * pattern.metadata.height,
            "width": pattern.metadata.width,
            "height": pattern.metadata.height,
            "fps": pattern.metadata.fps or (1000.0 / pattern.frames[0].duration_ms if pattern.frames else 10.0),
            "frames": []
        }
        
        # Add frames
        for frame in pattern.frames:
            # Convert frame pixels to RGB array
            rgb_array = []
            for pixel in frame.pixels:
                if len(pixel) >= 3:
                    rgb_array.append([pixel[0], pixel[1], pixel[2]])
                else:
                    rgb_array.append([0, 0, 0])
            
            # Pad or trim to exact LED count
            while len(rgb_array) < falcon_data["leds"]:
                rgb_array.append([0, 0, 0])
            rgb_array = rgb_array[:falcon_data["leds"]]
            
            # Falcon Player frame format
            falcon_frame = {
                "duration": frame.duration_ms,  # Duration in milliseconds
                "pixels": rgb_array  # RGB data array
            }
            falcon_data["frames"].append(falcon_frame)
        
        # Add metadata for Budurasmala layouts
        if hasattr(pattern.metadata, 'layout_type') and pattern.metadata.layout_type != "rectangular":
            falcon_data["layout"] = {
                "type": pattern.metadata.layout_type,
                "circular_led_count": getattr(pattern.metadata, 'circular_led_count', None),
            }
            
            # Add multi-ring metadata (Budurasmala)
            if pattern.metadata.layout_type == "multi_ring":
                falcon_data["layout"]["multi_ring_count"] = getattr(pattern.metadata, 'multi_ring_count', None)
                falcon_data["layout"]["ring_led_counts"] = getattr(pattern.metadata, 'ring_led_counts', None)
                falcon_data["layout"]["ring_radii"] = getattr(pattern.metadata, 'ring_radii', None)
                falcon_data["layout"]["ring_spacing"] = getattr(pattern.metadata, 'ring_spacing', None)
            
            # Add radial ray metadata (Budurasmala)
            elif pattern.metadata.layout_type == "radial_rays":
                falcon_data["layout"]["ray_count"] = getattr(pattern.metadata, 'ray_count', None)
                falcon_data["layout"]["leds_per_ray"] = getattr(pattern.metadata, 'leds_per_ray', None)
                falcon_data["layout"]["ray_spacing_angle"] = getattr(pattern.metadata, 'ray_spacing_angle', None)
        
        # Add wiring information
        falcon_data["wiring"] = {
            "mode": pattern.metadata.wiring_mode,
            "data_in_corner": pattern.metadata.data_in_corner
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(falcon_data, f, indent=2, ensure_ascii=False)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "falcon", json.dumps(falcon_data, sort_keys=True).encode())
        
        return output_path
    
    def export_xlights(
        self,
        pattern: Pattern,
        output_path: Path,
        generate_manifest: bool = True
    ) -> Path:
        """
        Export pattern as xLights sequence format.
        
        xLights uses a JSON format with timing information and effect data.
        This creates a basic xLights-compatible sequence file.
        
        Args:
            pattern: Pattern to export
            output_path: Output file path
            generate_manifest: Whether to generate build manifest
            
        Returns:
            Path to exported file
        """
        import json
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # xLights sequence format
        xlights_data = {
            "name": pattern.name or "LED Pattern",
            "version": "1.0",
            "model": {
                "name": "LED Matrix",
                "width": pattern.metadata.width,
                "height": pattern.metadata.height,
                "leds": pattern.metadata.width * pattern.metadata.height
            },
            "sequence": {
                "fps": pattern.metadata.fps or (1000.0 / pattern.frames[0].duration_ms if pattern.frames else 10.0),
                "frames": []
            }
        }
        
        # Calculate total duration
        total_ms = sum(frame.duration_ms for frame in pattern.frames)
        xlights_data["sequence"]["duration_ms"] = total_ms
        
        # Add frames
        current_time_ms = 0
        for frame in pattern.frames:
            # Convert frame pixels to RGB array
            rgb_array = []
            for pixel in frame.pixels:
                if len(pixel) >= 3:
                    rgb_array.append([pixel[0], pixel[1], pixel[2]])
                else:
                    rgb_array.append([0, 0, 0])
            
            # Pad or trim to exact LED count
            while len(rgb_array) < xlights_data["model"]["leds"]:
                rgb_array.append([0, 0, 0])
            rgb_array = rgb_array[:xlights_data["model"]["leds"]]
            
            # xLights frame format
            xlights_frame = {
                "time_ms": current_time_ms,
                "duration_ms": frame.duration_ms,
                "pixels": rgb_array
            }
            xlights_data["sequence"]["frames"].append(xlights_frame)
            
            current_time_ms += frame.duration_ms
        
        # Add metadata for Budurasmala layouts
        if hasattr(pattern.metadata, 'layout_type') and pattern.metadata.layout_type != "rectangular":
            xlights_data["layout"] = {
                "type": pattern.metadata.layout_type,
                "circular_led_count": getattr(pattern.metadata, 'circular_led_count', None),
            }
            
            # Add multi-ring metadata (Budurasmala)
            if pattern.metadata.layout_type == "multi_ring":
                xlights_data["layout"]["multi_ring_count"] = getattr(pattern.metadata, 'multi_ring_count', None)
                xlights_data["layout"]["ring_led_counts"] = getattr(pattern.metadata, 'ring_led_counts', None)
                xlights_data["layout"]["ring_radii"] = getattr(pattern.metadata, 'ring_radii', None)
                xlights_data["layout"]["ring_spacing"] = getattr(pattern.metadata, 'ring_spacing', None)
            
            # Add radial ray metadata (Budurasmala)
            elif pattern.metadata.layout_type == "radial_rays":
                xlights_data["layout"]["ray_count"] = getattr(pattern.metadata, 'ray_count', None)
                xlights_data["layout"]["leds_per_ray"] = getattr(pattern.metadata, 'leds_per_ray', None)
                xlights_data["layout"]["ray_spacing_angle"] = getattr(pattern.metadata, 'ray_spacing_angle', None)
        
        # Add wiring information
        xlights_data["wiring"] = {
            "mode": pattern.metadata.wiring_mode,
            "data_in_corner": pattern.metadata.data_in_corner
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(xlights_data, f, indent=2, ensure_ascii=False)
        
        if generate_manifest:
            self._generate_manifest(pattern, output_path, "xlights", json.dumps(xlights_data, sort_keys=True).encode())
        
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
    elif format_lower == "wled":
        return exporter.export_wled(pattern, output_path, **kwargs)
    elif format_lower == "falcon":
        return exporter.export_falcon_player(pattern, output_path, **kwargs)
    elif format_lower == "xlights":
        return exporter.export_xlights(pattern, output_path, **kwargs)
    else:
        raise ValueError(f"Unknown export format: {format}")


__all__ = [
    'PatternExporter',
    'export_pattern',
    'ExportPreview',
    'ExportValidationError',
    'BuildManifest',
]

