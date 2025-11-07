# WiFi Upload Integration for Upload Bridge v3.0

This folder contains the WiFi upload system integrated into Upload Bridge v3.0, allowing wireless pattern uploads to ESP8266 devices.

## Overview

The WiFi upload system enables:
- **Wireless Pattern Upload**: Upload LED patterns to ESP8266 over WiFi
- **Real-time Status Monitoring**: Check ESP8266 status and loaded patterns
- **Web Interface**: Access ESP8266 web interface directly from Upload Bridge
- **Pattern Validation**: Validate patterns before upload to prevent errors
- **Progress Tracking**: Real-time upload progress with cancellation support

## Files

### Core Components
- `upload_bridge_wifi_uploader.py` - Main WiFi uploader class integrated with Upload Bridge
- `wifi_uploader.py` - Original WiFi uploader (legacy compatibility)
- `wifi_config.ini` - Configuration file for WiFi settings

### Firmware Templates
- `esp8266_wifi_pattern_player.ino` - WiFi-enabled ESP8266 firmware template
- `pattern_data.h` - Pattern data template for PROGMEM storage

### Documentation
- `WIFI_UPLOAD_GUIDE.md` - Comprehensive WiFi upload guide
- `WIFI_INTEGRATION_COMPLETE.md` - Integration completion summary

### Utilities
- `main_wifi.py` - Original Tkinter GUI (for reference)
- `RUN_WIFI.py` - Python launcher script
- `RUN_WIFI.bat` - Windows batch launcher

## Integration Features

### 1. Upload Bridge Integration
- **Seamless Pattern Loading**: Uses Upload Bridge's pattern system
- **Format Support**: Supports all Upload Bridge pattern formats
- **Validation**: Built-in pattern validation for ESP8266 constraints
- **Progress Tracking**: Real-time upload progress with Qt signals

### 2. ESP8266 WiFi Firmware
- **Access Point Mode**: ESP8266 creates its own WiFi network
- **Web Server**: Built-in web interface for pattern uploads
- **REST API**: Programmatic access via `/api/status` and `/api/upload`
- **Pattern Storage**: Dynamic pattern loading from RAM (no PROGMEM limits)

### 3. Web Interface
- **Modern UI**: Responsive web interface with drag-and-drop upload
- **Real-time Status**: Live status updates and pattern information
- **Progress Tracking**: Visual upload progress with cancellation
- **File Validation**: Client-side pattern validation before upload

## Usage

### 1. Flash WiFi Firmware
1. Open Upload Bridge v3.0
2. Go to "📡 WiFi Upload" tab
3. Click "Flash WiFi Firmware" button
4. Follow the instructions to flash the WiFi-enabled firmware

### 2. Connect to ESP8266
1. Power on ESP8266 with WiFi firmware
2. Connect to WiFi network "LEDMatrix_ESP8266" (password: "ledmatrix123")
3. Enter ESP8266 IP address (default: 192.168.4.1)

### 3. Upload Pattern
1. Load a pattern using File > Open in Upload Bridge
2. Go to "📡 WiFi Upload" tab
3. Click "Upload Pattern" button
4. Monitor progress in the log area

### 4. Monitor Status
- Click "Check Status" to see ESP8266 information
- Click "Open Web Interface" to access ESP8266 web interface
- Status updates automatically every 5 seconds

## Configuration

### WiFi Settings
Edit `wifi_config.ini` to customize:
- Default SSID and password
- IP address and port
- Timeout settings
- Pattern validation limits

### Firmware Settings
Modify `esp8266_wifi_pattern_player.ino` to customize:
- LED pin configuration
- Maximum LED count
- WiFi credentials
- Web interface settings

## API Endpoints

### Status Endpoint
```
GET /api/status
```
Returns JSON with ESP8266 status:
```json
{
  "status": "Pattern Loaded",
  "pattern_loaded": true,
  "num_leds": 64,
  "num_frames": 100,
  "pattern_size": 19204,
  "wifi_mode": "AP",
  "ssid": "LEDMatrix_ESP8266",
  "ip": "192.168.4.1"
}
```

### Upload Endpoint
```
POST /api/upload
Content-Type: multipart/form-data
```
Uploads pattern file and returns JSON response:
```json
{
  "success": true,
  "message": "Pattern loaded: 64 LEDs × 100 frames (19204 bytes)"
}
```

## Pattern Format

WiFi uploads use binary format:
- **Header**: 4 bytes (LED count + Frame count, little-endian)
- **Frames**: Each frame contains:
  - Delay (2 bytes, little-endian, milliseconds)
  - RGB data (3 bytes per LED: R, G, B)

## Troubleshooting

### Connection Issues
- Verify ESP8266 is powered on
- Check WiFi network connection
- Confirm IP address is correct (default: 192.168.4.1)
- Try pinging ESP8266: `ping 192.168.4.1`

### Upload Issues
- Check pattern size (max ~900KB)
- Verify LED count (max 512)
- Ensure pattern format is valid
- Check ESP8266 memory availability

### Firmware Issues
- Reflash WiFi firmware if web interface doesn't load
- Check Arduino IDE compilation errors
- Verify FastLED library is installed
- Check ESP8266 board package version

## Development

### Adding New Features
1. Modify `upload_bridge_wifi_uploader.py` for backend changes
2. Update `wifi_upload_tab.py` for UI changes
3. Modify `esp8266_wifi_pattern_player.ino` for firmware changes
4. Update documentation as needed

### Testing
1. Test with various pattern sizes and formats
2. Verify WiFi connection stability
3. Test upload cancellation and error handling
4. Validate web interface functionality

## Dependencies

### Python Requirements
- `requests>=2.25.0` - HTTP requests for WiFi communication
- `PySide6>=6.5.0` - Qt framework for UI
- `pyserial>=3.5` - Serial communication (for firmware flashing)

### Arduino Requirements
- ESP8266 board package
- FastLED library
- ESP8266WiFi library (included)
- ESP8266WebServer library (included)

## License

This WiFi upload system is part of Upload Bridge v3.0 and follows the same license terms.

