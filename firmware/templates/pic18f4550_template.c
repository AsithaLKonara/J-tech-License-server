/*
 * PIC18F4550 LED Pattern Firmware Template
 * 
 * This template is used by the PIC18F4550 uploader to generate firmware
 * from LED patterns. Pattern data is embedded at compile time.
 */

#include <xc.h>
#include "pattern_data.h"

// Configuration
#pragma config FOSC = INTOSC_HS
#pragma config WDT = OFF
#pragma config LVP = OFF

// LED pin configuration
#define LED_PORT PORTB
#define LED_PIN RB0
#define LED_TRIS TRISB0

// Main function
void main(void) {
    // Initialize system
    OSCCON = 0x70;  // 8MHz internal oscillator
    
    // Configure LED pin as output
    LED_TRIS = 0;  // Output
    LED_PORT = 0;  // Low
    
    // Main loop
    while (1) {
        for (uint8_t frame_idx = 0; frame_idx < FRAME_COUNT; frame_idx++) {
            // Get frame pixels from pattern_data.h
            const uint8_t* frame_pixels = frames[frame_idx];
            uint16_t frame_duration = frame_durations[frame_idx];
            
            // Send frame to LEDs (simplified)
            // In production, this would use SPI or bit-banging for WS2812
            for (uint8_t i = 0; i < LED_COUNT; i++) {
                // Send pixel data (simplified)
                // Actual implementation would handle WS2812 protocol
            }
            
            // Wait for frame duration
            delay_ms(frame_duration);
        }
    }
}

// Delay function
void delay_ms(uint16_t ms) {
    for (uint16_t i = 0; i < ms; i++) {
        for (volatile uint16_t j = 0; j < 1000; j++);
    }
}

