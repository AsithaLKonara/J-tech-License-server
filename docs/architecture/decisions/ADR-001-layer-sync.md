# ADR-001: LayerManager to PatternState Sync (One-way)

**Status**: Accepted  
**Date**: 2025-01-XX  
**Deciders**: Architecture Team

## Context

The Design Tools Tab supports multi-layer editing per frame, where users can create multiple layers, adjust opacity, toggle visibility, and composite them together. A key architectural question arose: should the synchronization between layers and frame pixels be bidirectional or one-way?

**Options considered**:
1. **Bidirectional sync**: Frame pixels and layers stay in sync in both directions
2. **One-way sync (layers → frame)**: Layers are authoritative for editing, frames are authoritative for persistence
3. **One-way sync (frame → layers)**: Frames are authoritative, layers are derived

## Decision

We chose **one-way synchronization from layers to frames**:
- **LayerManager** is the authoritative source for editing operations
- **PatternState.frame.pixels** is the authoritative source for persistence
- Layers sync to frames via `LayerManager.sync_frame_from_layers()`
- Frame pixels are updated from layer composite, not the reverse

**Rationale**:
- Layers provide editing flexibility (visibility, opacity, ordering)
- Frame pixels provide a simple, flat representation for persistence
- One-way sync prevents conflicts and maintains clear ownership
- Export/import systems work with frame pixels, not layers
- Undo/redo operates on frame state, which includes all layer changes

## Consequences

### Positive
- **Clear ownership**: No ambiguity about which component owns the data
- **Simple persistence**: Frame pixels are straightforward to serialize
- **Editing flexibility**: Layers can be modified without affecting persistence until sync
- **Undo/redo clarity**: History tracks frame state, which is the final result
- **Export compatibility**: Export formats work with frame pixels directly

### Negative
- **Sync overhead**: Must explicitly call `sync_frame_from_layers()` after layer changes
- **Potential inconsistency**: Layers and frames can be temporarily out of sync
- **No frame-to-layer editing**: Cannot directly edit frame pixels and have it reflect in layers
- **Layer reconstruction**: Loading a pattern requires reconstructing layers from frame pixels

### Mitigations
- `sync_frame_from_layers()` is called automatically after pixel operations
- Layer operations are designed to be atomic (complete before sync)
- Pattern loading creates a default layer with frame pixels
- Clear documentation of sync points in workflows

## Implementation Details

```python
# LayerManager.sync_frame_from_layers()
def sync_frame_from_layers(frame_index: int) -> None:
    # Get composite of all visible layers
    composite = self.get_composite_pixels(frame_index)
    # Update frame pixels (one-way: layers → frame)
    frame = self._pattern_state.pattern().frames[frame_index]
    frame.pixels = composite
```

## References

- `domain/layers.py` - LayerManager implementation
- `domain/pattern_state.py` - PatternState implementation
- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Source of Truth Clarification section

