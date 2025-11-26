# User Flow Testing Guide

This guide explains how to use the automated user flow testing system that simulates real user interactions with the Upload Bridge application.

## Overview

The user flow testing system includes:
1. **Automated Test Suite** (`tests/e2e/test_user_flows_automated.py`) - Comprehensive tests that simulate user interactions
2. **Command-Line Runner** (`run_user_flow_tests.py`) - Script to run tests from command line
3. **Interactive GUI Runner** (`tests/e2e/interactive_test_runner.py`) - GUI application for running tests

## Quick Start

### Option 1: Command Line (Recommended)

Run all tests:
```bash
python run_user_flow_tests.py
```

Run with verbose output:
```bash
python run_user_flow_tests.py --verbose
```

Run specific test class:
```bash
python run_user_flow_tests.py --specific TestUserFlow_PatternCreation
```

Run specific test method:
```bash
python run_user_flow_tests.py --specific TestUserFlow_PatternCreation::test_create_new_pattern
```

### Option 2: Interactive GUI Runner

Launch the GUI test runner:
```bash
python tests/e2e/interactive_test_runner.py
```

Features:
- Select which tests to run
- See real-time test output
- View results summary
- Re-run failed tests

### Option 3: Direct pytest

Run tests directly with pytest:
```bash
python -m pytest tests/e2e/test_user_flows_automated.py -v
```

## Test Coverage

The automated test suite covers:

### ✅ Application Startup
- Application launches correctly
- Main window is visible
- Tabs are created

### ✅ Pattern Creation
- Create new pattern via dialog
- Pattern is created successfully

### ✅ Pattern Loading
- Load pattern from file
- Handle invalid/corrupted files
- Show appropriate error messages

### ✅ Drawing Tools
- Pixel brush drawing
- Canvas interaction
- Tool selection

### ✅ Frame Management
- Add frames
- Delete frames
- Cannot delete last frame (shows error)
- Duplicate frames

### ✅ Brush Broadcast
- Enable broadcast mode
- Warning dialog appears
- Visual indicators work

### ✅ Undo/Redo
- Undo/redo buttons work
- Button states update correctly
- History management

### ✅ Export
- Export pattern to file
- File dialog works
- Export validation

### ✅ Image Import
- Import image files
- Handle invalid files
- Error messages

### ✅ Unsaved Changes
- Warning when loading new file with unsaved changes
- Save/Discard/Cancel options
- Changes are preserved or discarded correctly

### ✅ Complete Workflow
- End-to-end workflow test
- Create → Draw → Add Frames → Export

## Test Structure

Each test class follows this pattern:

```python
class TestUserFlow_FeatureName:
    """Test: User performs some action"""
    
    def test_specific_action(self, design_tab, qtbot):
        """User does something specific"""
        # Setup
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        # Action
        # ... perform user action ...
        
        # Verification
        assert something == expected
```

## Running Tests

### All Tests
```bash
python run_user_flow_tests.py
```

### Specific Test Class
```bash
python run_user_flow_tests.py --specific TestUserFlow_PatternLoading
```

### With Coverage
```bash
python run_user_flow_tests.py --coverage
```

### Generate HTML Report
```bash
python run_user_flow_tests.py --html-report
```

## Understanding Test Output

### Success
```
✅ All tests passed!
```

### Failure
```
❌ Some tests failed
```

Test output includes:
- Test name
- Status (PASSED/FAILED/SKIPPED)
- Error messages (if any)
- Stack traces (for failures)

## Adding New Tests

To add a new user flow test:

1. Open `tests/e2e/test_user_flows_automated.py`
2. Create a new test class:
```python
class TestUserFlow_NewFeature:
    """Test: User uses new feature"""
    
    def test_new_feature(self, design_tab, qtbot):
        """User tests new feature"""
        qtbot.addWidget(design_tab)
        qtbot.wait(300)
        
        # Your test code here
        assert something
```

3. Run the test:
```bash
python run_user_flow_tests.py --specific TestUserFlow_NewFeature
```

## Troubleshooting

### Tests Hang or Timeout
- Increase wait times in tests
- Check if dialogs are blocking (use mocks)

### Widget Not Found Errors
- Ensure widgets are created before accessing
- Use `hasattr()` checks
- Wait for UI to initialize with `qtbot.wait()`

### Tests Fail Intermittently
- Add longer wait times
- Ensure proper cleanup between tests
- Check for race conditions

## Best Practices

1. **Always wait for UI**: Use `qtbot.wait()` after UI operations
2. **Mock dialogs**: Mock `QMessageBox` and `QFileDialog` to prevent blocking
3. **Clean up**: Ensure proper cleanup in fixtures
4. **Isolate tests**: Each test should be independent
5. **Verify state**: Always verify expected state after actions

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
- name: Run User Flow Tests
  run: |
    python run_user_flow_tests.py --verbose
```

## Performance

- Full test suite: ~2-5 minutes
- Individual test: ~5-30 seconds
- GUI tests are slower than unit tests (expected)

## Support

For issues or questions:
1. Check test output for error messages
2. Review test code in `test_user_flows_automated.py`
3. Check application logs
4. Run tests individually to isolate issues

## Next Steps

After running tests:
1. Review test results
2. Fix any failing tests
3. Add tests for new features
4. Update tests when UI changes

