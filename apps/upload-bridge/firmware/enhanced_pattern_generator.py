"""
Enhanced Pattern Data Generator - Generates firmware data with advanced features
Supports brightness curves, speed control, and hardware-specific mapping
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern, BrightnessCurve, HardwareBrightnessMapper


class EnhancedPatternGenerator:
    """
    Generates enhanced pattern data for firmware with advanced features
    
    Features:
    - Hardware-specific brightness mapping
    - Speed curve support
    - Per-channel brightness control
    - Variable speed keyframes
    - Frame interpolation
    """
    
    def __init__(self):
        self.brightness_curve_map = {
            "linear": 0,
            "gamma_corrected": 1,
            "logarithmic": 2,
            "exponential": 3,
            "s_curve": 4
        }
        
        self.speed_curve_map = {
            "linear": 0,
            "ease_in_quad": 1,
            "ease_out_quad": 2,
            "ease_in_out_quad": 3,
            "ease_in_cubic": 4,
            "ease_out_cubic": 5,
            "ease_in_out_cubic": 6
        }
    
    def generate_pattern_data_h(self, pattern: Pattern, output_path: str, 
                               build_opts: Dict = None) -> str:
        """
        Generate enhanced pattern_data.h file with metadata
        
        Args:
            pattern: Pattern object
            output_path: Output file path
            build_opts: Build options including GPIO pin, etc.
        
        Returns:
            Generated file path
        """
        build_opts = build_opts or {}
        gpio_pin = build_opts.get('gpio_pin', 2)
        
        # Generate pattern data
        pattern_bytes = self._generate_pattern_bytes(pattern)
        
        # Generate metadata
        metadata = self._generate_metadata(pattern, build_opts)
        
        # Generate C header
        header_content = self._generate_header_content(
            pattern, pattern_bytes, metadata, gpio_pin
        )
        
        # Write file
        with open(output_path, 'w') as f:
            f.write(header_content)
        
        return output_path
    
    def _generate_pattern_bytes(self, pattern: Pattern) -> bytes:
        """Generate raw pattern bytes with enhanced features"""
        # Start with header
        data = bytearray()
        
        # Header: LED count (2 bytes) + Frame count (2 bytes)
        data.extend(pattern.led_count.to_bytes(2, 'little'))
        data.extend(pattern.frame_count.to_bytes(2, 'little'))
        
        # Process each frame
        for frame in pattern.frames:
            # Frame delay (2 bytes)
            data.extend(frame.duration_ms.to_bytes(2, 'little'))
            
            # RGB data for all LEDs
            for r, g, b in frame.pixels:
                data.extend([r, g, b])
        
        return bytes(data)
    
    def _generate_metadata(self, pattern: Pattern, build_opts: Dict) -> Dict:
        """Generate metadata for enhanced features"""
        metadata = {
            # Basic settings
            'led_count': pattern.led_count,
            'frame_count': pattern.frame_count,
            'data_pin': build_opts.get('gpio_pin', 2),
            'brightness': pattern.metadata.brightness,
            'color_order': pattern.metadata.color_order,
            
            # Advanced brightness settings
            'brightness_curve': self.brightness_curve_map.get(
                pattern.metadata.brightness_curve, 1
            ),
            'led_type': pattern.metadata.led_type,
            'per_channel_brightness': pattern.metadata.per_channel_brightness,
            'red_brightness': int(pattern.metadata.red_brightness * 255),
            'green_brightness': int(pattern.metadata.green_brightness * 255),
            'blue_brightness': int(pattern.metadata.blue_brightness * 255),
            
            # Advanced speed settings
            'speed_curve': self.speed_curve_map.get(
                pattern.metadata.speed_curve, 0
            ),
            'variable_speed': pattern.metadata.variable_speed,
            'interpolation_enabled': pattern.metadata.interpolation_enabled,
            'interpolation_factor': int(pattern.metadata.interpolation_factor * 10),
            
            # Speed keyframes
            'num_keyframes': len(pattern.metadata.speed_keyframes),
            'speed_keyframes': pattern.metadata.speed_keyframes
        }
        
        return metadata
    
    def _generate_header_content(self, pattern: Pattern, pattern_bytes: bytes, 
                                metadata: Dict, gpio_pin: int) -> str:
        """Generate C header file content"""
        # Convert pattern data to C array
        pattern_array = self._bytes_to_c_array(pattern_bytes)
        
        # Generate keyframes array
        keyframes_array = self._generate_keyframes_array(metadata['speed_keyframes'])
        
        # Generate header content
        content = f"""/**
 * Enhanced Pattern Data - Auto-generated by Upload Bridge
 * 
 * Pattern: {pattern.name}
 * LEDs: {metadata['led_count']}
 * Frames: {metadata['frame_count']}
 * Size: {len(pattern_bytes)} bytes
 * 
 * Advanced Features:
 * - Brightness Curve: {pattern.metadata.brightness_curve}
 * - LED Type: {pattern.metadata.led_type}
 * - Per-Channel: {'Yes' if pattern.metadata.per_channel_brightness else 'No'}
 * - Speed Curve: {pattern.metadata.speed_curve}
 * - Variable Speed: {'Yes' if pattern.metadata.variable_speed else 'No'}
 * - Interpolation: {'Yes' if pattern.metadata.interpolation_enabled else 'No'}
 */

#ifndef PATTERN_DATA_H
#define PATTERN_DATA_H

// Build configuration
#define DATA_PIN {gpio_pin}
#define LED_COUNT {metadata['led_count']}
#define BRIGHTNESS {metadata['brightness']}
#define COLOR_ORDER {metadata['color_order']}

// Pattern data
const uint8_t pattern_data[] PROGMEM = {{
{pattern_array}
}};

const uint32_t pattern_data_size = {len(pattern_bytes)};

// Advanced brightness settings
const uint8_t brightness_curve = {metadata['brightness_curve']};
const char led_type[] = "{metadata['led_type']}";
const bool per_channel_brightness = {str(metadata['per_channel_brightness']).lower()};
const uint8_t red_brightness = {metadata['red_brightness']};
const uint8_t green_brightness = {metadata['green_brightness']};
const uint8_t blue_brightness = {metadata['blue_brightness']};

// Advanced speed settings
const uint8_t speed_curve = {metadata['speed_curve']};
const bool variable_speed = {str(metadata['variable_speed']).lower()};
const bool interpolation_enabled = {str(metadata['interpolation_enabled']).lower()};
const uint8_t interpolation_factor = {metadata['interpolation_factor']};

// Speed keyframes
const uint8_t num_keyframes = {metadata['num_keyframes']};
const struct SpeedKeyframe speed_keyframes[] = {{
{keyframes_array}
}};

#endif // PATTERN_DATA_H
"""
        
        return content
    
    def _bytes_to_c_array(self, data: bytes) -> str:
        """Convert bytes to C array format"""
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_values = [f"0x{b:02x}" for b in chunk]
            lines.append("    " + ", ".join(hex_values) + ",")
        
        return "\n".join(lines)
    
    def _generate_keyframes_array(self, keyframes: List[Tuple[int, float]]) -> str:
        """Generate C array for speed keyframes"""
        if not keyframes:
            return "    // No keyframes"
        
        lines = []
        for frame, multiplier in keyframes:
            lines.append(f"    {{{frame}, {multiplier:.2f}f}},")
        
        return "\n".join(lines)
    
    def generate_enhanced_firmware(self, pattern: Pattern, template_path: str, 
                                  output_path: str, build_opts: Dict = None) -> str:
        """
        Generate enhanced firmware with pattern data embedded
        
        Args:
            pattern: Pattern object
            template_path: Path to firmware template
            output_path: Output firmware path
            build_opts: Build options
        
        Returns:
            Generated firmware path
        """
        build_opts = build_opts or {}
        
        # Read template
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Generate pattern data
        pattern_data_path = Path(output_path).parent / "pattern_data.h"
        self.generate_pattern_data_h(pattern, str(pattern_data_path), build_opts)
        
        # Replace template placeholders
        enhanced_content = self._replace_template_placeholders(
            template_content, pattern, build_opts
        )
        
        # Write enhanced firmware
        with open(output_path, 'w') as f:
            f.write(enhanced_content)
        
        return output_path
    
    def _replace_template_placeholders(self, template: str, pattern: Pattern, 
                                     build_opts: Dict) -> str:
        """Replace template placeholders with actual values"""
        replacements = {
            '{{LED_COUNT}}': str(pattern.led_count),
            '{{FRAME_COUNT}}': str(pattern.frame_count),
            '{{DATA_PIN}}': str(build_opts.get('gpio_pin', 2)),
            '{{BRIGHTNESS}}': str(pattern.metadata.brightness),
            '{{COLOR_ORDER}}': pattern.metadata.color_order,
            '{{BRIGHTNESS_CURVE}}': str(self.brightness_curve_map.get(
                pattern.metadata.brightness_curve, 1
            )),
            '{{LED_TYPE}}': pattern.metadata.led_type,
            '{{PER_CHANNEL_BRIGHTNESS}}': str(pattern.metadata.per_channel_brightness).lower(),
            '{{RED_BRIGHTNESS}}': str(int(pattern.metadata.red_brightness * 255)),
            '{{GREEN_BRIGHTNESS}}': str(int(pattern.metadata.green_brightness * 255)),
            '{{BLUE_BRIGHTNESS}}': str(int(pattern.metadata.blue_brightness * 255)),
            '{{SPEED_CURVE}}': str(self.speed_curve_map.get(
                pattern.metadata.speed_curve, 0
            )),
            '{{VARIABLE_SPEED}}': str(pattern.metadata.variable_speed).lower(),
            '{{INTERPOLATION_ENABLED}}': str(pattern.metadata.interpolation_enabled).lower(),
            '{{INTERPOLATION_FACTOR}}': str(int(pattern.metadata.interpolation_factor * 10)),
            '{{NUM_KEYFRAMES}}': str(len(pattern.metadata.speed_keyframes))
        }
        
        # Apply replacements
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        return template
    
    def estimate_memory_usage(self, pattern: Pattern) -> Dict[str, int]:
        """
        Estimate memory usage for enhanced pattern
        
        Args:
            pattern: Pattern object
        
        Returns:
            Dictionary with memory usage estimates
        """
        # Base pattern data
        pattern_size = pattern.estimate_memory_bytes()
        
        # Metadata overhead
        metadata_size = 64  # Approximate size of metadata
        
        # Keyframes overhead
        keyframes_size = len(pattern.metadata.speed_keyframes) * 6  # 2 bytes frame + 4 bytes multiplier
        
        # Enhanced features overhead
        features_size = 32  # Brightness curves, speed curves, etc.
        
        total_size = pattern_size + metadata_size + keyframes_size + features_size
        
        return {
            'pattern_data': pattern_size,
            'metadata': metadata_size,
            'keyframes': keyframes_size,
            'features': features_size,
            'total': total_size
        }













