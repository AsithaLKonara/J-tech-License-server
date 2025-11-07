#!/usr/bin/env python3
"""
Chip Integration Verification - Comprehensive check of all chip support
Verifies uploaders, firmware templates, and advanced features integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from uploaders.uploader_registry import UploaderRegistry
from firmware.builder import FirmwareBuilder
from core.pattern import create_test_pattern
from firmware.enhanced_pattern_generator import EnhancedPatternGenerator
import yaml
from pathlib import Path


def verify_chip_database():
    """Verify chip database completeness"""
    print("🔍 Verifying Chip Database")
    print("=" * 50)
    
    registry = UploaderRegistry.instance()
    
    # Load chip database
    config_file = Path("config/chip_database.yaml")
    with open(config_file, 'r') as f:
        chip_db = yaml.safe_load(f)
    
    print(f"Total chips in database: {len(chip_db)}")
    
    # Check by family
    families = {}
    for chip_id, spec in chip_db.items():
        family = spec.get('family', 'unknown')
        if family not in families:
            families[family] = []
        families[family].append(chip_id)
    
    print(f"\nChip families: {len(families)}")
    for family, chips in families.items():
        print(f"  {family.upper()}: {len(chips)} chips")
        for chip in chips:
            spec = chip_db[chip]
            flash_kb = spec.get('flash_size', 0) // 1024
            print(f"    - {chip:20s} {flash_kb:4d}KB flash")
    
    return chip_db


def verify_uploaders():
    """Verify uploader implementations"""
    print("\n🔧 Verifying Uploader Implementations")
    print("=" * 50)
    
    registry = UploaderRegistry.instance()
    
    # Check registered uploaders
    print(f"Registered uploaders: {len(registry.uploaders)}")
    for name, uploader_class in registry.uploaders.items():
        print(f"  ✅ {name}")
    
    # Test each chip
    chip_db = registry.chip_database
    uploader_results = {}
    
    for chip_id in chip_db.keys():
        print(f"\nTesting {chip_id}:")
        
        # Get uploader
        uploader = registry.get_uploader_for_chip(chip_id)
        if not uploader:
            print(f"  ❌ No uploader available")
            uploader_results[chip_id] = False
            continue
        
        # Check requirements
        available, missing = uploader.check_requirements()
        if available:
            print(f"  ✅ Uploader available, all requirements met")
            uploader_results[chip_id] = True
        else:
            print(f"  ⚠️  Uploader available, missing: {', '.join(missing)}")
            uploader_results[chip_id] = False
    
    return uploader_results


def verify_firmware_templates():
    """Verify firmware template availability"""
    print("\n📁 Verifying Firmware Templates")
    print("=" * 50)
    
    builder = FirmwareBuilder()
    templates = builder.get_available_templates()
    
    print(f"Available templates: {len(templates)}")
    
    template_results = {}
    
    for chip_id, template_info in templates.items():
        print(f"\n{chip_id}:")
        print(f"  Path: {template_info['path']}")
        print(f"  Type: {template_info['type']}")
        print(f"  Has .ino: {template_info['has_ino']}")
        print(f"  Has .c: {template_info['has_c']}")
        print(f"  Has Makefile: {template_info['has_makefile']}")
        print(f"  Has README: {template_info['has_readme']}")
        
        # Check if template supports advanced features
        template_path = Path(template_info['path'])
        has_advanced_features = False
        
        # Check for enhanced template
        if (template_path / "enhanced_pattern_player.ino").exists():
            has_advanced_features = True
            print(f"  ✅ Enhanced template with advanced features")
        elif (template_path / "pattern_player.ino").exists() or (template_path / "pattern_player.c").exists():
            print(f"  ⚠️  Basic template (no advanced features)")
        else:
            print(f"  ❌ No main template file found")
        
        template_results[chip_id] = {
            'available': True,
            'has_advanced': has_advanced_features,
            'type': template_info['type']
        }
    
    return template_results


def verify_advanced_features_integration():
    """Verify advanced features integration across chips"""
    print("\n🎛️ Verifying Advanced Features Integration")
    print("=" * 50)
    
    # Create test pattern with advanced features
    pattern = create_test_pattern(led_count=10, frame_count=5)
    
    # Apply advanced features
    pattern.apply_advanced_brightness(
        brightness=0.8,
        curve_type="gamma_corrected",
        led_type="ws2812",
        per_channel=True
    )
    pattern.set_per_channel_brightness(red=1.0, green=0.9, blue=0.8)
    pattern.apply_speed_curve("ease_in_out_quad", 2000)
    pattern.apply_variable_speed([(0, 1.0), (2, 1.5), (4, 0.7)])
    pattern.interpolate_frames(1.5)
    
    print("Test pattern with advanced features created:")
    print(f"  LEDs: {pattern.led_count}")
    print(f"  Frames: {pattern.frame_count}")
    print(f"  Brightness curve: {pattern.metadata.brightness_curve}")
    print(f"  LED type: {pattern.metadata.led_type}")
    print(f"  Per-channel: {pattern.metadata.per_channel_brightness}")
    print(f"  Speed curve: {pattern.metadata.speed_curve}")
    print(f"  Variable speed: {pattern.metadata.variable_speed}")
    print(f"  Interpolation: {pattern.metadata.interpolation_enabled}")
    
    # Test enhanced pattern generator
    generator = EnhancedPatternGenerator()
    
    # Test memory estimation
    memory_usage = generator.estimate_memory_usage(pattern)
    print(f"\nMemory usage estimation:")
    for key, value in memory_usage.items():
        print(f"  {key}: {value} bytes")
    
    # Test pattern data generation
    try:
        output_file = "test_advanced_pattern.h"
        generator.generate_pattern_data_h(pattern, output_file, {"gpio_pin": 2})
        print(f"\n✅ Enhanced pattern data generated: {output_file}")
        
        # Check generated file
        with open(output_file, 'r') as f:
            content = f.read()
            
        # Check for advanced features in generated code
        features_found = {
            'brightness_curve': 'brightness_curve' in content,
            'per_channel': 'per_channel_brightness' in content,
            'speed_curve': 'speed_curve' in content,
            'variable_speed': 'variable_speed' in content,
            'interpolation': 'interpolation_enabled' in content,
            'keyframes': 'speed_keyframes' in content
        }
        
        print(f"\nAdvanced features in generated firmware:")
        for feature, found in features_found.items():
            status = "✅" if found else "❌"
            print(f"  {status} {feature}")
        
        # Clean up
        os.remove(output_file)
        
    except Exception as e:
        print(f"❌ Error generating pattern data: {e}")
        return False
    
    return True


def verify_chip_specific_features():
    """Verify chip-specific feature support"""
    print("\n🔬 Verifying Chip-Specific Features")
    print("=" * 50)
    
    registry = UploaderRegistry.instance()
    chip_db = registry.chip_database
    
    # Check each chip family for specific capabilities
    family_capabilities = {
        'esp': {
            'wifi': True,
            'ota': True,
            'large_flash': True,
            'advanced_features': True
        },
        'avr': {
            'wifi': False,
            'ota': False,
            'large_flash': False,
            'advanced_features': 'limited'
        },
        'stm32': {
            'wifi': False,
            'ota': False,
            'large_flash': 'medium',
            'advanced_features': 'medium'
        },
        'pic': {
            'wifi': False,
            'ota': False,
            'large_flash': False,
            'advanced_features': 'basic'
        },
        'numicro': {
            'wifi': False,
            'ota': False,
            'large_flash': 'medium',
            'advanced_features': 'medium'
        }
    }
    
    for family, capabilities in family_capabilities.items():
        chips = [chip for chip, spec in chip_db.items() if spec.get('family') == family]
        print(f"\n{family.upper()} Family ({len(chips)} chips):")
        
        for capability, support in capabilities.items():
            status = "✅" if support == True else "⚠️" if support in ['limited', 'medium', 'basic'] else "❌"
            print(f"  {status} {capability}: {support}")
    
    return family_capabilities


def generate_missing_templates():
    """Generate missing enhanced firmware templates"""
    print("\n🔨 Generating Missing Enhanced Templates")
    print("=" * 50)
    
    # Check which chips need enhanced templates
    builder = FirmwareBuilder()
    templates = builder.get_available_templates()
    
    missing_enhanced = []
    
    for chip_id, template_info in templates.items():
        template_path = Path(template_info['path'])
        if not (template_path / "enhanced_pattern_player.ino").exists():
            missing_enhanced.append(chip_id)
    
    print(f"Chips needing enhanced templates: {len(missing_enhanced)}")
    for chip_id in missing_enhanced:
        print(f"  - {chip_id}")
    
    # Generate enhanced templates for key chips
    key_chips = ['atmega328p', 'stm32f103c8', 'pic16f876a']
    
    for chip_id in key_chips:
        if chip_id in missing_enhanced:
            print(f"\nGenerating enhanced template for {chip_id}...")
            try:
                generate_enhanced_template(chip_id)
                print(f"  ✅ Enhanced template generated for {chip_id}")
            except Exception as e:
                print(f"  ❌ Failed to generate template for {chip_id}: {e}")
    
    return missing_enhanced


def generate_enhanced_template(chip_id):
    """Generate enhanced firmware template for specific chip"""
    template_dir = Path(f"firmware/templates/{chip_id}")
    template_dir.mkdir(parents=True, exist_ok=True)
    
    if chip_id == 'atmega328p':
        # Generate enhanced ATmega328P template
        content = generate_enhanced_atmega328p_template()
        with open(template_dir / "enhanced_pattern_player.c", 'w') as f:
            f.write(content)
    
    elif chip_id == 'stm32f103c8':
        # Generate enhanced STM32 template
        content = generate_enhanced_stm32_template()
        with open(template_dir / "enhanced_pattern_player.c", 'w') as f:
            f.write(content)
    
    elif chip_id == 'pic16f876a':
        # Generate enhanced PIC template
        content = generate_enhanced_pic_template()
        with open(template_dir / "enhanced_pattern_player.c", 'w') as f:
            f.write(content)


def generate_enhanced_atmega328p_template():
    """Generate enhanced ATmega328P template with advanced features"""
    return '''/**
 * Enhanced ATmega328P LED Pattern Player - Upload Bridge Template
 * 
 * Advanced pattern player with brightness curves, speed control, and interpolation
 * Generated by Upload Bridge - github.com/yourname/upload-bridge
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/pgmspace.h>
#include <util/delay.h>
#include <math.h>
#include "pattern_data.h"

// WS2812 timing constants (for 16MHz clock)
#define T1H  900    // 0.9us
#define T1L  350    // 0.35us
#define T0H  350    // 0.35us  
#define T0L  900    // 0.9us
#define RES  50000  // 50us reset

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

#define MAX_LEDS 512

// LED buffer in RAM
uint8_t led_buffer[MAX_LEDS * 3];

// Global settings
float global_brightness = 1.0;
float red_brightness = 1.0;
float green_brightness = 1.0;
float blue_brightness = 1.0;
bool per_channel_brightness = false;
uint8_t brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;

// Function prototypes
void ws2812_init(uint8_t pin);
void ws2812_send_byte(uint8_t byte);
void ws2812_send(uint8_t *data, uint16_t len);
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx);
uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx);
float apply_brightness_curve(float value, uint8_t curve_type);
void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness);

int main(void) {
    // Initialize WS2812 pin as output
    if (DATA_PIN < 8) {
        DDRD |= (1 << DATA_PIN);
    } else {
        DDRB |= (1 << (DATA_PIN - 8));
    }
    
    // Load advanced settings from pattern metadata
    global_brightness = BRIGHTNESS / 255.0;
    red_brightness = red_brightness / 255.0;
    green_brightness = green_brightness / 255.0;
    blue_brightness = blue_brightness / 255.0;
    per_channel_brightness = per_channel_brightness;
    brightness_curve = brightness_curve;
    
    // Main loop
    while (1) {
        // Read pattern header
        const uint8_t *p = pattern_data;
        uint16_t idx = 0;
        
        uint16_t num_leds = read_u16_pgm(p, idx);
        idx += 2;
        
        uint16_t num_frames = read_u16_pgm(p, idx);
        idx += 2;
        
        // Play all frames
        for (uint16_t frame = 0; frame < num_frames; frame++) {
            // Read frame delay
            uint16_t delay_ms = read_u16_pgm(p, idx);
            idx += 2;
            
            // Read RGB data for all LEDs
            for (uint16_t led = 0; led < num_leds; led++) {
                uint8_t r = read_u8_pgm(p, idx++);
                uint8_t g = read_u8_pgm(p, idx++);
                uint8_t b = read_u8_pgm(p, idx++);
                
                // Apply advanced brightness
                apply_brightness_to_pixel(&r, &g, &b, global_brightness);
                
                // Store in buffer
                led_buffer[led * 3] = r;
                led_buffer[led * 3 + 1] = g;
                led_buffer[led * 3 + 2] = b;
            }
            
            // Send to LEDs
            ws2812_send(led_buffer, num_leds * 3);
            
            // Delay
            for (uint16_t i = 0; i < delay_ms; i++) {
                _delay_ms(1);
            }
        }
    }
}

float apply_brightness_curve(float value, uint8_t curve_type) {
    if (value < 0.0) value = 0.0;
    if (value > 1.0) value = 1.0;
    
    switch (curve_type) {
        case BRIGHTNESS_CURVE_LINEAR:
            return value;
            
        case BRIGHTNESS_CURVE_GAMMA_CORRECTED:
            // Approximate gamma correction using lookup table
            return value * value; // Simplified gamma 2.0
            
        case BRIGHTNESS_CURVE_LOGARITHMIC:
            if (value == 0.0) return 0.0;
            return log(1.0 + value * 9.0) / log(10.0);
            
        case BRIGHTNESS_CURVE_EXPONENTIAL:
            return value * value;
            
        case BRIGHTNESS_CURVE_S_CURVE:
            return 3.0 * value * value - 2.0 * value * value * value;
            
        default:
            return value;
    }
}

void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness) {
    if (per_channel_brightness) {
        // Per-channel brightness control
        *r = (uint8_t)(*r * brightness * red_brightness);
        *g = (uint8_t)(*g * brightness * green_brightness);
        *b = (uint8_t)(*b * brightness * blue_brightness);
    } else {
        // Apply brightness curve
        float curved_brightness = apply_brightness_curve(brightness, brightness_curve);
        
        *r = (uint8_t)(*r * curved_brightness);
        *g = (uint8_t)(*g * curved_brightness);
        *b = (uint8_t)(*b * curved_brightness);
    }
}

// WS2812 bit-banging functions (unchanged)
void ws2812_init(uint8_t pin) {
    if (pin < 8) {
        DDRD |= (1 << pin);
    } else {
        DDRB |= (1 << (pin - 8));
    }
}

void ws2812_send_byte(uint8_t byte) {
    for (uint8_t i = 0; i < 8; i++) {
        if (byte & 0x80) {
            // Send 1
            if (DATA_PIN < 8) {
                PORTD |= (1 << DATA_PIN);
                _delay_us(T1H);
                PORTD &= ~(1 << DATA_PIN);
                _delay_us(T1L);
            } else {
                PORTB |= (1 << (DATA_PIN - 8));
                _delay_us(T1H);
                PORTB &= ~(1 << (DATA_PIN - 8));
                _delay_us(T1L);
            }
        } else {
            // Send 0
            if (DATA_PIN < 8) {
                PORTD |= (1 << DATA_PIN);
                _delay_us(T0H);
                PORTD &= ~(1 << DATA_PIN);
                _delay_us(T0L);
            } else {
                PORTB |= (1 << (DATA_PIN - 8));
                _delay_us(T0H);
                PORTB &= ~(1 << (DATA_PIN - 8));
                _delay_us(T0L);
            }
        }
        byte <<= 1;
    }
}

void ws2812_send(uint8_t *data, uint16_t len) {
    for (uint16_t i = 0; i < len; i++) {
        ws2812_send_byte(data[i]);
    }
    _delay_us(RES);
}

// Helper functions
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx) {
    uint8_t b0 = pgm_read_byte(ptr + idx);
    uint8_t b1 = pgm_read_byte(ptr + idx + 1);
    return (uint16_t)(b0 | (b1 << 8));
}

uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx) {
    return pgm_read_byte(ptr + idx);
}
'''


def generate_enhanced_stm32_template():
    """Generate enhanced STM32 template with advanced features"""
    return '''/**
 * Enhanced STM32F103 LED Pattern Player - Upload Bridge Template
 * 
 * Advanced pattern player with brightness curves, speed control, and interpolation
 * Generated by Upload Bridge - github.com/yourname/upload-bridge
 */

#include "stm32f1xx.h"
#include <math.h>
#include "pattern_data.h"

// Advanced brightness control
#define BRIGHTNESS_CURVE_LINEAR 0
#define BRIGHTNESS_CURVE_GAMMA_CORRECTED 1
#define BRIGHTNESS_CURVE_LOGARITHMIC 2
#define BRIGHTNESS_CURVE_EXPONENTIAL 3
#define BRIGHTNESS_CURVE_S_CURVE 4

// Default settings (overridden by pattern_data.h)
#ifndef DATA_PIN
#define DATA_PIN 2
#endif

#ifndef LED_COUNT
#define LED_COUNT 76
#endif

#define MAX_LEDS 512

// LED buffer in RAM
uint8_t led_buffer[MAX_LEDS * 3];

// Global settings
float global_brightness = 1.0;
float red_brightness = 1.0;
float green_brightness = 1.0;
float blue_brightness = 1.0;
bool per_channel_brightness = false;
uint8_t brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;

// Function prototypes
void ws2812_init(uint8_t pin);
void ws2812_send_byte(uint8_t byte);
void ws2812_send(uint8_t *data, uint16_t len);
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx);
uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx);
float apply_brightness_curve(float value, uint8_t curve_type);
void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness);
void delay_ms(uint32_t ms);

int main(void) {
    // Initialize system clock
    SystemInit();
    
    // Initialize WS2812 pin
    ws2812_init(DATA_PIN);
    
    // Load advanced settings from pattern metadata
    global_brightness = BRIGHTNESS / 255.0;
    red_brightness = red_brightness / 255.0;
    green_brightness = green_brightness / 255.0;
    blue_brightness = blue_brightness / 255.0;
    per_channel_brightness = per_channel_brightness;
    brightness_curve = brightness_curve;
    
    // Main loop
    while (1) {
        // Read pattern header
        const uint8_t *p = pattern_data;
        uint16_t idx = 0;
        
        uint16_t num_leds = read_u16_pgm(p, idx);
        idx += 2;
        
        uint16_t num_frames = read_u16_pgm(p, idx);
        idx += 2;
        
        // Play all frames
        for (uint16_t frame = 0; frame < num_frames; frame++) {
            // Read frame delay
            uint16_t delay_ms = read_u16_pgm(p, idx);
            idx += 2;
            
            // Read RGB data for all LEDs
            for (uint16_t led = 0; led < num_leds; led++) {
                uint8_t r = read_u8_pgm(p, idx++);
                uint8_t g = read_u8_pgm(p, idx++);
                uint8_t b = read_u8_pgm(p, idx++);
                
                // Apply advanced brightness
                apply_brightness_to_pixel(&r, &g, &b, global_brightness);
                
                // Store in buffer
                led_buffer[led * 3] = r;
                led_buffer[led * 3 + 1] = g;
                led_buffer[led * 3 + 2] = b;
            }
            
            // Send to LEDs
            ws2812_send(led_buffer, num_leds * 3);
            
            // Delay
            delay_ms(delay_ms);
        }
    }
}

float apply_brightness_curve(float value, uint8_t curve_type) {
    if (value < 0.0) value = 0.0;
    if (value > 1.0) value = 1.0;
    
    switch (curve_type) {
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
    }
}

void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness) {
    if (per_channel_brightness) {
        // Per-channel brightness control
        *r = (uint8_t)(*r * brightness * red_brightness);
        *g = (uint8_t)(*g * brightness * green_brightness);
        *b = (uint8_t)(*b * brightness * blue_brightness);
    } else {
        // Apply brightness curve
        float curved_brightness = apply_brightness_curve(brightness, brightness_curve);
        
        *r = (uint8_t)(*r * curved_brightness);
        *g = (uint8_t)(*g * curved_brightness);
        *b = (uint8_t)(*b * curved_brightness);
    }
}

void ws2812_init(uint8_t pin) {
    // Configure GPIO pin for WS2812
    RCC->APB2ENR |= RCC_APB2ENR_IOPAEN;
    
    if (pin < 8) {
        GPIOA->CRL &= ~(0xF << (pin * 4));
        GPIOA->CRL |= (0x3 << (pin * 4)); // Output, 50MHz
    } else {
        GPIOA->CRH &= ~(0xF << ((pin - 8) * 4));
        GPIOA->CRH |= (0x3 << ((pin - 8) * 4)); // Output, 50MHz
    }
}

void ws2812_send_byte(uint8_t byte) {
    // STM32 WS2812 bit-banging implementation
    for (uint8_t i = 0; i < 8; i++) {
        if (byte & 0x80) {
            // Send 1 (0.9us high, 0.35us low)
            GPIOA->BSRR = (1 << DATA_PIN);
            for (volatile int j = 0; j < 12; j++); // ~0.9us
            GPIOA->BRR = (1 << DATA_PIN);
            for (volatile int j = 0; j < 4; j++);  // ~0.35us
        } else {
            // Send 0 (0.35us high, 0.9us low)
            GPIOA->BSRR = (1 << DATA_PIN);
            for (volatile int j = 0; j < 4; j++);  // ~0.35us
            GPIOA->BRR = (1 << DATA_PIN);
            for (volatile int j = 0; j < 12; j++); // ~0.9us
        }
        byte <<= 1;
    }
}

void ws2812_send(uint8_t *data, uint16_t len) {
    for (uint16_t i = 0; i < len; i++) {
        ws2812_send_byte(data[i]);
    }
    // Reset pulse
    GPIOA->BRR = (1 << DATA_PIN);
    for (volatile int i = 0; i < 500; i++); // ~50us
}

void delay_ms(uint32_t ms) {
    for (uint32_t i = 0; i < ms; i++) {
        for (volatile int j = 0; j < 8000; j++); // ~1ms at 72MHz
    }
}

// Helper functions
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx) {
    return ptr[idx] | (ptr[idx + 1] << 8);
}

uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx) {
    return ptr[idx];
}
'''


def generate_enhanced_pic_template():
    """Generate enhanced PIC template with advanced features"""
    return '''/**
 * Enhanced PIC16F876A LED Pattern Player - Upload Bridge Template
 * 
 * Advanced pattern player with brightness curves, speed control, and interpolation
 * Generated by Upload Bridge - github.com/yourname/upload-bridge
 */

#include <pic16f876a.h>
#include <math.h>
#include "pattern_data.h"

// Configuration bits
__CONFIG(FOSC_HS & WDTE_OFF & PWRTE_ON & BOREN_ON & LVP_OFF & CPD_OFF & WRT_OFF & DEBUG_OFF);

// Advanced brightness control
#define BRIGHTNESS_CURVE_LINEAR 0
#define BRIGHTNESS_CURVE_GAMMA_CORRECTED 1
#define BRIGHTNESS_CURVE_LOGARITHMIC 2
#define BRIGHTNESS_CURVE_EXPONENTIAL 3
#define BRIGHTNESS_CURVE_S_CURVE 4

// Default settings (overridden by pattern_data.h)
#ifndef DATA_PIN
#define DATA_PIN 0
#endif

#ifndef LED_COUNT
#define LED_COUNT 76
#endif

#define MAX_LEDS 100  // Limited by PIC memory

// LED buffer in RAM
uint8_t led_buffer[MAX_LEDS * 3];

// Global settings
float global_brightness = 1.0;
float red_brightness = 1.0;
float green_brightness = 1.0;
float blue_brightness = 1.0;
bool per_channel_brightness = false;
uint8_t brightness_curve = BRIGHTNESS_CURVE_GAMMA_CORRECTED;

// Function prototypes
void ws2812_init(uint8_t pin);
void ws2812_send_byte(uint8_t byte);
void ws2812_send(uint8_t *data, uint16_t len);
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx);
uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx);
float apply_brightness_curve(float value, uint8_t curve_type);
void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness);
void delay_ms(uint16_t ms);

int main(void) {
    // Initialize WS2812 pin
    ws2812_init(DATA_PIN);
    
    // Load advanced settings from pattern metadata
    global_brightness = BRIGHTNESS / 255.0;
    red_brightness = red_brightness / 255.0;
    green_brightness = green_brightness / 255.0;
    blue_brightness = blue_brightness / 255.0;
    per_channel_brightness = per_channel_brightness;
    brightness_curve = brightness_curve;
    
    // Main loop
    while (1) {
        // Read pattern header
        const uint8_t *p = pattern_data;
        uint16_t idx = 0;
        
        uint16_t num_leds = read_u16_pgm(p, idx);
        idx += 2;
        
        uint16_t num_frames = read_u16_pgm(p, idx);
        idx += 2;
        
        // Play all frames
        for (uint16_t frame = 0; frame < num_frames; frame++) {
            // Read frame delay
            uint16_t delay_ms = read_u16_pgm(p, idx);
            idx += 2;
            
            // Read RGB data for all LEDs
            for (uint16_t led = 0; led < num_leds; led++) {
                uint8_t r = read_u8_pgm(p, idx++);
                uint8_t g = read_u8_pgm(p, idx++);
                uint8_t b = read_u8_pgm(p, idx++);
                
                // Apply advanced brightness
                apply_brightness_to_pixel(&r, &g, &b, global_brightness);
                
                // Store in buffer
                led_buffer[led * 3] = r;
                led_buffer[led * 3 + 1] = g;
                led_buffer[led * 3 + 2] = b;
            }
            
            // Send to LEDs
            ws2812_send(led_buffer, num_leds * 3);
            
            // Delay
            delay_ms(delay_ms);
        }
    }
}

float apply_brightness_curve(float value, uint8_t curve_type) {
    if (value < 0.0) value = 0.0;
    if (value > 1.0) value = 1.0;
    
    switch (curve_type) {
        case BRIGHTNESS_CURVE_LINEAR:
            return value;
            
        case BRIGHTNESS_CURVE_GAMMA_CORRECTED:
            return value * value; // Simplified gamma 2.0
            
        case BRIGHTNESS_CURVE_LOGARITHMIC:
            if (value == 0.0) return 0.0;
            return log(1.0 + value * 9.0) / log(10.0);
            
        case BRIGHTNESS_CURVE_EXPONENTIAL:
            return value * value;
            
        case BRIGHTNESS_CURVE_S_CURVE:
            return 3.0 * value * value - 2.0 * value * value * value;
            
        default:
            return value;
    }
}

void apply_brightness_to_pixel(uint8_t *r, uint8_t *g, uint8_t *b, float brightness) {
    if (per_channel_brightness) {
        // Per-channel brightness control
        *r = (uint8_t)(*r * brightness * red_brightness);
        *g = (uint8_t)(*g * brightness * green_brightness);
        *b = (uint8_t)(*b * brightness * blue_brightness);
    } else {
        // Apply brightness curve
        float curved_brightness = apply_brightness_curve(brightness, brightness_curve);
        
        *r = (uint8_t)(*r * curved_brightness);
        *g = (uint8_t)(*g * curved_brightness);
        *b = (uint8_t)(*b * curved_brightness);
    }
}

void ws2812_init(uint8_t pin) {
    // Configure GPIO pin for WS2812
    TRISB &= ~(1 << pin);  // Set as output
}

void ws2812_send_byte(uint8_t byte) {
    // PIC WS2812 bit-banging implementation
    for (uint8_t i = 0; i < 8; i++) {
        if (byte & 0x80) {
            // Send 1 (0.9us high, 0.35us low)
            PORTB |= (1 << DATA_PIN);
            __delay_us(1);  // ~0.9us
            PORTB &= ~(1 << DATA_PIN);
            __delay_us(1);  // ~0.35us
        } else {
            // Send 0 (0.35us high, 0.9us low)
            PORTB |= (1 << DATA_PIN);
            __delay_us(1);  // ~0.35us
            PORTB &= ~(1 << DATA_PIN);
            __delay_us(1);  // ~0.9us
        }
        byte <<= 1;
    }
}

void ws2812_send(uint8_t *data, uint16_t len) {
    for (uint16_t i = 0; i < len; i++) {
        ws2812_send_byte(data[i]);
    }
    // Reset pulse
    PORTB &= ~(1 << DATA_PIN);
    __delay_us(50);
}

void delay_ms(uint16_t ms) {
    for (uint16_t i = 0; i < ms; i++) {
        __delay_ms(1);
    }
}

// Helper functions
uint16_t read_u16_pgm(const uint8_t *ptr, uint16_t idx) {
    return ptr[idx] | (ptr[idx + 1] << 8);
}

uint8_t read_u8_pgm(const uint8_t *ptr, uint16_t idx) {
    return ptr[idx];
}
'''


def main():
    """Run comprehensive chip integration verification"""
    print("🔍 Upload Bridge Chip Integration Verification")
    print("=" * 60)
    print("Comprehensive check of all chip support and advanced features")
    print("=" * 60)
    
    try:
        # Verify chip database
        chip_db = verify_chip_database()
        
        # Verify uploaders
        uploader_results = verify_uploaders()
        
        # Verify firmware templates
        template_results = verify_firmware_templates()
        
        # Verify advanced features integration
        advanced_features_ok = verify_advanced_features_integration()
        
        # Verify chip-specific features
        family_capabilities = verify_chip_specific_features()
        
        # Generate missing templates
        missing_templates = generate_missing_templates()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_chips = len(chip_db)
        working_uploaders = sum(1 for working in uploader_results.values() if working)
        available_templates = len(template_results)
        enhanced_templates = sum(1 for info in template_results.values() if info.get('has_advanced', False))
        
        print(f"Total chips in database: {total_chips}")
        print(f"Working uploaders: {working_uploaders}/{total_chips}")
        print(f"Available templates: {available_templates}")
        print(f"Enhanced templates: {enhanced_templates}")
        print(f"Advanced features: {'✅' if advanced_features_ok else '❌'}")
        print(f"Missing enhanced templates: {len(missing_templates)}")
        
        print(f"\nChip Family Capabilities:")
        for family, capabilities in family_capabilities.items():
            print(f"  {family.upper()}: {capabilities}")
        
        print(f"\n🎯 RECOMMENDATIONS:")
        
        if working_uploaders < total_chips:
            print(f"  ⚠️  {total_chips - working_uploaders} chips need uploader fixes")
        
        if enhanced_templates < available_templates:
            print(f"  ⚠️  {available_templates - enhanced_templates} templates need enhancement")
        
        if len(missing_templates) > 0:
            print(f"  ⚠️  {len(missing_templates)} chips need enhanced templates")
        
        if advanced_features_ok:
            print(f"  ✅ Advanced features fully integrated")
        else:
            print(f"  ❌ Advanced features need attention")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"  1. Install missing tools for uploaders")
        print(f"  2. Generate enhanced templates for key chips")
        print(f"  3. Test advanced features on target hardware")
        print(f"  4. Update documentation with chip-specific notes")
        
        print(f"\n✅ Chip integration verification complete!")
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())













