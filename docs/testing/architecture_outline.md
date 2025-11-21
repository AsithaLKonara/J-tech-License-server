# Modular Architecture Outline for Design Tools Tab

This document proposes the modularisation required to make `DesignToolsTab`
testable and maintainable. It defines boundaries, interfaces, and dependencies.

## High-Level Structure

```
ui/
  tabs/
    design_tools_tab.py        # Presentation layer
domain/
  pattern_state.py             # Shared PatternState + events
  frames.py                    # FrameManager
  layers.py                    # LayerManager
  canvas.py                    # CanvasController
  palette.py                   # Palette/GradientManager
  matrix.py                    # MatrixConfigurator
  automation/
    queue.py                   # AutomationQueueManager
    actions.py                 # Action implementations
    presets.py                 # PresetRepository & preview service
services/
  history.py                   # HistoryManager & commands
  storage.py                   # File IO abstraction
```

## Shared `PatternState`

```python
class PatternState:
    pattern: Pattern
    active_frame: int
    layers: Dict[int, List[LayerData]]
    active_layers: Dict[int, int]
    metadata: PatternMetadata
```

- Emits hooks: `on_pattern_changed`, `on_frame_changed`, `on_layers_changed`.
- Provides safe accessors/mutators for frames and layers.
- Managers receive `PatternState` via DI; history snapshots use immutable copies.

## Manager Interfaces (examples)

### FrameManager (`domain/frames.py`)

```python
class FrameManager:
    def __init__(self, state: PatternState, history: HistoryManager): ...
    def add_blank(self) -> int: ...
    def duplicate(self, index: int) -> int: ...
    def delete(self, index: int) -> None: ...
    def move(self, src: int, dest: int) -> None: ...
    def set_duration(self, index: int, ms: int) -> None: ...
```

### LayerManager (`domain/layers.py`)

```python
class LayerManager:
    def add(self, frame_index: int, name: str | None = None) -> int: ...
    def duplicate(self, frame_index: int, layer_index: int) -> int: ...
    def delete(self, frame_index: int, layer_index: int) -> None: ...
    def set_visibility(self, frame_index: int, layer_index: int, visible: bool): ...
    def set_opacity(...): ...
    def apply_pixel(...): ...
```

### CanvasController (`domain/canvas.py`)

```python
class CanvasController:
    updated = Signal(FramePixels)
    def composite_frame(self, frame_index: int) -> List[RGB]: ...
    def recompute_active_frame(self) -> None: ...
```

### AutomationQueueManager (`domain/automation/queue.py`)

```python
class AutomationQueueManager:
    def enqueue(self, action: AutomationAction) -> None: ...
    def clear(self) -> None: ...
    def apply(self, frame_range: FrameRange, mode: ProcessingMode) -> AutomationResult: ...
```

### PresetRepository (`domain/automation/presets.py`)

```python
class PresetRepository:
    def list(self) -> Dict[str, AutomationPreset]: ...
    def save(self, name: str, preset: AutomationPreset) -> None: ...
    def delete(self, name: str) -> None: ...
```

## Dependency Flow

```
DesignToolsTab (UI)
    -> Managers (Frame/Layer/Canvas/Automation/Palette/Matrix)
        -> PatternState
        -> HistoryManager
        -> Storage backend
```

- Managers expose signals/callbacks; UI only binds data to widgets.
- No manager depends on Qt widgets; all operations are pure Python plus events.

## Testing Benefits

- Managers unit-testable with fake `PatternState`.
- Integration tests instantiate multiple managers sharing state.
- GUI tests reduced to wiring verification.

## Migration Path

1. Introduce `PatternState` and migrate helper logic.
2. Extract frame/layer methods into managers; refactor UI to use new APIs.
3. Add tests as modules are extracted; swap in real implementations gradually.

