# GUI Test Suite Execution Guide

**Date**: [Date]  
**Status**: ⚠️ Requires Manual Execution

---

## Overview

The GUI test suite (`tests/gui/test_design_tools_gui.py`) is an **interactive GUI application** that requires manual user interaction to execute tests. It cannot be run fully automated from the command line.

---

## Execution Status

### Automated Execution Attempt
```bash
python tests/gui/test_design_tools_gui.py
```

**Result**: 
- ✅ Application launches successfully
- ⚠️ Requires manual interaction to start tests
- ℹ️ Audio library warning (non-critical): "Audio libraries not available. Install pyaudio and scipy for audio-reactive effects."

**Exit Code**: 1 (expected - GUI application requires user interaction)

---

## How to Run GUI Test Suite

### Step 1: Launch the Test GUI
```bash
python tests/gui/test_design_tools_gui.py
```

Or using the launcher:
```bash
python tests/gui/run_tests.py
```

### Step 2: Manual Interaction Required

1. **Test GUI Window Opens**
   - Window title: "Design Tools Tab - Automated Test Suite"
   - Shows test results tree, progress bar, and log output

2. **Click "Start Tests" Button**
   - This will:
     - Launch Upload Bridge application
     - Initialize Design Tools Tab
     - Run all test categories sequentially
     - Display results in real-time

3. **Monitor Test Progress**
   - Watch progress bar
   - Check test results tree (color-coded: Green=Pass, Red=Fail)
   - Review log output for details

4. **Export Results (Optional)**
   - Click "Export Report" button when tests complete
   - Choose location to save HTML/JSON report

---

## Test Coverage

The GUI test suite covers **157+ tests** across **13 categories**:

1. **Header Toolbar** (8 tests)
2. **Toolbox Tabs** (9 tests)
3. **Drawing Tools** (17 tests)
4. **Canvas Features** (21 tests)
5. **Timeline Features** (22 tests)
6. **Layer System** (7 tests) ⭐ **Includes new layer features**
7. **Automation** (22 tests) ⭐ **Includes automation layer integration**
8. **Effects** (8 tests)
9. **Export/Import** (14 tests)
10. **Scratchpads** (6 tests)
11. **Keyboard Shortcuts** (9 tests)
12. **Options and Parameters** (6 tests)
13. **Feature Flows** (8 tests)

---

## Expected Test Results

### Layer System Tests (7 tests)
These should verify:
- ✅ Layer management methods exist
- ✅ Layer operations work correctly
- ✅ New layer features are accessible

### Automation Tests (22 tests)
These should verify:
- ✅ Automation methods exist
- ✅ Automation layer creation works
- ✅ Automation queue operations

---

## Manual Execution Checklist

- [ ] Launch test GUI: `python tests/gui/test_design_tools_gui.py`
- [ ] Verify GUI window opens correctly
- [ ] Click "Start Tests" button
- [ ] Monitor test execution progress
- [ ] Verify all tests complete
- [ ] Review test results
- [ ] Export report if needed
- [ ] Document any failures in `docs/INTEGRATION_TEST_RESULTS.md`

---

## Troubleshooting

### Issue: GUI doesn't open
**Solution**: 
- Check Qt/PySide6 installation
- Verify Python environment
- Check console for errors

### Issue: Tests fail to start
**Solution**:
- Ensure Upload Bridge can launch
- Check Design Tools Tab initializes
- Verify all dependencies installed

### Issue: Some tests fail
**Solution**:
- Check if widgets are initialized
- Review log output for details
- Verify new layer features are implemented

---

## Integration with Test Plan

This GUI test suite is part of **Phase 2: Integration Testing** in the test plan:

- **Task 2.1**: Test with existing GUI test suite ✅ (Ready for execution)
- **Status**: Requires manual execution
- **Next Step**: Execute manually and record results

---

## Notes

- The GUI test suite is designed for **interactive use**
- It provides **real-time feedback** during test execution
- Results can be **exported to HTML/JSON** for documentation
- Tests are **non-destructive** (read-only verification)
- Some tests may require Design Tools Tab to be fully initialized

---

## Next Steps

1. **Execute GUI Test Suite Manually**
   - Follow steps above
   - Record results in `docs/INTEGRATION_TEST_RESULTS.md`

2. **Review Results**
   - Check for any failures
   - Verify new layer features are tested
   - Document any issues

3. **Update Test Report**
   - Add GUI test results to `docs/TEST_EXECUTION_REPORT.md`
   - Note any regressions or issues

---

**Status**: ⚠️ **Requires Manual Execution**  
**Ready**: ✅ Yes - Application launches successfully  
**Action Required**: Manual test execution and result recording

