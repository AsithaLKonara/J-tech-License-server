# Test Data Directory

This directory contains test data files used for testing Upload Bridge.

## Test Patterns

### Rectangular Patterns
- `test_rect_16x16.ledproj` - 16×16 single frame pattern
- `test_rect_16x16.json` - JSON format
- `test_rect_32x32_5frames.ledproj` - 32×32 with 5 frames
- `test_rect_64x64_10frames.ledproj` - 64×64 with 10 frames (large pattern)

### Circular Patterns
- `test_circular_60leds.ledproj` - Circular pattern with 60 LEDs
- `test_circular_60leds.json` - JSON format
- `test_circular_120leds.ledproj` - Circular pattern with 120 LEDs

### Multi-Ring Patterns
- `test_multiring_3rings.ledproj` - Multi-ring pattern with 3 rings
- `test_multiring_3rings.json` - JSON format

### Radial Rays Patterns
- `test_radial_rays_8x10.ledproj` - Radial rays pattern (8 rays, 10 LEDs each)
- `test_radial_rays_8x10.json` - JSON format

## Generating Test Patterns

Run the generator script to create all test patterns:

```bash
python tests/data/test_patterns_generator.py
```

## Test Media Files

For media import testing, you'll need:
- Sample images: PNG, JPG, BMP (various sizes)
- Animated GIFs
- Video files: MP4, AVI, MOV

These should be placed in a `media/` subdirectory (not included in repo due to size).

## Invalid Test Files

For negative testing:
- Corrupted pattern files
- Invalid format files
- Files with wrong extensions

These should be created manually for specific test scenarios.

