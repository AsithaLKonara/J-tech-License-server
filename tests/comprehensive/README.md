# Comprehensive Deep Testing Suite

This directory contains comprehensive test suites covering all features documented in:
- `docs/FEATURE_OVERVIEW.txt`
- `docs/DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md`
- `docs/FEATURE_LINKAGE_DIAGRAM.md`

## Test Suite Organization

### Test Suite 1: Design Tools Tab Core Features
**File**: `test_suite_1_design_tools_core.py`

Tests all 21 core features (DT-1 to DT-21) of the Design Tools Tab:
- DT-1: Pattern Creation
- DT-2: Pattern Loading
- DT-3: Pattern Export
- DT-4: Canvas Drawing
- DT-5: Color Selection
- DT-6: Brush Tools
- DT-7: Frame Management
- DT-8: Layer Management
- DT-9: Timeline Navigation
- DT-10: Playback Control
- DT-11: Undo/Redo
- DT-12: Matrix Configuration
- DT-13: Automation Queue
- DT-14: LMS Automation
- DT-15: Effects Library
- DT-16: Scratchpads
- DT-17: Text Animation
- DT-18: Image Import
- DT-19: Gradient Tools
- DT-20: Zoom Controls
- DT-21: Preview Mode

### Test Suite 2: Feature Overview Areas
**File**: `test_suite_2_feature_overview.py`

Tests all 12 major feature areas from FEATURE_OVERVIEW.txt:
1. Canvas Authoring Toolbox
2. Frame & Layer Management
3. Automation Queue (Legacy Frame Baking Flow)
4. LMS Automation Suite
5. Custom Effects Engine
6. File Importers, Exporters, and Metadata Guards
7. Diagnostics & Hardware Support
8. Theme & UX Facilities
9. Package Creation & Distribution Scripts
10. Documentation Set
11. Testing & Validation
12. Safety, Scratchpads & Template Tooling

### Test Suite 3: All Tabs Integration
**File**: `test_suite_3_all_tabs_integration.py`

Tests integration between all 10 tabs and MainWindow:
- MediaUploadTab
- DesignToolsTab
- PreviewTab
- FlashTab
- BatchFlashTab
- PatternLibraryTab
- AudioReactiveTab
- WiFiUploadTab
- ArduinoIDETab
- ESP32SDCardTab

### Test Suite 4: Signal Connections & Linkages
**File**: `test_suite_4_signal_connections.py`

Tests all signal connections between components:
- DesignToolsTab signals
- FrameManager signals
- LayerManager signals
- AutomationQueueManager signals
- Canvas widget signals
- MainWindow signal connections
- Missing signal connections (documented requirements)

### Test Suite 5: Error Handling & Edge Cases
**File**: `test_suite_5_error_handling.py`

Tests all error handling scenarios:
- Pattern creation errors
- Pattern loading errors
- Canvas drawing errors
- Frame management errors
- Layer management errors
- Playback errors
- Export errors
- Undo/redo errors

### Test Suite 6: UI Components & Interactions
**File**: `test_suite_6_ui_components.py`

Tests all UI components and their interactions:
- Header toolbar
- Canvas panel
- Toolbox tabs
- Timeline dock
- Brushes tab components
- Layers tab components
- Automation tab components
- UI interactions

### Test Suite 7: Manager Interactions
**File**: `test_suite_7_manager_interactions.py`

Tests interactions between different managers:
- PatternState manager
- FrameManager and LayerManager interactions
- LayerManager and Canvas interactions
- HistoryManager interactions
- AutomationQueueManager interactions

### Test Suite 8: File I/O & Export/Import
**File**: `test_suite_8_file_io.py`

Tests all file import/export functionality:
- DAT file I/O
- HEX file I/O
- BIN file I/O
- LEDS file I/O
- JSON file I/O
- Code template export
- File format detection

## Running the Tests

### Run All Test Suites
```bash
python tests/comprehensive/run_all_tests.py
```

### Run Individual Test Suite
```bash
pytest tests/comprehensive/test_suite_1_design_tools_core.py -v
pytest tests/comprehensive/test_suite_2_feature_overview.py -v
# ... etc
```

### Run Specific Test Class
```bash
pytest tests/comprehensive/test_suite_1_design_tools_core.py::TestDT1_PatternCreation -v
```

### Run Specific Test
```bash
pytest tests/comprehensive/test_suite_1_design_tools_core.py::TestDT1_PatternCreation::test_create_default_pattern -v
```

### Run with Coverage
```bash
pytest tests/comprehensive/ --cov=ui.tabs.design_tools_tab --cov=domain --cov-report=html
```

## Test Requirements

### Dependencies
- pytest >= 8.0
- pytest-qt >= 4.3
- PySide6
- All project dependencies

### Environment Setup
```bash
# Set Qt platform for headless testing
export QT_QPA_PLATFORM=offscreen

# Or on Windows
set QT_QPA_PLATFORM=offscreen
```

## Test Coverage Goals

- **Unit Tests**: Individual components and managers
- **Integration Tests**: Component interactions
- **UI Tests**: Widget interactions and signals
- **Error Handling**: All error scenarios
- **Edge Cases**: Boundary conditions and invalid inputs

## Notes

- Some tests may be skipped if features are not yet implemented
- Tests use `pytest.skip()` for missing implementations
- Tests use mocks for file dialogs and external dependencies
- All tests use `qtbot` fixture for Qt widget testing
- Tests are designed to be run in CI/CD pipelines

## Contributing

When adding new features:
1. Add corresponding test cases to the appropriate test suite
2. Follow the existing test structure and naming conventions
3. Ensure tests pass before submitting
4. Update this README if adding new test suites

