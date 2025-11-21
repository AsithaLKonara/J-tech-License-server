# Testing Tooling & Configuration

## Python Dependencies

Add to `requirements-dev.txt` or `pyproject.toml`:

- `pytest>=8.0`
- `pytest-cov>=5.0`
- `pytest-qt>=4.3`
- `hypothesis>=6.100`
- `pytest-benchmark>=4.0` (optional)
- `pytest-mock>=3.12`
- `freezegun>=1.5`
- `pytest-randomly`, `pytest-xdist` (optional)
- Type hints: `types-PySide6` or `types-PyQt6`

## Directory Layout

```
tests/
  unit/
    test_frames.py
    test_layers.py
    test_canvas.py
    automation/
      test_actions.py
      test_queue.py
  integration/
    test_frame_layer_canvas.py
    test_automation_pipeline.py
    test_presets.py
  property/
    test_random_operations.py
  gui/
    test_design_tab.py
  regression/
    snapshots/
      ...
    test_exports.py
  conftest.py
```

## `pytest.ini`

```ini
[pytest]
addopts = -ra --strict-markers --strict-config
markers =
    unit: Unit tests
    integration: Integration tests
    property: Property-based tests
    gui: GUI automation tests
    regression: Snapshot tests
testpaths = tests
python_files = test_*.py
filterwarnings =
    error
    ignore::DeprecationWarning:PySide6.*
```

## Coverage Settings

`pyproject.toml` or `.coveragerc`:

```toml
[tool.coverage.run]
branch = true
source = ["domain", "services", "ui/tabs/design_tools_tab.py"]

[tool.coverage.report]
show_missing = true
fail_under = 85
```

## Hypothesis Configuration

```toml
[tool.hypothesis]
deadline = 500
max_examples = 200
stateful_step_count = 30
derandomize = true
```

## Qt Test Setup

- Set `QT_QPA_PLATFORM=offscreen` in CI.  
- Use `pytest-qt` `qtbot` fixture.  
- Ensure PySide6/PyQt6 installed in dev environment.

## Command Shortcuts

```
make test
make test-unit
make test-gui
make coverage
```

