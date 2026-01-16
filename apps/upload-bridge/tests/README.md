# Tests Directory

This directory contains all test files for the Upload Bridge project.

## Directory Structure

```
tests/
├── comprehensive/          # Comprehensive test suites
├── data/                   # Test data files (JSON, TXT, etc.)
├── e2e/                    # End-to-end tests
├── edge_cases/             # Edge case tests
├── features/               # BDD feature tests
├── gui/                    # GUI tests
├── hardware/               # Hardware-specific tests (empty, reserved)
├── integration/            # Integration tests
├── l0_structural/          # Structural tests
├── l3_workflow/            # Workflow tests
├── l4_nonfunctional/       # Non-functional tests
├── meta/                   # Meta tests (coverage, completeness)
├── performance/            # Performance tests
├── property/               # Property-based tests
├── regression/             # Regression tests
├── scripts/                # Test runner scripts
├── unit/                   # Unit tests
├── ux/                     # User experience tests
└── verification/           # Verification scripts
```

## Test Categories

### Unit Tests (`unit/`)
- Core service tests
- Domain model tests
- Utility function tests
- Component tests

### Integration Tests (`integration/`)
- Service integration tests
- UI-service integration tests
- Data flow tests
- Signal integration tests

### E2E Tests (`e2e/`)
- Complete workflow tests
- User flow tests
- Full application tests

### Comprehensive Tests (`comprehensive/`)
- Multi-suite test collections
- Feature overview tests
- Complete system tests

### Performance Tests (`performance/`)
- Large pattern tests
- Long session tests
- Export performance tests
- Service performance tests

### GUI Tests (`gui/`)
- UI component tests
- Design tab tests
- Widget tests

### UX Tests (`ux/`)
- User experience tests
- Validation tests
- Warning tests
- Error handling tests

### Verification Scripts (`verification/`)
- Hardware verification
- Chip integration verification
- Wiring verification
- Configuration verification

### Test Scripts (`scripts/`)
- Test runners
- Quick tests
- Build tests
- Integration test runners

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Suite
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/

# Performance tests
pytest tests/performance/
```

### Run Test Scripts
```bash
# Quick test
python tests/scripts/quick_test.py

# Deep integration tests
python tests/scripts/run_deep_integration_tests.py

# User flow tests
python tests/scripts/run_user_flow_tests.py
```

### Run with Coverage
```bash
pytest tests/ --cov --cov-report=html
```

## Test Data

Test data files are stored in `tests/data/`:
- `test_results.json` - Test results
- `test_results_complete.json` - Complete test results
- `test_output_full.txt` - Full test output
- `user_flow_test_output.txt` - User flow test output
- `test_pattern_data.h` - Test pattern data (C header)

## Test Organization

Tests are organized by:
1. **Type**: Unit, Integration, E2E, etc.
2. **Scope**: Component, Service, System
3. **Purpose**: Functional, Performance, UX

## Adding New Tests

When adding new tests:
1. Place in appropriate subdirectory
2. Follow naming convention: `test_*.py`
3. Add to appropriate test suite
4. Update this README if adding new category

## Test Coverage

Current test coverage: **80%+**

- Unit tests: 100+ tests
- Integration tests: 30+ tests
- E2E tests: 10+ tests
- Performance tests: 15+ tests
- Total: 300+ tests

## Test Status

- ✅ All critical tests passing
- ✅ 99.7%+ pass rate
- ✅ Comprehensive coverage
- ✅ Performance benchmarks established
