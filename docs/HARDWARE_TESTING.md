# Hardware Testing Guide

Guide for testing Upload Bridge with actual hardware devices.

---

## Overview

This guide provides procedures for testing Upload Bridge with real microcontroller hardware and LED matrices.

---

## Prerequisites

### Required Hardware

- Microcontroller board (ESP32, ATmega, STM32, etc.)
- LED matrix or LED strip
- USB cable for programming
- Power supply (if needed)
- Breadboard and jumper wires (if needed)

### Required Software

- Upload Bridge installed
- Device drivers installed
- Serial port access configured

---

## Hardware Compatibility Matrix

| Chip | Tested | Status | Notes |
|------|--------|--------|-------|
| ESP32 | ⚠️ | Pending | Requires hardware |
| ESP32-S | ⚠️ | Pending | Requires hardware |
| ESP32-C3 | ⚠️ | Pending | Requires hardware |
| ESP32-S3 | ⚠️ | Pending | Requires hardware |
| ATmega2560 | ⚠️ | Pending | Requires hardware |
| ATtiny85 | ⚠️ | Pending | Requires hardware |
| STM32F407 | ⚠️ | Pending | Requires hardware |
| PIC18F4550 | ⚠️ | Pending | Requires hardware |
| Nuvoton M051 | ⚠️ | Pending | Requires hardware |

**Legend:**
- ✅ Tested and working
- ⚠️ Not yet tested (requires hardware)
- ❌ Issues found

---

## Testing Procedures

### 1. ESP32 Testing

#### Setup
1. Connect ESP32 to computer via USB
2. Install ESP32 drivers if needed
3. Note COM port (Windows) or /dev/tty* (Linux/Mac)

#### Test Steps
1. Open Upload Bridge
2. Go to Flash tab
3. Select "ESP32" from chip dropdown
4. Select COM port
5. Configure LED settings:
   - LED type: WS2812B
   - Color order: GRB
   - Number of LEDs: Match your hardware
   - GPIO pin: 3 (or your pin)
6. Create a simple test pattern (red square)
7. Click "Build Firmware"
8. Wait for compilation
9. Click "Flash Firmware"
10. Wait for upload
11. Verify pattern plays on hardware

#### Expected Results
- Firmware compiles successfully
- Firmware uploads successfully
- Pattern displays correctly on LEDs
- Colors are accurate
- Timing is correct

#### Troubleshooting
- **Upload fails**: Check COM port, try different USB port
- **Wrong colors**: Check color order setting
- **No display**: Check wiring, power supply, GPIO pin
- **Timing issues**: Adjust frame duration

---

### 2. ATmega2560 Testing

#### Setup
1. Connect ATmega2560 (Arduino Mega) to computer
2. Install Arduino drivers
3. Note COM port

#### Test Steps
1. Select "ATmega2560" from chip dropdown
2. Follow similar steps as ESP32
3. Note: ATmega2560 may have different pin requirements

#### Expected Results
- Similar to ESP32
- May have different performance characteristics

---

### 3. Other Chips

Follow similar procedures for other chips:
- STM32F407: May require ST-Link programmer
- PIC18F4550: Requires MPLAB X and PICkit
- ATtiny85: Requires USBasp or similar programmer
- Nuvoton M051: Requires Nu-Link programmer

---

## Pattern Testing

### Test Patterns

Create these test patterns to verify functionality:

1. **Solid Color Test**
   - Single frame, solid color
   - Verifies basic display

2. **Color Test**
   - Red, Green, Blue frames
   - Verifies color accuracy

3. **Animation Test**
   - 10 frames, simple animation
   - Verifies timing

4. **Large Pattern Test**
   - Full matrix pattern
   - Verifies memory handling

5. **Long Pattern Test**
   - 100+ frames
   - Verifies storage and playback

---

## Wiring Verification

### Common Wiring Issues

1. **Data Line**
   - Check data line connected to correct GPIO
   - Verify data line not loose
   - Check for interference

2. **Power**
   - Verify adequate power supply
   - Check for voltage drop
   - Ensure stable 5V (or 3.3V)

3. **Ground**
   - Verify common ground
   - Check ground connections

4. **LED Order**
   - Verify LED strip direction
   - Check first LED position
   - Verify last LED position

---

## Performance Testing

### Test Scenarios

1. **Small Matrix (8x8)**
   - Should work smoothly
   - Fast frame updates

2. **Medium Matrix (32x32)**
   - Should work well
   - Acceptable frame rate

3. **Large Matrix (64x64)**
   - May have performance limits
   - Test frame rate
   - Test memory usage

4. **Long Patterns (1000+ frames)**
   - Test storage capacity
   - Test playback smoothness
   - Test memory management

---

## Test Checklist

### Pre-Flash Checklist
- [ ] Hardware connected
- [ ] Drivers installed
- [ ] COM port identified
- [ ] Power supply adequate
- [ ] Wiring verified
- [ ] LED count matches settings

### Post-Flash Checklist
- [ ] Firmware compiled successfully
- [ ] Firmware uploaded successfully
- [ ] Pattern displays correctly
- [ ] Colors are accurate
- [ ] Timing is correct
- [ ] No flickering
- [ ] No memory issues

### Regression Testing
- [ ] Test with different patterns
- [ ] Test with different chip types
- [ ] Test with different LED types
- [ ] Test with different matrix sizes
- [ ] Test error handling

---

## Hardware Limitations

### Known Limitations

1. **Memory Constraints**
   - Small chips (ATtiny85) have limited memory
   - Large patterns may not fit
   - Use smaller patterns or fewer frames

2. **Processing Power**
   - Some chips are slower
   - Complex patterns may lag
   - Adjust frame rate accordingly

3. **GPIO Limitations**
   - Some chips have limited GPIO
   - Verify pin availability
   - Check pin capabilities

---

## Test Results Template

### Test Report Format

```
Chip: [Chip Name]
Date: [Date]
Tester: [Name]

Hardware:
- Board: [Board Model]
- LEDs: [LED Type, Count]
- Matrix Size: [Width x Height]

Test Results:
- Compilation: [Pass/Fail]
- Upload: [Pass/Fail]
- Display: [Pass/Fail]
- Colors: [Accurate/Issues]
- Timing: [Correct/Issues]

Issues Found:
[Description of any issues]

Notes:
[Additional notes]
```

---

## Troubleshooting

### Common Issues

1. **Firmware Won't Compile**
   - Check toolchain installation
   - Verify template files
   - Check error messages

2. **Firmware Won't Upload**
   - Check COM port
   - Check drivers
   - Try different USB port
   - Check boot mode (ESP32)

3. **Pattern Won't Display**
   - Check wiring
   - Check power supply
   - Verify GPIO pin
   - Check LED count

4. **Wrong Colors**
   - Check color order setting
   - Verify LED type
   - Check wiring

5. **Timing Issues**
   - Adjust frame duration
   - Check clock speed
   - Verify timing code

---

## Safety Considerations

1. **Electrical Safety**
   - Use appropriate power supplies
   - Check voltage ratings
   - Avoid short circuits
   - Use fuses if needed

2. **Heat Management**
   - LEDs can get hot
   - Ensure adequate cooling
   - Monitor temperature

3. **Eye Safety**
   - Some LEDs are very bright
   - Avoid direct eye exposure
   - Use appropriate brightness

---

## Next Steps

After hardware testing:

1. Document test results
2. Update compatibility matrix
3. Report any issues
4. Create test patterns library
5. Update documentation

---

**Note**: Hardware testing requires actual hardware. If hardware is not available, testing can be done with simulators or deferred until hardware is available.

**Last Updated**: 2024-11-XX

