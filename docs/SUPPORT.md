# Support Guide - Upload Bridge

**Version**: 1.0.0  
**Last Updated**: 2024-11-XX

---

## Getting Help

### Documentation
- **User Manual**: `docs/USER_MANUAL.md` - Comprehensive guide
- **Quick Start**: `docs/QUICKSTART.md` - Get started quickly
- **Installation**: `docs/INSTALLATION.md` - Installation instructions
- **FAQ**: See [Frequently Asked Questions](#frequently-asked-questions) below

### Community Support
- **Issue Tracker**: [GitHub Issues URL]
- **Discussions**: [GitHub Discussions URL]
- **Wiki**: [Project Wiki URL]

---

## Troubleshooting

### Common Issues

#### Application Won't Start

**Symptoms**:
- Application doesn't launch
- Error message on startup
- Blank window appears

**Solutions**:
1. **Check Python Version**:
   ```bash
   python --version
   ```
   Should be 3.10 or higher.

2. **Check Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Logs**:
   - Look for error messages in console
   - Check log files in application directory

4. **Reinstall**:
   - Uninstall current version
   - Download fresh installer
   - Reinstall

---

#### Pattern Not Displaying Correctly

**Symptoms**:
- Pattern appears wrong on hardware
- Colors are incorrect
- Pattern is flipped or rotated

**Solutions**:
1. **Check Wiring Configuration**:
   - Verify wiring mode (Serpentine, Row-major, etc.)
   - Check data-in corner position
   - Use auto-detection if available

2. **Check Color Order**:
   - Verify RGB/GRB/BGR order matches your LEDs
   - Test different color orders

3. **Check Brightness**:
   - Adjust brightness settings
   - Check gamma correction

4. **Check Hardware**:
   - Verify LED connections
   - Check power supply
   - Test with known-good pattern

---

#### Firmware Flashing Fails

**Symptoms**:
- Flash operation fails
- Device not detected
- Upload timeout

**Solutions**:
1. **Check Device Connection**:
   - Verify USB cable is connected
   - Try different USB port
   - Check cable quality

2. **Check Drivers**:
   - Install device drivers
   - Update drivers if needed
   - Check Device Manager (Windows)

3. **Check COM Port**:
   - Verify correct COM port selected
   - Check if port is in use by another application
   - Try different port

4. **Check Chip Selection**:
   - Verify correct chip type selected
   - Check chip compatibility

5. **Check Boot Mode**:
   - Some chips require boot mode entry
   - Follow chip-specific instructions

---

#### Performance Issues

**Symptoms**:
- Application is slow
- Canvas rendering is laggy
- Export takes too long

**Solutions**:
1. **Check System Resources**:
   - Close other applications
   - Check available RAM
   - Check CPU usage

2. **Reduce Pattern Size**:
   - Use smaller matrix dimensions
   - Reduce frame count
   - Lower preview FPS

3. **Update Graphics Drivers**:
   - Update GPU drivers
   - Check hardware acceleration

4. **Check System Requirements**:
   - Verify system meets minimum requirements
   - Consider upgrading hardware

---

#### Media Import Issues

**Symptoms**:
- Media file won't import
- Conversion fails
- Colors are wrong

**Solutions**:
1. **Check File Format**:
   - Verify file format is supported
   - Check file is not corrupted
   - Try different file

2. **Check File Size**:
   - Large files may take time
   - Check available memory
   - Try smaller file

3. **Check Settings**:
   - Adjust conversion settings
   - Try different dimensions
   - Adjust brightness/color

---

### Error Messages

#### "Pattern metadata missing width/height"

**Cause**: Pattern file is corrupted or invalid.

**Solution**:
- Try opening a different pattern file
- Recreate the pattern
- Check file integrity

---

#### "Device not found"

**Cause**: Microcontroller not connected or not detected.

**Solution**:
- Check USB connection
- Install device drivers
- Select correct COM port
- Try different USB port

---

#### "Firmware compilation failed"

**Cause**: Build tools not installed or configured.

**Solution**:
- Install required build tools (Arduino IDE, etc.)
- Check tool paths in settings
- Verify chip support

---

## Frequently Asked Questions

### General

**Q: What is Upload Bridge?**  
A: Upload Bridge is a desktop application for creating, editing, and uploading LED animation patterns to microcontroller boards.

**Q: Which platforms are supported?**  
A: Windows 10+, macOS 10.14+, and Linux (Ubuntu 20.04+).

**Q: Is Upload Bridge free?**  
A: [License information]

---

### Features

**Q: Which microcontrollers are supported?**  
A: ESP32 (4 variants), ATmega2560, ATtiny85, STM32F407, PIC18F4550, Nuvoton M051.

**Q: Can I import images/videos?**  
A: Yes! Upload Bridge supports PNG, JPG, BMP, GIF, MP4, AVI, MOV, MKV, WebM.

**Q: Can I save my work?**  
A: Yes! Projects are saved in `.ledproj` format with all pattern data, metadata, and presets.

**Q: Can I use multiple layers?**  
A: Yes! Upload Bridge supports multiple layers with blend modes and opacity control.

---

### Technical

**Q: What Python version is required?**  
A: Python 3.10 or higher.

**Q: Do I need Arduino IDE?**  
A: For some chips (ESP32, ATmega), Arduino IDE or build tools may be required. See installation guide.

**Q: How do I update Upload Bridge?**  
A: Download the latest installer and run it. Your projects will be preserved.

**Q: Can I use Upload Bridge offline?**  
A: Yes! Upload Bridge works completely offline. Internet is only needed for updates.

---

### Hardware

**Q: Which LED types are supported?**  
A: WS2812B, SK6812, APA102, and other addressable RGB LEDs.

**Q: What matrix sizes are supported?**  
A: Any size! Upload Bridge can handle matrices from 8x8 to 128x128+.

**Q: Do I need special drivers?**  
A: Some microcontrollers require drivers (e.g., CH340 for ESP32). See installation guide.

**Q: Can I flash multiple devices?**  
A: Currently, flashing is done one device at a time. Batch flashing is planned for future releases.

---

## Reporting Issues

### Before Reporting

1. **Check Documentation**: Review relevant documentation
2. **Search Issues**: Check if issue already reported
3. **Try Troubleshooting**: Follow troubleshooting steps above

### When Reporting

Include the following information:

1. **Description**: Clear description of the problem
2. **Steps to Reproduce**: Detailed steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **System Information**:
   - OS and version
   - Python version
   - Upload Bridge version
   - Hardware (if applicable)
6. **Error Messages**: Full error messages/logs
7. **Screenshots**: If applicable

### Issue Template

```
**Description**:
[Clear description of the issue]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**System Information**:
- OS: [OS and version]
- Python: [Version]
- Upload Bridge: [Version]
- Hardware: [If applicable]

**Error Messages**:
[Error messages/logs]

**Screenshots**:
[If applicable]
```

---

## Feature Requests

Have an idea for a new feature? We'd love to hear it!

1. **Check Existing Requests**: Search for similar requests
2. **Create Feature Request**: Use issue tracker with "Feature Request" label
3. **Provide Details**: Describe the feature and use case

---

## Contributing

Interested in contributing? See `CONTRIBUTING.md` for guidelines.

---

## Contact

- **Issues**: [GitHub Issues URL]
- **Discussions**: [GitHub Discussions URL]
- **Email**: [Support Email]

---

## Additional Resources

- **User Manual**: `docs/USER_MANUAL.md`
- **Quick Start**: `docs/QUICKSTART.md`
- **Installation**: `docs/INSTALLATION.md`
- **Changelog**: `CHANGELOG.md`
- **Release Notes**: `RELEASE_NOTES.md`

---

**Thank you for using Upload Bridge!**

---

**Last Updated**: 2024-11-XX

