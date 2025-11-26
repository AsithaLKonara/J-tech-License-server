# 🔧 Troubleshooting Guide

**Upload Bridge - Common Issues and Solutions**

This guide helps diagnose and resolve common issues with Upload Bridge.

---

## Table of Contents

1. [Startup Issues](#startup-issues)
2. [Runtime Issues](#runtime-issues)
3. [Performance Issues](#performance-issues)
4. [File Operations](#file-operations)
5. [Hardware Issues](#hardware-issues)
6. [Configuration Issues](#configuration-issues)
7. [Log Analysis](#log-analysis)

---

## Startup Issues

### Application Won't Start

**Symptoms:**
- Application crashes immediately
- Error message on startup
- No window appears

**Diagnosis:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "PySide6|psutil"

# Check logs
cat logs/errors.log
```

**Solutions:**
1. **Python Version**
   - Ensure Python 3.8+ is installed
   - Update Python if needed

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Import Errors**
   - Check file permissions
   - Verify all files are present
   - Check Python path

4. **Qt Issues**
   ```bash
   # Try software OpenGL
   QT_OPENGL=software python main.py
   
   # Debug Qt plugins
   UPLOADBRIDGE_DEBUG=1 python main.py
   ```

### Configuration Errors

**Symptoms:**
- Configuration not loading
- Wrong environment detected
- Missing configuration values

**Diagnosis:**
```bash
# Check environment variable
echo $ENVIRONMENT

# Check configuration file
cat config/development.json
```

**Solutions:**
1. **Set Environment**
   ```bash
   export ENVIRONMENT=development
   python main.py
   ```

2. **Create Configuration**
   - Copy template: `config/development.json.template`
   - Edit configuration
   - Verify JSON syntax

3. **Configuration Validation**
   - Check JSON syntax
   - Verify required fields
   - Check file permissions

---

## Runtime Issues

### Application Crashes

**Symptoms:**
- Application closes unexpectedly
- Error dialog appears
- System becomes unresponsive

**Diagnosis:**
```bash
# Check error logs
tail -50 logs/errors.log

# Check application logs
tail -50 logs/application.log

# Check system resources
# Use health check
```

**Solutions:**
1. **Memory Issues**
   - Reduce pattern size
   - Close other applications
   - Increase system memory
   - Reduce `CACHE_SIZE` in config

2. **Unhandled Exceptions**
   - Check error logs
   - Report bug with logs
   - Try restarting application

3. **Resource Exhaustion**
   - Check disk space: `df -h`
   - Check memory: `free -h`
   - Clean up temporary files

### Pattern Loading Issues

**Symptoms:**
- Pattern won't load
- Error message on load
- Pattern appears corrupted

**Diagnosis:**
```bash
# Check pattern file
file pattern.bin
ls -lh pattern.bin

# Check logs
grep "pattern_load" logs/application.log
```

**Solutions:**
1. **File Format**
   - Verify file format is supported
   - Check file isn't corrupted
   - Try different format

2. **File Size**
   - Check file size limits
   - Reduce pattern size
   - Increase `MAX_PATTERN_SIZE` in config

3. **File Permissions**
   ```bash
   # Check permissions
   ls -l pattern.bin
   
   # Fix permissions
   chmod 644 pattern.bin
   ```

### Pattern Saving Issues

**Symptoms:**
- Pattern won't save
- Save fails silently
- File not created

**Diagnosis:**
```bash
# Check write permissions
ls -ld /path/to/save/directory

# Check disk space
df -h /path/to/save/directory

# Check logs
grep "pattern_save" logs/application.log
```

**Solutions:**
1. **Permissions**
   ```bash
   # Fix directory permissions
   chmod 755 /path/to/save/directory
   ```

2. **Disk Space**
   - Free up disk space
   - Choose different location
   - Clean up old files

3. **Path Issues**
   - Use absolute paths
   - Avoid special characters
   - Check path length

---

## Performance Issues

### Slow Operations

**Symptoms:**
- Pattern loading is slow
- Export takes too long
- UI is unresponsive

**Diagnosis:**
```bash
# Check performance logs
grep "Performance:" logs/application.log | tail -20

# Check system resources
# Use health check API
```

**Solutions:**
1. **Large Patterns**
   - Reduce pattern size
   - Optimize frame count
   - Use compression

2. **System Resources**
   - Close other applications
   - Increase system memory
   - Use faster storage

3. **Configuration**
   - Reduce `CACHE_SIZE`
   - Disable unnecessary features
   - Optimize logging level

### High Memory Usage

**Symptoms:**
- Application uses too much memory
- System becomes slow
- Out of memory errors

**Diagnosis:**
```bash
# Check memory usage
ps aux | grep python

# Check health status
# Use health check API
```

**Solutions:**
1. **Reduce Cache**
   - Lower `CACHE_SIZE` in config
   - Clear cache periodically
   - Restart application

2. **Pattern Size**
   - Work with smaller patterns
   - Split large patterns
   - Use compression

3. **Memory Leaks**
   - Check for memory leaks
   - Report bug with details
   - Restart application regularly

---

## File Operations

### Export Failures

**Symptoms:**
- Export fails
- Wrong format output
- File not created

**Diagnosis:**
```bash
# Check export logs
grep "pattern_export" logs/application.log

# Check file permissions
ls -l /path/to/export/directory
```

**Solutions:**
1. **Format Support**
   - Verify format is supported
   - Check format name spelling
   - Use correct file extension

2. **Validation**
   - Validate pattern before export
   - Check pattern completeness
   - Fix pattern issues

3. **Permissions**
   - Check write permissions
   - Use absolute paths
   - Verify directory exists

### Import Failures

**Symptoms:**
- Import fails
- Pattern not recognized
- Wrong format detected

**Diagnosis:**
```bash
# Check import logs
grep "pattern_load" logs/application.log

# Check file format
file imported_file.bin
```

**Solutions:**
1. **Format Detection**
   - Specify format manually
   - Check file extension
   - Verify file format

2. **File Validation**
   - Check file isn't corrupted
   - Verify file size
   - Try different file

---

## Hardware Issues

### Device Not Detected

**Symptoms:**
- Device not found
- Port not available
- Connection fails

**Diagnosis:**
```bash
# Check serial ports
ls /dev/tty*  # Linux/Mac
# Or check Device Manager on Windows

# Check permissions
ls -l /dev/ttyUSB0  # Linux
```

**Solutions:**
1. **Port Issues**
   - Check device is connected
   - Verify port name
   - Try different port

2. **Permissions** (Linux)
   ```bash
   # Add user to dialout group
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

3. **Driver Issues**
   - Install device drivers
   - Check device manager
   - Update drivers

### Firmware Upload Failures

**Symptoms:**
- Upload fails
- Device not responding
- Verification fails

**Diagnosis:**
```bash
# Check upload logs
grep "firmware_upload" logs/application.log

# Check device connection
# Use device-specific tools
```

**Solutions:**
1. **Connection**
   - Check cable connection
   - Verify port selection
   - Try different cable

2. **Device State**
   - Put device in boot mode
   - Check device power
   - Reset device

3. **Firmware**
   - Verify firmware file
   - Check firmware compatibility
   - Rebuild firmware

---

## Configuration Issues

### Configuration Not Loading

**Symptoms:**
- Default values used
- Configuration ignored
- Wrong environment

**Diagnosis:**
```bash
# Check environment
echo $ENVIRONMENT

# Check config file
cat config/development.json

# Check logs
grep "config" logs/application.log
```

**Solutions:**
1. **Environment Variable**
   ```bash
   export ENVIRONMENT=development
   python main.py
   ```

2. **Configuration File**
   - Verify file exists
   - Check JSON syntax
   - Verify file permissions

3. **Configuration Reload**
   ```python
   from core.config import get_config
   config = get_config()
   config.reload()
   ```

### Logging Issues

**Symptoms:**
- No logs created
- Wrong log level
- Logs not rotating

**Diagnosis:**
```bash
# Check log directory
ls -la logs/

# Check log configuration
grep "LOG_" config/development.json
```

**Solutions:**
1. **Log Directory**
   ```bash
   # Create log directory
   mkdir -p logs
   chmod 755 logs
   ```

2. **Log Level**
   ```bash
   # Set log level
   export LOG_LEVEL=DEBUG
   python main.py
   ```

3. **Log Rotation**
   - Check disk space
   - Verify permissions
   - Check rotation settings

---

## Log Analysis

### Finding Errors

```bash
# Recent errors
tail -50 logs/errors.log

# Errors by type
grep ERROR logs/application.log | sort | uniq -c

# Specific error
grep "pattern_load" logs/application.log | grep ERROR
```

### Performance Analysis

```bash
# Slow operations
grep "Performance:" logs/application.log | \
  awk -F'took ' '{print $2}' | \
  awk -F'ms' '{if ($1 > 1000) print $1}'

# Average times
grep "Performance:" logs/application.log | \
  awk -F'took ' '{print $2}' | \
  awk -F'ms' '{sum+=$1; count++} END {print "Average: " sum/count "ms"}'
```

### Audit Trail

```bash
# User actions
grep "Audit:" logs/audit.log

# Specific action
grep "pattern_loaded" logs/audit.log

# Recent activity
tail -50 logs/audit.log
```

---

## Getting Help

### Before Asking for Help

1. **Check Logs**
   - Review error logs
   - Check application logs
   - Review audit logs

2. **Gather Information**
   - Error messages
   - Log excerpts
   - System information
   - Steps to reproduce

3. **Check Documentation**
   - This troubleshooting guide
   - Operations runbook
   - API documentation

### Reporting Issues

When reporting issues, include:
- Error messages
- Relevant log excerpts
- Steps to reproduce
- System information
- Configuration (sanitized)

---

*Troubleshooting Guide - Updated: 2024*

