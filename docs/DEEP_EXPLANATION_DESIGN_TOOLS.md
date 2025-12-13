# Deep Explanation: Design Tools Tab & Design Tools

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Drawing Tools](#drawing-tools)
4. [Canvas System](#canvas-system)
5. [Layer System](#layer-system)
6. [Frame Management](#frame-management)
7. [Automation Actions](#automation-actions)
8. [Effects Library](#effects-library)
9. [Pattern State Management](#pattern-state-management)
10. [History & Undo/Redo](#history--undoredo)
11. [Integration Points](#integration-points)

---

## Overview

The **Design Tools Tab** (`ui/tabs/design_tools_tab.py`) is the core authoring environment for creating LED matrix patterns. It provides a comprehensive studio interface where users can:

- Paint and draw on LED matrices using 8 different drawing tools
- Manage multiple layers per frame (up to 16 layers)
- Create and edit animation frames
- Apply automation actions (scroll, rotate, mirror, etc.)
- Apply visual effects (92+ effects)
- Manage color palettes
- Render text with bitmap fonts
- Preview patterns in real-time

### Key Capabilities

```python
class DesignToolsTab(QWidget):
    """
    Comprehensive LED matrix design studio.
    
    Key capabilities:
        - Interactive matrix painting canvas
        - Palette-based color selection
        - Frame management (add, duplicate, delete, reorder)
        - Automation action queue (scroll, rotate, mirror, invert, etc.)
        - Pattern import/export with rest of application
    """
```

---

## Architecture

### Component Hierarchy

```
DesignToolsTab (Main Widget)
├── Canvas Panel
│   ├── MatrixDesignCanvas (Drawing surface)
│   ├── CircularPreviewCanvas (Circular layout preview)
│   └── Canvas Controls (Zoom, Pan, Reset)
├── Toolbox Column
│   ├── Drawing Tools Tab
│   ├── Color Palette Tab
│   ├── Layers Tab
│   ├── Effects Tab
│   └── Automation Tab
├── Timeline Dock
│   ├── TimelineWidget (Frame navigation)
│   └── Playback Controls
└── Status Bar
    ├── Matrix Status (dimensions, color mode)
    ├── Frame Status (current frame, duration)
    └── Memory Status (pattern size)
```

### Core Dependencies

```python
# Pattern Management
from core.pattern import Pattern, Frame, PatternMetadata
from core.repositories.pattern_repository import PatternRepository

# Drawing & Canvas
from ui.widgets.matrix_design_canvas import MatrixDesignCanvas, DrawingMode
from domain.canvas import CanvasController
from domain.drawing.tools import *  # All drawing tools

# Layer System
from domain.layers import LayerManager, Layer

# Frame Management
from domain.frames import FrameManager

# History & Undo/Redo
from domain.history import HistoryManager, FrameStateCommand

# Automation
from domain.automation.queue import AutomationQueueManager
from domain.actions import DesignAction

# Effects
from domain.effects import EffectLibrary, apply_effect_to_frames

# Text Rendering
from domain.text.text_renderer import TextRenderer
from domain.text.bitmap_font import BitmapFontRepository
```

### State Management

The Design Tools Tab uses a **multi-layered state management system**:

1. **Pattern State** (`domain/pattern_state.py`)
   - Manages the current pattern
   - Provides reactive updates to all components
   - Handles pattern loading/saving

2. **Frame Manager** (`domain/frames.py`)
   - Manages frame collection
   - Handles frame selection, insertion, deletion
   - Maintains frame order and duration

3. **Layer Manager** (`domain/layers.py`)
   - Manages layers per frame
   - Handles layer composition and blending
   - Supports layer groups and masks

4. **History Manager** (`domain/history.py`)
   - Tracks all changes for undo/redo
   - Stores frame state snapshots
   - Manages command pattern for operations

---

## Drawing Tools

The Design Tools Tab provides **8 drawing tools** for creating patterns:

### 1. Pixel Tool (Freehand Drawing)
- **Mode**: `DrawingMode.PIXEL`
- **Purpose**: Single-pixel painting
- **Behavior**: Paints individual pixels as you drag
- **Brush Settings**: Size (1-50), Shape (square/circle), Hardness (0.0-1.0)

```python
# Tool selection
def _on_tool_selected(self, mode: DrawingMode):
    """Handle tool selection"""
    self.canvas.set_drawing_mode(mode)
    self._current_tool = mode
```

### 2. Rectangle Tool
- **Mode**: `DrawingMode.RECTANGLE`
- **Purpose**: Draw filled or outlined rectangles
- **Behavior**: Click and drag to define rectangle bounds
- **Options**: Filled/outlined, corner radius

### 3. Circle Tool
- **Mode**: `DrawingMode.CIRCLE`
- **Purpose**: Draw filled or outlined circles
- **Behavior**: Click center, drag to set radius
- **Options**: Filled/outlined, anti-aliasing

### 4. Line Tool
- **Mode**: `DrawingMode.LINE`
- **Purpose**: Draw straight lines
- **Behavior**: Click start point, drag to end point
- **Options**: Line width, anti-aliasing

### 5. Random Spray Tool
- **Mode**: `DrawingMode.RANDOM`
- **Purpose**: Random pixel placement
- **Behavior**: Sprays random pixels within brush area
- **Options**: Density, spread radius, color variation

### 6. Gradient Brush Tool
- **Mode**: `DrawingMode.GRADIENT`
- **Purpose**: Paint with color gradients
- **Behavior**: Blends between start and end colors
- **Options**: Gradient type (linear/radial), color stops

### 7. Bucket Fill Tool
- **Mode**: `DrawingMode.BUCKET_FILL`
- **Purpose**: Fill connected areas with same color
- **Behavior**: Flood fill algorithm
- **Options**: Tolerance, fill mode (all layers/current layer)

### 8. Eyedropper Tool
- **Mode**: `DrawingMode.EYEDROPPER`
- **Purpose**: Sample colors from canvas
- **Behavior**: Click to pick color, updates current color
- **Options**: Sample from all layers/current layer

### Tool Implementation

Each tool is implemented in `domain/drawing/tools.py`:

```python
class PixelTool:
    """Single pixel painting tool"""
    def on_mouse_press(self, x, y, color, brush_settings):
        """Handle mouse press"""
        self._paint_pixel(x, y, color, brush_settings)
    
    def on_mouse_drag(self, x, y, color, brush_settings):
        """Handle mouse drag"""
        self._paint_line(self._last_pos, (x, y), color, brush_settings)
        self._last_pos = (x, y)
```

### Brush Settings

All tools share common brush settings:

```python
class BrushSettings:
    size: int = 1  # 1-50 pixels
    shape: PixelShape = PixelShape.SQUARE  # SQUARE or CIRCLE
    hardness: float = 1.0  # 0.0 (soft) to 1.0 (hard)
    opacity: float = 1.0  # 0.0 to 1.0
```

---

## Canvas System

### MatrixDesignCanvas

The **MatrixDesignCanvas** (`ui/widgets/matrix_design_canvas.py`) is the primary drawing surface:

```python
class MatrixDesignCanvas(QWidget):
    """
    Interactive canvas for LED matrix pattern design.
    
    Features:
        - Real-time pixel painting
        - Zoom and pan
        - Grid overlay
        - Onion skinning
        - Wiring visualization
        - Multi-layer rendering
    """
```

### Canvas Features

1. **Pixel Grid Rendering**
   - Displays LED matrix as grid of colored squares
   - Updates in real-time as you paint
   - Supports zoom levels (1x to 20x)

2. **Mouse Interaction**
   - Converts mouse coordinates to pixel coordinates
   - Handles click, drag, and release events
   - Supports different drawing modes

3. **Visual Overlays**
   - Grid lines (optional)
   - Pixel coordinates
   - Selection rectangle
   - Onion skin (previous/next frame preview)

4. **Circular Layout Support**
   - Can render circular LED arrangements
   - Shows radial coordinates
   - Supports multi-ring layouts

### Canvas Controller

The **CanvasController** (`domain/canvas.py`) manages canvas state:

```python
class CanvasController:
    """Manages canvas state and operations"""
    
    def set_pattern(self, pattern: Pattern):
        """Load pattern into canvas"""
    
    def set_current_frame(self, frame_index: int):
        """Switch to different frame"""
    
    def paint_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Paint a single pixel"""
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get pixel color at position"""
```

### Canvas Signals

The canvas emits signals for UI updates:

```python
pixel_updated = Signal(int, int, tuple)  # x, y, color
frame_changed = Signal(int)  # frame_index
zoom_changed = Signal(float)  # zoom_level
```

---

## Layer System

### Layer Architecture

The Design Tools Tab supports **multi-layer editing** with up to 16 layers per frame:

```python
class LayerManager(QObject):
    """
    Multi-layer manager for LED matrix patterns.
    
    Each frame can have multiple layers that can be:
    - Shown/hidden independently
    - Adjusted for opacity
    - Reordered
    - Composed together for display
    - Grouped together
    - Masked with per-pixel masks
    """
```

### Layer Properties

```python
class Layer:
    name: str = "Layer"
    pixels: List[Color] = []  # Pixel data
    visible: bool = True
    opacity: float = 1.0  # 0.0 to 1.0
    blend_mode: str = "normal"  # normal, add, multiply, screen
    group_id: Optional[str] = None  # Layer group
    mask: Optional[List[float]] = None  # Per-pixel mask (0.0-1.0)
```

### Blend Modes

1. **Normal**: Standard alpha blending
2. **Add**: Additive blending (brightens)
3. **Multiply**: Multiplicative blending (darkens)
4. **Screen**: Screen blending (lightens)

### Layer Composition

When rendering, layers are composed bottom-to-top:

```python
def compose_layers(layers: List[Layer]) -> List[Color]:
    """Compose multiple layers into final frame"""
    result = [BLACK] * pixel_count
    
    for layer in layers:
        if not layer.visible:
            continue
        
        for i, pixel in enumerate(layer.pixels):
            if layer.mask:
                alpha = layer.opacity * layer.mask[i]
            else:
                alpha = layer.opacity
            
            result[i] = blend(result[i], pixel, alpha, layer.blend_mode)
    
    return result
```

### Layer Groups

Layers can be grouped for easier management:

```python
class LayerGroup:
    group_id: str
    name: str = "Group"
    visible: bool = True
    opacity: float = 1.0
```

### Layer Masks

Per-pixel masks allow selective transparency:

```python
# Mask value 0.0 = fully transparent
# Mask value 1.0 = fully opaque
layer.mask = [0.5, 1.0, 0.0, ...]  # Per-pixel mask
```

---

## Frame Management

### Frame Manager

The **FrameManager** (`domain/frames.py`) handles all frame operations:

```python
class FrameManager:
    """Manages frame collection and selection"""
    
    def add_frame(self, frame: Frame, index: Optional[int] = None):
        """Add new frame"""
    
    def delete_frame(self, index: int):
        """Delete frame (cannot delete last frame)"""
    
    def duplicate_frame(self, index: int) -> int:
        """Duplicate frame, returns new frame index"""
    
    def reorder_frames(self, from_index: int, to_index: int):
        """Reorder frames"""
    
    def select(self, index: int):
        """Select frame"""
    
    def current_index(self) -> int:
        """Get current frame index"""
```

### Frame Structure

```python
class Frame:
    pixels: List[Tuple[int, int, int]]  # RGB pixel data
    duration_ms: int  # Frame duration (1-65535ms)
    layers: List[Layer]  # Multi-layer support
```

### Timeline Widget

The **TimelineWidget** (`ui/widgets/timeline_widget.py`) provides visual frame management:

- Visual frame thumbnails
- Frame selection
- Frame reordering (drag & drop)
- Frame duration editing
- Playhead indicator
- Playback controls

### Frame Operations

1. **Add Frame**: Creates new empty frame
2. **Duplicate Frame**: Copies current frame
3. **Delete Frame**: Removes frame (minimum 1 frame required)
4. **Reorder Frames**: Drag to reorder
5. **Set Duration**: Change frame display time

---

## Automation Actions

### Automation Queue

The **AutomationQueueManager** (`domain/automation/queue.py`) manages automation actions:

```python
class AutomationQueueManager:
    """Manages queue of automation actions"""
    
    def enqueue_action(self, action: DesignAction):
        """Add action to queue"""
    
    def apply_all(self, pattern: Pattern):
        """Apply all queued actions"""
    
    def clear(self):
        """Clear queue"""
```

### Available Actions

1. **Scroll Up/Down/Left/Right**
   - Shifts pattern pixels in specified direction
   - Wraps around edges

2. **Rotate** (90°, 180°, 270°)
   - Rotates pattern clockwise
   - Maintains pixel positions

3. **Mirror** (Horizontal/Vertical)
   - Flips pattern along axis
   - Preserves pixel colors

4. **Invert**
   - Inverts all colors
   - RGB inversion: (255-R, 255-G, 255-B)

5. **Fade In/Out**
   - Gradual opacity transition
   - Creates smooth transitions

6. **Shift** (with wrap)
   - Similar to scroll but with configurable wrap

7. **Flip** (Horizontal/Vertical)
   - Same as mirror

8. **Color Replace**
   - Replace specific color with another

### Action Application

Actions are applied to frames:

```python
def apply_scroll_up(pattern: Pattern, pixels: int = 1):
    """Scroll pattern up by N pixels"""
    for frame in pattern.frames:
        new_pixels = []
        for i in range(len(frame.pixels)):
            # Calculate new position
            new_index = (i + pixels * pattern.metadata.width) % len(frame.pixels)
            new_pixels.append(frame.pixels[new_index])
        frame.pixels = new_pixels
```

---

## Effects Library

### Effect System

The **EffectLibrary** (`domain/effects.py`) provides 92+ visual effects:

```python
class EffectLibrary:
    """Library of visual effects"""
    
    def get_effect(self, name: str) -> EffectDefinition:
        """Get effect definition"""
    
    def list_effects(self) -> List[str]:
        """List all available effects"""
```

### Effect Categories

1. **Linear Effects** (30+)
   - Wave, Ripple, Pulse, Fade
   - Color cycling, Rainbow, Fire
   - Sparkle, Twinkle, Chase

2. **Radial Effects** (20+)
   - Radial gradient, Spiral
   - Explosion, Implosion
   - Radial wave, Radial pulse

3. **Pattern Effects** (20+)
   - Checkerboard, Stripes
   - Grid, Dots, Lines
   - Maze, Labyrinth

4. **Color Effects** (15+)
   - Color shift, Color cycle
   - Saturation, Brightness
   - Contrast, Gamma

5. **Animation Effects** (7+)
   - Bounce, Elastic, Ease
   - Spring, Overshoot

### Applying Effects

```python
def apply_effect_to_frames(
    frames: List[Frame],
    effect: EffectDefinition,
    intensity: float = 1.0,
    parameters: Dict = {}
):
    """Apply effect to frame sequence"""
    for frame in frames:
        for i, pixel in enumerate(frame.pixels):
            x, y = index_to_coords(i, frame.width)
            new_color = effect.apply(x, y, pixel, intensity, parameters)
            frame.pixels[i] = new_color
```

### Effect Parameters

Each effect has configurable parameters:

```python
class EffectDefinition:
    name: str
    category: str
    parameters: Dict[str, Parameter]  # Parameter definitions
    
    def apply(self, x: int, y: int, base_color: Color, 
              intensity: float, params: Dict) -> Color:
        """Apply effect to pixel"""
```

---

## Pattern State Management

### Pattern State

The **PatternState** (`domain/pattern_state.py`) manages the current pattern:

```python
class PatternState:
    """Reactive pattern state management"""
    
    def pattern(self) -> Pattern:
        """Get current pattern"""
    
    def set_pattern(self, pattern: Pattern):
        """Set new pattern"""
    
    def frames(self) -> List[Frame]:
        """Get frames"""
    
    def current_frame(self) -> Frame:
        """Get current frame"""
```

### Pattern Repository

The **PatternRepository** (`core/repositories/pattern_repository.py`) provides global pattern access:

```python
class PatternRepository:
    """Singleton repository for current pattern"""
    
    @classmethod
    def instance(cls) -> 'PatternRepository':
        """Get singleton instance"""
    
    def get_current_pattern(self) -> Optional[Pattern]:
        """Get current pattern"""
    
    def set_current_pattern(self, pattern: Pattern, file_path: Optional[str] = None):
        """Set current pattern"""
```

### Pattern Modification Flow

1. User performs action (paint, apply effect, etc.)
2. Action modifies pattern data
3. PatternState emits change signal
4. All registered components update
5. HistoryManager records change
6. Pattern marked as "dirty" (unsaved)

---

## History & Undo/Redo

### History Manager

The **HistoryManager** (`domain/history.py`) tracks all changes:

```python
class HistoryManager:
    """Manages undo/redo history"""
    
    def push_command(self, command: FrameStateCommand):
        """Add command to history"""
    
    def undo(self, frame_index: int) -> Optional[FrameStateCommand]:
        """Undo last command"""
    
    def redo(self, frame_index: int) -> Optional[FrameStateCommand]:
        """Redo last undone command"""
    
    def can_undo(self, frame_index: int) -> bool:
        """Check if undo is possible"""
    
    def can_redo(self, frame_index: int) -> bool:
        """Check if redo is possible"""
```

### Frame State Commands

Commands store frame state snapshots:

```python
class FrameStateCommand:
    """Command storing frame state"""
    
    frame_index: int
    before_state: List[Color]  # Pixel data before
    after_state: List[Color]  # Pixel data after
    
    def undo(self):
        """Restore before state"""
    
    def redo(self):
        """Restore after state"""
```

### Unlimited History

The history system supports unlimited undo/redo:
- Each frame has its own history stack
- Commands are stored efficiently (only pixel changes)
- History persists until pattern is closed

---

## Integration Points

### Signal Connections

The Design Tools Tab emits signals for integration:

```python
pattern_modified = Signal()  # Pattern was modified
pattern_created = Signal(Pattern)  # New pattern created
playback_state_changed = Signal(bool)  # Playback state changed
frame_changed = Signal(int)  # Frame index changed
```

### Cross-Tab Integration

1. **Pattern Repository**: All tabs share the same pattern
2. **Signal Broadcasting**: Changes propagate to all tabs
3. **Real-time Updates**: Preview tab updates automatically
4. **Synchronized State**: All tabs stay in sync

### File Operations

- **Load Pattern**: Loads pattern into repository, all tabs update
- **Save Pattern**: Saves current pattern state
- **Export**: Uses ExportService for format conversion
- **Import**: Uses ImageImporter, MediaConverter, etc.

---

## Advanced Features

### Text Rendering

- Bitmap font support
- Text tool for adding text to patterns
- Scroll text animations
- Multiple font sizes

### Color Palette

- 16 default colors
- Custom palette creation
- Color picker (eyedropper)
- Gradient support

### Onion Skinning

- Preview previous/next frames
- Adjustable opacity
- Helps with animation timing

### Zoom & Pan

- Zoom levels: 1x to 20x
- Pan with mouse drag
- Reset zoom button
- Fit to window option

### Grid Overlay

- Optional grid display
- Pixel coordinate labels
- Snap to grid option

---

## Performance Considerations

### Optimization Strategies

1. **Lazy Rendering**: Only render visible areas
2. **Pixel Caching**: Cache rendered pixel data
3. **Incremental Updates**: Only update changed pixels
4. **Frame Thumbnails**: Generate thumbnails asynchronously
5. **Memory Management**: Efficient pixel storage

### Memory Usage

- Pattern size calculation
- Memory warnings (>24KB)
- Frame count limits
- Layer count limits (16 max)

---

## Conclusion

The Design Tools Tab is a comprehensive pattern authoring environment that combines:

- **8 Drawing Tools** for creative expression
- **Multi-Layer System** for complex compositions
- **Frame Management** for animations
- **Automation Actions** for transformations
- **92+ Effects** for visual enhancement
- **History System** for undo/redo
- **Real-time Preview** for immediate feedback

All components work together through a reactive state management system, ensuring smooth user experience and consistent data integrity.

