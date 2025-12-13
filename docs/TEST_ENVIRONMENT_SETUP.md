# Test Environment Setup Guide

## Hardware Requirements

### Required Hardware
- **Development Machine**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS 11+
- **ESP8266 Development Board**: For firmware flashing tests
- **ESP32 Development Board**: For ESP32-specific tests
- **USB Cables**: For connecting development boards
- **Network Access**: For WiFi upload testing

### Optional Hardware
- **Additional Microcontrollers**: For testing other chip types (ATmega328P, STM32, etc.)
- **LED Strips**: For physical verification of patterns

## Software Requirements

### Python Environment
- **Python**: 3.9 or higher
- **Package Manager**: pip

### Required Python Packages
Install from `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key dependencies:
- PySide6 (Qt framework)
- pytest (testing framework)
- coverage (code coverage)
- All other dependencies listed in requirements.txt

### Development Tools
- **Code Editor**: VS Code, PyCharm, or similar
- **Git**: For version control
- **Serial Monitor**: For debugging device communication

## Test Environment Configuration

### 1. Clone Repository
```bash
git clone <repository-url>
cd upload_bridge
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Test Data
```bash
python tests/data/test_patterns_generator.py
```

This creates test patterns in `tests/data/`:
- Rectangular patterns (16×16, 32×32, 64×64)
- Circular patterns (60 LEDs, 120 LEDs)
- Multi-ring patterns (3 rings)
- Radial rays patterns (8 rays × 10 LEDs)

### 4. Prepare Media Files (Optional)
For media import testing, place sample files in `tests/data/media/`:
- Images: PNG, JPG, BMP files
- Animated GIFs
- Video files: MP4, AVI, MOV

### 5. Configure Test Settings
Create `tests/test_config.py` if needed for test-specific configuration:
```python
# Test configuration
TEST_DATA_DIR = "tests/data"
TEST_OUTPUT_DIR = "tests/output"
TEST_PATTERNS_DIR = "tests/data"
```

## Test Execution Setup

### Running Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=core --cov=ui --cov-report=html
```

### Running Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v
```

### Running GUI Tests
```bash
# Run GUI tests (requires display)
pytest tests/gui/ -v
```

### Running All Tests
```bash
# Run comprehensive test suite
pytest tests/comprehensive/ -v

# Run all tests
pytest tests/ -v
```

## Environment Variables

### Debug Mode
```bash
# Enable debug logging
export UPLOADBRIDGE_DEBUG=1
```

### Log Level
```bash
# Set log level
export UPLOADBRIDGE_LOG_LEVEL=DEBUG
```

## Hardware Setup for Flash Testing

### ESP8266 Setup
1. Connect ESP8266 board via USB
2. Identify COM port (Windows) or /dev/ttyUSB* (Linux)
3. Note GPIO pin for data (typically GPIO 2)

### ESP32 Setup
1. Connect ESP32 board via USB
2. Identify COM port
3. Note GPIO pin for data

### Testing Without Hardware
- Use mock uploaders for unit tests
- Skip hardware-dependent tests if devices unavailable
- Use `--skip-hardware` pytest marker if implemented

## Test Data Structure

```
tests/
├── data/
│   ├── test_rect_16x16.ledproj
│   ├── test_rect_32x32_5frames.ledproj
│   ├── test_circular_60leds.ledproj
│   ├── test_multiring_3rings.ledproj
│   ├── test_radial_rays_8x10.ledproj
│   ├── *.json (JSON format patterns)
│   └── media/ (optional media files)
├── output/ (test output files)
└── ...
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure Python path includes project root
   - Check all dependencies installed

2. **Qt/Display Issues**
   - GUI tests require display (X11 on Linux)
   - Use virtual display for CI: `xvfb-run pytest tests/gui/`

3. **Hardware Not Found**
   - Check USB connection
   - Verify drivers installed
   - Check COM port permissions (Linux)

4. **Test Data Missing**
   - Run test data generator: `python tests/data/test_patterns_generator.py`
   - Verify files in `tests/data/`

## CI/CD Setup

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python tests/data/test_patterns_generator.py
      - run: pytest tests/ -v --cov=core --cov=ui
```

## Next Steps

After environment setup:
1. Run test data generator
2. Execute unit tests to verify setup
3. Run integration tests
4. Proceed with test execution plan

