# Design Tools Tab - Automated Test GUI

Automated test suite for verifying all Design Tools Tab features and flows.

## Overview

This test GUI application:
- Launches the Upload Bridge application
- Automatically tests all 157 verified features
- Tests all 8 documented feature flows
- Displays real-time test progress and results
- Generates detailed HTML and JSON reports

## Usage

### Running the Test GUI

```bash
python tests/gui/test_design_tools_gui.py
```

### Test Categories

The test suite covers 13 categories:

1. **Header Toolbar** (8 tests) - All header buttons and toolbar creation
2. **Toolbox Tabs** (9 tests) - All 8 toolbox tabs and column creation
3. **Drawing Tools** (17 tests) - All 8 drawing tools and related controls
4. **Canvas Features** (21 tests) - Canvas methods, signals, overlays, shapes
5. **Timeline Features** (22 tests) - Frame operations, playback, signals
6. **Layer System** (7 tests) - Layer management and operations
7. **Automation** (22 tests) - Canvas Automation and LMS Automation
8. **Effects** (8 tests) - Effects library and application
9. **Export/Import** (14 tests) - Export/import methods and groups
10. **Scratchpads** (6 tests) - Scratchpad operations
11. **Keyboard Shortcuts** (9 tests) - All keyboard shortcuts
12. **Options and Parameters** (6 tests) - All parameter controls
13. **Feature Flows** (8 tests) - All documented workflows

### Test Execution

1. Launch the test GUI application
2. Click "Start Tests" button
3. The application will:
   - Launch Upload Bridge
   - Initialize Design Tools Tab
   - Run all test categories sequentially
   - Display results in real-time
4. When complete, click "Export Report" to save results

### Report Formats

- **HTML Report**: Visual report with color-coded results, suitable for viewing in a browser
- **JSON Report**: Machine-readable format for CI/CD integration

## Test Results

### Status Indicators

- **Pass** (Green): Test passed successfully
- **Fail** (Red): Test failed with error details
- **Pending** (Gray): Test not yet executed
- **In Progress** (Yellow): Test currently running

### Understanding Results

Each test verifies:
- Method/attribute existence
- Signal definitions
- Enum values
- Import success
- Code presence (for shortcuts and options)

## Files

- `test_design_tools_gui.py` - Main GUI application
- `test_runner.py` - Test execution engine
- `test_cases.py` - Individual test implementations
- `report_generator.py` - HTML/JSON report generation

## Dependencies

- PySide6 (Qt framework)
- QTest (for widget testing)
- Standard library: json, datetime, pathlib

## Notes

- Tests run in a separate thread to keep GUI responsive
- Some tests require the Design Tools Tab to be fully initialized
- Canvas and Timeline tests may fail if widgets aren't initialized
- All tests are non-destructive (read-only verification)

## Troubleshooting

**Tests fail to start:**
- Ensure Upload Bridge can launch successfully
- Check that all dependencies are installed
- Verify Design Tools Tab initializes correctly

**Some tests fail:**
- Check if widgets are initialized (canvas, timeline, etc.)
- Verify all required modules are imported
- Check test log for detailed error messages

**Application doesn't close:**
- Use "Stop Tests" button to halt execution
- Close Upload Bridge window manually if needed

