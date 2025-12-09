# GUI Test Suite Troubleshooting Guide

**Issue**: GUI Test Suite "Not Responding" / Hanging

---

## Problem Description

The GUI test suite may appear to hang or show "Not Responding" when:
1. Launching Upload Bridge application
2. Initializing Design Tools Tab
3. Waiting for widgets to become available

---

## Root Causes

### 1. Main Window Initialization Blocking
- The main window may be performing blocking operations during initialization
- File system operations, network calls, or heavy computations can block the UI thread

### 2. Design Tools Tab Initialization
- Design Tools Tab initialization may be slow or blocking
- Widget creation, signal connections, or data loading can take time

### 3. Event Loop Not Processing
- Qt events not being processed frequently enough
- Long-running operations blocking the event loop

---

## Solutions

### Solution 1: Use Fixed Test Runner (Recommended)

The fixed test runner (`test_runner_fixed.py`) includes:
- Better timeout handling
- More frequent event processing
- Graceful degradation on failures

**Status**: ✅ Already integrated - the GUI will automatically use the fixed version if available.

### Solution 2: Increase Timeout

If tests are hanging, you can:
1. Wait up to 30 seconds for initialization
2. The GUI will show a warning if tests don't start within 30 seconds
3. Click "Stop Tests" if initialization is taking too long

### Solution 3: Launch Application First

**Workaround**: Launch Upload Bridge manually first, then run tests:
1. Launch: `python main.py`
2. Wait for application to fully load
3. Run GUI test suite: `python tests/gui/test_design_tools_gui.py`
4. Click "Start Tests"

**Note**: The fixed test runner can detect existing instances and skip app launch.

### Solution 4: Check for Blocking Operations

If the application is hanging, check:
1. **Console Output**: Look for error messages or warnings
2. **File System**: Check if files are being accessed (may be slow on network drives)
3. **Network**: Check if network operations are blocking
4. **Dependencies**: Verify all required libraries are installed

---

## Prevention Measures

### Already Implemented:

1. ✅ **Event Timer**: Processes events every 50ms to keep GUI responsive
2. ✅ **Timeout Protection**: 30-second warning if tests don't start
3. ✅ **Better Timeout Handling**: Fixed test runner with improved timeouts
4. ✅ **Frequent Event Processing**: More `app.processEvents()` calls
5. ✅ **Thread-based Execution**: Tests run in separate thread

### Additional Recommendations:

1. **Monitor Console**: Watch for error messages during initialization
2. **Check System Resources**: Ensure sufficient RAM and CPU available
3. **Close Other Applications**: Free up system resources
4. **Check Dependencies**: Verify all required packages are installed

---

## Debugging Steps

### Step 1: Check Console Output
```bash
python tests/gui/test_design_tools_gui.py
```
Look for:
- Error messages
- Warnings about initialization
- Timeout messages

### Step 2: Verify Application Can Launch
```bash
python main.py
```
If the main application doesn't launch, fix that first.

### Step 3: Check Design Tools Tab Initialization
- Launch main application
- Navigate to Design Tools Tab
- Verify it loads without errors

### Step 4: Run Tests with Verbose Logging
- Check the "Test Log" panel in the GUI
- Look for initialization messages
- Check for timeout warnings

---

## Known Issues

### Issue: Tests Hang at "Launching Upload Bridge application..."
**Cause**: Main window initialization blocking  
**Solution**: 
- Wait up to 30 seconds
- Check console for errors
- Try launching application manually first

### Issue: Tests Hang at "Initializing Design Tools Tab..."
**Cause**: Design Tools Tab initialization blocking  
**Solution**:
- Check if tab initializes manually
- Look for errors in console
- Verify all dependencies are installed

### Issue: GUI Becomes Unresponsive
**Cause**: Event loop not processing  
**Solution**:
- The event timer should prevent this
- If it still happens, click "Stop Tests"
- Restart the test GUI

---

## Workarounds

### Workaround 1: Skip App Launch
If you have the application already running:
- The fixed test runner can detect existing instances
- It will skip the app launch step
- This avoids initialization blocking

### Workaround 2: Run Tests in Smaller Batches
Instead of running all 157 tests at once:
- Run specific test categories
- This reduces initialization overhead
- Faster feedback on specific features

### Workaround 3: Use Automated Tests Instead
For faster feedback, use the automated test scripts:
```bash
python tests/test_new_layer_features.py
python -m pytest tests/unit/test_layers.py -v
```

---

## Status

**Fixed Test Runner**: ✅ Created and integrated  
**Timeout Protection**: ✅ Implemented  
**Event Processing**: ✅ Improved  
**Documentation**: ✅ Complete

---

## Next Steps

1. **Try the Fixed Test Runner**: It should handle timeouts better
2. **Monitor Console**: Watch for specific error messages
3. **Report Issues**: If problems persist, document the specific error messages
4. **Use Workarounds**: Launch app manually if needed

---

**Last Updated**: [Date]  
**Version**: [Version]

