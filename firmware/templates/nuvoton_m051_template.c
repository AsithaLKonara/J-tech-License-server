/*
 * Nuvoton M051 LED Pattern Firmware Template
 * 
 * This template is used by the Nuvoton M051 uploader to generate firmware
 * from LED patterns. Pattern data is embedded at compile time.
 */

#include "NUC100Series.h"
#include "pattern_data.h"

// LED pin configuration
#define LED_PORT P0
#define LED_PIN BIT0

// Main function
int main(void) {
    // Initialize system
    SYS_Init();
    
    // Configure LED pin as output
    GPIO_SetMode(LED_PORT, LED_PIN, GPIO_PMD_OUTPUT);
    GPIO_CLR(LED_PORT, LED_PIN);
    
    // Main loop
    while (1) {
        for (uint16_t frame_idx = 0; frame_idx < FRAME_COUNT; frame_idx++) {
            // Get frame pixels from pattern_data.h
            const uint8_t* frame_pixels = frames[frame_idx];
            uint16_t frame_duration = frame_durations[frame_idx];
            
            // Send frame to LEDs (simplified)
            // In production, this would use SPI or bit-banging for WS2812
            for (uint16_t i = 0; i < LED_COUNT; i++) {
                // Send pixel data (simplified)
                // Actual implementation would handle WS2812 protocol
                // WS2812_Send(frame_pixels + (i * 3), 3);
            }
            
            // Wait for frame duration
            delay_ms(frame_duration);
        }
    }
}

// Delay function
void delay_ms(uint16_t ms) {
    for (uint16_t i = 0; i < ms; i++) {
        CLK_SysTickDelay(1000);  // 1ms delay
    }
}

