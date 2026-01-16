# Troubleshooting Guide

**Upload Bridge v3.0.0**

This guide helps resolve common issues encountered when installing, running, or using Upload Bridge.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Application Launch Issues](#application-launch-issues)
3. [License Activation Issues](#license-activation-issues)
4. [Hardware Connection Issues](#hardware-connection-issues)
5. [Pattern Import/Export Issues](#pattern-importexport-issues)
6. [Performance Issues](#performance-issues)
7. [UI/Display Issues](#uidisplay-issues)

---

## Installation Issues

### Installer Won't Build

**Symptoms**: WiX build fails, error about missing tools

**Solution**:
1. Install WiX Toolset from https://wixtoolset.org/
2. Add WiX bin directory to PATH
3. Verify installation: `candle.exe -?` and `light.exe -?` should work

### Installation Fails

**Symptoms**: Installer fails with error message

**Solutions**:
1. **Check Logs**: Run installer with logging:
   ```powershell
   msiexec /i "upload_bridge_3.0.0.msi" /L*v install.log
   ```
   Review `install.log` for specific error messages

2. **Check Permissions**: Run installer as Administrator:
   - Right-click installer → "Run as administrator"

3. **Check Disk Space**: Ensure at least 500 MB free disk space

4. **Check Antivirus**: Temporarily disable antivirus and retry

5. **Check Previous Installation**: 
   - Uninstall any previous version first
   - Check Control Panel → Programs and Features

### Files Not Installed Correctly

**Symptoms**: Application won't launch, missing files

**Solutions**:
1. Verify installation directory exists: `C:\Program Files\UploadBridge`
2. Check for `UploadBridge.exe` in installation directory
3. Verify firmware templates directory exists: `firmware/templates`
4. Reinstall if files are missing

### Shortcuts Not Created

**Symptoms**: No Start Menu or Desktop shortcuts

**Solutions**:
1. Check Start Menu: `Start Menu\Programs\Upload Bridge`
2. Check Desktop for shortcut
3. Manually create shortcut pointing to `UploadBridge.exe`
4. Reinstall if shortcuts missing

---

## Application Launch Issues

### Application Won't Start

**Symptoms**: Double-clicking executable does nothing, or error message appears

**Solutions**:
1. **Check Dependencies**:
   - Ensure all required DLLs are present
   - Install Visual C++ Redistributable if needed

2. **Check Logs**:
   - Check `%USERPROFILE%\.upload_bridge\logs\` for error logs
   - Look for `application.log` and `errors.log`

3. **Run from Command Line**:
   ```powershell
   cd "C:\Program Files\UploadBridge"
   .\UploadBridge.exe
   ```
   Check for error messages in console

4. **Check Windows Event Viewer**:
   - Open Event Viewer → Windows Logs → Application
   - Look for Upload Bridge errors

### Application Crashes on Startup

**Symptoms**: Application starts then immediately crashes

**Solutions**:
1. Check error logs: `%USERPROFILE%\.upload_bridge\logs\errors.log`
2. Verify license activation (see License Activation Issues)
3. Check for corrupted user data:
   - Backup `%USERPROFILE%\.upload_bridge\`
   - Delete and let application recreate
4. Reinstall application

---

## License Activation Issues

### License Key Not Accepted

**Symptoms**: "Invalid license key" error message

**Solutions**:
1. **Check Key Format**:
   - Ensure key is copied completely (no extra spaces)
   - Check `LICENSE_KEYS.txt` file in installation directory

2. **Check Offline Activation**:
   - Verify `LICENSE_KEYS.txt` file exists in installation directory
   - Verify file contains valid license keys

3. **Check License File**:
   - Check `%USERPROFILE%\.upload_bridge\license\` directory
   - Verify `license.enc` and `license_cache.json` files exist
   - Delete license files and reactivate if corrupted

4. **Hardware Binding**:
   - License is bound to your hardware
   - Cannot activate on different machine without new key

### License Expired

**Symptoms**: "License has expired" message

**Solutions**:
1. Check expiration date in license information
2. Contact support for license renewal
3. Verify system clock is correct (see Clock Issues)

### Clock Tampering Warning

**Symptoms**: Warning about suspicious clock changes

**Solutions**:
1. **Check System Clock**:
   - Ensure system clock is correct
   - Enable automatic time synchronization

2. **Time Zone Changes**:
   - If you changed time zones, wait for system to adjust
   - License system allows small time adjustments

3. **If Legitimate**:
   - Warning is logged but doesn't block application
   - License validation continues normally

---

## Hardware Connection Issues

### Device Not Detected

**Symptoms**: Device doesn't appear in port list

**Solutions**:
1. **Check USB Connection**:
   - Ensure USB cable is connected
   - Try different USB port
   - Try different USB cable

2. **Check Device Manager**:
   - Open Device Manager (Win+X → Device Manager)
   - Look for device under "Ports (COM & LPT)"
   - Check for yellow warning icons

3. **Check Drivers**:
   - Install device-specific drivers (e.g., CH340, CP2102 for ESP32)
   - Check device manufacturer website for drivers

4. **Check Port Access**:
   - Ensure no other application is using the port
   - Close other serial port applications

### Upload Fails

**Symptoms**: Firmware upload fails with error

**Solutions**:
1. **Check Port Selection**:
   - Verify correct COM port selected
   - Try manual port override if auto-detection fails

2. **Check Bootloader Mode**:
   - ESP32/ESP8266: Hold BOOT button, press RESET, release RESET, release BOOT
   - Arduino: No special steps needed usually
   - STM32: May need BOOT0 pin configuration

3. **Check Baud Rate**:
   - Try different baud rates (115200, 921600, etc.)
   - Lower baud rate if connection unstable

4. **Check Firmware File**:
   - Verify firmware file exists and is readable
   - Check file size (should be reasonable, not empty or huge)
   - Verify firmware format matches device type

5. **Safe Disconnect**:
   - If device disconnected during upload, reconnect and retry
   - Application should handle disconnect gracefully

### Device Disconnects During Upload

**Symptoms**: Upload fails mid-way, connection lost

**Solutions**:
1. **Check USB Connection**:
   - Ensure stable USB connection
   - Avoid USB hubs, connect directly to computer

2. **Check Power Supply**:
   - Some devices need external power during upload
   - ESP32 may need sufficient power supply

3. **Retry Upload**:
   - Application should handle disconnect gracefully
   - Retry upload after reconnecting device
   - No device damage should occur from safe disconnect

---

## Pattern Import/Export Issues

### Import Fails

**Symptoms**: Cannot import image/video file

**Solutions**:
1. **Check File Format**:
   - Supported: PNG, JPG, GIF, MP4, AVI
   - Verify file is not corrupted
   - Try opening file in other application first

2. **Check File Size**:
   - Very large files may take time to process
   - Try smaller test file first

3. **Check File Permissions**:
   - Ensure file is readable
   - Check file is not locked by another application

### Export Fails

**Symptoms**: Cannot export pattern

**Solutions**:
1. **Check Output Directory**:
   - Ensure directory exists and is writable
   - Check available disk space

2. **Check Pattern Size**:
   - Very large patterns may take time to export
   - Verify pattern is valid (not empty)

3. **Check Export Format**:
   - Verify selected export format is supported
   - Check format-specific requirements

### GIF Timing Not Preserved

**Symptoms**: Imported GIF animation timing is wrong

**Solutions**:
1. Check original GIF frame delays
2. Verify GIF import preserves timing information
3. Check pattern frame duration settings

---

## Performance Issues

### Slow Application Performance

**Symptoms**: Application is slow, laggy, unresponsive

**Solutions**:
1. **Check System Resources**:
   - Check CPU and memory usage
   - Close other resource-intensive applications

2. **Check Pattern Size**:
   - Very large patterns (256×256, 500+ frames) may be slow
   - Consider reducing pattern size for testing

3. **Check Memory Usage**:
   - Monitor memory usage in Task Manager
   - Restart application if memory usage grows continuously (possible leak)

4. **Check Disk Space**:
   - Ensure adequate free disk space
   - Clear temporary files

### High Memory Usage

**Symptoms**: Application uses excessive memory

**Solutions**:
1. **Check for Memory Leaks**:
   - Monitor memory usage over time
   - If memory grows continuously, may indicate leak
   - Report with diagnostic report (Help → Export Diagnostic Report)

2. **Reduce Pattern Size**:
   - Smaller patterns use less memory
   - Fewer frames = less memory usage

3. **Restart Application**:
   - Periodically restart to clear memory
   - Close unused patterns/tabs

---

## UI/Display Issues

### UI Elements Don't Scale Correctly

**Symptoms**: Text/icons too small or too large, UI doesn't fit screen

**Solutions**:
1. **Check DPI Settings**:
   - Right-click desktop → Display settings
   - Check scale percentage (100%, 125%, 150%, 200%)
   - Application should scale with DPI settings

2. **Check Application Settings**:
   - Look for UI scaling options in preferences
   - Try different window sizes

3. **Check Graphics Drivers**:
   - Update graphics drivers
   - Ensure hardware acceleration enabled

### Icons Not Displaying

**Symptoms**: Icons missing or corrupted in UI

**Solutions**:
1. **Check Icon Files**:
   - Verify icon files exist in application directory
   - Reinstall if icons missing

2. **Check High DPI**:
   - Icons should scale with DPI
   - Report issue if icons don't render correctly at high DPI

### Canvas Not Rendering

**Symptoms**: Pattern canvas is blank or shows incorrectly

**Solutions**:
1. **Check Pattern Loaded**:
   - Verify pattern is loaded and has frames
   - Try different pattern

2. **Check Canvas Settings**:
   - Verify canvas size matches pattern
   - Check zoom level settings

3. **Check Graphics**:
   - Update graphics drivers
   - Try disabling hardware acceleration (if option available)

---

## Getting Additional Help

### Diagnostic Report

If issues persist, generate a diagnostic report:
1. Open application
2. Go to Help → Export Diagnostic Report
3. Save report file
4. Include report when contacting support

### Log Files

Check log files for detailed error information:
- Location: `%USERPROFILE%\.upload_bridge\logs\`
- Files: `application.log`, `errors.log`
- Include relevant log entries when reporting issues

### Support

For additional support:
- Check documentation: [docs/](docs/)
- Review known issues: [docs/REMAINING_TASKS.md](REMAINING_TASKS.md)
- Submit issue reports with diagnostic information

---

**Last Updated**: 2025-01-27  
**Version**: 3.0.0

