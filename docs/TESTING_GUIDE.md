# Testing Guide

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Purpose**: Guide for testing the Design Tools Tab system, including unit tests, integration tests, manual test checklists, and test data requirements

---

## Overview

This guide covers testing strategies, test organization, running tests, and test data requirements for the Design Tools Tab. The testing approach includes unit tests, integration tests, and manual test checklists.

---

## Test Organization

### Directory Structure

```
tests/
├── unit/
│   ├── test_pattern_state.py
│   ├── test_frame_manager.py
│   ├── test_layer_manager.py
│   ├── test_history_manager.py
│   ├── test_automation_queue.py
│   └── ...
├── integration/
│   ├── test_pattern_loading.py
│   ├── test_canvas_drawing.py
│   ├── test_layer_compositing.py
│   ├── test_export_import.py
│   └── ...
├── automation/
│   ├── test_lms_automation.py
│   ├── test_effects_application.py
│   └── ...
└── fixtures/
    ├── sample_patterns/
    ├── test_fonts/
    └── test_images/
```

---

## Unit Tests

### What's Tested

Unit tests focus on individual components (managers, utilities) in isolation.

**PatternState Tests**:
- Pattern getter/setter
- Frame access
- Metadata access
- Dimension access
- None pattern handling

**FrameManager Tests**:
- Frame add/delete/duplicate
- Frame selection
- Frame duration
- Frame move/reorder
- Signal emission
- Index validation

**LayerManager Tests**:
- Layer add/remove
- Pixel application
- Layer visibility/opacity
- Layer compositing
- Frame sync
- Signal emission

**HistoryManager Tests**:
- Command push
- Undo/redo operations
- Frame-specific history
- History stack limits

**AutomationQueueManager Tests**:
- Action enqueue/dequeue
- Action reorder
- Queue clearing
- Signal emission

### Test Examples

#### PatternState Unit Test

```python
import pytest
from domain.pattern_state import PatternState
from domain.pattern import Pattern

def test_pattern_getter():
    state = PatternState()
    assert state.pattern() is None
    
    pattern = Pattern.create_blank(16, 16, 1)
    state.set_pattern(pattern)
    assert state.pattern() == pattern

def test_dimensions():
    state = PatternState()
    pattern = Pattern.create_blank(32, 24, 1)
    state.set_pattern(pattern)
    assert state.width() == 32
    assert state.height() == 24
```

#### FrameManager Unit Test

```python
import pytest
from domain.frames import FrameManager
from domain.pattern_state import PatternState

def test_add_frame():
    state = PatternState()
    state.set_pattern(Pattern.create_blank(16, 16, 1))
    manager = FrameManager(state)
    
    index = manager.add()
    assert index == 1  # Second frame
    assert len(state.pattern().frames) == 2

def test_delete_frame():
    state = PatternState()
    pattern = Pattern.create_blank(16, 16, 3)
    state.set_pattern(pattern)
    manager = FrameManager(state)
    
    manager.delete(1)
    assert len(state.pattern().frames) == 2

def test_cannot_delete_last_frame():
    state = PatternState()
    pattern = Pattern.create_blank(16, 16, 1)
    state.set_pattern(pattern)
    manager = FrameManager(state)
    
    with pytest.raises(ValueError):
        manager.delete(0)
```

#### LayerManager Unit Test

```python
import pytest
from domain.layers import LayerManager
from domain.pattern_state import PatternState

def test_add_layer():
    state = PatternState()
    state.set_pattern(Pattern.create_blank(16, 16, 1))
    manager = LayerManager(state)
    
    index = manager.add_layer(0, "Test Layer")
    assert index == 1  # Second layer
    layers = manager.get_layers(0)
    assert len(layers) == 2

def test_apply_pixel():
    state = PatternState()
    state.set_pattern(Pattern.create_blank(16, 16, 1))
    manager = LayerManager(state)
    
    manager.apply_pixel(0, 5, 10, (255, 0, 0), 16, 16, 0)
    layer = manager.get_layers(0)[0]
    pixel_index = 10 * 16 + 5
    assert layer.pixels[pixel_index] == (255, 0, 0)

def test_composite_pixels():
    state = PatternState()
    state.set_pattern(Pattern.create_blank(16, 16, 1))
    manager = LayerManager(state)
    
    # Add two layers with different colors
    manager.add_layer(0, "Layer 1")
    manager.apply_pixel(0, 5, 10, (255, 0, 0), 16, 16, 0)
    manager.apply_pixel(0, 5, 10, (0, 255, 0), 16, 16, 1)
    
    composite = manager.get_composite_pixels(0)
    pixel_index = 10 * 16 + 5
    # Should be blended (green over red)
    assert composite[pixel_index] != (255, 0, 0)
    assert composite[pixel_index] != (0, 255, 0)
```

---

## Integration Tests

### What's Tested

Integration tests verify interactions between multiple components.

**Pattern Loading Integration**:
- File parsing → PatternState → FrameManager → LayerManager
- Signal propagation
- UI updates

**Canvas Drawing Integration**:
- Canvas signal → DesignToolsTab → LayerManager → PatternState
- HistoryManager integration
- Canvas refresh

**Layer Compositing Integration**:
- Multiple layers → Composite → Frame sync → Canvas display

**Export/Import Integration**:
- Pattern → Export → File → Import → Pattern
- Format round-trip testing

### Test Examples

#### Pattern Loading Integration Test

```python
import pytest
from pathlib import Path
from ui.tabs.design_tools_tab import DesignToolsTab
from domain.pattern_state import PatternState

def test_load_pattern_integration(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    
    # Load a test pattern file
    test_file = Path("tests/fixtures/sample_patterns/test.leds")
    tab._on_open_pattern_clicked()
    
    # Verify all managers are updated
    assert tab.pattern_state.pattern() is not None
    assert len(tab.frame_manager.frames()) > 0
    assert len(tab.layer_manager.get_layers(0)) > 0
```

#### Canvas Drawing Integration Test

```python
import pytest
from ui.tabs.design_tools_tab import DesignToolsTab

def test_canvas_drawing_integration(qtbot):
    tab = DesignToolsTab()
    qtbot.addWidget(tab)
    
    # Create new pattern
    tab._on_new_pattern_clicked()
    
    # Simulate pixel paint
    tab._on_canvas_pixel_updated(5, 10, (255, 0, 0))
    
    # Verify layer updated
    layers = tab.layer_manager.get_layers(0)
    pixel_index = 10 * 16 + 5
    assert layers[0].pixels[pixel_index] == (255, 0, 0)
    
    # Verify history updated
    command = tab.history_manager.undo(0)
    assert command is not None
```

---

## Manual Test Checklists

### Feature-by-Feature Testing

#### DT-1: Pattern Creation

- [ ] Click "New" button creates blank pattern
- [ ] Default dimensions are 16x16
- [ ] Default frame count is 1
- [ ] Canvas displays blank pattern
- [ ] Timeline shows 1 frame
- [ ] Layer panel shows default layer

#### DT-2: Pattern Loading

- [ ] "Open" button opens file dialog
- [ ] Can load DAT files
- [ ] Can load HEX files
- [ ] Can load BIN files
- [ ] Can load LEDS files
- [ ] Can load JSON files
- [ ] Error shown for invalid files
- [ ] Error shown for unsupported formats
- [ ] Pattern dimensions match file
- [ ] Frame count matches file
- [ ] Canvas displays loaded pattern

#### DT-4: Canvas Drawing

- [ ] Can click to paint pixels
- [ ] Can drag to paint multiple pixels
- [ ] Color selection works
- [ ] Brush size affects painting
- [ ] Paint applies to active layer
- [ ] Canvas updates immediately
- [ ] Undo works after painting
- [ ] Redo works after undo

#### DT-7: Frame Management

- [ ] "Add Frame" creates new frame
- [ ] "Delete Frame" removes frame
- [ ] Cannot delete last frame
- [ ] "Duplicate Frame" creates copy
- [ ] Can reorder frames in timeline
- [ ] Frame selection updates canvas
- [ ] Timeline reflects frame changes

#### DT-8: Layer Management

- [ ] "Add Layer" creates new layer
- [ ] "Remove Layer" removes layer
- [ ] Cannot remove last layer
- [ ] Layer visibility toggle works
- [ ] Layer opacity slider works
- [ ] Layer rename works
- [ ] Can reorder layers
- [ ] Composite updates when layers change

#### DT-11: Undo/Redo

- [ ] Ctrl+Z undoes last operation
- [ ] Ctrl+Y redoes undone operation
- [ ] Undo button works
- [ ] Redo button works
- [ ] Undo/redo is frame-specific
- [ ] History persists across frame switches

#### DT-14: LMS Automation

- [ ] Can add LMS instructions
- [ ] Can configure instruction parameters
- [ ] Preview sequence works
- [ ] Export LEDS creates valid file
- [ ] Exported file can be loaded back

### Regression Testing

**Critical Paths**:
- [ ] Create pattern → Paint → Save → Load → Verify
- [ ] Create pattern → Add layers → Paint → Export → Load → Verify
- [ ] Load pattern → Modify → Undo → Redo → Save
- [ ] Load pattern → Apply effects → Export → Load → Verify

**Edge Cases**:
- [ ] Very large patterns (64x64, 100+ frames)
- [ ] Many layers (10+ layers per frame)
- [ ] Empty patterns
- [ ] Single-pixel patterns
- [ ] Patterns with all frames identical
- [ ] Patterns with all layers identical

---

## Test Data Requirements

### Sample Patterns

**Basic Patterns**:
- `blank_16x16.leds` - Blank 16x16 pattern, 1 frame
- `blank_32x32.leds` - Blank 32x32 pattern, 1 frame
- `simple_16x16.leds` - Simple pattern with a few pixels, 5 frames

**Complex Patterns**:
- `multi_layer.leds` - Pattern with 5 layers per frame, 10 frames
- `large_pattern.leds` - 64x64 pattern, 50 frames
- `many_frames.leds` - 16x16 pattern, 200 frames

**Edge Cases**:
- `single_pixel.leds` - 1x1 pattern, 1 frame
- `wide_pattern.leds` - 64x8 pattern (wide), 10 frames
- `tall_pattern.leds` - 8x64 pattern (tall), 10 frames

### Test Images

- `test_image.png` - 16x16 PNG image
- `test_image.jpg` - 16x16 JPG image
- `test_animation.gif` - 16x16 GIF with 10 frames

### Test Fonts

- `test_font.json` - Custom bitmap font for text animation tests

### Mock Data

**Pattern Mock**:
```python
def create_mock_pattern(width=16, height=16, frames=1):
    pattern = Pattern.create_blank(width, height, frames)
    # Add some test pixels
    for frame in pattern.frames:
        frame.pixels[0] = (255, 0, 0)  # Red pixel at (0, 0)
    return pattern
```

**Layer Mock**:
```python
def create_mock_layer(name="Test Layer", visible=True, opacity=1.0):
    layer = Layer(name=name, visible=visible, opacity=opacity)
    layer.pixels = [(0, 0, 0)] * (16 * 16)  # Black pixels
    return layer
```

---

## Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_frame_manager.py

# Run with coverage
pytest tests/unit/ --cov=domain --cov-report=html

# Run with verbose output
pytest tests/unit/ -v
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration test
pytest tests/integration/test_canvas_drawing.py

# Run with Qt bot (for UI tests)
pytest tests/integration/ --qtbot
```

### All Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run with parallel execution
pytest tests/ -n auto
```

---

## Test Best Practices

### Writing Tests

1. **Test one thing**: Each test should verify one specific behavior
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification
4. **Use fixtures**: Reuse test data and setup code
5. **Test edge cases**: Include tests for boundary conditions and error cases
6. **Mock external dependencies**: Mock file I/O, UI components, etc.

### Test Organization

1. **Group related tests**: Use test classes or modules for related tests
2. **Use parametrize**: Use `@pytest.mark.parametrize` for testing multiple inputs
3. **Use fixtures**: Create reusable test fixtures for common setup
4. **Keep tests independent**: Tests should not depend on each other

### Test Maintenance

1. **Update tests with code changes**: Keep tests in sync with implementation
2. **Remove obsolete tests**: Delete tests for removed features
3. **Fix flaky tests**: Investigate and fix tests that fail intermittently
4. **Monitor test coverage**: Aim for >80% code coverage

---

## Test Coverage Goals

### Target Coverage

- **Unit Tests**: >90% coverage for domain logic
- **Integration Tests**: >70% coverage for integration paths
- **Overall**: >80% total coverage

### Critical Components

These components should have 100% test coverage:
- PatternState
- FrameManager
- LayerManager
- HistoryManager
- Export/Import parsers

---

## Continuous Integration

### CI Configuration

Tests should run automatically on:
- Every commit to main branch
- Every pull request
- Nightly builds

### CI Pipeline

1. **Lint**: Run code linters
2. **Unit Tests**: Run unit test suite
3. **Integration Tests**: Run integration test suite
4. **Coverage Report**: Generate coverage report
5. **Publish Results**: Publish test results and coverage

---

## Debugging Failed Tests

### Common Issues

1. **Signal timing**: Qt signals may need `qtbot.wait()` for async operations
2. **State pollution**: Tests may affect each other if state isn't reset
3. **File paths**: Use `Path` objects and relative paths for test files
4. **Mock setup**: Ensure mocks are properly configured

### Debugging Tips

1. **Use `pytest -v`**: Verbose output shows which tests fail
2. **Use `pytest --pdb`**: Drop into debugger on failure
3. **Use `print()` statements**: Add debug output to understand test flow
4. **Isolate failing test**: Run single test to focus on issue

---

## References

- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Architecture overview
- API_REFERENCE.md - API documentation
- pytest Documentation: https://docs.pytest.org/
- Qt Testing: https://doc.qt.io/qt-5/qttest-index.html

