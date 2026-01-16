# Automation System: Upload Bridge vs LED Matrix Studio Comparison

## Critical Differences Found

### ❌ **ISSUE 1: Frame Generation Uses Absolute Frame Index Instead of Local Step**

#### LED Matrix Studio (Correct Behavior):
- Uses **frame-relative (local) step**: `step = frame_index - action.start_frame`
- If action starts at frame 5:
  - Frame 5 → step = 0 (first frame of action)
  - Frame 6 → step = 1 (second frame of action)
  - Frame 7 → step = 2 (third frame of action)

#### Upload Bridge Current Implementation:
- Frame generation (`_generate_frames_with_actions`) uses **absolute frame_index**:
  ```python
  absolute_frame_index = starting_frame_index + i
  transformed = _transform_pixels(..., absolute_frame_index)  # ❌ WRONG
  ```
- This means:
  - If appending to frame 5, first generated frame gets step = 5 (should be step = 0)
  - Action transformations start with wrong offset

#### What Should Happen:
```python
# Correct approach for frame generation
for i in range(frame_count):
    # Calculate absolute frame index in pattern
    absolute_frame_index = starting_frame_index + i
    
    # But use LOCAL STEP relative to action start
    for action in actions:
        if action.start_frame <= absolute_frame_index <= (action.end_frame or float('inf')):
            # Use local step, not absolute frame_index
            local_step = absolute_frame_index - action.start_frame
            transformed = _transform_pixels(..., local_step)
```

---

### ❌ **ISSUE 2: Frame Generation Ignores Action Start/End Frames**

#### LED Matrix Studio:
- Actions have `start_frame` and `end_frame` properties
- Action only applies when: `start_frame <= frame_index <= end_frame`
- If frame_index < start_frame: action doesn't apply (returns None/0 step)
- If frame_index > end_frame: action doesn't apply

#### Upload Bridge Current Implementation:
- Frame generation doesn't check `action.start_frame` or `action.end_frame`
- All actions apply to all generated frames regardless of their frame ranges
- Generated frames always start from step 0, even if action.start_frame > 0

#### What Should Happen:
```python
for i in range(frame_count):
    absolute_frame_index = starting_frame_index + i
    frame_pixels = copy(original_pixels)
    
    for action in actions:
        # Check if action is active at this frame
        if not action.is_active_at_frame(absolute_frame_index):
            continue  # Skip this action for this frame
        
        # Use local step (relative to action start)
        local_step = get_action_step(action, absolute_frame_index)
        if local_step is not None:
            transformed = _transform_pixels(frame_pixels, action, width, height, local_step)
```

---

### ❌ **ISSUE 3: Inconsistency Between Render-Time and Frame Generation**

#### Render-Time Automation (CORRECT - matches LMS):
- Location: `layers.py::_apply_layer_automation()`
- Uses `get_action_step(action, frame_index)` → returns local step
- Respects `start_frame` and `end_frame`
- Matches LMS behavior exactly

#### Frame Generation (INCORRECT):
- Location: `design_tools_tab.py::_generate_frames_with_actions()`
- Uses `absolute_frame_index` directly
- Ignores `start_frame` and `end_frame`
- **Does NOT match LMS behavior**

---

## Correct LMS Behavior (Reference)

### Step Calculation (LMS-Style):
```python
def get_action_step(action: LayerAction, frame_index: int) -> Optional[int]:
    """
    LMS-style frame-relative step calculation.
    
    - If frame_index < start_frame: return None (action not active)
    - If frame_index > end_frame: return None (action not active)
    - Otherwise: return frame_index - start_frame (local step)
    """
    if frame_index < action.start_frame:
        return None  # Action hasn't started yet
    if action.end_frame is not None and frame_index > action.end_frame:
        return None  # Action has ended
    return frame_index - action.start_frame  # Local step (0-based)
```

### Action Application (LMS-Style):
```python
# For each frame:
1. Check if action is active: start_frame <= frame_index <= end_frame
2. Calculate local step: step = frame_index - start_frame
3. Apply transformation: transform(pixels, action, step)
```

---

## Example: The Problem in Action

### Scenario:
- Pattern has 3 existing frames (indices 0, 1, 2)
- User adds Scroll action with `start_frame=5, end_frame=10`
- User generates 8 new frames

### What Happens Currently (WRONG):
```python
starting_frame_index = 3  # After existing frames
for i in range(8):
    absolute_frame_index = 3 + i  # Frames 3, 4, 5, 6, 7, 8, 9, 10
    
    # Current code passes absolute_frame_index directly
    transformed = _transform_pixels(..., absolute_frame_index)
    # Frame 5 gets step=5 (should be step=0)
    # Frame 6 gets step=6 (should be step=1)
```

### What Should Happen (CORRECT - LMS-style):
```python
starting_frame_index = 3
for i in range(8):
    absolute_frame_index = 3 + i  # Frames 3, 4, 5, 6, 7, 8, 9, 10
    
    for action in actions:
        # Check if action is active
        if not action.is_active_at_frame(absolute_frame_index):
            continue  # Skip for frames 3, 4 (before start_frame=5)
        
        # Use LOCAL STEP
        local_step = get_action_step(action, absolute_frame_index)
        # Frame 5: local_step = 5 - 5 = 0 ✓
        # Frame 6: local_step = 6 - 5 = 1 ✓
        # Frame 10: local_step = 10 - 5 = 5 ✓
        
        transformed = _transform_pixels(..., local_step)
```

---

## Fix Required

### In `_generate_frames_with_actions()`:

```python
# BEFORE (WRONG):
for i in range(frame_count):
    absolute_frame_index = starting_frame_index + i
    for action in actions:
        transformed = _transform_pixels(..., absolute_frame_index)  # ❌

# AFTER (CORRECT):
for i in range(frame_count):
    absolute_frame_index = starting_frame_index + i
    frame_pixels = copy(original_pixels)
    
    for action in actions:
        # Check if action is active at this frame
        if not action.is_active_at_frame(absolute_frame_index):
            continue
        
        # Use local step (frame-relative)
        local_step = get_action_step(action, absolute_frame_index)
        if local_step is not None:
            transformed = _transform_pixels(frame_pixels, action, width, height, local_step)
            if transformed:
                frame_pixels = transformed
```

### In `_generate_layer_frames_with_actions()`:

Same fix needed - use local step instead of absolute frame_index.

---

## Summary of Issues

| Issue | Current Behavior | LMS Behavior | Status |
|-------|-----------------|--------------|--------|
| Step Calculation | Uses absolute `frame_index` | Uses local `step = frame_index - start_frame` | ❌ Wrong |
| Start Frame Check | Ignored | Action only active if `frame_index >= start_frame` | ❌ Wrong |
| End Frame Check | Ignored | Action only active if `frame_index <= end_frame` | ✅ **FIXED** - Now checks `is_active_at_frame()` |
| Render-Time Mode | ✅ Correct (uses local step) | ✅ Correct | ✅ Matches |
| Frame Generation | ✅ **FIXED** (uses local step) | ✅ Correct | ✅ **FIXED** - Now matches |

---

## Fixes Applied

✅ **Fixed Step Calculation**: Both frame generation and render-time now use unified `get_action_step()` for local step calculation (`step = frame_index - action.start_frame`)

✅ **Fixed Offset Speed**: Scroll/wipe/reveal now use `offset = base_offset * step` instead of `offset = base_offset * frame_index`

✅ **Fixed Action Activation**: Frame generation now checks `action.is_active_at_frame()` before applying actions

✅ **Fixed Layer Window**: Frame generation now checks `is_layer_active()` to respect layer active windows

✅ **Added Baked Frame Protection**: Frames generated from automation are marked with `is_baked=True` to prevent re-automation

✅ **Fixed Frame Count Calculation**: Frame count is now UI-only suggestion (not semantic enforcement), respecting `action.end_frame` when present

✅ **Fixed Black Transparency**: All transform functions use black `(0,0,0)` for out-of-bounds pixels (no wrap/modulo)

✅ **Removed Non-LMS Actions**: Brightness and fade removed from automation priority table

---

## Status

✅ **All critical issues fixed!** Frame generation and render-time automation now match LMS behavior for:

- Step calculation (local step, not absolute frame_index)
- Action activation (respects start_frame/end_frame)
- Offset speed (uses step, not frame_index)
- Layer windows (respects is_layer_active)
- Baked frame protection (prevents re-automation)
- Frame count (UI suggestion, not enforcement)
- **Unified pipeline model** ✅ **FIXED**: All actions are applied in a single unified pipeline, sorted by ACTION_PRIORITY. Rotate, mirror, and flip operate on the result of earlier actions in the same frame, not on base pixels separately.

**Implementation**: Transform pipeline is unified:
1. All actions sorted by ACTION_PRIORITY (fixed LMS order)
2. Actions applied sequentially in one pipeline
3. Rotate/mirror/flip participate in the same pipeline and operate on transformed pixels from earlier actions
4. No split-phase processing - continuous pipeline per frame

This ensures pixel-exact LMS parity.