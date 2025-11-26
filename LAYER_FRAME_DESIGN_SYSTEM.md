# Layer and Frame Based Design System

## Overview

The Upload Bridge application implements a sophisticated **layer and frame-based design system** that is similar to video editing software like Adobe After Effects or Premiere Pro, but optimized for LED matrix animations.

---

## System Architecture

### 1. **Frames** (Time Dimension)
Frames represent different moments in time, similar to video frames:

```
Frame 0  |  Frame 1  |  Frame 2  |  Frame 3  |  ...
[RED]    |  [GREEN]  |  [BLUE]   |  [YELLOW] |  ...
```

**Properties:**
- Each frame has a **duration** (milliseconds)
- Frames are displayed sequentially to create animation
- Frame count determines animation length
- Each frame contains pixel data for the entire LED matrix

**Similar to Video Editing:**
- ✅ **Timeline-based**: Frames arranged horizontally on timeline
- ✅ **Frame-by-frame editing**: Edit each frame independently
- ✅ **Frame duration control**: Adjust timing per frame
- ✅ **Frame duplication/copying**: Reuse frame content

### 2. **Layers** (Z-Stack Dimension)
Layers represent different visual elements stacked on top of each other:

```
Layer 3 (Top)    ████████  (Text overlay)
Layer 2          ░░░░░░░░  (Animation layer)
Layer 1          ▒▒▒▒▒▒▒▒  (Background)
Layer 0 (Bottom) ▓▓▓▓▓▓▓▓  (Base pattern)
```

**Properties:**
- Multiple layers per frame
- Layers can be **visible/invisible**
- Layers have **opacity/transparency**
- Layers can be **reordered** (z-order)
- Each layer has independent pixel data

**Similar to Video Editing:**
- ✅ **Layer compositing**: Stack multiple visual elements
- ✅ **Layer opacity**: Blend layers with transparency
- ✅ **Layer visibility**: Show/hide layers
- ✅ **Layer ordering**: Control which layer is on top

---

## Complete System Structure

```
Pattern
├── Frame 0
│   ├── Layer 0 (Background) - 16x16 pixels
│   ├── Layer 1 (Animation)  - 16x16 pixels
│   └── Layer 2 (Text)       - 16x16 pixels
├── Frame 1
│   ├── Layer 0 (Background) - 16x16 pixels
│   ├── Layer 1 (Animation)  - 16x16 pixels
│   └── Layer 2 (Text)       - 16x16 pixels
└── Frame 2
    ├── Layer 0 (Background) - 16x16 pixels
    ├── Layer 1 (Animation)  - 16x16 pixels
    └── Layer 2 (Text)       - 16x16 pixels
```

---

## Comparison: Upload Bridge vs Video Editing Software

### Similarities ✅

| Feature | Upload Bridge | Video Editing (After Effects/Premiere) |
|---------|--------------|----------------------------------------|
| **Frames** | ✅ Sequential frames for animation | ✅ Sequential frames for video |
| **Layers** | ✅ Multiple layers per frame | ✅ Multiple layers per composition |
| **Timeline** | ✅ Horizontal timeline with frames | ✅ Horizontal timeline with clips |
| **Layer Compositing** | ✅ Stack layers with blending | ✅ Stack video/audio tracks |
| **Opacity** | ✅ Layer transparency control | ✅ Track opacity/transparency |
| **Visibility** | ✅ Show/hide layers | ✅ Enable/disable tracks |
| **Frame Duration** | ✅ Millisecond-based timing | ✅ Frame-based timing |
| **Copy/Duplicate** | ✅ Duplicate frames | ✅ Duplicate clips |

### Key Differences 🔄

| Aspect | Upload Bridge | Video Editing |
|--------|--------------|---------------|
| **Resolution** | Small (typically 8x8 to 128x128) | Large (HD, 4K, etc.) |
| **Color Depth** | RGB (24-bit) | RGB/YCbCr with codecs |
| **Frame Rate** | Variable (user-controlled) | Fixed (24/30/60 FPS) |
| **Content Type** | LED matrix patterns | Video/audio content |
| **Export Format** | Binary/hex patterns | Video files (MP4, etc.) |
| **Hardware Target** | Microcontrollers | Screens/displays |

---

## How It Works

### Frame-Based Animation

1. **Create Frames**
   - Each frame represents a snapshot in time
   - Frames are displayed sequentially
   - Frame duration controls playback speed

2. **Edit Frames**
   - Paint/edit pixels on each frame
   - Copy frame content between frames
   - Delete or insert frames

3. **Playback**
   - Frames play in order: 0 → 1 → 2 → 3...
   - Total animation time = sum of all frame durations

### Layer-Based Compositing

1. **Create Layers**
   - Multiple layers per frame
   - Each layer has independent pixel data
   - Layers stack on top of each other

2. **Compose Layers**
   - Bottom layer = background
   - Top layers = foreground elements
   - Layers blend together to create final image

3. **Layer Operations**
   - Reorder layers (move up/down)
   - Toggle visibility
   - Adjust opacity
   - Edit layer content independently

---

## Example Use Case

**Creating an Animated LED Sign:**

```
Frame 0:
├── Layer 0 (Background): Solid blue background
├── Layer 1 (Text): "HELLO" text in white
└── Layer 2 (Sparkle): Random sparkle effects

Frame 1:
├── Layer 0 (Background): Solid blue background (same)
├── Layer 1 (Text): "HELLO" text shifted 1 pixel left
└── Layer 2 (Sparkle): Different sparkle pattern

Frame 2:
├── Layer 0 (Background): Solid blue background (same)
├── Layer 1 (Text): "HELLO" text shifted 2 pixels left
└── Layer 2 (Sparkle): Different sparkle pattern

...and so on
```

**Result:** Animated scrolling text with sparkle effects on a blue background!

---

## Implementation Details

### Data Structure

```python
Pattern
├── metadata: PatternMetadata (width, height, etc.)
└── frames: List[Frame]
    └── Frame
        ├── pixels: List[Tuple[int, int, int]]  # RGB values
        ├── duration_ms: int
        └── layers: List[Layer]  # Multiple layers per frame
            └── Layer
                ├── pixels: List[Tuple[int, int, int]]
                ├── visible: bool
                ├── opacity: float (0.0-1.0)
                └── name: str
```

### Managers

1. **FrameManager**: Manages frame operations
   - Add/remove frames
   - Duplicate frames
   - Reorder frames
   - Frame selection/navigation

2. **LayerManager**: Manages layer operations
   - Add/remove layers per frame
   - Layer visibility/opacity
   - Layer reordering
   - Layer composition/blending

3. **PatternState**: Single source of truth
   - Stores current pattern
   - Tracks frame/layer state
   - Notifies observers of changes

---

## Advantages of This System

1. **Flexibility**: Mix static and animated elements easily
2. **Reusability**: Reuse layers across frames
3. **Organization**: Separate concerns (background, animation, text)
4. **Non-destructive**: Edit layers independently
5. **Professional**: Industry-standard approach (like video editing)

---

## Comparison Summary

| Feature | Upload Bridge | Video Editing Software |
|---------|--------------|------------------------|
| **Time Dimension** | ✅ Frames | ✅ Timeline |
| **Z-Stack Dimension** | ✅ Layers | ✅ Video Tracks |
| **Compositing** | ✅ Layer blending | ✅ Track compositing |
| **Animation** | ✅ Frame-by-frame | ✅ Keyframe animation |
| **Editing Style** | ✅ Frame-based + Layer-based | ✅ Track-based + Layer-based |

---

**Conclusion**: Upload Bridge implements a **dual-dimension design system**:
- **Horizontal (Time)**: Frames for animation
- **Vertical (Z-Stack)**: Layers for compositing

This gives you the power of video editing software, optimized for LED matrix patterns!

