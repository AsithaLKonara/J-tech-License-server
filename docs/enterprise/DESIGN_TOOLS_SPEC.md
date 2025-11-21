# Design Tools Tab - Enterprise Specification

## Overview

The Design Tools Tab is the primary interface for creating and editing LED matrix patterns. This document specifies the complete feature set, architecture, and implementation details.

## Architecture

### MVC Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   View Layer (UI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Canvas Widget│  │ Timeline     │  │ Tool Palette │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↓ Signals
┌─────────────────────────────────────────────────────────┐
│                Controller Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ DesignTools  │  │ FrameManager │  │ LayerManager │ │
│  │ Tab          │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↓ Operations
┌─────────────────────────────────────────────────────────┐
│                  Model Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ PatternState │  │ Pattern      │  │ History      │ │
│  │              │  │              │  │ Manager      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **PatternState** (`domain/pattern_state.py`)
   - Lightweight holder for active Pattern
   - Provides validated access to pattern data
   - Single source of truth for pattern state

2. **FrameManager** (`domain/frames.py`)
   - Manages frame operations (add, delete, duplicate, move)
   - Emits signals for UI updates
   - Maintains current frame index

3. **LayerManager** (`domain/layers.py`)
   - Multi-layer support per frame
   - Layer operations (add, remove, reorder, merge)
   - Compositing with blend modes

4. **CanvasController** (`domain/canvas.py`)
   - Bridges pattern data to rendering canvas
   - Emits frame_ready signals
   - Handles frame supplier logic

5. **HistoryManager** (`domain/history.py`)
   - Undo/redo system
   - Per-frame history tracking
   - Command pattern for actions

## Features

### Drawing Tools

All tools are deterministic and testable:

1. **Pixel Tool**
   - Single pixel painting
   - Left click: paint, Right click: erase

2. **Rectangle Tool**
   - Filled or outline rectangles
   - Drag to define bounds

3. **Circle Tool**
   - Filled or outline circles
   - Drag to define radius

4. **Line Tool**
   - Bresenham's line algorithm
   - Straight line drawing

5. **Fill Tool**
   - Flood fill connected pixels
   - Same color fill algorithm

6. **Gradient Tool**
   - Linear gradient between two colors
   - Interpolation along line

7. **Random Spray Tool**
   - Random pixel spray
   - Configurable density

8. **Text Tool**
   - Bitmap font rendering
   - Text placement

### Brush System

- **Size**: 1-max pixels (default: 1)
- **Shape**: Square or Circle
- **Hardness**: 0.0-1.0 (edge falloff)
- **Opacity**: 0.0-1.0 (brush transparency)

### Layer System

- **Multiple Layers**: Up to 16 layers per frame
- **Opacity**: 0.0-1.0 per layer
- **Blend Modes**: normal, add, multiply, screen
- **Visibility**: Per-layer toggle
- **Reordering**: Drag and drop
- **Solo Mode**: Show single layer

### Timeline Widget

- **Frame Visualization**: Thumbnail previews
- **Playhead**: Current frame indicator
- **Markers**: Visual markers on timeline
- **Overlays**: Automation action visualization
- **Layer Tracks**: Per-layer timeline rows
- **Zoom**: 25%-400%
- **Drag & Drop**: Frame reordering

### Automation & Effects

**Parametric Actions** (deterministic):

1. **Scroll** - Direction (up/down/left/right), speed, distance
2. **Rotate** - 90° clockwise rotation
3. **Mirror** - Horizontal or vertical axis
4. **Flip** - Same as mirror
5. **Invert** - Color inversion
6. **Wipe** - Direction, color, progression
7. **Reveal** - Direction, progression
8. **Bounce** - Direction, oscillation

**Effects Library**:
- Procedural effect generation
- Preview thumbnails
- Intensity control
- Frame range selection

### Scratchpads

- **8 Slots**: Persistent per project
- **Metadata**: Source frame, layer, timestamp
- **Copy/Paste**: Quick pixel data transfer
- **Provenance**: Track where data came from

### History & Undo/Redo

- **Unlimited Depth**: Configurable maximum
- **Delta Compression**: Only store changes
- **Per-Frame History**: Independent undo stacks
- **Batch Operations**: Atomic transactions
- **Memory Efficient**: Scales with changes

### Performance

**Performance Budgets**:
- 8×8: 60 FPS
- 16×16: 60 FPS
- 32×32: 60 FPS
- 64×32: 30 FPS
- 128×64: 15 FPS

**Optimizations**:
- Hardware-accelerated rendering (OpenGL)
- Worker threads for heavy operations
- Bounded frame buffer queues
- Dirty region tracking
- Precomputed frames for large matrices

### Accessibility

- **Screen Reader Support**: All UI elements labeled
- **Keyboard Navigation**: Full keyboard-only operation
- **High Contrast Mode**: Improved visibility
- **Tooltips**: Descriptive tooltips for all controls
- **ARIA Labels**: Semantic markup

### Internationalization

- **Externalized Strings**: All UI strings in translation files
- **Language Support**: Multi-language support
- **Locale-Aware**: Date/time formatting
- **RTL Support**: Right-to-left language support (future)

## API Reference

### PatternState

```python
class PatternState:
    def set_pattern(self, pattern: Pattern) -> None
    def pattern(self) -> Pattern
    def metadata(self) -> PatternMetadata
    def frames(self) -> list[Frame]
    def frame_count(self) -> int
    def width(self) -> int
    def height(self) -> int
    def create_blank_frame(self, duration_ms: int) -> Frame
```

### FrameManager

```python
class FrameManager(QObject):
    frames_changed = Signal()
    frame_index_changed = Signal(int)
    frame_duration_changed = Signal(int, int)
    
    def select(self, index: int) -> None
    def add_blank_after_current(self, duration_ms: int) -> int
    def duplicate(self, index: Optional[int] = None) -> int
    def delete(self, index: Optional[int] = None) -> None
    def move(self, src: int, dest: int) -> None
    def set_duration(self, index: int, duration_ms: int) -> None
```

### LayerManager

```python
class LayerManager(QObject):
    pixel_changed = Signal(int, int, int, tuple)
    layers_changed = Signal(int)
    layer_added = Signal(int, int)
    
    def add_layer(self, frame_index: int, name: Optional[str] = None) -> int
    def remove_layer(self, frame_index: int, layer_index: int) -> bool
    def move_layer(self, frame_index: int, from_index: int, to_index: int) -> bool
    def set_layer_visible(self, frame_index: int, layer_index: int, visible: bool) -> None
    def set_layer_opacity(self, frame_index: int, layer_index: int, opacity: float) -> None
    def set_layer_blend_mode(self, frame_index: int, layer_index: int, blend_mode: str) -> None
    def get_composite_pixels(self, frame_index: int) -> List[Color]
```

### Drawing Tools

```python
class DrawingTool(ABC):
    def apply(self, frame: Frame, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
              color: RGB, width: int, height: int) -> Frame

class PixelTool(DrawingTool): ...
class RectangleTool(DrawingTool): ...
class CircleTool(DrawingTool): ...
class LineTool(DrawingTool): ...
class FillTool(DrawingTool): ...
class GradientTool(DrawingTool): ...
class RandomSprayTool(DrawingTool): ...
class TextTool(DrawingTool): ...
```

### Automation Actions

```python
class ParametricAction:
    def __init__(self, action_type: ActionType, parameters: ActionParameters,
                 frame_range: Optional[Tuple[int, int]] = None)
    def apply(self, pattern: Pattern) -> Pattern

def create_action(action_type: str, parameters: Optional[Dict[str, Any]] = None,
                  frame_range: Optional[Tuple[int, int]] = None) -> ParametricAction
```

## Performance Requirements

- **Canvas Rendering**: 60 FPS for 32×32 matrices
- **Frame Operations**: < 10ms for add/delete/duplicate
- **Layer Compositing**: < 5ms per frame for 16×16 with 4 layers
- **Drawing Tools**: < 1ms per pixel operation
- **Memory Usage**: < 100MB for 64×32 pattern with 100 frames

## Test Coverage

- **Unit Tests**: 80%+ coverage for core modules
- **Integration Tests**: All workflows tested
- **Performance Tests**: Benchmarks for all operations
- **Accessibility Tests**: Screen reader compatibility
- **Deterministic Tests**: All tools and effects are testable

## Security

- **Input Validation**: All user inputs validated
- **File Validation**: Pattern files validated before loading
- **Type Safety**: Type checking for all operations
- **Optional Encryption**: Project file encryption (enterprise)
- **Optional Signing**: Digital signatures for tamper detection

