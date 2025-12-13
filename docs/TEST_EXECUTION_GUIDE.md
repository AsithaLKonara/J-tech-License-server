# Test Execution Guide

## Quick Start

### Run All Tests
```bash
python tests/test_execution_scripts/run_all_tests.py
```

### Run Tests with Coverage
```bash
python tests/test_execution_scripts/run_with_coverage.py
```

## Test Execution Phases

### Phase 1: Unit Testing
**Duration**: Week 1  
**Target**: 90%+ code coverage

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=core --cov=ui --cov-report=html
```

**Test Areas**:
- Core pattern classes
- Services (Export, Flash, Pattern)
- Managers (Frame, Layer, Automation, History)
- Mappers (Circular, Wiring)
- Export/Import modules

### Phase 2: Integration Testing
**Duration**: Week 2

```bash
# Run integration tests
pytest tests/integration/ -v
```

**Test Areas**:
- Tab-to-tab integration
- Service integration
- Repository integration
- Signal connections

### Phase 3: System Testing
**Duration**: Week 3-4

```bash
# Run comprehensive tests
pytest tests/comprehensive/ -v

# Run specific feature tests
pytest tests/test_budurasmala_*.py -v
```

**Test Areas**:
- Complete user workflows
- Circular layout features
- Export/import formats
- Design Tools features

### Phase 4: Performance Testing
**Duration**: Week 5

```bash
# Run performance tests
pytest tests/performance/ -v
```

**Test Areas**:
- Large pattern handling
- Real-time update performance
- Export performance
- Memory usage

### Phase 5: Regression Testing
**Duration**: Week 6

```bash
# Run full regression suite
pytest tests/ -v --maxfail=1
```

### Phase 6: Acceptance Testing
**Duration**: Week 7

Manual testing with real users and hardware.

## Test Case Execution

### By Feature Area

#### Application Launch
```bash
pytest tests/comprehensive/test_suite_1_design_tools_core.py::test_app_launch -v
```

#### Design Tools
```bash
pytest tests/comprehensive/test_suite_1_design_tools_core.py -v
```

#### Media Upload
```bash
pytest tests/comprehensive/test_suite_2_feature_overview.py::test_media_upload -v
```

#### Circular Layouts
```bash
pytest tests/test_budurasmala_multi_ring.py -v
pytest tests/test_budurasmala_radial_rays.py -v
pytest tests/test_budurasmala_custom_positions.py -v
```

#### Export/Import
```bash
pytest tests/test_budurasmala_export.py -v
```

## Test Reporting

### Coverage Reports
After running with coverage:
- **HTML Report**: Open `htmlcov/index.html` in browser
- **Terminal Report**: Shown in console
- **JSON Report**: `coverage.json` for CI integration

### Test Results
- **JUnit XML**: `pytest tests/ --junitxml=results.xml`
- **HTML Report**: Use pytest-html plugin
- **JSON Report**: Use pytest-json-report plugin

## Continuous Integration

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    python tests/data/test_patterns_generator.py
    pytest tests/ -v --cov=core --cov=ui --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v2
  with:
    files: ./coverage.xml
```

## Troubleshooting

### Tests Failing
1. Check test data exists: `ls tests/data/test_*.ledproj`
2. Regenerate test data: `python tests/data/test_patterns_generator.py`
3. Check dependencies: `pip install -r requirements.txt`
4. Check Python version: `python --version` (should be 3.9+)

### Coverage Low
1. Review uncovered lines in HTML report
2. Add tests for uncovered code
3. Exclude test files from coverage if needed

### Performance Issues
1. Run tests individually to identify slow tests
2. Use `--durations=10` to see slowest tests
3. Consider parallel execution: `pytest -n auto`

