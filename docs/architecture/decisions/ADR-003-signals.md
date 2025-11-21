# ADR-003: Signal-based Communication

**Status**: Accepted  
**Date**: 2025-01-XX  
**Deciders**: Architecture Team

## Context

The Design Tools Tab has multiple managers (FrameManager, LayerManager, AutomationQueueManager, etc.) that need to communicate with the UI (DesignToolsTab) and with each other. We needed to choose a communication mechanism that supports loose coupling and event-driven updates.

**Options considered**:
1. **Direct method calls**: Managers call UI methods directly (tight coupling)
2. **Observer pattern**: Custom observer/notifier implementation
3. **Qt signals/slots**: Qt's built-in signal-slot mechanism
4. **Event bus**: Central event bus for all communication

## Decision

We chose **Qt signals/slots for inter-component communication**:
- Managers inherit from `QObject` and emit signals
- UI components connect to manager signals
- Signals carry typed parameters (int, tuple, etc.)
- Signal emission is asynchronous and decoupled

**Rationale**:
- Qt signals are native to the framework (PyQt/PySide)
- Loose coupling: managers don't need to know about UI
- Type-safe: signals have typed signatures
- Multiple listeners: multiple components can listen to same signal
- Thread-safe: signals work across threads if needed
- Well-documented: Qt signal/slot is a well-understood pattern

## Consequences

### Positive
- **Loose coupling**: Managers don't depend on UI components
- **Multiple listeners**: UI, timeline, canvas can all listen to same signal
- **Type safety**: Signal signatures enforce parameter types
- **Asynchronous**: Signal emission doesn't block
- **Standard pattern**: Qt developers are familiar with signals/slots
- **Testability**: Easy to mock signal connections in tests

### Negative
- **Qt dependency**: Requires QObject inheritance (not pure Python)
- **Signal overhead**: Slight performance overhead vs direct calls
- **Debugging complexity**: Signal connections can be harder to trace
- **Documentation burden**: Must document all signals and their listeners

### Mitigations
- Clear signal naming conventions (e.g., `frame_index_changed`, `layers_changed`)
- Comprehensive signal documentation with examples
- Signal connection verification in tests
- Use of Qt's signal debugging tools when needed

## Implementation Details

```python
# Manager emits signal
class FrameManager(QObject):
    frame_index_changed = Signal(int)
    
    def select(self, index: int):
        self._current_index = index
        self.frame_index_changed.emit(index)  # Emit signal

# UI connects to signal
class DesignToolsTab(QWidget):
    def __init__(self):
        self.frame_manager.frame_index_changed.connect(
            self._on_manager_frame_selected
        )
    
    def _on_manager_frame_selected(self, frame_index: int):
        # Handle frame selection change
        self._load_current_frame_into_canvas()
```

## References

- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Signal/Event Connections section
- `domain/frames.py` - FrameManager signals
- `domain/layers.py` - LayerManager signals
- Qt Documentation: Signals and Slots

