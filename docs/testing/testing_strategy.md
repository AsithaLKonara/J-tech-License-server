# Testing Strategy for Design Tools Subsystems

## 1. Unit Tests

| Subsystem | Key Tests |
| --------- | --------- |
| FrameManager | add/duplicate/delete/move frames, duration validation, active index adjustments |
| LayerManager | add/delete/duplicate layers, opacity/visibility toggles, pixel writes, bounds validation |
| CanvasController | composite calculations, blending, mismatched layer lengths |
| PaletteManager | gradient generation, RGB clamps, roundtrip colour updates |
| MatrixConfigurator | resizing behaviour, blank frame creation |
| AutomationQueueManager | enqueue/clear, parameter adjustments, easing |
| PresetRepository | serialization, overwrite protection, storage errors |
| History Commands | undo/redo application, snapshot integrity |

Use `pytest` with fake `PatternState` and `HistoryManager` to isolate logic.

## 2. Integration Tests

1. Frame + Layer + Canvas: verify composite correctness after edits.  
2. Automation Queue + FrameManager: ensure multi-frame application works and history updates.  
3. Presets + Automation Queue: roundtrip preset storage/application.  
4. MatrixConfigurator + FrameManager: resizing maintains data integrity.

## 3. Property-Based Tests (Hypothesis)

| Scenario | Property |
| -------- | -------- |
| Random frame/layer operations | No crashes; undo restores state |
| Gradient generation | Colours remain 0–255; monotonic transitions |
| Automation actions | Deterministic results; distance bounds hold |
| Preset roundtrip | Saved + loaded queue equals original |

## 4. GUI Tests (`pytest-qt`)

- Simulate timeline frame addition and ensure frame count updates.  
- Draw pixel via canvas; assert layer update + history entry.  
- Save/apply preset via UI; confirm queue contents.  
- Keyboard shortcut coverage (play/pause, step).

## 5. Regression & Snapshot Tests

- Golden files for pattern export, preset JSON.  
- Timeline visual snapshot for regression detection.

## 6. Performance / Stress (optional)

- Benchmark automation application on large project via `pytest-benchmark`.  
- Measure timeline responsiveness with 500 frames.

## 7. Execution Matrix

| Stage | Command | Frequency |
| ----- | ------- | --------- |
| Unit | `pytest -m unit` | Every CI run |
| Integration | `pytest -m integration` | Every CI run |
| Property | `pytest -m property` | Nightly |
| GUI | `pytest -m gui` | Nightly/manual |
| Regression | `pytest -m regression` | Weekly or release |

## 8. Fixtures & Utilities

- `pattern_state_factory`  
- `history_spy`  
- `temp_preset_repo` (in-memory)  
- `qt_design_tab` (UI fixture with mocks)

## 9. Coverage Goals

- Overall ≥85% initially, ramp to 90%+.  
- Automation actions, gradient generation ≥100%.  
- Configure `pytest.ini` to enforce thresholds.

