# Layer Animation System - Clarifications

This document addresses ambiguities and clarifies the layer animation system implementation.

## 1. Pixel Storage Model

**Clarification**: Each `LayerFrame` stores its own pixel array per frame. Pixels are stored per frame (not shared across frames), but animations transform them at render time without modifying the stored pixels.

**Why this matters**:
- Base pixels are preserved (non-destructive animations)
- Same base pixels can be transformed differently per frame
- Efficient: transform only when rendering, not stored

**Implementation**:
- `LayerFrame.pixels` is a list stored per frame
- `_apply_layer_animation()` creates a transformed copy
- Original `LayerFrame.pixels` remains unchanged

## 2. Keyframe Normalization

**Clarification**: Animation keyframes use **normalized frame indices** (0-100), not absolute pattern frame numbers.

**How it works**:
- Keyframe `frame_index=0` = start of animation
- Keyframe `frame_index=100` = end of animation
- The animation system maps actual frame range (start_frame to end_frame) to normalized 0-100 space
- Interpolation happens in normalized space, then mapped back to actual frames

**Example**:
```
Pattern: 10 frames (0-9)
Animation: spans frames 0-9 (all frames)
Keyframes:
  - frame_index=0 (normalized) → pattern frame 0
  - frame_index=100 (normalized) → pattern frame 9
  - frame_index=50 (normalized) → pattern frame 4.5 (interpolated)
```

**Why normalized**:
- Animations work consistently regardless of pattern length
- Keyframes are reusable across different pattern sizes
- Interpolation is frame-count independent

## 3. Visibility Handling

**Clarification**: Visibility is checked **before** animation application in the render flow.

**Render Flow**:
1. Check layer visibility (skip if invisible) ← **Visibility check here**
2. Get base pixels from LayerFrame
3. Apply animation transformations
4. Apply mask
5. Blend with composite

**Implementation**:
- `get_composite_pixels()` calls `track.get_effective_visibility(frame_index)` first
- Invisible layers are skipped entirely (no animation computation)
- Per-frame visibility overrides are respected

## 4. Single Animation Per Layer

**Clarification**: Each layer track can have **one animation** at a time.

**Current Implementation**:
- `LayerAnimationManager._animations` is a `Dict[int, LayerAnimation]` (one per layer)
- Setting a new animation replaces any existing animation
- `get_animation(track_index)` returns a single animation or None

**Future Consideration**:
- Multiple animations per layer (stacking) could be added
- Would require animation composition/merging logic
- Currently not implemented

## 5. Scroll Wrapping Behavior

**Clarification**: Scroll animations **wrap pixels at edges** (circular scroll).

**Behavior**:
- Pixels that scroll off one edge appear on the opposite edge
- Uses modulo arithmetic: `src_x = (x - distance_x) % width`
- Creates seamless looping effect
- Original pixels are not modified (creates new array)

**Example**:
```
Scroll right by 1 pixel:
  [A][B][C][D] → [D][A][B][C]
  (D wraps from right to left)
```

## 6. Animation Frame Range

**Clarification**: Animations respect `start_frame` and `end_frame` parameters.

**Behavior**:
- Animation only affects frames within its range
- Frames outside range return `None` from `get_property_at_frame()`
- `end_frame=None` means animation spans to end of pattern
- Frame range is in **absolute pattern frame numbers**, not normalized

**Example**:
```
Pattern: 20 frames (0-19)
Animation: start_frame=5, end_frame=14
  - Frames 0-4: No animation (returns None)
  - Frames 5-14: Animation active
  - Frames 15-19: No animation (returns None)
```

## Summary

| Concept | Clarification |
|---------|---------------|
| Pixel Storage | Per-frame storage, animations transform at render time (non-destructive) |
| Keyframes | Normalized 0-100, not absolute frame numbers |
| Visibility | Checked before animation application |
| Animations per Layer | One animation per layer track |
| Scroll Wrapping | Circular wrap at edges |
| Frame Range | Absolute frame numbers, keyframes normalized |

All clarifications are now reflected in:
- Code docstrings
- Documentation files
- Implementation comments
