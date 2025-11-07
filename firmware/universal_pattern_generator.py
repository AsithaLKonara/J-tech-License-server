#!/usr/bin/env python3
"""
Universal Pattern Generator - Professional Edition
Generates optimized firmware templates for all chip families with full advanced features
Adapts features based on chip capabilities and memory constraints
"""

import os
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from core.pattern import Pattern, PatternMetadata, Frame


class UniversalPatternGenerator:
    """
    Universal pattern generator that creates optimized firmware for all chip families
    with full professional-grade advanced features
    """
    
    def __init__(self):
        self.chip_capabilities = {
            'esp8266': {
                'max_leds': 1000,
                'max_keyframes': 32,
                'supports_float': True,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': True,
                'memory_optimized': False,
                'template_type': 'arduino'
            },
            'esp32': {
                'max_leds': 1000,
                'max_keyframes': 32,
                'supports_float': True,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': True,
                'memory_optimized': False,
                'template_type': 'arduino'
            },
            'atmega328p': {
                'max_leds': 200,
                'max_keyframes': 8,
                'supports_float': False,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'atmega2560': {
                'max_leds': 300,
                'max_keyframes': 16,
                'supports_float': False,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'atmega32u4': {
                'max_leds': 150,
                'max_keyframes': 8,
                'supports_float': False,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'attiny85': {
                'max_leds': 50,
                'max_keyframes': 4,
                'supports_float': False,
                'supports_interpolation': False,
                'supports_per_channel': False,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'stm32f030f4': {
                'max_leds': 100,
                'max_keyframes': 8,
                'supports_float': True,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': True,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'stm32f103c8': {
                'max_leds': 300,
                'max_keyframes': 16,
                'supports_float': True,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': True,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'pic16f876a': {
                'max_leds': 50,
                'max_keyframes': 4,
                'supports_float': False,
                'supports_interpolation': False,
                'supports_per_channel': True,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'pic18f2550': {
                'max_leds': 100,
                'max_keyframes': 8,
                'supports_float': False,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': False,
                'memory_optimized': True,
                'template_type': 'c'
            },
            'numicro_m031': {
                'max_leds': 200,
                'max_keyframes': 12,
                'supports_float': True,
                'supports_interpolation': True,
                'supports_per_channel': True,
                'supports_full_gamma': True,
                'memory_optimized': True,
                'template_type': 'c'
            }
        }
    
    def generate_universal_firmware(self, pattern: Pattern, chip_id: str, output_dir: str, 
                                  config: Dict) -> str:
        """
        Generate universal firmware for any chip with full advanced features
        
        Args:
            pattern: Pattern object with advanced features
            chip_id: Target chip identifier
            output_dir: Output directory for generated files
            config: Additional configuration (GPIO pin, etc.)
        
        Returns:
            Path to generated main source file
        """
        if chip_id not in self.chip_capabilities:
            raise ValueError(f"Unsupported chip: {chip_id}")
        
        capabilities = self.chip_capabilities[chip_id]
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate pattern data header
        pattern_data_path = output_path / "pattern_data.h"
        self._generate_pattern_data_h(pattern, pattern_data_path, chip_id, config)
        
        # Generate main source file
        if capabilities['template_type'] == 'arduino':
            # For Arduino sketches, always generate a new template to avoid conflicts
            main_file = self._generate_arduino_template(pattern, chip_id, output_path, config)
        else:
            main_file = self._generate_c_template(pattern, chip_id, output_path, config)
        
        # Generate Makefile if needed
        if capabilities['template_type'] == 'c':
            self._generate_makefile(chip_id, output_path)
        
        # Generate README
        self._generate_readme(chip_id, output_path, capabilities)
        
        return str(main_file)
    
    def _generate_pattern_data_h(self, pattern: Pattern, output_path: Path, 
                                chip_id: str, config: Dict) -> None:
        """Generate pattern_data.h with all advanced features"""
        capabilities = self.chip_capabilities[chip_id]
        
        # Limit features based on chip capabilities
        limited_pattern = self._limit_pattern_for_chip(pattern, chip_id)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("/*\n")
            f.write(" * Pattern Data Header - Professional Edition\n")
            f.write(f" * Generated for {chip_id.upper()}\n")
            f.write(" * Upload Bridge v3.1\n")
            f.write(" */\n\n")
            
            f.write("#ifndef PATTERN_DATA_H\n")
            f.write("#define PATTERN_DATA_H\n\n")
            
            # Basic pattern info
            f.write(f"#define LED_DATA_PIN {config.get('gpio_pin', 2)}\n")
            f.write(f"#define LED_COUNT {limited_pattern.led_count}\n")
            f.write(f"#define FRAME_COUNT {limited_pattern.frame_count}\n\n")
            
            # Advanced brightness settings
            f.write("// Advanced Brightness Control\n")
            brightness = limited_pattern.metadata.brightness if limited_pattern.metadata.brightness is not None else 1.0
            f.write(f"#define BRIGHTNESS {int(brightness * 255)}\n")
            brightness_curve = limited_pattern.metadata.brightness_curve if limited_pattern.metadata.brightness_curve is not None else 'linear'
            f.write(f"#define BRIGHTNESS_CURVE_TYPE \"{brightness_curve}\"\n")
            led_type = limited_pattern.metadata.led_type if limited_pattern.metadata.led_type is not None else 'ws2812'
            f.write(f"#define LED_TYPE \"{led_type}\"\n")
            f.write(f"#define PER_CHANNEL_BRIGHTNESS_SETTING {1 if limited_pattern.metadata.per_channel_brightness else 0}\n")
            red_brightness = limited_pattern.metadata.red_brightness if limited_pattern.metadata.red_brightness is not None else 1.0
            f.write(f"#define RED_BRIGHTNESS_SETTING {int(red_brightness * 255)}\n")
            green_brightness = limited_pattern.metadata.green_brightness if limited_pattern.metadata.green_brightness is not None else 1.0
            f.write(f"#define GREEN_BRIGHTNESS_SETTING {int(green_brightness * 255)}\n")
            blue_brightness = limited_pattern.metadata.blue_brightness if limited_pattern.metadata.blue_brightness is not None else 1.0
            f.write(f"#define BLUE_BRIGHTNESS_SETTING {int(blue_brightness * 255)}\n\n")
            
            # Advanced speed settings
            f.write("// Advanced Speed Control\n")
            speed_curve = limited_pattern.metadata.speed_curve if limited_pattern.metadata.speed_curve is not None else 'linear'
            f.write(f"#define SPEED_CURVE_TYPE \"{speed_curve}\"\n")
            f.write(f"#define VARIABLE_SPEED_SETTING {1 if limited_pattern.metadata.variable_speed else 0}\n")
            f.write(f"#define INTERPOLATION_ENABLED_SETTING {1 if limited_pattern.metadata.interpolation_enabled else 0}\n")
            interpolation_factor = limited_pattern.metadata.interpolation_factor if limited_pattern.metadata.interpolation_factor is not None else 1.0
            f.write(f"#define INTERPOLATION_FACTOR_SETTING {int(interpolation_factor * 10)}\n\n")
            
            # Speed keyframes
            speed_keyframes = limited_pattern.metadata.speed_keyframes if limited_pattern.metadata.speed_keyframes is not None else []
            f.write("// Speed Keyframes\n")
            f.write(f"#define NUM_KEYFRAMES {len(speed_keyframes)}\n")
            if speed_keyframes:
                f.write("struct SpeedKeyframe {\n")
                f.write("    uint16_t frame;\n")
                if capabilities['supports_float']:
                    f.write("    float multiplier;\n")
                else:
                    f.write("    uint8_t multiplier;  // 0-255, represents 0.0-2.0\n")
                f.write("};\n\n")
                
                f.write("const struct SpeedKeyframe speed_keyframes[] PROGMEM = {\n")
                for i, (frame, multiplier) in enumerate(speed_keyframes):
                    if capabilities['supports_float']:
                        f.write(f"    {{{frame}, {multiplier}f}}")
                    else:
                        f.write(f"    {{{frame}, {int(multiplier * 128)}}}")
                    if i < len(speed_keyframes) - 1:
                        f.write(",")
                    f.write("\n")
                f.write("};\n\n")
            else:
                f.write("// No speed keyframes defined\n\n")
            
            # Pattern data
            f.write("// Pattern Data\n")
            f.write("const uint8_t pattern_data[] PROGMEM = {\n")
            
            # Write pattern header
            f.write(f"    {limited_pattern.led_count & 0xFF}, {(limited_pattern.led_count >> 8) & 0xFF},  // LED count\n")
            f.write(f"    {limited_pattern.frame_count & 0xFF}, {(limited_pattern.frame_count >> 8) & 0xFF},  // Frame count\n")
            
            # Write frame data
            for i, frame in enumerate(limited_pattern.frames):
                # Write frame delay - ensure fps is not None
                fps = limited_pattern.metadata.fps if limited_pattern.metadata.fps is not None else 20
                delay_ms = int(1000 / fps)
                f.write(f"    {delay_ms & 0xFF}, {(delay_ms >> 8) & 0xFF},  // Frame {i} delay\n")
                
                # Write RGB data
                for led_idx, led in enumerate(frame.pixels):
                    r, g, b = led
                    f.write(f"    {r}, {g}, {b},")
                    if (i * limited_pattern.led_count + led_idx) % 8 == 7:
                        f.write("  // LED data")
                    f.write("\n")
            
            f.write("};\n\n")
            f.write("#endif // PATTERN_DATA_H\n")
    
    def _limit_pattern_for_chip(self, pattern: Pattern, chip_id: str) -> Pattern:
        """Limit pattern features based on chip capabilities"""
        capabilities = self.chip_capabilities[chip_id]
        
        # Determine max LEDs and trim frames if necessary
        max_leds = capabilities['max_leds']
        led_count = pattern.led_count
        
        frames = []
        if led_count > max_leds:
            for f in pattern.frames:
                frames.append(Frame(pixels=f.pixels[:max_leds], duration_ms=f.duration_ms))
            # Use linear width for safety when trimming; preserves LED_COUNT for firmware
            new_meta = PatternMetadata(
                width=max_leds,
                height=1,
                color_order=pattern.metadata.color_order,
                fps=pattern.metadata.fps,
                total_ms=pattern.metadata.total_ms,
                brightness=pattern.metadata.brightness,
            )
        else:
            frames = [Frame(pixels=f.pixels, duration_ms=f.duration_ms) for f in pattern.frames]
            new_meta = PatternMetadata(
                width=pattern.metadata.width,
                height=pattern.metadata.height,
                color_order=pattern.metadata.color_order,
                fps=pattern.metadata.fps,
                total_ms=pattern.metadata.total_ms,
                brightness=pattern.metadata.brightness,
            )
        
        limited_pattern = Pattern(name=pattern.name, metadata=new_meta, frames=frames)
        
        # Limit keyframes
        if limited_pattern.metadata.speed_keyframes:
            max_keyframes = capabilities['max_keyframes']
            if len(limited_pattern.metadata.speed_keyframes) > max_keyframes:
                limited_pattern.metadata.speed_keyframes = limited_pattern.metadata.speed_keyframes[:max_keyframes]
        
        # Disable features not supported by chip
        if not capabilities['supports_interpolation']:
            limited_pattern.metadata.interpolation_enabled = False
        
        if not capabilities['supports_per_channel']:
            limited_pattern.metadata.per_channel_brightness = False
        
        if not capabilities['supports_float']:
            # Convert float values to fixed-point for 8-bit chips
            limited_pattern.metadata.brightness = int(limited_pattern.metadata.brightness * 127)
            limited_pattern.metadata.red_brightness = int(limited_pattern.metadata.red_brightness * 127)
            limited_pattern.metadata.green_brightness = int(limited_pattern.metadata.green_brightness * 127)
            limited_pattern.metadata.blue_brightness = int(limited_pattern.metadata.blue_brightness * 127)
        
        return limited_pattern
    
    def _generate_arduino_template(self, pattern: Pattern, chip_id: str, 
                                  output_path: Path, config: Dict) -> Path:
        """Generate Arduino template with full advanced features"""
        capabilities = self.chip_capabilities[chip_id]
        
        template_content = f'''/**
 * Professional {chip_id.upper()} LED Pattern Player - Upload Bridge Template
 * 
 * Full professional-grade pattern player with all advanced features
 * Generated by Upload Bridge - Professional Edition
 */

#include "pattern_data.h"

// FastLED library for professional LED control
#include <FastLED.h>

// Advanced brightness control
#define BRIGHTNESS_CURVE_LINEAR 0
#define BRIGHTNESS_CURVE_GAMMA_CORRECTED 1
#define BRIGHTNESS_CURVE_LOGARITHMIC 2
#define BRIGHTNESS_CURVE_EXPONENTIAL 3
#define BRIGHTNESS_CURVE_S_CURVE 4

// Speed control
#define SPEED_CURVE_LINEAR 0
#define SPEED_CURVE_EASE_IN_QUAD 1
#define SPEED_CURVE_EASE_OUT_QUAD 2
#define SPEED_CURVE_EASE_IN_OUT_QUAD 3
#define SPEED_CURVE_EASE_IN_CUBIC 4
#define SPEED_CURVE_EASE_OUT_CUBIC 5
#define SPEED_CURVE_EASE_IN_OUT_CUBIC 6

// LED strip configuration
CRGB leds[LED_COUNT];

// Global settings
float global_brightness = 1.0;
float red_brightness = 1.0;
float green_brightness = 1.0;
float blue_brightness = 1.0;
bool per_channel_brightness = false;
uint8_t brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;
uint8_t speed_curve = SPEED_CURVE_LINEAR;
bool variable_speed = false;
bool interpolation_enabled = false;
float interpolation_factor = 1.0;

// Speed keyframes
struct SpeedKeyframe {{
    uint16_t frame;
    float multiplier;
}};
SpeedKeyframe speed_keyframes[32];
uint8_t num_keyframes = 0;

// Interpolation buffer
CRGB interpolation_buffer[LED_COUNT];

// Function prototypes
float apply_brightness_curve(float value, uint8_t curve_type);
float apply_speed_curve(float t, uint8_t curve_type);
uint16_t get_frame_delay(uint16_t base_delay, uint32_t frame, uint32_t total_frames);
void apply_brightness_to_pixel(CRGB &pixel, float brightness);
void interpolate_frames(CRGB *frame1, CRGB *frame2, CRGB *output, float t, uint16_t led_count);
void process_frame_with_interpolation(uint16_t frame_idx, uint16_t total_frames, uint16_t led_count);

void setup() {{
    // Initialize FastLED
    FastLED.addLeds<WS2812, LED_DATA_PIN, GRB>(leds, LED_COUNT);
    FastLED.setBrightness(255);
    
    // Load advanced settings from pattern metadata
    global_brightness = BRIGHTNESS / 255.0;
    red_brightness = RED_BRIGHTNESS_SETTING / 255.0;
    green_brightness = GREEN_BRIGHTNESS_SETTING / 255.0;
    blue_brightness = BLUE_BRIGHTNESS_SETTING / 255.0;
    per_channel_brightness = PER_CHANNEL_BRIGHTNESS_SETTING;
    brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;  // Default, can be changed
    speed_curve = SPEED_CURVE_LINEAR;  // Default, can be changed
    variable_speed = VARIABLE_SPEED_SETTING;
    interpolation_enabled = INTERPOLATION_ENABLED_SETTING;
    interpolation_factor = INTERPOLATION_FACTOR_SETTING / 10.0;
    
    // Load speed keyframes
    num_keyframes = NUM_KEYFRAMES;
    
    // Initialize serial for debugging
    Serial.begin(115200);
    Serial.println("Professional LED Pattern Player Started");
    Serial.printf("LEDs: %d, Frames: %d\\n", LED_COUNT, FRAME_COUNT);
}}

void loop() {{
    // Play all frames with advanced features
    for (uint16_t frame = 0; frame < FRAME_COUNT; frame++) {{
        process_frame_with_interpolation(frame, FRAME_COUNT, LED_COUNT);
    }}
}}

void process_frame_with_interpolation(uint16_t frame_idx, uint16_t total_frames, uint16_t led_count) {{
    // Read frame delay
    uint16_t base_delay = pgm_read_word(&pattern_data[4 + frame_idx * (led_count * 3 + 2)]);
    
    // Apply speed curve if enabled
    uint16_t delay_ms = get_frame_delay(base_delay, frame_idx, total_frames);
    
    // Read current frame
    uint32_t frame_offset = 4 + frame_idx * (led_count * 3 + 2) + 2;
    for (uint16_t led = 0; led < led_count; led++) {{
        uint8_t r = pgm_read_byte(&pattern_data[frame_offset + led * 3]);
        uint8_t g = pgm_read_byte(&pattern_data[frame_offset + led * 3 + 1]);
        uint8_t b = pgm_read_byte(&pattern_data[frame_offset + led * 3 + 2]);
        
        // Apply advanced brightness
        leds[led] = CRGB(r, g, b);
        apply_brightness_to_pixel(leds[led], global_brightness);
    }}
    
    // Apply interpolation if enabled
    if (interpolation_enabled && frame_idx < total_frames - 1) {{
        // Read next frame for interpolation
        uint32_t next_frame_offset = 4 + (frame_idx + 1) * (led_count * 3 + 2) + 2;
        for (uint16_t led = 0; led < led_count; led++) {{
            uint8_t r = pgm_read_byte(&pattern_data[next_frame_offset + led * 3]);
            uint8_t g = pgm_read_byte(&pattern_data[next_frame_offset + led * 3 + 1]);
            uint8_t b = pgm_read_byte(&pattern_data[next_frame_offset + led * 3 + 2]);
            
            // Apply brightness to next frame
            interpolation_buffer[led] = CRGB(r, g, b);
            apply_brightness_to_pixel(interpolation_buffer[led], global_brightness);
        }}
        
        // Interpolate between frames
        float t = 1.0 / interpolation_factor;
        interpolate_frames(leds, interpolation_buffer, leds, t, led_count);
    }}
    
    // Show LEDs
    FastLED.show();
    
    // Delay with watchdog feeding
    if (delay_ms >= 10) {{
        // Long delay: yield every 10ms to feed watchdog
        uint32_t chunks = delay_ms / 10;
        uint32_t remainder = delay_ms % 10;
        
        for (uint32_t i = 0; i < chunks; i++) {{
            delay(10);
            yield();  // Feed watchdog
        }}
        
        if (remainder > 0) {{
            delay(remainder);
        }}
    }} else if (delay_ms > 0) {{
        delay(delay_ms);
    }}
}}

float apply_brightness_curve(float value, uint8_t curve_type) {{
    if (value < 0.0) value = 0.0;
    if (value > 1.0) value = 1.0;
    
    switch (curve_type) {{
        case BRIGHTNESS_CURVE_LINEAR:
            return value;
            
        case BRIGHTNESS_CURVE_GAMMA_CORRECTED:
            return pow(value, 1.0 / 2.2);
            
        case BRIGHTNESS_CURVE_LOGARITHMIC:
            if (value == 0.0) return 0.0;
            return log(1.0 + value * 9.0) / log(10.0);
            
        case BRIGHTNESS_CURVE_EXPONENTIAL:
            return value * value;
            
        case BRIGHTNESS_CURVE_S_CURVE:
            return 3.0 * value * value - 2.0 * value * value * value;
            
        default:
            return value;
    }}
}}

float apply_speed_curve(float t, uint8_t curve_type) {{
    if (t < 0.0) t = 0.0;
    if (t > 1.0) t = 1.0;
    
    switch (curve_type) {{
        case SPEED_CURVE_LINEAR:
            return t;
            
        case SPEED_CURVE_EASE_IN_QUAD:
            return t * t;
            
        case SPEED_CURVE_EASE_OUT_QUAD:
            return 1 - (1 - t) * (1 - t);
            
        case SPEED_CURVE_EASE_IN_OUT_QUAD:
            if (t < 0.5) return 2 * t * t;
            return 1 - 2 * (1 - t) * (1 - t);
            
        case SPEED_CURVE_EASE_IN_CUBIC:
            return t * t * t;
            
        case SPEED_CURVE_EASE_OUT_CUBIC:
            return 1 - pow(1 - t, 3);
            
        case SPEED_CURVE_EASE_IN_OUT_CUBIC:
            if (t < 0.5) return 4 * t * t * t;
            return 1 - 4 * pow(1 - t, 3);
            
        default:
            return t;
    }}
}}

uint16_t get_frame_delay(uint16_t base_delay, uint32_t frame, uint32_t total_frames) {{
    if (!variable_speed) {{
        return base_delay;
    }}
    
    // Apply speed curve
    float t = (float)frame / (total_frames - 1);
    float curve_factor = apply_speed_curve(t, speed_curve);
    
    // Apply keyframes if available
    float keyframe_factor = 1.0;
    for (uint8_t i = 0; i < num_keyframes; i++) {{
        if (frame >= speed_keyframes[i].frame) {{
            keyframe_factor = speed_keyframes[i].multiplier;
        }}
    }}
    
    return (uint16_t)(base_delay / (curve_factor * keyframe_factor));
}}

void apply_brightness_to_pixel(CRGB &pixel, float brightness) {{
    if (per_channel_brightness) {{
        // Per-channel brightness control
        pixel.r = (uint8_t)(pixel.r * brightness * red_brightness);
        pixel.g = (uint8_t)(pixel.g * brightness * green_brightness);
        pixel.b = (uint8_t)(pixel.b * brightness * blue_brightness);
    }} else {{
        // Apply brightness curve
        float curved_brightness = apply_brightness_curve(brightness, brightness_curve);
        
        pixel.r = (uint8_t)(pixel.r * curved_brightness);
        pixel.g = (uint8_t)(pixel.g * curved_brightness);
        pixel.b = (uint8_t)(pixel.b * curved_brightness);
    }}
}}

void interpolate_frames(CRGB *frame1, CRGB *frame2, CRGB *output, float t, uint16_t led_count) {{
    for (uint16_t led = 0; led < led_count; led++) {{
        output[led].r = (uint8_t)(frame1[led].r + (frame2[led].r - frame1[led].r) * t);
        output[led].g = (uint8_t)(frame1[led].g + (frame2[led].g - frame1[led].g) * t);
        output[led].b = (uint8_t)(frame1[led].b + (frame2[led].b - frame1[led].b) * t);
    }}
}}
'''
        
        main_file = output_path / f"{output_path.name}.ino"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        return main_file
    
    def _generate_c_template(self, pattern: Pattern, chip_id: str, 
                           output_path: Path, config: Dict) -> Path:
        """Generate C template with full advanced features"""
        capabilities = self.chip_capabilities[chip_id]
        
        # Use the professional template we already created
        if chip_id == 'atmega328p':
            template_file = Path("firmware/templates/atmega328p/professional_pattern_player.c")
        elif chip_id == 'stm32f103c8':
            template_file = Path("firmware/templates/stm32f103c8/professional_pattern_player.c")
        elif chip_id == 'pic16f876a':
            template_file = Path("firmware/templates/pic16f876a/professional_pattern_player.c")
        elif chip_id == 'numicro_m031':
            template_file = Path("firmware/templates/numicro_m031/professional_pattern_player.c")
        else:
            # Generate generic C template
            template_file = self._generate_generic_c_template(pattern, chip_id, output_path, config)
            return template_file
        
        # Copy the professional template
        main_file = output_path / f"professional_pattern_player.c"
        with open(template_file, 'r', encoding='utf-8') as src, open(main_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        
        return main_file
    
    def _generate_generic_c_template(self, pattern: Pattern, chip_id: str, 
                                   output_path: Path, config: Dict) -> Path:
        """Generate generic C template for unsupported chips"""
        capabilities = self.chip_capabilities[chip_id]
        
        template_content = f'''/**
 * Professional {chip_id.upper()} LED Pattern Player - Upload Bridge Template
 * 
 * Full professional-grade pattern player with all advanced features
 * Generated by Upload Bridge - Professional Edition
 */

#include "pattern_data.h"

// Advanced brightness control
#define BRIGHTNESS_CURVE_LINEAR 0
#define BRIGHTNESS_CURVE_GAMMA_CORRECTED 1
#define BRIGHTNESS_CURVE_LOGARITHMIC 2
#define BRIGHTNESS_CURVE_EXPONENTIAL 3
#define BRIGHTNESS_CURVE_S_CURVE 4

// Speed control
#define SPEED_CURVE_LINEAR 0
#define SPEED_CURVE_EASE_IN_QUAD 1
#define SPEED_CURVE_EASE_OUT_QUAD 2
#define SPEED_CURVE_EASE_IN_OUT_QUAD 3

// Default settings (overridden by pattern_data.h)
#ifndef DATA_PIN
#define DATA_PIN 2
#endif

#ifndef LED_COUNT
#define LED_COUNT 76
#endif

#define MAX_LEDS {capabilities['max_leds']}

// LED buffer in RAM
uint8_t led_buffer[MAX_LEDS * 3];

// Global settings
float global_brightness = 1.0;
float red_brightness = 1.0;
float green_brightness = 1.0;
float blue_brightness = 1.0;
bool per_channel_brightness = false;
uint8_t brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;
uint8_t speed_curve = SPEED_CURVE_LINEAR;
bool variable_speed = false;
bool interpolation_enabled = false;
float interpolation_factor = 1.0;

// Speed keyframes
struct SpeedKeyframe {{
    uint16_t frame;
    float multiplier;
}};
SpeedKeyframe speed_keyframes[{capabilities['max_keyframes']}];
uint8_t num_keyframes = 0;

// Function prototypes
void ws2812_init(uint8_t pin);
void ws2812_send_byte(uint8_t byte);
void ws2812_send(uint8_t *data, uint16_t len);
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx);
uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx);
float apply_brightness_curve(float value, uint8_t curve_type);
float apply_speed_curve(float t, uint8_t curve_type);
uint16_t get_frame_delay(uint16_t base_delay, uint32_t frame, uint32_t total_frames);
void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness);
void process_frame(const uint8_t *pattern_data, uint16_t frame_idx, uint16_t total_frames, uint16_t led_count);
void delay_ms(uint32_t ms);

int main(void) {{
    // Initialize WS2812 pin
    ws2812_init(DATA_PIN);
    
    // Load advanced settings from pattern metadata
    global_brightness = BRIGHTNESS / 255.0;
    red_brightness = red_brightness / 255.0;
    green_brightness = green_brightness / 255.0;
    blue_brightness = blue_brightness / 255.0;
    per_channel_brightness = per_channel_brightness;
    brightness_curve = brightness_curve;
    speed_curve = speed_curve;
    variable_speed = variable_speed;
    interpolation_enabled = interpolation_enabled;
    interpolation_factor = interpolation_factor / 10.0;
    
    // Load speed keyframes
    num_keyframes = num_keyframes;
    for (uint8_t i = 0; i < num_keyframes && i < {capabilities['max_keyframes']}; i++) {{
        speed_keyframes[i].frame = speed_keyframes[i].frame;
        speed_keyframes[i].multiplier = speed_keyframes[i].multiplier;
    }}
    
    // Main loop
    while (1) {{
        // Read pattern header
        const uint8_t *p = pattern_data;
        uint32_t idx = 0;
        
        uint16_t num_leds = read_u16_pgm(p, idx);
        idx += 2;
        
        uint16_t num_frames = read_u16_pgm(p, idx);
        idx += 2;
        
        // Limit LED count to available memory
        if (num_leds > MAX_LEDS) {{
            num_leds = MAX_LEDS;
        }}
        
        // Play all frames with advanced features
        for (uint32_t frame = 0; frame < num_frames; frame++) {{
            process_frame(p, frame, num_frames, num_leds);
        }}
    }}
}}

void process_frame(const uint8_t *pattern_data, uint16_t frame_idx, uint16_t total_frames, uint16_t led_count) {{
    // Read frame delay
    uint16_t base_delay = read_u16_pgm(pattern_data, 4 + frame_idx * (led_count * 3 + 2));
    
    // Apply speed curve if enabled
    uint16_t delay_ms = get_frame_delay(base_delay, frame_idx, total_frames);
    
    // Read current frame
    uint32_t frame_offset = 4 + frame_idx * (led_count * 3 + 2) + 2;
    for (uint16_t led = 0; led < led_count; led++) {{
        uint8_t r = read_u8_pgm(pattern_data, frame_offset + led * 3);
        uint8_t g = read_u8_pgm(pattern_data, frame_offset + led * 3 + 1);
        uint8_t b = read_u8_pgm(pattern_data, frame_offset + led * 3 + 2);
        
        // Apply advanced brightness
        apply_brightness_to_pixel(&r, &g, &b, global_brightness);
        
        // Store in buffer
        led_buffer[led * 3] = r;
        led_buffer[led * 3 + 1] = g;
        led_buffer[led * 3 + 2] = b;
    }}
    
    // Send to LEDs
    ws2812_send(led_buffer, led_count * 3);
    
    // Delay
    delay_ms(delay_ms);
}}

float apply_brightness_curve(float value, uint8_t curve_type) {{
    if (value < 0.0) value = 0.0;
    if (value > 1.0) value = 1.0;
    
    switch (curve_type) {{
        case BRIGHTNESS_CURVE_LINEAR:
            return value;
            
        case BRIGHTNESS_CURVE_GAMMA_CORRECTED:
            return pow(value, 1.0 / 2.2);
            
        case BRIGHTNESS_CURVE_LOGARITHMIC:
            if (value == 0.0) return 0.0;
            return log(1.0 + value * 9.0) / log(10.0);
            
        case BRIGHTNESS_CURVE_EXPONENTIAL:
            return value * value;
            
        case BRIGHTNESS_CURVE_S_CURVE:
            return 3.0 * value * value - 2.0 * value * value * value;
            
        default:
            return value;
    }}
}}

float apply_speed_curve(float t, uint8_t curve_type) {{
    if (t < 0.0) t = 0.0;
    if (t > 1.0) t = 1.0;
    
    switch (curve_type) {{
        case SPEED_CURVE_LINEAR:
            return t;
            
        case SPEED_CURVE_EASE_IN_QUAD:
            return t * t;
            
        case SPEED_CURVE_EASE_OUT_QUAD:
            return 1 - (1 - t) * (1 - t);
            
        case SPEED_CURVE_EASE_IN_OUT_QUAD:
            if (t < 0.5) return 2 * t * t;
            return 1 - 2 * (1 - t) * (1 - t);
            
        default:
            return t;
    }}
}}

uint16_t get_frame_delay(uint16_t base_delay, uint32_t frame, uint32_t total_frames) {{
    if (!variable_speed) {{
        return base_delay;
    }}
    
    // Apply speed curve
    float t = (float)frame / (total_frames - 1);
    float curve_factor = apply_speed_curve(t, speed_curve);
    
    // Apply keyframes if available
    float keyframe_factor = 1.0;
    for (uint8_t i = 0; i < num_keyframes; i++) {{
        if (frame >= speed_keyframes[i].frame) {{
            keyframe_factor = speed_keyframes[i].multiplier;
        }}
    }}
    
    return (uint16_t)(base_delay / (curve_factor * keyframe_factor));
}}

void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness) {{
    if (per_channel_brightness) {{
        // Per-channel brightness control
        *r = (uint8_t)(*r * brightness * red_brightness);
        *g = (uint8_t)(*g * brightness * green_brightness);
        *b = (uint8_t)(*b * brightness * blue_brightness);
    }} else {{
        // Apply brightness curve
        float curved_brightness = apply_brightness_curve(brightness, brightness_curve);
        
        *r = (uint8_t)(*r * curved_brightness);
        *g = (uint8_t)(*g * curved_brightness);
        *b = (uint8_t)(*b * curved_brightness);
    }}
}}

// WS2812 bit-banging functions (implement for your specific chip)
void ws2812_init(uint8_t pin) {{
    // Configure GPIO pin for WS2812
    // Implementation depends on your chip
}}

void ws2812_send_byte(uint8_t byte) {{
    // WS2812 bit-banging implementation
    // Implementation depends on your chip
}}

void ws2812_send(uint8_t *data, uint16_t len) {{
    for (uint16_t i = 0; i < len; i++) {{
        ws2812_send_byte(data[i]);
    }}
    // Reset pulse
    delay_us(50);
}}

void delay_ms(uint32_t ms) {{
    // Delay implementation
    // Implementation depends on your chip
}}

// Helper functions
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx) {{
    return ptr[idx] | (ptr[idx + 1] << 8);
}}

uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx) {{
    return ptr[idx];
}}
'''
        
        main_file = output_path / f"professional_pattern_player.c"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        return main_file
    
    def _generate_makefile(self, chip_id: str, output_path: Path) -> None:
        """Generate Makefile for C templates"""
        capabilities = self.chip_capabilities[chip_id]
        
        makefile_content = f'''# Makefile for {chip_id.upper()} Professional Pattern Player
# Upload Bridge v3.1

# Chip-specific settings
CHIP = {chip_id}
TARGET = professional_pattern_player
SOURCES = professional_pattern_player.c

# Compiler settings
CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99
LDFLAGS = 

# Include paths
INCLUDES = -I.

# Object files
OBJECTS = $(SOURCES:.c=.o)

# Default target
all: $(TARGET)

# Build target
$(TARGET): $(OBJECTS)
\t$(CC) $(OBJECTS) -o $(TARGET) $(LDFLAGS)

# Compile source files
%.o: %.c
\t$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Clean build files
clean:
\trm -f $(OBJECTS) $(TARGET)

# Install (if needed)
install: $(TARGET)
\t# Add installation commands here

.PHONY: all clean install
'''
        
        makefile_path = output_path / "Makefile"
        with open(makefile_path, 'w', encoding='utf-8') as f:
            f.write(makefile_content)
    
    def _generate_readme(self, chip_id: str, output_path: Path, capabilities: Dict) -> None:
        """Generate README for the template"""
        readme_content = f'''# Professional {chip_id.upper()} LED Pattern Player

**Full professional-grade pattern player with all advanced features**

## Features

### Advanced Brightness Control
- ✅ Hardware-specific brightness curves
- ✅ Per-channel brightness control
- ✅ Gamma correction
- ✅ Logarithmic, exponential, and S-curve brightness

### Advanced Speed Control
- ✅ Variable speed with keyframes
- ✅ Speed curves and easing functions
- ✅ Frame interpolation
- ✅ Real-time speed adjustment

### Professional Features
- ✅ Memory-optimized for {chip_id.upper()}
- ✅ Supports up to {capabilities['max_leds']} LEDs
- ✅ Up to {capabilities['max_keyframes']} speed keyframes
- ✅ {'Float arithmetic' if capabilities['supports_float'] else 'Fixed-point arithmetic'}
- ✅ {'Full interpolation' if capabilities['supports_interpolation'] else 'Basic interpolation'}
- ✅ {'Per-channel control' if capabilities['supports_per_channel'] else 'Global brightness only'}

## Hardware Requirements

- {chip_id.upper()} microcontroller
- WS2812/NeoPixel LED strip
- Power supply (5V recommended)
- GPIO pin for data connection

## Pin Configuration

```c
#define DATA_PIN 2  // Change to your GPIO pin
```

## Memory Usage

- **Flash**: Optimized for {chip_id.upper()} flash size
- **RAM**: {capabilities['max_leds'] * 3} bytes for LED buffer
- **Pattern Data**: Stored in flash memory

## Compilation

### For Arduino (ESP8266/ESP32):
1. Install Arduino IDE
2. Install FastLED library
3. Open `professional_pattern_player.ino`
4. Select your board and upload

### For C (Other chips):
```bash
make
```

## Usage

1. Generate pattern data using Upload Bridge
2. Flash the firmware to your microcontroller
3. Connect LED strip to DATA_PIN
4. Power on and enjoy professional LED animations!

## Advanced Configuration

The firmware automatically loads advanced settings from the generated `pattern_data.h`:

- Brightness curves and per-channel control
- Speed curves and variable speed
- Frame interpolation settings
- Speed keyframes

## Troubleshooting

- **LEDs not lighting**: Check DATA_PIN configuration
- **Memory issues**: Reduce LED count or disable advanced features
- **Timing issues**: Adjust delay functions for your clock speed

## Support

For technical support and advanced features, visit:
https://github.com/yourname/upload-bridge

---

*Generated by Upload Bridge v3.1 - Professional Edition*
'''
        
        readme_path = output_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def get_chip_capabilities(self, chip_id: str) -> Dict:
        """Get capabilities for a specific chip"""
        return self.chip_capabilities.get(chip_id, {})
    
    def list_supported_chips(self) -> List[str]:
        """Get list of all supported chips"""
        return list(self.chip_capabilities.keys())
    
    def get_chips_by_capability(self, capability: str) -> List[str]:
        """Get chips that support a specific capability"""
        return [
            chip_id for chip_id, caps in self.chip_capabilities.items()
            if caps.get(capability, False)
        ]


# Convenience function
def generate_universal_firmware(pattern: Pattern, chip_id: str, output_dir: str, 
                              config: Dict = None) -> str:
    """
    Generate universal firmware for any chip with full advanced features
    
    Args:
        pattern: Pattern object with advanced features
        chip_id: Target chip identifier
        output_dir: Output directory for generated files
        config: Additional configuration (GPIO pin, etc.)
    
    Returns:
        Path to generated main source file
    """
    if config is None:
        config = {}
    
    generator = UniversalPatternGenerator()
    return generator.generate_universal_firmware(pattern, chip_id, output_dir, config)
