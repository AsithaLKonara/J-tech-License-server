# Layer Animation Integration

## Overview

The layer animation system has been integrated with the compositing system, allowing multiple layers to animate independently and overlay correctly during playback.

## How It Works

### Architecture

1. **LayerAnimationManager**: Manages animations per layer track
2. **LayerManager Integration**: `get_composite_pixels()` applies animations before compositing
3. **Animation Types**: Scroll, Fade, Pulse, Rotate, Scale, Custom

### Animation Flow

```
Frame Playback
    ↓
get_composite_pixels(frame_index)
    ↓
For each LayerTrack (sorted by z_index):
    1. Check visibility (skip if invisible)
    2. Get base pixels from LayerFrame
    3. Apply animation transformations (_apply_layer_animation)
       - Scroll: Transform pixel positions (wraps at edges)
       - Fade/Pulse: Adjust opacity
       - Rotate/Scale: Transform pixels (if implemented)
    4. Apply mask if present
    5. Blend with composite using opacity and blend mode
    ↓
Return composite pixels
```

## Usage Example

### Creating Scroll Animations

```python
from domain.layer_animation import create_scroll_animation

# Create scroll right animation for layer 1
scroll_right = create_scroll_animation(
    direction="right",
    speed=1.0,
    start_frame=0,
    end_frame=None  # None = all frames
)

# Create scroll up animation for layer 2
scroll_up = create_scroll_animation(
    direction="up",
    speed=1.0,
    start_frame=0,
    end_frame=None
)

# Apply animations to layers
layer_manager.set_layer_animation(0, scroll_right)  # Layer 1
layer_manager.set_layer_animation(1, scroll_up)      # Layer 2
```

### During Playback

When playing the animation:
1. **Frame 0**: Both layers at starting positions
2. **Frame 1**: Layer 1 scrolls right, Layer 2 scrolls up
3. **Frame 2**: Both continue scrolling independently
4. **Composite**: Both layers overlay correctly on the matrix

## Answer to User's Question

**Q: If I create Layer 1 with scroll right animation and Layer 2 with scroll up animation, will both play simultaneously overlaying on the matrix?**

**A: YES!** ✅

With the integrated animation system:
- Layer 1 scrolls right independently
- Layer 2 scrolls up independently
- Both layers composite together during playback
- Each layer maintains its own animation state
- Animations are applied per-frame during compositing

## Implementation Details

### Keyframe Normalization

**Important**: Animation keyframes use **normalized frame indices** (0-100), not absolute pattern frame numbers.

- Keyframe `frame_index=0` means "start of animation"
- Keyframe `frame_index=100` means "end of animation"
- The animation system maps the actual frame range (start_frame to end_frame) to this normalized 0-100 space
- This allows animations to work consistently regardless of pattern length

**Example**:
- Pattern has 10 frames (0-9)
- Animation spans frames 0-9 (all frames)
- Keyframe at `frame_index=0` = pattern frame 0
- Keyframe at `frame_index=100` = pattern frame 9
- Keyframe at `frame_index=50` = pattern frame 4.5 (interpolated)

### Scroll Animation

- **Direction**: "right", "left", "up", "down"
- **Offset**: Normalized value (1.0 = full width/height)
- **Speed**: Multiplier for animation speed
- **Loop**: Animations loop by default
- **Keyframes**: Uses normalized indices (0 = start, 100 = end)

### Pixel Transformation

The `_scroll_pixels()` method:
- Transforms pixel positions based on offset
- **Wraps pixels at edges** (circular scroll - pixels that go off one edge appear on the opposite edge)
- Supports both positive and negative offsets
- Applied per-frame during compositing
- **Does not modify stored pixels** - creates transformed copy

### Pixel Storage Model

**Important**: Each `LayerFrame` stores its own pixel array per frame. Pixels are stored per frame (not shared across frames), but animations transform them at render time without modifying the stored pixels. This allows:
- Same base pixels to be transformed differently per frame
- Animations to be non-destructive (original pixels preserved)
- Efficient rendering (transform only when needed)

### Compositing Order

1. Layers sorted by z_index (bottom to top)
2. For each layer:
   - **Check visibility** (skip if invisible)
   - Get base pixels from LayerFrame
   - Apply animation transformation (non-destructive)
   - Apply mask
   - Blend with composite
3. Return final composite

## Animation Limitations

- **One animation per layer**: Each layer track can have at most one animation
- **Scroll wrapping**: Scroll animations wrap pixels at edges (circular scroll)
- **Keyframe normalization**: Keyframes use normalized indices (0-100), not absolute frame numbers

## Current Status

✅ **Implemented**:
- Scroll animation (right, left, up, down) with wrapping
- Animation keyframe interpolation (normalized 0-100)
- Per-layer independent animations (one per layer)
- Compositing with animations
- Visibility checking before animation application

⚠️ **Placeholder** (not yet implemented):
- Rotate animation pixel transformation
- Scale animation pixel transformation
- Custom animation functions
- Multiple animations per layer (stacking)

## Testing

To test multi-layer animations:

1. Create Layer 1
2. Add scroll right animation to Layer 1
3. Create Layer 2 (under Layer 1)
4. Add scroll up animation to Layer 2
5. Play animation
6. Verify both layers animate independently and overlay correctly

## Future Enhancements

1. **UI Integration**: Add animation controls in layer panel
2. **Animation Presets**: Pre-configured animations
3. **Keyframe Editor**: Visual keyframe editing
4. **Animation Preview**: Preview animations before applying
5. **Animation Export**: Export animations to patterns
