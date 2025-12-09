# WLED Export Format

## Overview

The WLED export format creates JSON files compatible with WLED (ESP32-based LED controller firmware) and can be used with Falcon Player (FPP) for light show management.

## Format Specification

### File Structure

```json
{
  "name": "Pattern Name",
  "leds": 100,
  "description": "Pattern description",
  "layout": {
    "type": "multi_ring",
    "circular_led_count": 36,
    "multi_ring_count": 3,
    "ring_led_counts": [8, 12, 16],
    "ring_radii": [5.0, 10.0, 15.0],
    "ring_spacing": 5.0
  },
  "frames": [
    {
      "dur": 100,
      "data": [
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
        ...
      ]
    }
  ]
}
```

### Fields

- **name**: Pattern name
- **leds**: Total number of LEDs (physical LED count)
- **description**: Optional pattern description
- **layout**: Layout metadata (for Budurasmala patterns)
  - **type**: Layout type (`rectangular`, `circular`, `multi_ring`, `radial_rays`)
  - **circular_led_count**: Physical LED count for circular layouts
  - For **multi_ring**: `multi_ring_count`, `ring_led_counts`, `ring_radii`, `ring_spacing`
  - For **radial_rays**: `ray_count`, `leds_per_ray`, `ray_spacing_angle`
- **frames**: Array of frame objects
  - **dur**: Frame duration in milliseconds
  - **data**: Array of RGB values `[R, G, B]` for each LED

## Usage

### Exporting to WLED

1. Create or load a pattern in Upload Bridge
2. Go to Export dialog
3. Select "WLED" format
4. Save the JSON file
5. Import into WLED via web interface or API

### Budurasmala Support

The export format includes special metadata for Budurasmala layouts:

- **Multi-ring patterns**: Exports ring configuration (count, LED counts per ring, radii)
- **Radial ray patterns**: Exports ray configuration (ray count, LEDs per ray, spacing angle)

This metadata helps WLED or other players understand the physical LED arrangement for proper rendering.

### LED Ordering

For circular layouts (multi-ring, radial rays, etc.), pixels are automatically reordered according to the physical LED wiring order using the mapping table. This ensures the exported data matches the actual LED positions in the hardware.

## Integration with Falcon Player

FPP version 6.x+ supports WLED effects and can import WLED JSON format. The exported files can be:

1. Imported directly into FPP sequences
2. Used with WLED controllers via FPP's WLED integration
3. Scheduled as part of light shows

## Example: Multi-Ring Budurasmala

```json
{
  "name": "Vesak Halo",
  "leds": 36,
  "description": "Budurasmala multi-ring pattern: 3 rings",
  "layout": {
    "type": "multi_ring",
    "circular_led_count": 36,
    "multi_ring_count": 3,
    "ring_led_counts": [8, 12, 16],
    "ring_radii": [5.0, 10.0, 15.0],
    "ring_spacing": 5.0
  },
  "frames": [
    {
      "dur": 100,
      "data": [
        [255, 200, 0],
        [255, 200, 0],
        ...
      ]
    }
  ]
}
```

## Notes

- RGB values are in 0-255 range
- Frame durations are in milliseconds
- LED count must match the physical LED count (not grid size for circular layouts)
- The export automatically handles pixel reordering for circular layouts

