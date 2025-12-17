# Layer Track System - New Architecture

## Overview

The layer system has been refactored from a per-frame architecture to a **layer track architecture**, similar to video editing software like Adobe After Effects or Premiere Pro. This provides better organization, efficiency, and enables independent layer animations.

## Architecture

### Old Architecture (Per-Frame Layers)
```
Pattern
├── Frame 0
│   ├── Layer 0
│   └── Layer 1
├── Frame 1
│   ├── Layer 0 (separate instance)
│   └── Layer 1 (separate instance)
└── Frame 2
    ├── Layer 0 (separate instance)
    └── Layer 1 (separate instance)
```

**Problems:**
- Background layer must be manually copied to each frame
- No layer continuity across frames
- Difficult to animate layers independently
- Manual synchronization required

### New Architecture (Layer Tracks)
```
Pattern
├── LayerTrack 0: "Background"
│   ├── Frame 0: LayerFrame
│   ├── Frame 1: LayerFrame
│   └── Frame 2: LayerFrame
└── LayerTrack 1: "Foreground"
    ├── Frame 0: LayerFrame
    ├── Frame 1: LayerFrame
    └── Frame 2: LayerFrame
```

**Benefits:**
- Layers span across all frames automatically
- Independent animations per layer
- Efficient editing (edit once, affects all frames)
- Better organization
- Industry-standard workflow

## Core Classes

### LayerTrack
Represents a layer that spans across multiple frames.

**Properties:**
- `name: str` - Layer name
- `frames: Dict[int, LayerFrame]` - Frame data for this layer
- `visible: bool` - Global visibility (can be overridden per-frame)
- `opacity: float` - Global opacity (can be overridden per-frame)
- `blend_mode: str` - Blend mode ("normal", "add", "multiply", "screen")
- `locked: bool` - Lock state
- `group_id: Optional[str]` - Group membership
- `z_index: int` - Rendering order (lower = bottom, higher = top)

**Methods:**
- `get_frame(frame_index)` - Get frame data
- `set_frame(frame_index, layer_frame)` - Set frame data
- `get_or_create_frame(frame_index, width, height)` - Get or create frame
- `get_effective_visibility(frame_index)` - Get visibility (with overrides)
- `get_effective_opacity(frame_index)` - Get opacity (with overrides)

### LayerFrame
Represents frame data within a layer track.

**Properties:**
- `pixels: List[Color]` - Pixel data for this frame
- `visible: Optional[bool]` - Frame-specific visibility (None = use layer default)
- `opacity: Optional[float]` - Frame-specific opacity (None = use layer default)
- `mask: Optional[List[float]]` - Per-pixel mask (0.0-1.0)

## Usage

### Creating Layer Tracks

```python
from domain.layers import LayerManager, LayerTrack, LayerFrame
from domain.pattern_state import PatternState

# Initialize
state = PatternState()
state.set_pattern(pattern)
layer_manager = LayerManager(state)

# Add a new layer track
track_index = layer_manager.add_layer_track("Background")

# Get layer track
track = layer_manager.get_layer_track(track_index)

# Add frame data
frame = LayerFrame(pixels=[(0, 0, 255)] * 256)  # Blue
track.set_frame(0, frame)
```

### Painting to Layers

```python
# Paint to layer track at specific frame
layer_manager.apply_pixel(
    frame_index=0,
    x=5,
    y=10,
    color=(255, 0, 0),
    width=16,
    height=16,
    layer_index=0  # Layer track index
)
```

### Compositing

```python
# Get composite pixels for a frame
composite = layer_manager.get_composite_pixels(frame_index=0)

# Composite automatically:
# 1. Gets all layer tracks
# 2. Filters visible layers
# 3. Sorts by z_index
# 4. Blends bottom-to-top with blend modes
```

### Per-Frame Property Overrides

```python
# Set global visibility
track.visible = True

# Override for specific frame
frame = track.get_frame(0)
frame.visible = False  # Hidden only in frame 0

# Frame 0: hidden
# Frame 1: visible (uses global)
# Frame 2: visible (uses global)
```

## Backward Compatibility

The old per-frame layer API is still supported through a compatibility layer:

```python
# Old API still works
layers = layer_manager.get_layers(frame_index)
layer_manager.add_layer(frame_index, "Background")
layer_manager.set_layer_visible(frame_index, layer_index, True)
layer_manager.set_layer_opacity(frame_index, layer_index, 0.5)
```

These methods automatically convert between LayerTracks and the old Layer format.

## Migration

Old patterns are automatically migrated when loaded:

1. Detects old per-frame layer structure
2. Groups layers by name across frames
3. Creates LayerTracks from grouped layers
4. Preserves all properties (visibility, opacity, pixels)

Migration is transparent and happens automatically.

## Independent Layer Animations

Each layer track can have independent animations:

```python
from domain.layer_animation import LayerAnimationManager, create_fade_animation

animation_manager = LayerAnimationManager()

# Create fade-in animation
fade_anim = create_fade_animation(fade_in=True, duration_frames=10)
animation_manager.set_animation(layer_track_index=0, animation=fade_anim)

# Apply animation
animation_manager.apply_animation_to_frame(
    layer_track=track,
    layer_track_index=0,
    frame_index=5,
    total_frames=20
)
```

## Key Features

1. **Layer Continuity**: Background layers exist across all frames automatically
2. **Independent Animations**: Each layer can animate differently
3. **Efficient Editing**: Edit a layer once, affects all frames (or specific frames)
4. **Better Organization**: Layers are first-class entities
5. **Industry Standard**: Matches video editing software workflows
6. **Backward Compatible**: Existing code works without changes

## Examples

### Static Background + Animated Foreground

```python
# Background: Static blue across all frames
bg_track = layer_manager.get_layer_track(0)
for i in range(total_frames):
    frame = bg_track.get_or_create_frame(i, width, height)
    frame.pixels = [(0, 0, 255)] * (width * height)  # Blue

# Foreground: Animated (different content per frame)
fg_index = layer_manager.add_layer_track("Animation")
fg_track = layer_manager.get_layer_track(fg_index)
for i in range(total_frames):
    frame = fg_track.get_or_create_frame(i, width, height)
    # Different content per frame
    frame.pixels = [(255, 0, 0)] * (width * height)  # Red, animated
```

### Per-Frame Visibility Control

```python
# Layer visible in frames 0 and 2, hidden in frame 1
track = layer_manager.get_layer_track(0)

frame0 = track.get_or_create_frame(0, width, height)
frame0.visible = True

frame1 = track.get_or_create_frame(1, width, height)
frame1.visible = False  # Override: hidden in frame 1

frame2 = track.get_or_create_frame(2, width, height)
frame2.visible = True  # Uses global (True)
```

## Performance

- **Efficient**: Layers stored once, referenced per frame
- **Fast Compositing**: Optimized blend operations
- **Memory Efficient**: Shared layer properties, per-frame pixel data only

## Migration Guide

If you have code using the old API, it will continue to work. However, for new code, prefer the new API:

**Old API (still works):**
```python
layers = layer_manager.get_layers(frame_index)
layer_manager.add_layer(frame_index, "Background")
```

**New API (recommended):**
```python
tracks = layer_manager.get_layer_tracks()
layer_manager.add_layer_track("Background")
```

## See Also

- `domain/layers.py` - LayerManager and LayerTrack implementation
- `domain/layer_animation.py` - Animation system
- `core/migration/layer_migration.py` - Migration utilities
- `docs/LAYER_AND_FRAME_DESIGN_SYSTEM.md` - Original documentation (legacy)
