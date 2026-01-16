# UX Testing Suite

This directory contains automated tests for the 15 UX issues identified in `DESIGN_TOOLS_UX_ANALYSIS.md`.

## Test Structure

- `test_pattern_loading_errors.py` - TC-UX-001: Pattern loading error handling
- `test_brush_broadcast_warning.py` - TC-UX-002: Brush broadcast warning
- `test_delete_frame_validation.py` - TC-UX-004: Delete frame feedback
- `test_undo_redo_states.py` - TC-UX-005: Undo/redo visual indication
- `test_unsaved_changes_warning.py` - TC-UX-006: Unsaved changes warning
- `test_export_validation.py` - TC-UX-008: Export validation

## Running Tests

```bash
# Run all UX tests
pytest tests/ux/ -v

# Run specific test
pytest tests/ux/test_pattern_loading_errors.py -v

# Run with GUI (requires display)
pytest tests/ux/ -v -m gui

# Run without GUI tests
pytest tests/ux/ -v -m "not gui"
```

## Test Coverage

- **Critical Issues:** 3 test files
- **High Priority Issues:** 4 test files
- **Medium/Low Priority:** Manual testing (see QA_TESTING_PLAN.md)

## Notes

- Some tests require mocking QMessageBox dialogs
- GUI tests require a display (X11 on Linux, or headless mode)
- Tests may need adjustment based on actual implementation

