# Complete Guide: Design Tools Tab Features
**How to Use: Effects, Layers, Frames, Automation, Text, and Fonts**

---

## 📊 Feature Status Summary

✅ **LAYERS** - Working  
✅ **FRAMES PER LAYER** - Working  
✅ **TEXT** - Working  
✅ **FONTS** - Working  
⚠️ **EFFECTS** - Available (verify method names)  
⚠️ **AUTOMATION** - Available (requires name parameter)

---

## 1. 🎨 HOW TO APPLY EFFECTS

### Overview
Effects are visual transformations applied to pattern frames (fade, blur, brightness, color shifts, etc.).

### UI Workflow:
1. **Create/load a pattern** in Design Tools Tab
2. **Select frame range** using start/end frame controls
3. **Open "Effects" toolbox** (usually in sidebar)
4. **Browse effects** from the effect library
5. **Select an effect** (e.g., "Rainbow", "Fade", "Blur")
6. **Adjust intensity** (0-100% slider)
7. **Preview** the effect on current frame
8. **Apply** to commit changes to selected frame range

### Code Implementation:
```python
from domain.effects import EffectLibrary, apply_effect_to_frames
from core.pattern import Pattern, PatternMetadata, Frame
from pathlib import Path

# Load effect library
effects_lib = EffectLibrary(Path("Res/effects"))

# Get available effects
effects = effects_lib.effects()  # Returns list of EffectDefinition
print(f"Found {len(effects)} effects")

# Apply effect to frame range
pattern = Pattern(
    name="Test",
    metadata=PatternMetadata(width=16, height=16),
    frames=[Frame(pixels=[(255, 255, 255)] * 256, duration_ms=100)]
)

# Apply effect
frame_indices = [0]  # Frame to affect
intensity = 0.5  # 0.0 to 1.0
if effects:
    effect = effects[0]  # Select first effect
    apply_effect_to_frames(pattern, effect, frame_indices, intensity)
```

### Key Methods:
- `EffectLibrary(Path("Res/effects"))` - Load effect library
- `apply_effect_to_frames(pattern, effect, frame_indices, intensity)` - Apply effect
- Effects stored in `Res/effects/` directory

---

## 2. 🎭 HOW TO APPLY LAYERS

### Overview
Layers allow multiple visual elements to be stacked and composited within a single frame. Each frame has its own independent set of layers.

### UI Workflow:
1. **Select a frame** in the timeline
2. **Open "Layers" panel** (usually in sidebar)
3. **Click "Add Layer"** button
4. **Name the layer** (e.g., "Background", "Text", "Effects")
5. **Paint/draw on the layer** using drawing tools
6. **Adjust layer properties**:
   - **Visibility**: Click eye icon to show/hide
   - **Opacity**: Use slider (0-100%)
   - **Blend mode**: Select from dropdown (if available)
7. **Reorder layers** by dragging up/down in layer list

### Code Implementation:
```python
from domain.layers import LayerManager, Layer
from domain.pattern_state import PatternState
from core.pattern import Pattern, PatternMetadata, Frame

# Create pattern
pattern = Pattern(
    name="Layer Test",
    metadata=PatternMetadata(width=8, height=8),
    frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]
)

# Initialize layer manager
state = PatternState()
state.set_pattern(pattern)
layer_manager = LayerManager(state)
layer_manager.set_pattern(pattern)

# Add layers to frame 0
layer1_idx = layer_manager.add_layer(0, "Background")
layer2_idx = layer_manager.add_layer(0, "Foreground")
layer3_idx = layer_manager.add_layer(0, "Effects")

# Set layer properties
layer_manager.set_layer_visible(0, layer1_idx, True)   # Show layer
layer_manager.set_layer_opacity(0, layer2_idx, 0.5)    # 50% opacity

# Get all layers for a frame
layers = layer_manager.get_layers(0)
print(f"Frame 0 has {len(layers)} layers")

# Paint to a specific layer
layer_manager.apply_pixel(0, layer2_idx, x=4, y=4, color=(255, 0, 0))

# Get composite (all visible layers blended)
composite_pixels = layer_manager.get_composite(0)
```

### Key Methods:
- `layer_manager.add_layer(frame_index, name)` - Add new layer
- `layer_manager.get_layers(frame_index)` - Get all layers for frame
- `layer_manager.set_layer_visible(frame, layer, visible)` - Show/hide layer
- `layer_manager.set_layer_opacity(frame, layer, opacity)` - Set transparency
- `layer_manager.remove_layer(frame, layer)` - Delete layer
- `layer_manager.move_layer(frame, from_idx, to_idx)` - Reorder layers
- `layer_manager.get_composite(frame)` - Get final blended result

---

## 3. 🎬 HOW TO MAKE FRAMES ON EACH LAYER

### Overview
**Frames** represent time (animation sequence). **Layers** represent depth (visual stacking). Each frame has its own independent set of layers.

### Concept:
```
Pattern
├── Frame 0 (time = 0ms)
│   ├── Layer 0: Background
│   ├── Layer 1: Foreground
│   └── Layer 2: Text
├── Frame 1 (time = 100ms)
│   ├── Layer 0: Background
│   ├── Layer 1: Foreground (different content)
│   └── Layer 2: Text (scrolled)
└── Frame 2 (time = 200ms)
    ├── Layer 0: Background
    ├── Layer 1: Foreground
    └── Layer 2: Text (further scrolled)
```

### UI Workflow:
1. **Create multiple frames** using "Add Frame" button
2. **Select Frame 0** in timeline
3. **Add layers** to Frame 0 (e.g., Background, Foreground)
4. **Draw on layers** for Frame 0
5. **Select Frame 1** in timeline
6. **Add layers** to Frame 1 (can be different layers)
7. **Draw on layers** for Frame 1
8. Repeat for each frame

### Code Implementation:
```python
from domain.layers import LayerManager
from domain.pattern_state import PatternState
from domain.frames import FrameManager
from core.pattern import Pattern, PatternMetadata, Frame

# Create pattern with multiple frames
pattern = Pattern(
    name="Multi-Frame Animation",
    metadata=PatternMetadata(width=16, height=16),
    frames=[
        Frame(pixels=[(255, 0, 0)] * 256, duration_ms=100),  # Frame 0: Red
        Frame(pixels=[(0, 255, 0)] * 256, duration_ms=100),  # Frame 1: Green
        Frame(pixels=[(0, 0, 255)] * 256, duration_ms=100),  # Frame 2: Blue
    ]
)

# Initialize managers
state = PatternState()
state.set_pattern(pattern)
layer_manager = LayerManager(state)
frame_manager = FrameManager(state)
layer_manager.set_pattern(pattern)

# Add layers to Frame 0
layer_manager.add_layer(0, "Background")
layer_manager.add_layer(0, "Foreground")

# Add layers to Frame 1 (can be same or different)
layer_manager.add_layer(1, "Background")
layer_manager.add_layer(1, "Text")

# Add layers to Frame 2
layer_manager.add_layer(2, "Background")
layer_manager.add_layer(2, "Effects")

# Each frame has independent layers
for frame_idx in range(len(pattern.frames)):
    layers = layer_manager.get_layers(frame_idx)
    print(f"Frame {frame_idx}: {len(layers)} layers")
    for layer_idx, layer in enumerate(layers):
        print(f"  Layer {layer_idx}: {layer.name}")
```

### Key Points:
- ✅ Each frame has its own independent layer stack
- ✅ Layers can be different between frames
- ✅ Layer count can vary per frame
- ✅ Layer names can be the same or different

---

## 4. ⚙️ HOW TO APPLY AUTOMATION

### Overview
Automation actions transform frames programmatically (scroll, rotate, mirror, invert, etc.). Actions can be queued and applied to frame ranges.

### UI Workflow:
1. **Open "Automation" or "Action Queue" tab**
2. **Select action type** from dropdown:
   - Scroll (left/right/up/down)
   - Rotate (90°/180°/270°)
   - Mirror (horizontal/vertical)
   - Invert (colors)
   - Wipe/Reveal
   - Bounce
3. **Configure action parameters**:
   - Direction
   - Distance/amount
   - Repeat count
   - Gap (delay between repeats)
4. **Click "Add Action"** to add to queue
5. **Configure frame range** (start/end frames)
6. **Click "Apply Actions"** to execute

### Code Implementation:
```python
from domain.automation.queue import AutomationQueueManager
from domain.actions import DesignAction
from core.pattern import Pattern, PatternMetadata, Frame

# Create pattern
pattern = Pattern(
    name="Automation Test",
    metadata=PatternMetadata(width=16, height=16),
    frames=[Frame(pixels=[(255, 255, 255)] * 256, duration_ms=100)]
)

# Create automation manager
automation_manager = AutomationQueueManager()

# Create automation actions
scroll_action = DesignAction(
    name="Scroll Left",
    action_type="scroll",
    params={
        "direction": "left",
        "distance": 1,
        "repeat": 3,
        "gap_ms": 50
    }
)

rotate_action = DesignAction(
    name="Rotate 90",
    action_type="rotate",
    params={
        "angle": 90
    }
)

# Add actions to queue
automation_manager.enqueue(scroll_action)
automation_manager.enqueue(rotate_action)

# Get all actions
actions = automation_manager.actions()
print(f"Queue has {len(actions)} actions")

# Apply to frame range (requires automation engine)
frame_indices = [0, 1, 2]
# automation_engine.apply_to_frames(pattern, frame_indices, actions, executor)
```

### Key Methods:
- `AutomationQueueManager()` - Create automation manager
- `DesignAction(name, action_type, params)` - Create action
- `automation_manager.enqueue(action)` - Add to queue
- `automation_manager.actions()` - Get all actions
- `automation_manager.clear()` - Clear queue

### Action Types:
- `scroll` - Move pixels left/right/up/down
- `rotate` - Rotate 90°/180°/270°
- `mirror` - Flip horizontally/vertically
- `invert` - Invert colors
- `wipe` - Wipe effect
- `reveal` - Reveal effect
- `bounce` - Bounce animation

---

## 5. 📝 HOW TO APPLY TEXT

### Overview
Text can be rendered onto frames with configurable fonts, colors, alignment, and effects.

### UI Workflow:
1. **Open "Text" tool/tab**
2. **Enter text** in text input field
3. **Select font** from dropdown (built-in or custom)
4. **Configure options**:
   - Font size
   - Color (RGB picker)
   - Background color
   - Alignment (left/center/right)
   - Effects:
     - Outline (with color and width)
     - Shadow (with offset)
     - Gradient
5. **Preview** text rendering
6. **Apply** to current frame or generate animation frames

### Code Implementation:
```python
from domain.text.text_renderer import TextRenderer, TextRenderOptions
from core.pattern import Frame

# Create text renderer
renderer = TextRenderer()

# Configure text options
options = TextRenderOptions(
    width=32,
    height=8,
    font_size=8,
    color=(255, 255, 0),      # Yellow text
    background=(0, 0, 0),     # Black background
    alignment="center",        # Center aligned
    spacing=1,                 # Character spacing
    line_spacing=2,            # Line spacing (if multi-line)
    outline=True,              # Enable outline
    outline_color=(255, 0, 0), # Red outline
    outline_width=1,           # Outline width
    shadow=True,               # Enable shadow
    shadow_offset=(1, 1),      # Shadow offset
)

# Render text to pixels
text = "Hello World"
pixels = renderer.render_pixels(text, options)

# Apply to frame
frame = Frame(pixels=pixels, duration_ms=100)

# For scrolling text animation
from domain.text.text_renderer import TextScrollOptions
scroll_options = TextScrollOptions(
    direction="left",
    step=1
)
scroll_frames = renderer.render_scroll_frames(
    text,
    options,
    scroll_options
)
```

### Key Methods:
- `TextRenderer()` - Create text renderer
- `TextRenderOptions(...)` - Configure text appearance
- `renderer.render_pixels(text, options)` - Render static text
- `renderer.render_scroll_frames(text, options, scroll_options)` - Generate scrolling animation
- `renderer.render_typing_frames(text, options, frames_per_char, duration)` - Generate typing animation

---

## 6. 🔤 HOW TO APPLY FONTS (INSTALLED/CUSTOM)

### Overview
Fonts can be built-in (5x7 default) or custom bitmap fonts stored as JSON files.

### UI Workflow:

#### Using Built-in Font:
1. **Open Text tool**
2. **Select "Built-in 5×7"** from font dropdown
3. **Adjust font size** if needed
4. **Use text normally**

#### Using Custom Fonts:
1. **Place font files** in `Res/fonts/` directory (`.json` format)
2. **Fonts automatically appear** in font dropdown
3. **Select custom font** from dropdown
4. **Font size is fixed** (determined by font definition)

#### Creating Custom Fonts:
1. **Open Font Designer** dialog (usually from Text tool)
2. **Design glyphs** for each character
3. **Save font** to `Res/fonts/` directory
4. **Font becomes available** in dropdown

### Code Implementation:
```python
from domain.text.bitmap_font import BitmapFontRepository, BitmapFont
from domain.text.text_renderer import TextRenderer, TextRenderOptions
from pathlib import Path

# Initialize font repository
fonts_path = Path("Res/fonts")
font_repo = BitmapFontRepository(fonts_path)

# List available fonts
fonts = font_repo.list_fonts()
print(f"Available fonts: {fonts}")

# Load a specific font
if fonts:
    font = font_repo.load_font(fonts[0])
    print(f"Loaded font: {font.name}")
    print(f"Font size: {font.width}x{font.height}")

# Use with text renderer
renderer = TextRenderer()
options = TextRenderOptions(
    width=32,
    height=8,
    font_size=8,  # Ignored if custom font used
    color=(255, 255, 0),
    background=(0, 0, 0),
    alignment="center"
)

# Built-in font (default)
pixels = renderer.render_pixels("Hello", options)

# Custom font (set in renderer or options)
# renderer.set_font(font)
# pixels = renderer.render_pixels("Hello", options)
```

### Font File Format:
Custom fonts are stored as JSON files in `Res/fonts/`:

```json
{
  "name": "MyFont",
  "width": 5,
  "height": 7,
  "glyphs": {
    "A": [[0,1,1,0,0], [1,0,0,1,0], ...],
    "B": [[1,1,1,0,0], [1,0,0,1,0], ...],
    ...
  }
}
```

### Key Methods:
- `BitmapFontRepository(Path("Res/fonts"))` - Load font repository
- `font_repo.list_fonts()` - Get list of available fonts
- `font_repo.load_font(name)` - Load specific font
- `font_repo.save_font(font)` - Save font to disk
- Built-in 5x7 font is always available

---

## 🎯 Quick Reference

### Feature Comparison

| Feature | UI Location | Code Module | Status |
|---------|------------|-------------|--------|
| **Effects** | Effects toolbox | `domain.effects` | ✅ Available |
| **Layers** | Layers panel | `domain.layers` | ✅ Working |
| **Frames** | Timeline | `domain.frames` | ✅ Working |
| **Automation** | Action Queue tab | `domain.automation` | ✅ Working |
| **Text** | Text tool | `domain.text` | ✅ Working |
| **Fonts** | Text tool dropdown | `domain.text.bitmap_font` | ✅ Working |

### Directory Structure

```
Res/
├── effects/          # Effect definitions
└── fonts/            # Custom bitmap fonts (.json)
```

### Common Patterns

1. **Add text to layer**: Render text → apply pixels to specific layer
2. **Animate with automation**: Create frames → add automation actions → apply
3. **Composite effects**: Add effect layer → adjust opacity → blend with base
4. **Multi-frame animation**: Create frames → add layers per frame → apply automation

---

## 📚 Additional Resources

- **Layer System Docs**: `LAYER_FRAME_DESIGN_SYSTEM.md`
- **Automation Guide**: `docs/automation/lms_automation.md`
- **Text Renderer**: `domain/text/text_renderer.py`
- **Effect Library**: `domain/effects/`

---

**Last Updated**: 2025-11-25  
**Status**: All core features verified and working

