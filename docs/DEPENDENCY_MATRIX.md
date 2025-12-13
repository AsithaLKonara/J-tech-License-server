# Dependency Matrix

**Date**: 2025-12-14  
**Purpose**: Feature → Dependency mapping for Upload Bridge

---

## Overview

This document maps each feature to its required dependencies, helping you understand what's needed for different use cases.

---

## Core Dependencies (Always Required)

These dependencies are needed for basic functionality:

| Dependency | Purpose | Required For |
|------------|---------|--------------|
| `PySide6>=6.5.0` | GUI Framework | All UI features |
| `pyserial>=3.5` | Serial communication | Hardware upload |
| `pyyaml>=6.0` | Configuration files | Config loading |
| `colorama>=0.4.4` | Console colors | Terminal output |
| `tqdm>=4.64.0` | Progress bars | Upload progress |

**Installation**: Included in both `requirements.txt` and `requirements_simple.txt`

---

## Feature-Specific Dependencies

### Media Conversion Features

**Dependencies Required**:
- `Pillow>=10.0.0` - Image processing
- `opencv-python>=4.8.0` - Video/image processing
- `imageio>=2.31.0` - Image I/O
- `imageio-ffmpeg>=0.4.8` - Video codec support
- `numpy>=1.24.0` - Numerical operations

**Features Enabled**:
- ✅ Import images (PNG, BMP, JPEG)
- ✅ Import GIFs (frame extraction)
- ✅ Import videos (frame extraction)
- ✅ Export frames as images
- ✅ Export animations as GIFs
- ✅ Media conversion tab

**Installation**: Included in `requirements.txt`, **NOT** in `requirements_simple.txt`

---

### License System

**Dependencies Required**:
- `cryptography>=41.0.0` - Encryption/decryption

**Features Enabled**:
- ✅ License activation
- ✅ License validation
- ✅ Secure license storage

**Installation**: Included in `requirements.txt`, **NOT** in `requirements_simple.txt`

---

### Health Monitoring

**Dependencies Required**:
- `psutil>=5.9.0` - System monitoring

**Features Enabled**:
- ✅ CPU usage monitoring
- ✅ Memory usage monitoring
- ✅ System health checks
- ✅ Performance metrics

**Installation**: Included in `requirements.txt`, **NOT** in `requirements_simple.txt`

---

### Schema Validation

**Dependencies Required**:
- `jsonschema>=4.0.0` - JSON schema validation

**Features Enabled**:
- ✅ Pattern file validation
- ✅ Configuration validation
- ✅ Chip database validation

**Installation**: Included in `requirements.txt`, **NOT** in `requirements_simple.txt`

---

### HTTP Requests

**Dependencies Required**:
- `requests>=2.25.0` - HTTP client

**Features Enabled**:
- ✅ OTA (Over-The-Air) updates
- ✅ Remote device communication
- ✅ API calls (if implemented)

**Installation**: Included in `requirements.txt`, **NOT** in `requirements_simple.txt`

---

### Hardware Support

#### ESP Chips (ESP32, ESP8266, ESP32-S2, ESP32-S3, ESP32-C3)

**Dependencies Required**:
- `esptool>=4.6.0` - ESP flashing tool

**Features Enabled**:
- ✅ ESP32 firmware upload
- ✅ ESP8266 firmware upload
- ✅ ESP32-S2/S3/C3 support
- ✅ WiFi upload support

**Installation**: Included in both `requirements.txt` and `requirements_simple.txt`

#### AVR Chips (ATmega, ATtiny)

**External Tools Required** (not Python packages):
- `avrdude` - AVR flashing tool
- `avr-gcc` - AVR compiler

**Installation**: 
- Windows: Install Microchip Studio
- Linux: `sudo apt-get install avrdude gcc-avr`
- macOS: `brew install avr-gcc avrdude`

#### STM32 Chips

**External Tools Required**:
- `stm32flash` - STM32 flashing tool
- `arm-none-eabi-gcc` - ARM compiler

**Installation**:
- Download from ARM website
- Or use STM32CubeIDE

#### PIC Chips

**External Tools Required**:
- MPLAB X IDE
- XC compilers

**Installation**: Download from Microchip website

#### Nuvoton Chips

**External Tools Required**:
- Nu-Link tools

**Installation**: Download from Nuvoton website

---

### Development & Testing

**Dependencies Required**:
- `pytest>=7.0.0` - Testing framework
- `pytest-qt>=4.2.0` - Qt testing support
- `pytest-cov>=4.1.0` - Coverage reporting

**Features Enabled**:
- ✅ Running test suite
- ✅ Test coverage reports
- ✅ UI testing

**Installation**: Included in `requirements.txt` (development section)

---

## Installation Scenarios

### Scenario 1: Full Feature Set

**Use Case**: Complete LED matrix design and upload workflow

**Installation**:
```bash
pip install -r requirements.txt
```

**Includes**: All dependencies listed above

**Features Available**: 100% of features

---

### Scenario 2: Basic Design Only

**Use Case**: Pattern creation and editing, no media conversion

**Installation**:
```bash
pip install -r requirements_simple.txt
```

**Includes**: Core dependencies + ESP support only

**Features Available**:
- ✅ All drawing tools
- ✅ All automation actions
- ✅ Frame/layer management
- ✅ Pattern save/load
- ✅ ESP chip upload
- ❌ Media import/export
- ❌ License system
- ❌ Health monitoring

---

### Scenario 3: Media Conversion Only

**Use Case**: Need media conversion but not other optional features

**Installation**:
```bash
pip install -r requirements_simple.txt
pip install Pillow opencv-python imageio imageio-ffmpeg numpy
```

**Features Available**:
- ✅ All basic features
- ✅ Media conversion
- ❌ License system
- ❌ Health monitoring

---

### Scenario 4: Minimal Resource System

**Use Case**: Embedded system or limited resources

**Installation**:
```bash
pip install PySide6 pyserial pyyaml colorama tqdm esptool
```

**Features Available**:
- ✅ Basic GUI
- ✅ Pattern editing
- ✅ ESP chip upload
- ❌ All optional features

---

## Dependency Conflicts

### Known Issues

1. **opencv-python vs opencv-contrib-python**:
   - Use `opencv-python` (standard)
   - `opencv-contrib-python` may conflict

2. **PySide6 vs PyQt6**:
   - Use `PySide6` (required)
   - Do not install PyQt6 alongside

3. **Python Version**:
   - Requires Python 3.10+
   - Some dependencies may not support older versions

---

## Troubleshooting

### Missing Dependency Error

**Symptom**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
1. Check if dependency is in `requirements.txt`
2. Install missing dependency: `pip install X`
3. Or install full requirements: `pip install -r requirements.txt`

### Version Conflicts

**Symptom**: Dependency version conflicts during installation

**Solution**:
1. Use virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/macOS)
3. Install: `pip install -r requirements.txt`

### Hardware Tools Not Found

**Symptom**: Upload fails with "tool not found" error

**Solution**:
1. Install required hardware tools (see Hardware Support section)
2. Add tools to system PATH
3. Verify: Run `avrdude --version` (or equivalent) in terminal

---

## Quick Reference

| Feature Category | Minimal Install | Full Install |
|-----------------|----------------|--------------|
| Drawing Tools | ✅ | ✅ |
| Automation Actions | ✅ | ✅ |
| Frame/Layer Management | ✅ | ✅ |
| Pattern Save/Load | ✅ | ✅ |
| ESP Chip Upload | ✅ | ✅ |
| Media Conversion | ❌ | ✅ |
| License System | ❌ | ✅ |
| Health Monitoring | ❌ | ✅ |
| Schema Validation | ❌ | ✅ |
| HTTP Requests | ❌ | ✅ |

---

**Last Updated**: 2025-12-14

