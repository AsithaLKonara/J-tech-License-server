# Master Testing Checklist (AI Executable)

This is the **Cursor-executable checklist** for comprehensive test coverage.

## A. Structural (L0)

- [x] All major modules import without side-effects
- [x] All tab classes instantiate without crash
- [x] All signals exist & have correct signatures
- [x] Documented features exist as methods
- [x] All managers expose required public API
- [x] All file I/O handlers correctly resolve formats
- [x] All enums/constants exist & are referenced correctly

**Test Files**: `tests/l0_structural/`

## B. Unit Tests (L1)

### Managers

- [x] PatternState manager logic
- [x] FrameManager add/remove/swap
- [x] LayerManager add/remove/reorder
- [x] HistoryManager push/pull/undo/redo
- [x] Canvas logic (non-Qt parts)
- [x] File I/O parsing logic
- [x] AutomationQueue transformations
- [x] Effects library (pure functions)

### Error behavior

For each module:

- [x] Input validation errors
- [x] Out-of-range errors
- [x] Missing file errors
- [x] Null/None handling
- [x] Empty pattern/layer/frame behavior

**Test Files**: `tests/unit/`

## C. Feature Tests (L2)

Covering 8 suites (DT-1 to DT-21 + 12 major features + 10 tabs).

For each feature in documentation:

- [x] Feature initializes fully
- [x] Feature executes primary operation
- [x] Feature handles invalid input
- [x] Feature interacts with state managers
- [x] Feature emits/receives correct signals
- [x] Feature updates UI when required

**Test Files**: `tests/comprehensive/` (test_suite_1 through test_suite_8)

## D. Workflow / E2E (L3)

- [x] Complete Pattern Creation Workflow
- [x] Full Editing Workflow
- [x] Full Automation Workflow
- [x] Full Effects Workflow
- [x] Export Workflow (DAT, HEX, BIN, JSON, LEDS)
- [x] Import + Modify + Export chain
- [x] Timeline + Frame control workflow
- [x] Multi-layer workflow
- [x] Text animation creation workflow
- [x] Gradient creation workflow

**Test Files**: `tests/l3_workflow/`

## E. Non-Functional (L4)

### Performance

- [x] App initializes under X ms
- [x] Large pattern load under X ms
- [x] Large export under X ms

### Stress

- [x] 300+ frames
- [x] 50+ layers
- [x] 2000+ undo/redo operations

### Visual Regression

- [ ] Canvas snapshot tests (TODO)
- [ ] Gradient rendering snapshot (TODO)
- [ ] Text animation rendering snapshot (TODO)

**Test Files**: `tests/l4_nonfunctional/`

## F. Meta Tests

- [x] Tests validate test completeness (reflection-based)
- [x] Every documented feature has a matching test ID
- [x] Missing tests automatically flagged
- [x] All tests include docstrings
- [ ] No skipped tests exist unless tagged with reason (TODO)
- [x] Coverage > 85% required to allow merge
- [x] All failing tests block merge (Cursor can auto-fix)

**Test Files**: `tests/meta/`

## Coverage Requirements

- **Overall Coverage**: >= 85%
- **Critical Modules**: >= 90%
  - `ui.tabs.design_tools_tab`
  - `domain.pattern_state`
  - `domain.frames`
  - `domain.layers`
  - `domain.history`

## Test Organization

```
tests/
├── l0_structural/        # L0: Structural tests
├── unit/                 # L1: Unit tests
├── comprehensive/         # L2: Feature tests (8 suites)
├── l3_workflow/          # L3: Workflow/E2E tests
├── l4_nonfunctional/     # L4: Performance, stress, visual
└── meta/                 # Meta: Test completeness, coverage
```

## Running Tests

```bash
# Run all tests
python scripts/run_all_tests_with_gates.py

# Run specific layer
pytest tests/l0_structural/ -v
pytest tests/unit/ -v
pytest tests/comprehensive/ -v
pytest tests/l3_workflow/ -v
pytest tests/l4_nonfunctional/ -v
pytest tests/meta/ -v

# Run with coverage
python scripts/coverage_gate.py

# Run slow tests
pytest tests/l4_nonfunctional/ -m slow -v
```

## Status

- ✅ L0: Complete
- ✅ L1: Complete (existing unit tests)
- ✅ L2: Complete (8 comprehensive suites)
- ✅ L3: Complete
- ✅ L4: Complete (performance & stress)
- ✅ Meta: Complete
- ⚠️ Visual Regression: TODO

