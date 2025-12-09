# Canvas Features - Complete Overview & Integration Guide

**Version**: 1.0  
**Date**: 2025-01-27  
**Status**: ✅ Complete Documentation  
**Purpose**: 100% comprehensive overview of all canvas features, their integrations, and how each feature works

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Canvas Architecture](#canvas-architecture)
3. [Core Canvas Widgets](#core-canvas-widgets)
4. [Drawing Tools System](#drawing-tools-system)
5. [Canvas Rendering Features](#canvas-rendering-features)
6. [Integration Systems](#integration-systems)
7. [Feature Workflows](#feature-workflows)
8. [Technical Implementation Details](#technical-implementation-details)
9. [Complete Feature Reference](#complete-feature-reference)

---

## Executive Summary

The Upload Bridge canvas system provides a comprehensive LED matrix authoring environment with:

- **2 Main Canvas Widgets**: MatrixDesignCanvas (editable) and CircularPreviewCanvas (read-only)
- **8 Drawing Tools**: Pixel, Rectangle, Circle, Line, Fill, Gradient, Random, Eyedropper
- **Multi-Layer Support**: Full layer system with blend modes, opacity, visibility
- **Frame Management**: Multi-frame animation with timeline integration
- **Advanced Features**: Onion skinning, zoom/pan, geometry overlays, wiring visualization
- **Real-Time Integration**: Live updates with layers, frames, undo/redo, and circular preview

**Total Features**: 50+ canvas-related features across rendering, tools, and integrations

---

## Canvas Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Design Tools Tab                          │
│                                                              │
│  ┌──────────────────┐         ┌──────────────────────┐   │
│  │ MatrixDesignCanvas│         │ CircularPreviewCanvas│   │
│  │   (Editable)      │         │    (Read-Only)       │   │
│  │                   │         │                      │   │
│  │ • Pixel painting  │         │ • Circular preview    │   │
│  │ • Drawing tools   │         │ • Multi-ring preview │   │
│  │ • Zoom/Pan        │         │ • Radial ray preview │   │
│  │ • Onion skinning  │         │ • Real-time updates  │   │
│  └──────────────────┘         └──────────────────────┘   │
│           │                              │                  │
│           │ Signals                      │ Signals          │
│           ↓                              ↓                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Canvas Controller & Integration Layer        │  │
│  │                                                       │  │
│  │  • LayerManager    • FrameManager                    │  │
│  │  • HistoryManager  • PatternState                    │  │
│  │  • CanvasController • Drawing Tools                  │  │
│  └─────────────────────────────────────────────────────┘  │
│           │                              │                  │
│           ↓                              ↓                  │
│  ┌──────────────────┐         ┌──────────────────────┐   │
│  │   Timeline       │         │   Layer Panel        │   │
│  │   Widget         │         │   Widget             │   │
│  └──────────────────┘         └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

1. **MatrixDesignCanvas** → Main editable canvas widget
2. **CircularPreviewCanvas** → Read-only circular preview
3. **CanvasController** → Bridges pattern data to canvas
4. **LayerManager** → Manages multi-layer system
5. **FrameManager** → Manages animation frames
6. **HistoryManager** → Undo/redo system
7. **Drawing Tools** → Tool implementations

---

## Core Canvas Widgets

### 1. MatrixDesignCanvas

**Location**: `ui/widgets/matrix_design_canvas.py`  
**Purpose**: Interactive LED matrix editor widget

#### Key Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Pixel Grid** | 2D grid of RGB pixels | `_grid: List[List[RGB]]` |
| **Drawing Modes** | 8 drawing tools | `DrawingMode` enum |
| **Brush Size** | 1×1 to 8×8 pixel brush | `_brush_size: int` |
| **Zoom/Pan** | 25%-300% zoom, pan support | `_zoom_level`, `_pan_offset` |
| **Onion Skinning** | Previous/next frame overlays | `_onion_skin_prev_frames`, `_onion_skin_next_frames` |
| **Geometry Overlay** | Matrix/Circle/Ring/Radial overlays | `GeometryOverlay` enum |
| **Pixel Shapes** | Square/Round/Rounded rendering | `PixelShape` enum |
| **Wiring Overlay** | LED strip wiring visualization | `_draw_wiring_overlay()` |
| **Hover Feedback** | Shows pixel coordinates | `hover_changed` signal |
| **Color Picking** | Eyedropper tool | `color_picked` signal |

#### Signals

```python
pixel_updated = Signal(int, int, tuple)      # x, y, (r, g, b)
hover_changed = Signal(int, int)              # x, y under cursor
painting_finished = Signal()                 # Mouse released
color_picked = Signal(int, int, int)         # r, g, b from eyedropper
```

#### Core Methods

```python
# Pixel Management
set_frame_pixels(pixels: List[RGB])          # Load pixels from frame
get_grid_data() -> List[List[RGB]]           # Get current grid
to_pixels() -> List[RGB]                      # Export as linear list

# Drawing Configuration
set_drawing_mode(mode: DrawingMode)          # Set active tool
set_current_color(color: RGB)                # Set paint color
set_erase_color(color: RGB)                  # Set erase color
set_brush_size(size: int)                    # Set brush size (1-8)

# Visual Settings
set_pixel_shape(shape: PixelShape)           # Square/Round/Rounded
set_geometry_overlay(mode: GeometryOverlay)  # Matrix/Circle/Ring/Radial
set_border_width(width: int)                  # Pixel border (0-3)

# Zoom/Pan
set_zoom(level: float)                       # Set zoom level
reset_zoom()                                  # Reset to 100%
set_pan_offset(offset: QPoint)               # Pan canvas

# Onion Skinning
set_onion_skin_prev(frames: List[List[List[RGB]]], opacities: List[float])
set_onion_skin_next(frames: List[List[List[RGB]]], opacities: List[float])
```

#### Internal State

```python
_matrix_width: int                           # Grid width
_matrix_height: int                           # Grid height
_grid: List[List[RGB]]                       # 2D pixel grid
_current_color: RGB                          # Paint color
_erase_color: RGB                            # Erase color
_drawing_mode: DrawingMode                   # Active tool
_brush_size: int                             # Brush size (1-8)
_zoom_level: float                           # Zoom (0.25-3.0)
_pan_offset: QPoint                          # Pan offset
_pixel_shape: PixelShape                     # Rendering style
_geometry_overlay: GeometryOverlay           # Overlay type
_pattern_metadata: PatternMetadata           # Layout info
```

---

### 2. CircularPreviewCanvas

**Location**: `ui/widgets/circular_preview_canvas.py`  
**Purpose**: Read-only circular preview of grid data

#### Key Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Real-Time Updates** | Updates when grid changes | `set_grid_data()` |
| **Layout Support** | Multiple circular layouts | Layout type detection |
| **Multi-Ring Preview** | Concentric rings visualization | `_paint_multi_ring_preview()` |
| **Radial Ray Preview** | Ray-based layout preview | `_paint_radial_ray_preview()` |
| **Custom Positions** | Custom LED position preview | `_paint_custom_position_preview()` |
| **Standard Circular** | Circle/Ring/Arc preview | `_paint_circular_preview()` |

#### Core Methods

```python
set_grid_data(grid: List[List[RGB]])         # Update grid data
set_pattern_metadata(metadata: PatternMetadata)  # Set layout info
```

#### Rendering Methods

```python
_paint_circular_preview(painter, rect)        # Standard circle/ring
_paint_multi_ring_preview(painter, rect)     # Multi-ring layout
_paint_radial_ray_preview(painter, rect)     # Radial rays
_paint_custom_position_preview(painter, rect)  # Custom positions
_paint_radial_preview(painter, rect)         # Radial layout
```

---

## Drawing Tools System

### Drawing Tool Architecture

```
DrawingTool (ABC)
    │
    ├── PixelTool          → Single pixel painting
    ├── RectangleTool      → Rectangle/square drawing
    ├── CircleTool         → Circle/ellipse drawing
    ├── LineTool           → Straight line drawing
    ├── FillTool           → Bucket fill
    ├── GradientTool       → Gradient brush
    ├── RandomTool         → Random spray
    └── EyedropperTool     → Color picker
```

### Tool Details

#### 1. Pixel Tool

**Mode**: `DrawingMode.PIXEL`  
**Purpose**: Paint individual pixels or small areas

**How It Works**:
1. User clicks/drags on canvas
2. Canvas calculates pixel position from mouse coordinates
3. Applies brush size (1×1 to 8×8)
4. Updates pixel(s) in grid
5. Emits `pixel_updated` signal

**Implementation**:
```python
# In MatrixDesignCanvas
def _handle_paint_event(self, point: QPoint, button: Qt.MouseButton):
    if self._drawing_mode == DrawingMode.PIXEL:
        x, y = self._screen_to_grid(point)
        color = self._current_color if button == Qt.LeftButton else self._erase_color
        
        # Apply brush size
        for dy in range(-self._brush_size//2, self._brush_size//2 + 1):
            for dx in range(-self._brush_size//2, self._brush_size//2 + 1):
                px, py = x + dx, y + dy
                if 0 <= px < self._matrix_width and 0 <= py < self._matrix_height:
                    self._grid[py][px] = color
                    self.pixel_updated.emit(px, py, color)
```

**Integration**:
- Connected to `_on_canvas_pixel_updated()` in DesignToolsTab
- Updates active layer via LayerManager
- Triggers frame sync and canvas refresh

---

#### 2. Rectangle Tool

**Mode**: `DrawingMode.RECTANGLE`  
**Purpose**: Draw filled or outlined rectangles

**How It Works**:
1. User clicks to set start point
2. Drags to set end point
3. Preview shown while dragging
4. On release, draws rectangle

**Implementation**:
```python
def _draw_rectangle(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
    """Draw rectangle from (x1,y1) to (x2,y2)."""
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)
    
    if self._shape_filled:
        # Fill rectangle
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                    self._grid[y][x] = color
                    if not preview:
                        self.pixel_updated.emit(x, y, color)
    else:
        # Outline only
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if (x == x_min or x == x_max or y == y_min or y == y_max):
                    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
                        self._grid[y][x] = color
                        if not preview:
                            self.pixel_updated.emit(x, y, color)
```

**Features**:
- Filled or outline mode
- Preview while dragging
- Shift key for perfect square (future)

---

#### 3. Circle Tool

**Mode**: `DrawingMode.CIRCLE`  
**Purpose**: Draw filled or outlined circles/ellipses

**How It Works**:
1. User clicks to set center
2. Drags to set radius
3. Preview shown while dragging
4. On release, draws circle

**Implementation**:
```python
def _draw_circle(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
    """Draw circle/ellipse from center (x1,y1) to edge (x2,y2)."""
    center_x, center_y = x1, y1
    radius_x = abs(x2 - x1)
    radius_y = abs(y2 - y1)
    
    if self._shape_filled:
        # Fill ellipse
        for y in range(self._matrix_height):
            for x in range(self._matrix_width):
                dx = (x - center_x) / max(1, radius_x)
                dy = (y - center_y) / max(1, radius_y)
                if dx*dx + dy*dy <= 1.0:
                    self._grid[y][x] = color
                    if not preview:
                        self.pixel_updated.emit(x, y, color)
    else:
        # Outline only (Bresenham-like algorithm)
        # ... outline drawing code ...
```

---

#### 4. Line Tool

**Mode**: `DrawingMode.LINE`  
**Purpose**: Draw straight lines

**How It Works**:
1. User clicks to set start point
2. Drags to set end point
3. Preview shown while dragging
4. On release, draws line using Bresenham algorithm

**Implementation**:
```python
def _draw_line(self, x1: int, y1: int, x2: int, y2: int, color: RGB, preview: bool = False):
    """Draw line from (x1,y1) to (x2,y2) using Bresenham algorithm."""
    # Bresenham line algorithm
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    
    x, y = x1, y1
    while True:
        if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
            self._grid[y][x] = color
            if not preview:
                self.pixel_updated.emit(x, y, color)
        
        if x == x2 and y == y2:
            break
        
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
```

---

#### 5. Bucket Fill Tool

**Mode**: `DrawingMode.BUCKET_FILL`  
**Purpose**: Fill connected regions with color

**How It Works**:
1. User clicks on pixel
2. Flood fill algorithm finds connected pixels
3. Fills with tolerance (color similarity)
4. Updates all connected pixels

**Implementation**:
```python
def _bucket_fill(self, start_x: int, start_y: int, fill_color: RGB):
    """Flood fill algorithm with tolerance."""
    if not (0 <= start_x < self._matrix_width and 0 <= start_y < self._matrix_height):
        return
    
    target_color = self._grid[start_y][start_x]
    if target_color == fill_color:
        return  # Already filled
    
    # Flood fill with tolerance
    stack = [(start_x, start_y)]
    visited = set()
    tolerance = self._bucket_fill_tolerance
    
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        if not (0 <= x < self._matrix_width and 0 <= y < self._matrix_height):
            continue
        
        current_color = self._grid[y][x]
        if self._color_distance(current_color, target_color) <= tolerance:
            self._grid[y][x] = fill_color
            self.pixel_updated.emit(x, y, fill_color)
            visited.add((x, y))
            
            # Add neighbors
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
```

**Features**:
- Color tolerance (0-255)
- 4-directional flood fill
- Prevents infinite loops

---

#### 6. Gradient Tool

**Mode**: `DrawingMode.GRADIENT`  
**Purpose**: Paint with gradient colors

**How It Works**:
1. User configures start/end colors
2. Sets gradient steps
3. Paints with colors interpolated between start/end
4. Cycles through gradient as user paints

**Implementation**:
```python
def set_gradient_brush(self, start: RGB, end: RGB, steps: int):
    """Configure gradient brush."""
    self._gradient_start = start
    self._gradient_end = end
    self._gradient_steps = max(2, steps)
    self._gradient_step_index = 0

def _get_gradient_color(self) -> RGB:
    """Get current gradient color."""
    t = (self._gradient_step_index % self._gradient_steps) / self._gradient_steps
    r = int(self._gradient_start[0] * (1-t) + self._gradient_end[0] * t)
    g = int(self._gradient_start[1] * (1-t) + self._gradient_end[1] * t)
    b = int(self._gradient_start[2] * (1-t) + self._gradient_end[2] * t)
    self._gradient_step_index = (self._gradient_step_index + 1) % self._gradient_steps
    return (r, g, b)
```

**Features**:
- Configurable start/end colors
- Adjustable steps (2-32)
- Automatic color interpolation

---

#### 7. Random Tool

**Mode**: `DrawingMode.RANDOM`  
**Purpose**: Spray random colors from palette

**How It Works**:
1. User configures color palette
2. Clicks/drags on canvas
3. Random colors from palette applied
4. Density controlled by brush size

**Implementation**:
```python
def set_random_palette(self, palette: List[RGB]):
    """Set palette for random brush."""
    if palette:
        self._random_palette = [self._clamp_color(color) for color in palette]

def _get_random_color(self) -> RGB:
    """Get random color from palette."""
    if self._random_palette:
        return random.choice(self._random_palette)
    return self._current_color
```

**Features**:
- Custom color palette
- Random selection per pixel
- Brush size controls density

---

#### 8. Eyedropper Tool

**Mode**: `DrawingMode.EYEDROPPER`  
**Purpose**: Pick color from canvas

**How It Works**:
1. User clicks on pixel
2. Reads color from that pixel
3. Emits `color_picked` signal
4. Updates current color

**Implementation**:
```python
def _handle_paint_event(self, point: QPoint, button: Qt.MouseButton):
    if self._drawing_mode == DrawingMode.EYEDROPPER:
        x, y = self._screen_to_grid(point)
        if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
            color = self._grid[y][x]
            self.color_picked.emit(color[0], color[1], color[2])
            return
```

**Integration**:
- Connected to color picker in DesignToolsTab
- Updates current color immediately
- Works across all frames

---

## Canvas Rendering Features

### 1. Pixel Rendering

**Purpose**: Visual representation of pixels

**Shapes**:
- **Square**: Standard square pixels
- **Round**: Circular pixels
- **Rounded**: Rounded rectangle pixels

**Implementation**:
```python
def _draw_pixel_tile(self, painter: QPainter, rect_x: int, rect_y: int, 
                     rect_w: int, rect_h: int, color: RGB):
    """Draw a single pixel tile."""
    qcolor = QColor(color[0], color[1], color[2])
    
    if self._pixel_shape == PixelShape.SQUARE:
        painter.fillRect(rect_x, rect_y, rect_w, rect_h, qcolor)
    elif self._pixel_shape == PixelShape.ROUND:
        painter.setBrush(QBrush(qcolor))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(rect_x, rect_y, rect_w, rect_h)
    elif self._pixel_shape == PixelShape.ROUNDED:
        painter.setBrush(QBrush(qcolor))
        painter.setPen(Qt.NoPen)
        radius = min(rect_w, rect_h) * 0.2
        painter.drawRoundedRect(rect_x, rect_y, rect_w, rect_h, radius, radius)
    
    # Draw border if enabled
    if self._border_width > 0:
        border_pen = QPen(self._pixel_border_color, self._border_width)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        # ... draw border ...
```

**Features**:
- 3 pixel shapes
- Optional borders (0-3px)
- Anti-aliased rendering

---

### 2. Zoom & Pan

**Purpose**: Navigate large canvases

**Zoom Levels**: 25% - 300% (0.25x - 3.0x)

**Implementation**:
```python
def set_zoom(self, level: float):
    """Set zoom level (0.25 to 3.0)."""
    self._zoom_level = max(0.25, min(3.0, level))
    self._pixel_size = int(self._base_pixel_size * self._zoom_level)
    self.updateGeometry()
    self.update()

def _screen_to_grid(self, screen_point: QPoint) -> Tuple[int, int]:
    """Convert screen coordinates to grid coordinates."""
    # Account for zoom and pan
    x = int((screen_point.x() - self._pan_offset.x()) / self._pixel_size)
    y = int((screen_point.y() - self._pan_offset.y()) / self._pixel_size)
    return x, y
```

**Controls**:
- Zoom slider (25%-300%)
- Mouse wheel zoom
- Pan with middle-click drag
- Reset zoom button

---

### 3. Onion Skinning

**Purpose**: Show previous/next frames for animation reference

**How It Works**:
1. Loads previous/next frame pixels
2. Renders with reduced opacity
3. Shows ghost images of adjacent frames
4. Configurable opacity per frame

**Implementation**:
```python
def set_onion_skin_prev(self, frames: List[List[List[RGB]]], opacities: List[float]):
    """Set previous frames for onion skinning."""
    self._onion_skin_prev_frames = frames
    self._onion_skin_prev_opacities = opacities
    self.update()

def _draw_onion_skins(self, painter: QPainter):
    """Draw onion skin overlays."""
    # Draw previous frames
    for i, frame_grid in enumerate(self._onion_skin_prev_frames):
        opacity = self._onion_skin_prev_opacities[i] if i < len(self._onion_skin_prev_opacities) else 0.3
        for y in range(min(len(frame_grid), self._matrix_height)):
            for x in range(min(len(frame_grid[y]), self._matrix_width)):
                color = frame_grid[y][x]
                qcolor = QColor(color[0], color[1], color[2], int(255 * opacity))
                # Draw with opacity
                # ...
    
    # Draw next frames (similar)
```

**Features**:
- Multiple previous frames
- Multiple next frames
- Per-frame opacity control
- Semi-transparent rendering

---

### 4. Geometry Overlays

**Purpose**: Visualize different layout types

**Types**:
- **Matrix**: Standard rectangular grid
- **Circle**: Circular LED arrangement
- **Ring**: Ring/annulus arrangement
- **Radial**: Radial spoke arrangement

**Implementation**:
```python
def _draw_geometry_overlay(self, painter: QPainter):
    """Draw geometry overlay based on layout type."""
    if not self._pattern_metadata:
        return
    
    layout_type = getattr(self._pattern_metadata, 'layout_type', 'rectangular')
    
    if layout_type == 'rectangular':
        self._draw_wiring_overlay(painter, bounds)
    elif layout_type in ['circle', 'ring', 'arc']:
        self._draw_circular_overlay(painter, bounds)
    elif layout_type == 'multi_ring':
        self._draw_multi_ring_overlay(painter, bounds)
    elif layout_type == 'radial_rays':
        self._draw_radial_ray_overlay(painter, bounds)
```

**Features**:
- Layout-specific overlays
- Wiring path visualization
- LED index numbers
- Active cell highlighting

---

### 5. Wiring Overlay

**Purpose**: Show physical LED strip wiring order

**How It Works**:
1. Reads wiring_mode from PatternMetadata
2. Calculates LED order using WiringMapper
3. Draws path with arrows
4. Shows LED indices along path

**Implementation**:
```python
def _draw_wiring_overlay(self, painter: QPainter, bounds):
    """Draw wiring path overlay."""
    from core.wiring_mapper import WiringMapper
    
    wiring_mode = getattr(self._pattern_metadata, 'wiring_mode', 'Row-major')
    data_in_corner = getattr(self._pattern_metadata, 'data_in_corner', 'LT')
    
    mapper = WiringMapper(
        width=self._pattern_metadata.width,
        height=self._pattern_metadata.height,
        wiring_mode=wiring_mode,
        data_in_corner=data_in_corner
    )
    
    mapping = mapper._build_mapping_table()
    
    # Draw wiring path
    wiring_pen = QPen(QColor(255, 200, 0, 150), 2)
    painter.setPen(wiring_pen)
    
    prev_x, prev_y = None, None
    for hw_idx in range(len(mapping)):
        design_idx = mapping[hw_idx]
        grid_x = design_idx % self._pattern_metadata.width
        grid_y = design_idx // self._pattern_metadata.width
        
        x = bounds.x() + (grid_x + 0.5) * cell_width
        y = bounds.y() + (grid_y + 0.5) * cell_height
        
        if prev_x is not None:
            painter.drawLine(int(prev_x), int(prev_y), int(x), int(y))
        
        prev_x, prev_y = x, y
        
        # Draw LED number
        if hw_idx < 50:
            painter.setPen(QPen(QColor(255, 200, 0, 100), 1))
            painter.drawText(int(x - cell_width/4), int(y + cell_height/4), str(hw_idx))
```

**Features**:
- Supports Row-major, Serpentine, Column-major
- Shows data flow direction
- LED index labels
- Color-coded path

---

### 6. Grid Display

**Purpose**: Visual grid for alignment

**Features**:
- Grid lines between pixels
- Configurable grid color
- Toggle on/off
- Always visible in background

**Implementation**:
```python
def paintEvent(self, event):
    painter = QPainter(self)
    
    # Draw grid
    grid_pen = QPen(self._grid_color, 1)
    painter.setPen(grid_pen)
    
    for x in range(self._matrix_width + 1):
        x_pos = int(x * self._pixel_size)
        painter.drawLine(x_pos, 0, x_pos, self.height())
    
    for y in range(self._matrix_height + 1):
        y_pos = int(y * self._pixel_size)
        painter.drawLine(0, y_pos, self.width(), y_pos)
```

---

### 7. Hover Feedback

**Purpose**: Show pixel coordinates and preview

**How It Works**:
1. Mouse tracking enabled
2. Calculates grid position from mouse
3. Highlights hovered pixel
4. Emits hover_changed signal

**Implementation**:
```python
def mouseMoveEvent(self, event: QMouseEvent):
    """Handle mouse movement for hover feedback."""
    point = self._screen_to_grid(event.position().toPoint())
    x, y = point
    
    if 0 <= x < self._matrix_width and 0 <= y < self._matrix_height:
        if (x, y) != self._hover_cell:
            self._hover_cell = (x, y)
            self.hover_changed.emit(x, y)
            self.update()  # Redraw to show hover highlight
    else:
        if self._hover_cell != (-1, -1):
            self._hover_cell = (-1, -1)
            self.hover_changed.emit(-1, -1)
            self.update()
```

**Features**:
- Real-time coordinate display
- Pixel highlighting
- Status bar updates

---

## Integration Systems

### 1. Layer Integration

**How Canvas Integrates with Layers**:

```
User Paints on Canvas
    ↓
pixel_updated(x, y, color) signal
    ↓
_on_canvas_pixel_updated(x, y, color)
    ↓
Get active layer index from LayerPanel
    ↓
layer_manager.apply_pixel(frame_index, x, y, color, width, height, layer_index)
    ↓
Layer pixels updated
    ↓
layer_manager.sync_frame_from_layers(frame_index)
    ├─→ Get all visible layers
    ├─→ Blend with opacity
    └─→ Update frame.pixels with composite
    ↓
_load_current_frame_into_canvas()
    ↓
canvas.set_frame_pixels(composite_pixels)
    ↓
Canvas Redraw
```

**Key Points**:
- Canvas always displays **composite** of visible layers
- Painting updates **active layer** only
- Hidden layers are excluded from composite
- Layer opacity affects blending

---

### 2. Frame Integration

**How Canvas Integrates with Frames**:

```
Frame Selection in Timeline
    ↓
_on_frame_selected(frame_index)
    ↓
_current_frame_index = frame_index
    ↓
_load_current_frame_into_canvas()
    ├─→ Get composite pixels from LayerManager
    ├─→ canvas.set_frame_pixels(composite)
    └─→ Update onion skinning
    ↓
Canvas Redraw
```

**Frame Loading**:
```python
def _load_current_frame_into_canvas(self):
    """Load current frame into canvas."""
    if not self._pattern or not self._pattern.frames:
        return
    
    frame_index = self._current_frame_index
    if 0 <= frame_index < len(self._pattern.frames):
        # Get composite from all visible layers
        composite = self.layer_manager.get_composite_pixels(frame_index)
        
        # Load into canvas
        self.canvas.set_frame_pixels(composite)
        
        # Update onion skinning
        self._update_onion_skinning()
```

---

### 3. Undo/Redo Integration

**How Canvas Integrates with History**:

```
User Starts Painting
    ↓
Save pending state (before first pixel change)
    ↓
_pending_paint_state = copy of frame.pixels
    ↓
User Paints (multiple pixels)
    ↓
Each pixel update → layer_manager.apply_pixel()
    ↓
User Releases Mouse
    ↓
_commit_paint_operation()
    ├─→ Create FrameStateCommand
    │   ├─→ undo_state = _pending_paint_state
    │   └─→ redo_state = current frame.pixels
    └─→ history_manager.push_command(command)
    ↓
Undo/Redo Available
```

**Undo Flow**:
```python
def _on_undo(self):
    """Handle undo action."""
    command = self.history_manager.undo(self._current_frame_index)
    if command:
        frame = self._pattern.frames[self._current_frame_index]
        frame.pixels = command.undo()  # Restore previous state
        self._load_current_frame_into_canvas()  # Refresh canvas
```

**Redo Flow**:
```python
def _on_redo(self):
    """Handle redo action."""
    command = self.history_manager.redo(self._current_frame_index)
    if command:
        frame = self._pattern.frames[self._current_frame_index]
        frame.pixels = command.redo()  # Restore forward state
        self._load_current_frame_into_canvas()  # Refresh canvas
```

**Features**:
- Per-frame undo/redo stacks
- Batch operations (entire paint stroke = one undo)
- Keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- Button state updates

---

### 4. Circular Preview Integration

**How Canvas Integrates with Circular Preview**:

```
User Paints on Canvas
    ↓
pixel_updated(x, y, color) signal
    ↓
_on_canvas_pixel_updated(x, y, color)
    ↓
Update circular preview in real-time
    ↓
grid_data = canvas.get_grid_data()
    ↓
circular_preview.set_grid_data(grid_data)
    ↓
Circular Preview Redraw
    ├─→ Reads layout_type from PatternMetadata
    ├─→ Generates mapping using CircularMapper
    └─→ Renders circular arrangement
```

**Real-Time Updates**:
```python
def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
    # Update circular preview in real-time
    if hasattr(self, 'circular_preview') and hasattr(self.canvas, 'get_grid_data'):
        grid_data = self.canvas.get_grid_data()
        self.circular_preview.set_grid_data(grid_data)
```

**Layout Support**:
- Circle, Ring, Arc
- Multi-Ring (2-5 rings)
- Radial Rays
- Custom Positions

---

### 5. Brush Broadcast Integration

**How Canvas Integrates with Broadcast Mode**:

```
User Enables "Broadcast to All Frames"
    ↓
User Paints on Canvas
    ↓
_on_canvas_pixel_updated(x, y, color)
    ↓
Check broadcast mode
    ↓
if broadcast:
    target_frames = all frames
    Save state of ALL frames
else:
    target_frames = [current_frame]
    Save state of current frame only
    ↓
Apply pixel to all target frames
    ↓
for frame_index in target_frames:
    layer_manager.apply_pixel(frame_index, x, y, color, ...)
    ↓
Sync all modified frames
    ↓
Canvas shows current frame (others updated in background)
```

**Implementation**:
```python
def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
    is_broadcast = self.brush_broadcast_checkbox.isChecked()
    
    if is_broadcast:
        # Save state of all frames
        if self._pending_broadcast_states is None:
            self._pending_broadcast_states = {}
            for idx in range(len(self._pattern.frames)):
                frame = self._pattern.frames[idx]
                self._pending_broadcast_states[idx] = list(frame.pixels)
        target_frames = list(range(len(self._pattern.frames)))
    else:
        # Save state of current frame only
        if self._pending_paint_state is None:
            frame = self._pattern.frames[self._current_frame_index]
            self._pending_paint_state = list(frame.pixels)
        target_frames = [self._current_frame_index]
    
    # Apply to all target frames
    for frame_index in target_frames:
        self.layer_manager.apply_pixel(frame_index, x, y, color, width, height, active_layer)
```

**Features**:
- Applies changes to all frames simultaneously
- Separate undo stacks per frame
- Visual feedback (banner warning)
- Useful for static backgrounds

---

## Feature Workflows

### Workflow 1: Basic Pixel Painting

```
1. User selects Pixel Tool
2. User selects color from palette
3. User clicks/drags on canvas
4. Canvas calculates pixel position
5. Updates grid pixel
6. Emits pixel_updated signal
7. DesignToolsTab receives signal
8. Updates active layer
9. Syncs frame from layers
10. Refreshes canvas
11. Updates circular preview
```

### Workflow 2: Multi-Layer Painting

```
1. User creates new layer
2. User selects layer in LayerPanel
3. User paints on canvas
4. Pixel updates go to selected layer
5. LayerManager composites all visible layers
6. Composite displayed on canvas
7. Frame.pixels updated with composite
```

### Workflow 3: Shape Drawing

```
1. User selects Rectangle/Circle/Line tool
2. User clicks to set start point
3. User drags to set end point
4. Preview shown while dragging
5. User releases mouse
6. Shape drawn to canvas
7. All pixels in shape updated
8. Undo state saved
9. Canvas refreshed
```

### Workflow 4: Frame Animation

```
1. User creates multiple frames
2. User selects frame in timeline
3. Canvas loads frame composite
4. User paints on frame
5. User selects next frame
6. Canvas loads next frame
7. Onion skinning shows previous frame
8. User continues painting
```

### Workflow 5: Undo/Redo

```
1. User paints on canvas
2. State saved before first pixel
3. User continues painting
4. User releases mouse
5. Paint operation committed
6. Undo command created
7. User presses Ctrl+Z
8. Previous state restored
9. Canvas refreshed
10. User presses Ctrl+Y
11. Forward state restored
12. Canvas refreshed
```

---

## Technical Implementation Details

### Coordinate System

**Screen Coordinates** → **Grid Coordinates**:
```python
def _screen_to_grid(self, screen_point: QPoint) -> Tuple[int, int]:
    """Convert screen coordinates to grid coordinates."""
    # Account for zoom and pan
    x = int((screen_point.x() - self._pan_offset.x()) / self._pixel_size)
    y = int((screen_point.y() - self._pan_offset.y()) / self._pixel_size)
    return x, y
```

**Grid Coordinates** → **Screen Coordinates**:
```python
def _grid_to_screen(self, grid_x: int, grid_y: int) -> QPoint:
    """Convert grid coordinates to screen coordinates."""
    x = int(grid_x * self._pixel_size + self._pan_offset.x())
    y = int(grid_y * self._pixel_size + self._pan_offset.y())
    return QPoint(x, y)
```

### Pixel Data Format

**Internal Storage**:
- `_grid: List[List[RGB]]` - 2D list, row-major
- `RGB = Tuple[int, int, int]` - (R, G, B) values 0-255

**Frame Format**:
- `Frame.pixels: List[RGB]` - Linear list, row-major
- Conversion: `pixels[y * width + x] = grid[y][x]`

**Conversion Methods**:
```python
def set_frame_pixels(self, pixels: List[RGB]):
    """Load pixels from linear list (row-major)."""
    idx = 0
    for y in range(self._matrix_height):
        for x in range(self._matrix_width):
            self._grid[y][x] = tuple(pixels[idx])
            idx += 1

def to_pixels(self) -> List[RGB]:
    """Return current grid as linear row-major list."""
    pixels: List[RGB] = []
    for row in self._grid:
        pixels.extend(row)
    return pixels
```

### Rendering Pipeline

```
paintEvent() called
    ↓
1. Draw background
    ↓
2. Draw grid lines
    ↓
3. Draw onion skins (previous/next frames)
    ↓
4. Draw pixels (from _grid)
    ├─→ For each pixel:
    │   ├─→ Calculate screen position
    │   ├─→ Apply zoom/pan transform
    │   ├─→ Draw pixel shape (square/round/rounded)
    │   └─→ Draw border if enabled
    ↓
5. Draw hover highlight
    ↓
6. Draw geometry overlay
    ├─→ Wiring overlay (if rectangular)
    ├─→ Circular overlay (if circular layout)
    └─→ Active cell highlighting
    ↓
7. Draw preview shapes (if tool in preview mode)
    ↓
Complete
```

### Performance Optimizations

1. **Dirty Region Tracking**:
   - Only redraws changed areas
   - `mark_dirty(x, y, width, height)`
   - Batches multiple updates

2. **Batch Sync**:
   - Defers frame sync until paint operation completes
   - Reduces redundant layer compositing
   - `_frames_to_sync` set tracks pending syncs

3. **Lazy Onion Skinning**:
   - Only loads adjacent frames when needed
   - Caches onion skin data
   - Updates only when frame changes

4. **Optimized Redraws**:
   - `_full_repaint_needed` flag
   - Skips unnecessary calculations
   - Uses Qt's update() for efficient repaints

---

## Complete Feature Reference

### Canvas Widget Features (MatrixDesignCanvas)

| # | Feature | Type | Description | Status |
|---|---------|------|-------------|--------|
| 1 | Pixel Grid | Core | 2D RGB pixel matrix | ✅ |
| 2 | Pixel Painting | Core | Click/drag to paint | ✅ |
| 3 | Erase Mode | Core | Right-click to erase | ✅ |
| 4 | Brush Size | Tool | 1×1 to 8×8 pixels | ✅ |
| 5 | Zoom Control | View | 25%-300% zoom | ✅ |
| 6 | Pan Support | View | Middle-click drag | ✅ |
| 7 | Onion Skinning | View | Previous/next frame overlays | ✅ |
| 8 | Geometry Overlay | View | Matrix/Circle/Ring/Radial | ✅ |
| 9 | Pixel Shapes | View | Square/Round/Rounded | ✅ |
| 10 | Pixel Borders | View | 0-3px borders | ✅ |
| 11 | Grid Display | View | Visual grid lines | ✅ |
| 12 | Hover Feedback | Interaction | Pixel coordinate display | ✅ |
| 13 | Wiring Overlay | View | LED strip wiring path | ✅ |
| 14 | Active Cell Highlight | View | Highlights mapped cells | ✅ |
| 15 | LED Index Display | View | Shows LED indices | ✅ |

### Drawing Tools

| # | Tool | Mode | Description | Status |
|---|------|------|-------------|--------|
| 1 | Pixel Tool | PIXEL | Single pixel painting | ✅ |
| 2 | Rectangle Tool | RECTANGLE | Filled/outline rectangles | ✅ |
| 3 | Circle Tool | CIRCLE | Filled/outline circles | ✅ |
| 4 | Line Tool | LINE | Straight lines | ✅ |
| 5 | Bucket Fill | BUCKET_FILL | Flood fill with tolerance | ✅ |
| 6 | Gradient Tool | GRADIENT | Gradient color brush | ✅ |
| 7 | Random Tool | RANDOM | Random color spray | ✅ |
| 8 | Eyedropper | EYEDROPPER | Color picker | ✅ |

### Integration Features

| # | Feature | Integration | Description | Status |
|---|---------|-------------|-------------|--------|
| 1 | Layer Support | LayerManager | Multi-layer painting | ✅ |
| 2 | Frame Support | FrameManager | Multi-frame animation | ✅ |
| 3 | Undo/Redo | HistoryManager | Per-frame undo/redo | ✅ |
| 4 | Circular Preview | CircularPreviewCanvas | Real-time circular preview | ✅ |
| 5 | Brush Broadcast | DesignToolsTab | Apply to all frames | ✅ |
| 6 | Color Picker | DesignToolsTab | Eyedropper integration | ✅ |
| 7 | Status Updates | DesignToolsTab | Coordinate/color display | ✅ |
| 8 | Timeline Sync | TimelineWidget | Frame selection sync | ✅ |

### Circular Preview Features

| # | Feature | Description | Status |
|---|---------|-------------|--------|
| 1 | Circle Preview | Standard circular layout | ✅ |
| 2 | Ring Preview | Ring/annulus layout | ✅ |
| 3 | Multi-Ring Preview | 2-5 concentric rings | ✅ |
| 4 | Radial Ray Preview | Ray-based layout | ✅ |
| 5 | Custom Position Preview | Custom LED positions | ✅ |
| 6 | Real-Time Updates | Updates on canvas change | ✅ |

---

## Summary

### Total Features: 50+

**Core Canvas**: 15 features  
**Drawing Tools**: 8 tools  
**Integration**: 8 features  
**Circular Preview**: 6 features  
**Rendering**: 10+ features  
**Advanced**: 5+ features

### Key Integrations

1. **LayerManager** → Multi-layer support
2. **FrameManager** → Multi-frame animation
3. **HistoryManager** → Undo/redo
4. **CircularMapper** → Circular layouts
5. **WiringMapper** → Wiring visualization
6. **PatternMetadata** → Layout configuration

### Architecture Highlights

- **Signal-Based**: Qt signals for async updates
- **Composite Display**: Canvas shows composite of visible layers
- **Real-Time**: Immediate visual feedback
- **Non-Destructive**: Layers preserve original data
- **Optimized**: Dirty regions, batch sync, lazy loading

---

**Document Status**: ✅ Complete  
**Last Updated**: 2025-01-27  
**Coverage**: 100% of canvas features documented

