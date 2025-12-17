# GUI Test Monitoring Guide

**Test Running**: `python tests/gui/run_gui_tests_automated.py`

---

## What to Expect

### 1. GUI Window Opens
- **Window Title**: "Automated GUI Test Suite - Running..."
- **Contains**:
  - Status label (shows current activity)
  - Progress bar (0-100%)
  - Log output (scrollable, real-time)

### 2. Automatic Test Start
- Tests start automatically after 0.5 seconds
- No manual clicks required
- Fully automated execution

### 3. Real-Time Monitoring

**Console Output** (timestamped):
```
[HH:MM:SS] Starting Fully Automated GUI Test Suite
[HH:MM:SS] Creating test runner...
[HH:MM:SS] Starting test thread...
[HH:MM:SS] Launching Upload Bridge application...
[HH:MM:SS] Initializing Design Tools Tab...
[HH:MM:SS] Running Header Toolbar tests...
...
```

**GUI Window**:
- Progress bar updates in real-time
- Status label shows current activity
- Log output scrolls automatically

### 4. Test Execution

**13 Categories** (157+ tests):
1. Header Toolbar (8 tests)
2. Toolbox Tabs (9 tests)
3. Drawing Tools (17 tests)
4. Canvas Features (21 tests)
5. Timeline Features (22 tests)
6. **Layer System (7 tests)** ⭐
7. **Automation (22 tests)** ⭐
8. Effects (8 tests)
9. Export/Import (14 tests)
10. Scratchpads (6 tests)
11. Keyboard Shortcuts (9 tests)
12. Options and Parameters (6 tests)
13. Feature Flows (8 tests)

### 5. Completion

**When Complete**:
- Status: "✅ All tests completed! Check docs/GUI_TEST_RESULTS_AUTOMATED.md"
- Progress bar: 100%
- Report auto-generated
- Window auto-closes after 5 seconds (or close manually)

---

## Monitoring Tips

### Watch For:
- ✅ Progress bar advancing
- ✅ Status label updating
- ✅ Log messages appearing
- ✅ Test count increasing

### Time Estimates:
- **Initialization**: 10-30 seconds
- **Test Execution**: 3-8 minutes
- **Total**: 5-10 minutes

### If Test Hangs:
- Wait up to 60 seconds (timeout warning will appear)
- Check console for error messages
- Look for specific error in log output
- See `docs/GUI_TEST_TROUBLESHOOTING.md` for solutions

---

## Expected Output Files

### When Complete:
- **Report**: `docs/GUI_TEST_RESULTS_AUTOMATED.md`
  - Test summary
  - Detailed results by category
  - Full log output

---

## Troubleshooting

### Issue: Window Doesn't Open
- Check console for errors
- Verify Qt/PySide6: `python -c "from PySide6.QtWidgets import QApplication; print('OK')"`
- Try running again

### Issue: Tests Don't Start
- Check log output for errors
- Verify Upload Bridge can launch: `python main.py`
- Check for timeout warnings

### Issue: Tests Hang
- Wait for timeout warning (60 seconds)
- Check log for specific error
- See troubleshooting guide

---

## Status Check Commands

```bash
# Check if results file exists
Test-Path docs/GUI_TEST_RESULTS_AUTOMATED.md

# Run status checker
python scripts/check_gui_test_status.py

# Check for running Python processes
Get-Process python -ErrorAction SilentlyContinue
```

---

**Test Started**: [Time]  
**Expected Completion**: [Time + 5-10 minutes]  
**Monitor**: GUI window and console output

















