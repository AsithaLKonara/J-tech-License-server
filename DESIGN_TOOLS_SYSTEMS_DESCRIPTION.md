# Design Tools Tab - System Descriptions

## Overview

The Design Tools tab is a comprehensive LED matrix design studio that provides five major systems for creating and manipulating patterns:

1. **Layer System** - Multi-layer composition per frame
2. **Frame System** - Animation timeline management
3. **Automation System** - Parametric action sequences
4. **Effect Application System** - Procedural effect application
5. **Effect Library** - Effect discovery and management

---

## 1. Layer System

### Architecture

The layer system is managed by the `LayerManager` class (`domain/layers.py`), which provides multi-layer support for each frame in a pattern.

### Key Components

#### Layer Class
- **Purpose**: Represents a single layer within a frame
- **Properties**:
  - `name`: Layer name (e.g., "Layer 1", "Background")
  - `pixels`: List of RGB color tuples `(r, g, b)`
  - `visible`: Boolean visibility flag
  - `opacity`: Float value 0.0-1.0 (0 = transparent, 1 = opaque)
  - `blend_mode`: String ("normal", "add", "multiply", "screen")
  - `group_id`: Optional UUID string for layer grouping
  - `mask`: Optional per-pixel mask (List[float] 0.0-1.0)

#### LayerManager Class
- **Purpose**: Manages layers for all frames in a pattern
- **Storage**: `{frame_index: [Layer, ...]}` dictionary
- **Features**:
  - Multiple layers per frame
  - Independent visibility control
  - Opacity adjustment (0.0-1.0)
  - Layer reordering (move up/down)
  - Layer grouping
  - Per-pixel masking
  - Blend mode composition

### How It Works

1. **Initialization**:
   - When a pattern is loaded, each frame gets a default "Layer 1" containing the frame's pixels
   - Layers are stored separately from frames but sync to frames for display

2. **Layer Operations**:
   ```python
   # Add a new layer
   layer_manager.add_layer(frame_index=0, name="Background")
   
   # Set layer visibility
   layer_manager.set_layer_visible(frame_index=0, layer_index=1, visible=False)
   
   # Adjust opacity
   layer_manager.set_layer_opacity(frame_index=0, layer_index=0, opacity=0.5)
   
   # Reorder layers
   layer_manager.move_layer(frame_index=0, from_index=1, to_index=0)
   
   # Remove layer (can't remove last layer)
   layer_manager.remove_layer(frame_index=0, layer_index=1)
   ```

3. **Composition**:
   - `get_composite_pixels()` blends all visible layers using blend modes
   - Layers are composited from bottom to top
   - Supports blend modes: normal, add, multiply, screen
   - Group opacity multiplies with layer opacity
   - Masks are applied per-pixel before blending

4. **Synchronization**:
   - `sync_frame_from_layers()` updates frame pixels from layer composite
   - Called automatically when layers change
   - Canvas displays the composite result

### Layer Groups

- **Purpose**: Organize multiple layers together
- **Features**:
  - Group visibility control (hides/shows all layers in group)
  - Group opacity (multiplies with individual layer opacity)
  - Layers can be added/removed from groups

### Usage in Design Tools Tab

- **Layer Panel**: UI component showing layer list for current frame
- **Layer Controls**: Visibility toggles, opacity sliders, reorder buttons
- **Painting**: Paints to the active layer (default: layer 0)
- **Composition**: Canvas shows composite of all visible layers

---

## 2. Frame System

### Architecture

The frame system is managed by the `FrameManager` class (`domain/frames.py`), which handles animation timeline operations.

### Key Components

#### FrameManager Class
- **Purpose**: Manages frames (animation timeline) for a pattern
- **Storage**: Frames stored in `Pattern.frames` list
- **Current Frame**: Tracks which frame is currently selected/edited
- **Signals**: Emits Qt signals for UI updates:
  - `frames_changed`: Frames list modified
  - `frame_index_changed`: Current frame changed
  - `frame_duration_changed`: Frame duration modified

### How It Works

1. **Frame Structure**:
   ```python
   Frame(
       pixels=[(r, g, b), ...],  # LED colors
       duration_ms=50             # Display duration in milliseconds
   )
   ```

2. **Frame Operations**:
   ```python
   # Add blank frame after current
   frame_manager.add_blank_after_current(duration_ms=100)
   
   # Duplicate current frame
   frame_manager.duplicate(index=0)
   
   # Delete frame (requires at least 1 frame)
   frame_manager.delete(index=1)
   
   # Move frame (reorder)
   frame_manager.move(src=2, dest=0)
   
   # Set frame duration
   frame_manager.set_duration(index=0, duration_ms=200)
   
   # Select frame
   frame_manager.select(index=3)
   ```

3. **Timeline Management**:
   - Frames are displayed in a timeline widget
   - Current frame is highlighted
   - Frame thumbnails show preview
   - Duration displayed on each frame

4. **Frame Selection**:
   - Clicking a frame in timeline selects it
   - Canvas updates to show selected frame
   - Layer panel updates for selected frame
   - Each frame has its own layer stack

### Usage in Design Tools Tab

- **Timeline Widget**: Visual representation of all frames
- **Frame Controls**: Add, duplicate, delete, reorder buttons
- **Duration Editor**: Adjust frame display time
- **Frame Navigation**: Previous/Next buttons, frame selector
- **Playback**: Preview animation by playing frames sequentially

### Frame-Layer Relationship

- **Each frame has its own layer stack**
- Layers are independent per frame
- Frame 0 might have 3 layers, Frame 1 might have 2 layers
- When duplicating a frame, all its layers are duplicated

---

## 3. Automation System

### Architecture

The automation system uses parametric actions to generate animation sequences automatically. It's managed by `AutomationQueueManager` and uses `ParametricAction` classes.

### Key Components

#### ParametricAction Class (`domain/automation/parametric_actions.py`)
- **Purpose**: Deterministic, testable automation actions
- **Action Types**:
  - `SCROLL`: Scroll pixels in direction (left, right, up, down)
  - `ROTATE`: Rotate 90° clockwise
  - `MIRROR`: Mirror along axis (horizontal, vertical)
  - `FLIP`: Flip pixels (same as mirror)
  - `INVERT`: Invert colors (255-r, 255-g, 255-b)
  - `WIPE`: Wipe effect with color
  - `REVEAL`: Reveal effect (opposite of wipe)
  - `BOUNCE`: Oscillating scroll effect

#### ActionParameters
- `direction`: String ("left", "right", "up", "down")
- `speed`: Float multiplier (1.0 = normal)
- `distance`: Integer pixels/frames to move
- `axis`: String ("horizontal", "vertical")
- `color`: Optional RGB tuple for wipe/reveal
- `easing`: String ("linear", etc.)

#### AutomationQueueManager
- **Purpose**: Manages queue of automation actions
- **Features**:
  - Add/remove/reorder actions
  - Preview actions before applying
  - Apply actions to frame range
  - Convert to LMS pattern instructions

### How It Works

1. **Action Queue**:
   ```python
   # Add action to queue
   automation_manager.append(DesignAction(
       name="Scroll Right",
       action_type="scroll",
       params={"direction": "Right", "offset": 1}
   ))
   
   # Actions are queued, not immediately applied
   # User can preview, reorder, or remove actions
   ```

2. **Action Application**:
   ```python
   # Apply actions to selected frame range
   _apply_actions_to_frames(finalize=False)
   
   # Actions are applied sequentially to each frame
   # Each action transforms the frame pixels
   # Result is animated sequence
   ```

3. **Action Types**:

   **Scroll**:
   - Moves pixels in specified direction
   - Wraps around edges (circular scroll)
   - Distance increases per frame for animation

   **Rotate**:
   - Rotates entire frame 90° clockwise
   - Matrix dimensions may swap (width ↔ height)

   **Mirror/Flip**:
   - Reflects pixels along axis
   - Horizontal: left ↔ right
   - Vertical: top ↔ bottom

   **Invert**:
   - Inverts each pixel color
   - (r, g, b) → (255-r, 255-g, 255-b)

   **Wipe**:
   - Progressive color fill in direction
   - Creates wipe animation effect
   - Uses specified color

   **Reveal**:
   - Progressive reveal of original pixels
   - Opposite of wipe
   - Reveals from edge

   **Bounce**:
   - Oscillating scroll (back and forth)
   - Uses sine wave for smooth motion
   - Creates bouncing animation

4. **Frame Generation**:
   - Actions can generate multiple frames automatically
   - Each frame shows one step of the animation
   - Duration can be set per frame or globally

### Usage in Design Tools Tab

- **Automation Tab**: Dedicated tab for automation controls
- **Action Queue Panel**: Shows queued actions with controls
- **Action Buttons**: Quick buttons for common actions
- **Automation Wizard**: Dialog for creating complex sequences
- **Preview**: Preview automation before applying
- **Finalize**: Convert to LMS pattern instructions for MCU export

### Automation Presets

- Pre-configured action sequences
- Stored in `automation_presets.json`
- Can be saved/loaded
- Examples: "Rainbow Scroll", "Pulse", "Wave"

---

## 4. Effect Application System

### Architecture

The effect application system uses procedural effects to modify pattern frames. It's managed by the `EffectsEngine` and uses `EffectDefinition` objects.

### Key Components

#### EffectDefinition (`domain/effects/models.py`)
- **Purpose**: Defines a procedural effect
- **Properties**:
  - `identifier`: Unique effect ID
  - `name`: Human-readable name
  - `category`: Effect category (e.g., "Color", "Motion")
  - `source_path`: Path to effect file
  - `preview_path`: Path to preview image
  - `keywords`: List of searchable keywords

#### EffectsEngine (`domain/effects/engine.py`)
- **Purpose**: High-level effects engine interface
- **Features**:
  - Effect library management
  - Effect application to patterns
  - Effect preview generation
  - Deterministic effect processing

#### apply_effect_to_frames() (`domain/effects/apply.py`)
- **Purpose**: Applies procedural effect to frame range
- **Process**:
  1. Builds color palette from effect keywords
  2. Derives style (radial, horizontal, vertical, mirrored, gradient)
  3. Applies style to pixels with intensity blending
  4. Generates deterministic, visually pleasing overlays

### How It Works

1. **Effect Selection**:
   ```python
   # Get effect from library
   effect = effects_library.get_effect("rainbow_wave")
   
   # Or browse by category
   effects = effects_library.effects_by_category("Color")
   ```

2. **Effect Application**:
   ```python
   # Apply to frame range
   apply_effect_to_frames(
       pattern=pattern,
       effect=effect,
       frame_indices=[0, 1, 2, 3],
       intensity=0.7  # 0.0-1.0
   )
   ```

3. **Effect Processing**:
   - **Palette Building**: Extracts colors from effect keywords
     - Keywords like "red", "blue", "green" map to colors
     - Falls back to default palette if none found
   - **Style Derivation**: Determines effect style from keywords
     - "radial", "burst" → radial style
     - "mirror", "symmetrical" → mirrored style
     - "down", "up" → vertical style
     - "left", "right" → horizontal style
     - "gradient", "color" → gradient style
   - **Pixel Transformation**:
     - Samples position based on style
     - Samples color from palette gradient
     - Blends with existing pixels using intensity

4. **Intensity Control**:
   - `intensity=0.0`: No effect (original pixels)
   - `intensity=0.5`: 50% blend
   - `intensity=1.0`: Full effect (replaces pixels)
   - Blending formula: `pixel = base * (1-intensity) + effect * intensity`

5. **Deterministic Behavior**:
   - Same effect + same pattern = same result
   - Uses effect identifier as random seed
   - Ensures reproducible effects

### Usage in Design Tools Tab

- **Effects Panel**: Shows available effects by category
- **Effect Preview**: Thumbnail preview before applying
- **Frame Range Selection**: Select start/end frames
- **Intensity Slider**: Control effect strength (0-100%)
- **Apply Button**: Apply effect to selected frame range
- **Preview Button**: Preview effect without committing

### Effect Types

Effects are categorized by their visual style:

- **Color Effects**: Rainbow, gradient, color cycle
- **Motion Effects**: Wave, scroll, pulse
- **Radial Effects**: Burst, spiral, radial gradient
- **Pattern Effects**: Checkerboard, stripes, dots

---

## 5. Effect Library

### Architecture

The effect library (`domain/effects/library.py`) discovers and manages effect definitions from the filesystem.

### Key Components

#### EffectLibrary Class
- **Purpose**: Discovers effect assets and exposes them as `EffectDefinition`s
- **Root Directory**: `Res/effects/` (configurable)
- **Supported Formats**: `.swf`, `.json`, `.yaml`, `.yml`
- **Preview Formats**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`

### How It Works

1. **Effect Discovery**:
   ```python
   # Initialize library
   library = EffectLibrary(Path("Res/effects"))
   
   # Scan for effects
   library.reload()  # Scans filesystem
   
   # Get all effects
   effects = library.effects()
   ```

2. **File Structure**:
   ```
   Res/effects/
     Color/
       rainbow_wave.swf
       rainbow_wave.json        # Metadata
       rainbow_wave.png         # Preview
     Motion/
       scroll_left.swf
       scroll_left.json
   ```

3. **Metadata Loading**:
   - Looks for `.json`, `.yaml`, `.yml` files with same name
   - Metadata can override:
     - `name`: Effect display name
     - `category`: Effect category
     - `keywords`: Search keywords
     - `preview`: Preview image path

4. **Category Derivation**:
   - Uses parent directory name as category
   - Falls back to "Uncategorised" if no category
   - Filters out language folders ("effect_en", "effects")

5. **Preview Discovery**:
   - Checks metadata for `preview` field
   - Looks for image with same name (different extension)
   - Falls back to `preview.png` in same folder
   - Returns `None` if no preview found

6. **Keyword Extraction**:
   - Extracts keywords from filename (split by `_`, `-`)
   - Adds category words
   - Normalizes to lowercase
   - Used for search and palette building

### Usage in Design Tools Tab

- **Effect Browser**: Shows effects organized by category
- **Search**: Search effects by name/keywords
- **Preview Thumbnails**: Shows effect preview images
- **Refresh Button**: Reload effects from filesystem
- **Custom Effects**: Can add custom effects to library

### Adding New Effects

1. **Drop Files**: Place effect files in `Res/effects/` subdirectory
2. **Add Metadata** (optional): Create `.json` file:
   ```json
   {
     "name": "My Custom Effect",
     "category": "Custom",
     "keywords": ["custom", "special"],
     "preview": "preview.png"
   }
   ```
3. **Refresh**: Click refresh button in UI
4. **Use**: Effect appears in library, ready to use

### Effect Categories

Common categories:
- **Color**: Color-based effects
- **Motion**: Movement/animation effects
- **Radial**: Radial/center-based effects
- **Pattern**: Pattern/texture effects
- **Custom**: User-defined effects

---

## System Integration

### How Systems Work Together

1. **Frame + Layer**:
   - Each frame has its own layer stack
   - Canvas shows composite of current frame's layers
   - Painting affects active layer of current frame

2. **Frame + Automation**:
   - Automation actions are applied to frame range
   - Each frame gets transformed by actions
   - Creates animated sequence

3. **Frame + Effects**:
   - Effects are applied to frame range
   - Effects blend with existing pixels
   - Can be applied to specific layers

4. **Automation + Effects**:
   - Can combine automation and effects
   - Apply effect, then automate
   - Or automate, then apply effect

5. **Layer + Effects**:
   - Effects can target specific layers
   - Layer opacity affects effect visibility
   - Blend modes affect effect appearance

### Workflow Examples

**Example 1: Multi-Layer Animation**
1. Create pattern with 10 frames
2. Frame 0: Add "Background" layer (solid color)
3. Frame 0: Add "Foreground" layer (pattern)
4. Set foreground opacity to 0.5
5. Duplicate frame 0 to frames 1-9
6. Apply scroll automation to foreground layer
7. Result: Animated pattern over semi-transparent background

**Example 2: Effect + Automation**
1. Create pattern with 5 frames
2. Apply "Rainbow Wave" effect to all frames
3. Apply scroll automation (right, 1 pixel)
4. Result: Rainbow wave scrolling animation

**Example 3: Complex Composition**
1. Create pattern with 20 frames
2. Frame 0: Background layer (gradient)
3. Frame 0: Text layer (bitmap font)
4. Frame 0: Effect layer (pulse effect)
5. Duplicate to all frames
6. Apply bounce automation to text layer
7. Apply intensity animation to effect layer
8. Result: Bouncing text with pulsing effect over gradient

---

## Technical Details

### Performance Considerations

- **Layer Composition**: Computed on-demand, cached when possible
- **Effect Application**: Procedural (fast), no external dependencies
- **Frame Management**: Efficient list operations
- **Automation**: Deterministic, optimized pixel operations

### Memory Management

- **Layers**: Stored per-frame, cleared when pattern unloaded
- **Frames**: Stored in pattern object, managed by repository
- **Effects**: Lightweight definitions, loaded on-demand
- **Automation**: Queue stored in memory, cleared on apply

### Undo/Redo Support

- All operations support undo/redo
- Layer changes tracked
- Frame changes tracked
- Effect applications tracked
- Automation applications tracked

---

## Summary

The Design Tools tab provides a powerful, integrated system for creating LED matrix patterns:

- **Layers**: Multi-layer composition with blending and masking
- **Frames**: Animation timeline with duration control
- **Automation**: Parametric action sequences for animation
- **Effects**: Procedural effects with intensity control
- **Library**: Discoverable effect library with metadata

All systems work together seamlessly, allowing users to create complex, animated LED patterns with professional-quality tools.

