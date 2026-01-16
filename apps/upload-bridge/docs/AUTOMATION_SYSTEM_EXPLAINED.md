# Automation System Explained

## Overview

The Upload Bridge automation system creates animations by applying transformations to frames. Both modes use the **same LMS-correct semantic model** (unified step calculation):

1. **Frame Generation Mode** (Baked Frames) - Creates new frames by applying actions progressively, using LMS-correct step calculation
2. **Render-Time Mode** (Live Automation) - Applies actions at render time without modifying stored pixels (non-destructive), using LMS-correct step calculation

**Key Principle**: Both modes use `step = frame_index - action.start_frame` (local step calculation), ensuring pixel-exact LMS parity.

---

## How Automation Actions Are Applied

### 1. Action Structure

Each automation action (`LayerAction` or `DesignAction`) contains:

```python
- type: "scroll", "rotate", "wipe", "mirror", etc.
- start_frame: Frame index where action starts
- end_frame: Frame index where action ends (None = continues forever)
- params: Action-specific parameters (direction, offset, etc.)
- order: Execution order (lower values applied first)
```

### 2. Stateless Frame-Index Driven Model

**Key Principle**: All transformations are **stateless** and **frame-index driven**.

- Each frame calculates its transformation independently from base pixels
- No state accumulation between frames
- Same base pixels + frame_index always = same result

**Examples**:
- **Scroll**: Frame 0 = 0px offset, Frame 1 = 1px offset, Frame 2 = 2px offset
- **Rotate**: Frame 0 = 0°, Frame 1 = 90°, Frame 2 = 180°, Frame 3 = 270° (uses step % 4)
- **Wipe**: Frame 0 = 0px wipe position, Frame 1 = 1px, Frame 2 = 2px

**Note**: Rotate/mirror/flip use base-frame time logic (no accumulation across frames), but they still operate on the result of earlier actions in the same frame pipeline.

### 3. Unified Pipeline Model (LMS Requirement)

**Critical LMS Rule**: All actions are applied in a **single unified pipeline**, sorted by ACTION_PRIORITY. There is no split-phase processing.

**Key Principles**:
- All actions participate in the same pipeline in priority order
- Rotate/mirror/flip operate on the result of earlier actions in the same frame
- They do NOT accumulate across frames (use base-frame time logic with `step`)
- They DO participate in the same-frame pipeline and operate on transformed pixels

**How It Works**:
1. Actions are sorted by ACTION_PRIORITY (fixed LMS order)
2. All actions are applied sequentially to the pipeline result
3. Each action operates on the output of previous actions in the same frame

**Example**: If you have scroll (priority 10) + rotate (priority 20):
- Scroll operates on base pixels → produces scrolled pixels
- Rotate operates on scrolled pixels (not base pixels) → produces rotated + scrolled result
- Pipeline order: `base_pixels → scroll(base_pixels) → rotate(scrolled_pixels)`

### 4. Action Priority System

Actions are applied in **fixed priority order** (not insertion order):

```python
ACTION_PRIORITY = {
    'scroll': 10,
    'rotate': 20,
    'mirror': 30,
    'flip': 30,
    'bounce': 40,
    'wipe': 50,
    'reveal': 60,
    'radial': 70,
    'colour_cycle': 80,
    'invert': 90,
}
```

**Note**: `brightness` and `fade` are NOT part of LMS automation priority. They may exist as post-processing effects but are not automation actions.

This ensures consistent behavior: **scroll → rotate → mirror** always produces the same result.

---

## How the System Maps Actions to Frames

### Frame Mapping Process

1. **Action Activation Check**
   ```python
   def is_active_at_frame(frame_index):
       return (start_frame <= frame_index <= end_frame) and not finalized
   ```

2. **Step Calculation**
   ```python
   def get_step(frame_index):
       # Returns local step: frame_index - start_frame
       # Frame 0 of action = step 0
       # Frame 1 of action = step 1
       return frame_index - start_frame
   ```

3. **Progressive Transformation**
   ```python
   # Each frame uses ORIGINAL source pixels
   frame_pixels = copy(original_pixels)
   
   # Apply transformations with progressive offset
   for action in sorted_actions:
       step = action.get_step(frame_index)
       frame_pixels = transform(frame_pixels, action, step)
   ```

### Example: Scroll Action Mapping

**Source Frame**: 32x32 matrix with a red dot at (5, 5)

**Action**: Scroll Right, start_frame=0, offset=1 pixel per frame

| Frame | Step | Transformation | Result |
|-------|------|----------------|--------|
| 0 | 0 | offset = 0 | Red dot at (5, 5) |
| 1 | 1 | offset = 1 | Red dot at (6, 5) |
| 2 | 2 | offset = 2 | Red dot at (7, 5) |
| ... | ... | ... | ... |
| 26 | 26 | offset = 26 | Red dot at (31, 5) |

**Each frame starts from the original pixels**, not the previous frame's pixels.

---

## How Animations Are Created with New Frames

### Frame Generation Flow

#### Step 1: Calculate Required Frame Count

```python
def calculate_frame_count(actions, width, height):
    max_frames = 10  # Default minimum
    
    for action in actions:
        if action.type == "scroll":
            if direction in ["left", "right"]:
                frames_needed = width  # One frame per pixel
            else:
                frames_needed = height
        elif action.type == "rotate":
            frames_needed = 4  # 0°, 90°, 180°, 270°
        elif action.type in ["wipe", "reveal"]:
            frames_needed = width or height  # Depends on direction
        
        max_frames = max(max_frames, frames_needed * repeat)
    
    return max_frames
```

#### Step 2: Generate Frames with Progressive Transformations

```python
def _generate_frames_with_actions(actions, source_frame):
    original_pixels = copy(source_frame.pixels)
    frame_count = calculate_frame_count(actions)
    new_frames = []
    
    for i in range(frame_count):
        # Start with ORIGINAL pixels for each frame
        frame_pixels = copy(original_pixels)
        
        # Apply all actions with progressive frame_index
        for action in actions:
            step = i  # Progressive step
            frame_pixels = _transform_pixels(
                frame_pixels, 
                action, 
                width, 
                height, 
                step
            )
        
        # Create new frame with transformed pixels
        new_frame = Frame(
            pixels=frame_pixels,
            duration_ms=source_frame.duration_ms
        )
        new_frames.append(new_frame)
    
    # Append new frames to pattern
    pattern.frames.extend(new_frames)
```

#### Step 3: Transformation Application

```python
def _transform_pixels(pixels, action, width, height, frame_index):
    action_type = action.type.lower()
    params = action.params or {}
    
    if action_type == "scroll":
        direction = params.get("direction", "Right")
        offset = frame_index  # Progressive offset
        
        if direction == "Left":
            return scroll_left(pixels, width, height, offset)
        elif direction == "Right":
            return scroll_right(pixels, width, height, offset)
        # ... other directions
    
    elif action_type == "rotate":
        angle = (frame_index % 4) * 90  # 0°, 90°, 180°, 270°
        return rotate_90(pixels, width, height, angle)
    
    elif action_type == "wipe":
        direction = params.get("mode", "Left to Right")
        position = frame_index  # Progressive wipe position
        return wipe_effect(pixels, width, height, direction, position)
    
    # ... other action types
```

---

## Two Automation Modes

### Mode 1: Frame Generation (Baked Frames)

**Location**: `_generate_frames_with_actions()` in `design_tools_tab.py`

**Process**:
1. Takes source frame(s)
2. Calculates required frame count
3. Creates new frames by applying actions progressively
4. **Modifies stored pixels** - frames are "baked"

**Use Case**: 
- Create complete animation sequences
- Export to formats that don't support runtime automation
- Generate preview frames

**Example**:
```python
# User clicks "Generate Animation"
# System creates 32 frames for a scroll action
# Each frame has different pixels stored
```

### Mode 2: Render-Time Automation (Live)

**Location**: `_apply_layer_automation()` in `layers.py`

**Process**:
1. Stores base pixels in layer frames
2. Stores automation actions separately
3. At render time, applies actions to base pixels
4. **Does NOT modify stored pixels** - non-destructive

**Use Case**:
- Layer-based animations
- Preview without committing changes
- Adjustable animation parameters

**Example**:
```python
# Layer has base pixels + scroll action
# During preview/export:
#   Frame 0: base_pixels + scroll(offset=0)
#   Frame 1: base_pixels + scroll(offset=1)
#   Frame 2: base_pixels + scroll(offset=2)
# Base pixels never change
```

---

## Complete Example: Creating a Scrolling Text Animation

### Scenario
- Matrix: 32x32
- Source: Text "HELLO" at position (5, 10)
- Action: Scroll Right, 1 pixel per frame

### Step-by-Step Process

1. **Calculate Frame Count**
   ```
   Scroll Right → frames = width = 32 frames
   ```

2. **Generate Frames**
   ```python
   original_pixels = get_source_frame_pixels()
   
   for frame_index in range(32):
       frame_pixels = copy(original_pixels)
       
       # Apply scroll with progressive offset
       offset = frame_index
       frame_pixels = scroll_right(frame_pixels, width, height, offset)
       
       new_frame = Frame(pixels=frame_pixels, duration_ms=100)
       pattern.frames.append(new_frame)
   ```

3. **Result**
   - Frame 0: "HELLO" at (5, 10)
   - Frame 1: "HELLO" at (6, 10)
   - Frame 2: "HELLO" at (7, 10)
   - ...
   - Frame 26: "HELLO" at (31, 10) [last visible position]

### Visual Timeline

```
Frame:  0    1    2    3    4    ...  26   27   28   29   30   31
Offset: 0px  1px  2px  3px  4px  ...  26px 27px 28px 29px 30px 31px
        │    │    │    │    │         │    │    │    │    │    │
        ▼    ▼    ▼    ▼    ▼         ▼    ▼    ▼    ▼    ▼    ▼
       HELLO scrolls across the screen pixel by pixel
```

---

## Key Implementation Details

### 1. Progressive Transformation Formula

For time-based actions (scroll, rotate, wipe):
```python
effective_value = base_value * frame_index

# Scroll Right, offset=1 per frame:
#   Frame 0: scroll_by = 0
#   Frame 1: scroll_by = 1
#   Frame 2: scroll_by = 2
```

### 2. Action Chaining

Multiple actions are applied in sequence:
```python
# Actions: [Scroll Right, Rotate 90°]

for frame_index in range(frames):
    pixels = original_pixels
    
    # Apply scroll first (priority 1)
    pixels = scroll_right(pixels, offset=frame_index)
    
    # Then apply rotate (priority 2)
    pixels = rotate_90(pixels, angle=(frame_index % 4) * 90)
    
    new_frame.pixels = pixels
```

### 3. Action Parameters

Actions support parameters:
```python
{
    "direction": "Right",      # Scroll/Wipe direction
    "offset": 1,               # Pixels per frame
    "repeat": 2,               # Repeat action N times
    "gap_ms": 50,              # Delay between frames (ms)
    "mode": "Left to Right",   # Wipe/Reveal mode
}
```

---

## Summary

1. **Actions are stateless** - Each frame calculates from original pixels
2. **Frame-index driven** - Progressive transformations use frame_index as multiplier
3. **Priority-based ordering** - Actions apply in fixed priority order
4. **Two modes** - Baked frames (generated) or live (render-time)
5. **Automatic frame calculation** - System determines needed frames based on action type and parameters

The system ensures **deterministic, predictable animations** where the same input always produces the same output.

---

## ⚠️ Known Issues vs LED Matrix Studio

**See [AUTOMATION_LMS_COMPARISON.md](AUTOMATION_LMS_COMPARISON.md) for detailed analysis**

### Critical Differences:

1. **Frame Generation Uses Absolute Frame Index**
   - **Current**: Uses absolute `frame_index` directly
   - **Should be**: Uses local step `frame_index - action.start_frame`
   - **Impact**: Animations start with wrong offsets when appending frames

2. **Ignores Action Start/End Frames**
   - **Current**: Actions apply to all frames regardless of `start_frame`/`end_frame`
   - **Should be**: Actions only apply when `start_frame <= frame_index <= end_frame`
   - **Impact**: Actions affect frames outside their intended range

3. **Inconsistency Between Modes**
   - **Render-time mode**: ✅ Correctly uses local steps (matches LMS)
   - **Frame generation mode**: ❌ Uses absolute frame_index (doesn't match LMS)
   - **Impact**: Same actions produce different results in different modes

### Render-Time Mode (Correct):
- Uses `get_action_step(action, frame_index)` → returns local step
- Respects `start_frame` and `end_frame`
- Matches LED Matrix Studio behavior exactly

### Frame Generation Mode (Needs Fix):
- Uses `absolute_frame_index` directly instead of local step
- Ignores `start_frame` and `end_frame`
- Does NOT match LED Matrix Studio behavior
