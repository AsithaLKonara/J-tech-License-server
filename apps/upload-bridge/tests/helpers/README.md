# Comprehensive Automated Test Suite - Helper Modules

This directory contains helper modules for the comprehensive automated test suite.

## Modules

### `report_generator.py`
Generates comprehensive HTML and JSON reports from test results.

**Features:**
- HTML reports with visual styling
- JSON reports for machine-readable output
- Test result tracking and summarization
- Execution time tracking
- Error message capture

### `test_layer_features.py`
Automated tests for all 7 layer feature scenarios from `docs/REMAINING_TASKS.md`.

**Scenarios Covered:**
1. Automation Layer Creation
2. Layer Sync Warning
3. Brush Broadcast Feedback
4. Hidden Layer Prevention
5. Copy Layer to Frames
6. Multiple Automation Layers
7. Edge Cases

### `test_license_system.py`
Comprehensive license system testing.

**Test Categories:**
- License Activation (premade keys, file upload, invalid keys)
- License Validation (local cache, online validation, offline fallback)
- License Expiry (checking, remaining days calculation)
- License Cache (creation, validity period, updates)

### `test_integration.py`
Cross-feature integration tests.

**Integration Tests:**
- Automation + Layer integration
- Broadcast Mode + Multiple Frames
- Copy Layer + Undo/Redo
- Hidden Layer + Effects

### `test_performance.py`
Performance and scalability tests.

**Performance Tests:**
- Large patterns (64x64, 100+ frames)
- Many layers (10+ per frame)
- Many automation layers (5+)
- Batch operations

### `test_gui_interactions.py`
Automated GUI interaction tests.

**GUI Tests:**
- Application startup
- Main window creation
- Design tools tab creation
- License dialog creation
- Widget interactions
- Dialog mocking

## Usage

These modules are used by the main test orchestrator:

```bash
python tests/test_complete_system_automated.py
```

Individual modules can also be imported and used separately:

```python
from tests.helpers.test_layer_features import LayerFeaturesTestSuite
from tests.helpers.report_generator import ReportGenerator

# Create test suite
suite = LayerFeaturesTestSuite()

# Run tests
result = suite.run_all_tests()

# Generate report
generator = ReportGenerator()
generator.add_suite_result(result)
generator.generate_all()
```

