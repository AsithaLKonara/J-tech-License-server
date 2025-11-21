# ADR-004: PatternInstructionSequence Separation

**Status**: Accepted  
**Date**: 2025-01-XX  
**Deciders**: Architecture Team

## Context

The LMS Automation feature needs to store and manage a sequence of pattern instructions. We needed to decide whether to integrate this into AutomationQueueManager or create a separate data structure.

**Options considered**:
1. **Integrate into AutomationQueueManager**: Add instruction sequence as part of queue manager
2. **Separate data structure**: Create PatternInstructionSequence as standalone class
3. **Use list directly**: Just use Python list with no wrapper class

## Decision

We chose **PatternInstructionSequence as a separate data structure**:
- PatternInstructionSequence is a data structure (not a manager)
- AutomationQueueManager manages DesignAction objects (different from instructions)
- PatternInstructionSequence is used by LMS Automation tab
- Stored as `_lms_sequence` instance variable in DesignToolsTab

**Rationale**:
- **Separation of concerns**: Instructions are data, not actions
- **Different purposes**: AutomationQueueManager handles UI automation actions, PatternInstructionSequence handles LMS export instructions
- **Reusability**: PatternInstructionSequence can be used independently
- **Clarity**: Clear distinction between automation actions and LMS instructions
- **Serialization**: PatternInstructionSequence has specific serialization needs (to_list/from_list)

## Consequences

### Positive
- **Clear separation**: Automation actions vs LMS instructions are distinct
- **Reusability**: PatternInstructionSequence can be used in other contexts
- **Focused responsibility**: Each component has a single, clear purpose
- **Serialization clarity**: PatternInstructionSequence handles its own serialization
- **Testability**: Can test instruction sequence logic independently

### Negative
- **Two similar concepts**: AutomationQueueManager and PatternInstructionSequence may seem redundant
- **Potential confusion**: Developers may not understand when to use which
- **Code duplication**: Some similar operations (add, remove, move) in both
- **Documentation burden**: Must explain the difference clearly

### Mitigations
- Clear naming: "Queue" for actions, "Sequence" for instructions
- Documentation explains the distinction
- Different use cases: Queue for UI automation, Sequence for LMS export
- PatternInstructionSequence is simpler (just data), AutomationQueueManager is more complex (signals, UI integration)

## Implementation Details

```python
# PatternInstructionSequence (data structure)
class PatternInstructionSequence:
    def add(self, instruction: PatternInstruction) -> None:
        # Add instruction to sequence
    
    def to_list(self) -> List[Dict]:
        # Serialize for export

# AutomationQueueManager (manager with signals)
class AutomationQueueManager(QObject):
    queue_changed = Signal(list)
    
    def enqueue(self, action: DesignAction) -> None:
        # Add action to queue
        self.queue_changed.emit(list(self._actions))
```

## References

- `core/automation/instructions.py` - PatternInstructionSequence implementation
- `domain/automation/queue.py` - AutomationQueueManager implementation
- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - PatternInstructionSequence description

