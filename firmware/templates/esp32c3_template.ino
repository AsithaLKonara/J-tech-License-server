/*
 * ESP32-C3 LED Pattern Firmware Template
 * 
 * This template is used by the ESP32-C3 uploader to generate firmware
 * from LED patterns. Pattern data is embedded at compile time.
 */

#include <FastLED.h>

// Pattern data (injected at build time)
#include "pattern_data.h"

// Configuration
#define LED_PIN 3
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
#define NUM_LEDS LED_COUNT

CRGB leds[NUM_LEDS];

void setup() {
    FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, NUM_LEDS);
    FastLED.setBrightness(255);
}

void loop() {
    for (int frame_idx = 0; frame_idx < FRAME_COUNT; frame_idx++) {
        // Get frame pixels from pattern_data.h
        const CRGB* frame_pixels = frames[frame_idx];
        uint16_t frame_duration = frame_durations[frame_idx];
        
        // Copy frame to LEDs
        for (int i = 0; i < NUM_LEDS; i++) {
            leds[i] = frame_pixels[i];
        }
        
        FastLED.show();
        delay(frame_duration);
    }
}

