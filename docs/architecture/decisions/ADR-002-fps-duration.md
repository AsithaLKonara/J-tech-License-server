# ADR-002: FPS vs Frame Duration Coexistence

**Status**: Accepted  
**Date**: 2025-01-XX  
**Deciders**: Architecture Team

## Context

The Design Tools Tab needs to support both preview playback and export functionality. Preview playback requires smooth, consistent timing for user experience, while export needs to support format-specific timing requirements (e.g., per-frame durations in LEDS format).

**Options considered**:
1. **FPS only**: Use FPS for both preview and export (simpler, but loses per-frame timing)
2. **Duration only**: Use per-frame duration for both (more complex preview, but accurate export)
3. **Coexistence**: Use FPS for preview, duration_ms for export (separate concerns)

## Decision

We chose **coexistence of FPS and frame duration**:
- **FPS control** sets global playback speed for preview (overrides per-frame duration during preview)
- **Frame duration** (duration_ms) is stored per-frame for export compatibility
- During preview: FPS determines timing (all frames play at same rate)
- During export: Frame duration_ms is used if the export format supports per-frame timing

**Rationale**:
- Preview and export serve different purposes with different requirements
- FPS provides smooth, predictable preview experience
- Per-frame duration supports format-specific export requirements
- Both values can coexist without conflict (used in different contexts)
- User can adjust FPS for preview without affecting export timing

## Consequences

### Positive
- **Flexible preview**: User can adjust playback speed independently of export timing
- **Export accuracy**: Supports formats that require per-frame timing (LEDS, etc.)
- **User experience**: Smooth preview playback with consistent frame rate
- **Format compatibility**: Export can use per-frame durations when supported
- **Clear separation**: Preview and export concerns are separated

### Negative
- **Conceptual complexity**: Two timing systems can be confusing
- **Potential inconsistency**: Preview timing may not match export timing
- **UI complexity**: Need to display and manage both FPS and duration controls
- **Documentation burden**: Must explain when each is used

### Mitigations
- Clear UI labels distinguishing preview FPS from frame duration
- Documentation explains the difference and when each is used
- Export formats that don't support per-frame duration use FPS or average duration
- Preview can optionally respect frame durations (future enhancement)

## Implementation Details

```python
# Preview playback uses FPS
fps = self.fps_control.value()  # e.g., 10 FPS
frame_interval_ms = 1000 / fps  # 100ms per frame

# Export uses frame duration_ms
for frame in pattern.frames:
    duration = frame.duration_ms  # Per-frame duration
    # Use in export format if supported
```

## References

- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Playback Timing Clarification section
- `domain/frames.py` - FrameManager and Frame.duration_ms
- `ui/tabs/design_tools_tab.py` - FPS control and preview playback

