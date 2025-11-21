# Testing Plan Summary & Next Actions

## Deliverables

- Subsystem inventory (`docs/testing/subsystems_overview.md`)
- Architecture outline (`docs/testing/architecture_outline.md`)
- Testing strategy (`docs/testing/testing_strategy.md`)
- Tooling setup (`docs/testing/tooling_setup.md`)
- CI guidance (`docs/testing/ci_guidance.md`)
- Test suite skeleton (`tests/`)

## Immediate Actions

1. Extract managers (`FrameManager`, `LayerManager`, etc.) per architecture outline.
2. Replace skipped tests with real assertions as modules are implemented.
3. Configure `pytest.ini`, coverage, Hypothesis settings.
4. Add CI workflow and ensure coverage reporting.
5. Populate regression snapshots and enable regression tests.

## Incremental Migration

| Step | Description | Outcome |
| ---- | ----------- | ------- |
| 1 | Extract frame & layer logic + unit tests | Stable core data operations |
| 2 | Implement automation queue module + property tests | Reliable action execution |
| 3 | Move presets to repository + regression tests | Deterministic storage behaviour |
| 4 | Wire UI to managers + GUI tests | Confidence in interactions |
| 5 | Expand integration & regression coverage | Prevent cross-module regressions |

## Risk Mitigation

- Maintain feature flags during migration.  
- Run new tests alongside legacy checks until confident.  
- Use Hypothesis/property testing to catch edge cases early.

## Tracking Progress

- Update TODOs or task board per completed manager/test suite.  
- Document newly stabilised modules in architecture outline.  
- Review coverage metrics after each feature merge.

