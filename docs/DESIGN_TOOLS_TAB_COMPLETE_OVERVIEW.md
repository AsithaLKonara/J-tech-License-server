# Design Tools Tab - Complete Feature & Linkage Overview

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Scope**: Complete feature inventory, linkages, and workflows for the Design Tools Tab

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Managers & Components](#core-managers--components)
3. [Feature Inventory](#feature-inventory)
4. [Feature Linkages & Data Flow](#feature-linkages--data-flow)
5. [UI Components Mapping](#ui-components-mapping)
6. [Signal/Event Connections](#signalevent-connections)
7. [Key Workflows](#key-workflows)
8. [Pattern State Management](#pattern-state-management)
9. [Timeline Integration](#timeline-integration)
10. [Canvas & Drawing System](#canvas--drawing-system)

---

## Architecture Overview

The Design Tools Tab follows a **Model-View-Controller (MVC)** pattern with managers handling domain logic:

```
DesignToolsTab (View/Controller)
    ├── PatternState (Model - Single Source of Truth)
    ├── FrameManager (Frame Operations)
    ├── LayerManager (Multi-layer Support)
    ├── CanvasController (Canvas Rendering)
    ├── AutomationQueueManager (Automation Actions)
    ├── HistoryManager (Undo/Redo)
    ├── ScratchpadManager (Temporary Storage)
    ├── EffectLibrary (Visual Effects)
    ├── BitmapFontRepository (Font Assets)
    ├── ImageImporter (Image/GIF Import)
    ├── Export/Import System (File I/O Utilities)
    └── PresetRepository (Automation Presets)
    
Data Structures:
    └── PatternInstructionSequence (LMS Instruction Collection)
```

### Data Flow Pattern

```
User Action (UI Event)
    ↓
Manager Method (Domain Logic)
    ↓
PatternState Update (Model Change)
    ↓
Signal Emitted (State Change Notification)
    ↓
UI Update (View Refresh)
```

---

## Core Managers & Components

### 1. PatternState (`domain/pattern_state.py`)

**Role**: Single source of truth for the active pattern

**Responsibilities**:
- Holds the current `Pattern` object
- Provides accessors for frames, metadata, dimensions
- Emits signals when pattern changes

**Key Methods**:
```python
def pattern() -> Pattern              # Get current pattern
def frames() -> list[Frame]          # Get all frames
def metadata() -> PatternMetadata    # Get pattern metadata
def width() -> int                   # Get matrix width
def height() -> int                  # Get matrix height
def set_pattern(pattern: Pattern)    # Load new pattern
```

**Linkages**:
- Used by: FrameManager, LayerManager, CanvasController
- Updates from: File load, new pattern creation, dimension changes

**Usage Examples**:
```python
# Get current pattern and check if it exists
pattern = pattern_state.pattern()
if pattern is None:
    # No pattern loaded, disable operations
    return

# Get pattern dimensions
width = pattern_state.width()   # Returns int, e.g., 16
height = pattern_state.height()  # Returns int, e.g., 16

# Get all frames
frames = pattern_state.frames()  # Returns list[Frame]

# Get pattern metadata
metadata = pattern_state.metadata()  # Returns PatternMetadata object

# Set new pattern (typically called during load)
new_pattern = Pattern.create_blank(width=32, height=32, frames=5)
pattern_state.set_pattern(new_pattern)
# All managers are notified and updated
```

---

### 2. FrameManager (`domain/frames.py`)

**Role**: Manages frame operations (add, delete, duplicate, move, duration)

**Responsibilities**:
- Frame CRUD operations
- Frame selection tracking
- Duration management
- Frame index management

**Key Methods**:
```python
def add() -> int                              # Add new blank frame
def duplicate(index: int) -> int              # Duplicate frame
def delete(index: int) -> None                # Delete frame
def move(src: int, dest: int) -> None         # Reorder frames
def select(index: int) -> None                # Select active frame
def set_duration(index: int, ms: int) -> None # Set frame duration
def frame(index: int) -> Frame                # Get frame by index
```

**Signals**:
- `frame_index_changed.emit(int)` - Emitted when frame selection changes
- `frame_duration_changed.emit(int, int)` - Emitted when duration changes (frame_index, duration_ms)

**Linkages**:
- Updates: PatternState
- Triggers: Timeline refresh, canvas update, layer panel update
- Connected to: Timeline widget (selection), frame controls (add/delete/duplicate)

**Usage Examples**:
```python
# Add a new blank frame after current frame
new_frame_index = frame_manager.add_blank_after_current(duration_ms=100)
# Returns the index of the newly created frame
# Emits frames_changed signal automatically

# Select a specific frame
frame_manager.select(2)  # Selects frame at index 2
# Emits frame_index_changed signal automatically

# Get current frame
current_frame = frame_manager.frame()  # Returns Frame object
# Uses current_index() internally

# Duplicate current frame
duplicate_index = frame_manager.duplicate()  # Duplicates current frame
# Returns index of duplicate frame
# Emits frames_changed signal

# Delete a frame (with validation)
frame_manager.delete(1)  # Deletes frame at index 1
# Validates: won't delete if it's the last frame
# Emits frames_changed signal

# Move/reorder frames
frame_manager.move(src_index=0, dest_index=2)  # Moves frame 0 to position 2
# Emits frames_changed signal

# Set frame duration
frame_manager.set_duration(frame_index=0, duration_ms=200)
# Emits frame_duration_changed signal
```

---

### 3. LayerManager (`domain/layers.py`)

**Role**: Multi-layer management per frame with compositing

**Responsibilities**:
- Layer CRUD (create, read, update, delete)
- Layer visibility and opacity
- Pixel-level editing per layer
- Composite rendering (blending all visible layers)

**Key Methods**:
```python
def get_layers(frame_index: int) -> List[Layer]           # Get all layers for frame
def add_layer(frame_index: int, name: str) -> int         # Add new layer
def remove_layer(frame_index: int, layer_index: int)      # Remove layer
def apply_pixel(frame_index: int, x: int, y: int, colour: Optional[Color], width: int, height: int, layer_index: int = 0) -> None  # Paint pixel on layer
def get_composite_pixels(frame_index: int) -> List[RGB]   # Get blended result
def sync_frame_from_layers(frame_index: int)              # Update frame from layers
def resize_pixels(width: int, height: int)                # Resize all layers
def replace_pixels(frame_index: int, pixels, layer_index: int = 0) -> None  # Replace all pixels in layer
def move_layer(frame_index: int, from_index: int, to_index: int) -> bool  # Reorder layers
```

**Signals**:
- `layers_changed.emit(int)` - Emitted when layer structure changes
- `layer_added.emit(int, int)` - Emitted when layer added (frame_index, layer_index)
- `layer_removed.emit(int, int)` - Emitted when layer removed
- `layer_moved.emit(int, int, int)` - Emitted when layer reordered
- `frame_pixels_changed.emit(int)` - Emitted when layer pixels change

**Linkages**:
- Updates: PatternState (frame pixels via sync)
- Triggers: Canvas refresh, timeline layer tracks update
- Connected to: Layer Panel widget, Timeline layer tracks

**Usage Examples**:
```python
# Get all layers for a frame
layers = layer_manager.get_layers(frame_index=0)
# Returns List[Layer], creates default layer if none exist

# Add a new layer
new_layer_index = layer_manager.add_layer(
    frame_index=0,
    name="Background Layer"
)
# Returns the index of the newly created layer
# Emits layer_added and layers_changed signals

# Apply a pixel to a specific layer
layer_manager.apply_pixel(
    frame_index=0,
    x=5,
    y=10,
    colour=(255, 0, 0),  # Red color
    width=16,  # Pattern width
    height=16,  # Pattern height
    layer_index=0  # Active layer
)
# Updates layer pixel, syncs frame, emits signals

# Get composite (blended) pixels from all visible layers
composite_pixels = layer_manager.get_composite_pixels(frame_index=0)
# Returns List[RGB] with all visible layers alpha-blended
# Used for canvas display

# Sync frame pixels from layers (one-way: layers → frame)
layer_manager.sync_frame_from_layers(frame_index=0)
# Updates PatternState.frame.pixels from layer composite
# Called automatically after pixel changes

# Set layer visibility
layer_manager.set_layer_visible(frame_index=0, layer_index=1, visible=False)
# Hides layer 1 in frame 0
# Emits layers_changed signal

# Set layer opacity
layer_manager.set_layer_opacity(frame_index=0, layer_index=1, opacity=0.5)
# Sets layer 1 to 50% opacity
# Opacity is clamped to 0.0-1.0 range
# Emits layers_changed signal

# Replace all pixels in a layer (useful for bulk operations)
new_pixels = [(255, 255, 255)] * (16 * 16)  # White pixels
layer_manager.replace_pixels(
    frame_index=0,
    pixels=new_pixels,
    layer_index=0
)
# Replaces entire layer pixel array
# Emits frame_pixels_changed signal

# Move/reorder layers
layer_manager.move_layer(
    frame_index=0,
    from_index=1,
    to_index=0
)
# Moves layer 1 to position 0 (top)
# Returns True if successful, False if indices invalid
# Emits layer_moved and layers_changed signals

# Resize all layers (called when pattern dimensions change)
layer_manager.resize_pixels(width=32, height=32)
# Resizes all layers in all frames
# Updates pattern metadata
# Emits frame_pixels_changed signal for all frames
```

---

### 4. CanvasController (`domain/canvas.py`)

**Role**: Controls canvas rendering and interaction

**Responsibilities**:
- Frame rendering to canvas
- Canvas size management
- Provides frame supplier callback

**Key Methods**:
```python
def render_frame(frame_index: int) -> None    # Render frame to canvas
def set_frame_supplier(callback)              # Set callback for frame data
```

**Linkages**:
- Used by: DesignToolsTab for canvas rendering
- Provides: Frame data to canvas widget

**Usage Examples**:
```python
# Render a specific frame to canvas
canvas_controller.render_frame(frame_index=0)
# Loads frame 0 and displays it on canvas

# Set frame supplier callback (for dynamic frame loading)
def get_frame_data(frame_index: int) -> List[RGB]:
    # Custom logic to get frame pixels
    return layer_manager.get_composite_pixels(frame_index)

canvas_controller.set_frame_supplier(get_frame_data)
# Canvas will call this callback when it needs frame data
```

---

### 5. AutomationQueueManager (`domain/automation/queue.py`)

**Role**: Manages automation action queue

**Responsibilities**:
- Action enqueue/dequeue
- Action validation
- Queue serialization

**Key Methods**:
```python
def enqueue(action: DesignAction) -> None     # Add action to queue
def clear() -> None                           # Clear all actions
def actions() -> List[DesignAction]           # Get all actions
def remove(index: int) -> None                # Remove action by index
def move(src: int, dest: int) -> None         # Reorder actions
```

**Signals**:
- `queue_changed.emit(list)` - Emitted when queue changes

**Linkages**:
- Updates: Timeline overlays (action visualization)
- Triggers: Action inspector update, apply/finalize button states
- Connected to: Automation tab UI, Timeline widget

**Usage Examples**:
```python
# Create and enqueue an action
action = DesignAction(
    name="Scroll Left",
    action_type="scroll",
    params={"direction": "Left", "step": 1}
)
automation_manager.enqueue(action)
# Adds action to queue
# Emits queue_changed signal

# Get all actions in queue
actions = automation_manager.actions()  # Returns List[DesignAction]

# Remove an action by index
automation_manager.remove(index=2)  # Removes action at index 2
# Emits queue_changed signal

# Reorder actions
automation_manager.move(src=0, dest=2)  # Moves action 0 to position 2
# Emits queue_changed signal

# Clear all actions
automation_manager.clear()  # Removes all actions
# Emits queue_changed signal
```

---

### 6. HistoryManager (`domain/history.py`)

**Role**: Undo/Redo functionality

**Responsibilities**:
- Command stack management
- Frame-specific history
- Undo/Redo execution

**Key Methods**:
```python
def push_command(cmd, frame_index) -> None    # Save command to history
def undo(frame_index) -> Command              # Undo last command
def redo(frame_index) -> Command              # Redo last undone command
```

**Multi-Layer Support**:
- Commands (e.g., `FrameStateCommand`) capture full frame state, which includes all layers
- Undo/redo affects the composite frame (all layers combined)
- Layer-specific changes are tracked at the command level, not the manager level
- When undoing a paint operation, the entire frame state (including all layers) is restored

**Linkages**:
- Used by: Canvas paint operations, frame operations
- Connected to: Undo/Redo buttons, keyboard shortcuts (Ctrl+Z, Ctrl+Y)

**Usage Examples**:
```python
# Push a command to history (before making changes)
old_state = list(frame.pixels)  # Save current state
# ... make changes to frame ...
new_state = list(frame.pixels)  # Get new state

command = FrameStateCommand(
    frame_index=0,
    old_state=old_state,
    new_state=new_state,
    description="Paint pixels"
)
history_manager.push_command(command, frame_index=0)
# Command is added to history stack for frame 0

# Undo last operation
undone_command = history_manager.undo(frame_index=0)
# Returns the command that was undone
# Restores frame to previous state
# If no history available, returns None

# Redo last undone operation
redone_command = history_manager.redo(frame_index=0)
# Returns the command that was redone
# Restores frame to next state
# If nothing to redo, returns None

# Note: History is frame-specific
# Each frame maintains its own undo/redo stack
```

---

### 7. ScratchpadManager (`domain/scratchpads.py`)

**Role**: Temporary storage for reusable patterns

**Responsibilities**:
- Scratchpad CRUD operations
- Paste operations

**Key Methods**:
```python
def create(name: str, pixels: List[RGB]) -> None   # Save to scratchpad
def list_all() -> List[str]                        # List all scratchpads
def paste(name: str) -> List[RGB]                  # Get scratchpad pixels
def delete(name: str) -> None                      # Delete scratchpad
```

**Linkages**:
- Connected to: Scratchpad tab UI
- Used by: Canvas paste operations

**Usage Examples**:
```python
# Save pixels to scratchpad
pixels = [(255, 0, 0)] * (16 * 16)  # Red pixels
scratchpad_manager.create(name="Red Background", pixels=pixels)
# Saves pixels to scratchpad slot

# List all scratchpads
scratchpad_names = scratchpad_manager.list_all()
# Returns List[str] of all scratchpad names

# Paste pixels from scratchpad
pasted_pixels = scratchpad_manager.paste(name="Red Background")
# Returns List[RGB] from scratchpad
# Can be applied to frame/layer

# Delete a scratchpad
scratchpad_manager.delete(name="Red Background")
# Removes scratchpad from storage
```

---

### 8. EffectLibrary (`domain/effects/library.py`)

**Role**: Discovers and manages visual effects

**Responsibilities**:
- Effect asset discovery and loading
- Effect categorization
- Effect metadata management

**Key Methods**:
```python
def reload() -> None                           # Reload effects from disk
def categories() -> List[str]                  # Get all effect categories
def effects() -> List[EffectDefinition]        # Get all available effects
```

**Linkages**:
- Used by: Effects tab UI (DT-15)
- Connected to: Frame modification workflows, effect preview system

**Usage Examples**:
```python
# Reload effects from disk (after adding new effect files)
effect_library.reload()
# Scans Res/effects directory for new effects

# Get all effect categories
categories = effect_library.categories()
# Returns List[str], e.g., ["Blur", "Color", "Transform"]

# Get all available effects
effects = effect_library.effects()
# Returns List[EffectDefinition]
# Each effect has name, category, keywords, etc.

# Filter effects by category
blur_effects = [e for e in effects if e.category == "Blur"]
```

---

### 9. BitmapFontRepository (`domain/text/bitmap_font.py`)

**Role**: Manages bitmap font assets

**Responsibilities**:
- Font loading and saving
- Font listing and discovery
- Font asset persistence

**Key Methods**:
```python
def load_font(name: str) -> BitmapFont         # Load font by name
def save_font(font: BitmapFont) -> None        # Save font to disk
def list_fonts() -> List[str]                  # List all available fonts
```

**Linkages**:
- Used by: Text animation feature (DT-17)
- Connected to: Font Designer dialog, text generation workflows

**Usage Examples**:
```python
# Load a font by name
font = font_repo.load_font(name="MyCustomFont")
# Returns BitmapFont object
# Returns None if font doesn't exist

# Save a font
font = BitmapFont(name="MyCustomFont", glyphs={...})
font_repo.save_font(font)
# Saves font to Res/fonts directory as JSON

# List all available fonts
font_names = font_repo.list_fonts()
# Returns List[str] of all font names
# Includes built-in fonts and custom fonts
```

---

### 10. ImageImporter (Utility Functions)

**Role**: Handles image/GIF import operations

**Responsibilities**:
- Image file parsing (PNG, JPG, GIF)
- GIF frame extraction
- Pattern creation from images

**Key Functions**:
```python
def import_image(path: Path) -> Pattern        # Import single image as pattern
def import_gif(path: Path) -> Pattern         # Import GIF as multi-frame pattern
```

**Linkages**:
- Used by: Import group UI (DT-18)
- Connected to: Pattern loading workflow, file import dialogs

---

### 11. Export/Import System (`core/io/`)

**Role**: Pattern file I/O operations

**Responsibilities**:
- File format parsing (DAT, HEX, BIN, LEDS, JSON)
- File format writing/export
- Metadata extraction and validation

**Key Functions**:
```python
def parse_leds_file(path: Path) -> Dict        # Parse LEDS file
def write_leds_file(path, metadata, sequence)  # Write LEDS file
def parse_dat_file(path: Path) -> Pattern      # Parse DAT file
def parse_hex_file(path: Path) -> Pattern      # Parse HEX file
def parse_bin_stream(stream) -> Pattern        # Parse BIN file
```

**Linkages**:
- Used by: Export tab, file loading/saving workflows (DT-2, DT-3)
- Connected to: Pattern load/save operations, LEDS export/import

**Usage Examples**:
```python
# Parse a LEDS file
leds_data = parse_leds_file(path=Path("pattern.leds"))
# Returns Dict with metadata, instructions, frame_data
# Raises LMSFormatError if file is invalid

# Write a LEDS file
write_leds_file(
    path=Path("output.leds"),
    pattern_metadata={
        "width": 16,
        "height": 16,
        "frame_count": 10,
        "color_order": "RGB"
    },
    sequence=pattern_instruction_sequence,
    frame_data=None  # Optional: include frame pixel data
)
# Writes LEDS file with metadata and instructions

# Parse a DAT file
pattern = parse_dat_file(path=Path("pattern.dat"))
# Returns Pattern object
# Auto-detects dimensions if possible

# Parse a HEX file
pattern = parse_hex_file(path=Path("pattern.hex"))
# Returns Pattern object
# Validates Intel HEX format

# Parse a BIN file
pattern = parse_bin_stream(stream=open("pattern.bin", "rb"))
# Returns Pattern object
# Attempts to infer dimensions from file size
```

---

### 12. PatternInstructionSequence (`core/automation/instructions.py`)

**Role**: Ordered collection of LMS pattern instructions (Data Structure)

**Responsibilities**:
- Instruction sequence management
- Instruction serialization/deserialization
- Sequence manipulation (add, remove, reorder)

**Key Methods**:
```python
def add(instruction: PatternInstruction) -> None    # Add instruction
def insert(index: int, instruction) -> None         # Insert at index
def remove_at(index: int) -> None                   # Remove by index
def move(old_index: int, new_index: int) -> None    # Reorder instructions
def to_list() -> List[Dict]                         # Serialize to list
def from_list(payload: List[Dict]) -> PatternInstructionSequence  # Deserialize
```

**Linkages**:
- Used by: LMS Automation tab (DT-14)
- Connected to: LEDS export, PreviewSimulator, `_lms_sequence` instance variable in DesignToolsTab

**Usage Examples**:
```python
# Create a new sequence
sequence = PatternInstructionSequence()

# Add an instruction
instruction = PatternInstruction(
    source=LayerBinding(slot="Frame1", frame_index=0),
    instruction=LMSInstruction(code="moveLeft1", repeat=10, gap=1),
    layer2=None,
    mask=None
)
sequence.add(instruction)
# Adds instruction to end of sequence

# Insert instruction at specific index
sequence.insert(index=0, instruction=instruction)
# Inserts at beginning of sequence

# Remove instruction
sequence.remove_at(index=2)
# Removes instruction at index 2

# Reorder instructions
sequence.move(old_index=0, new_index=2)
# Moves first instruction to third position

# Serialize to list (for storage/export)
sequence_list = sequence.to_list()
# Returns List[Dict] suitable for JSON serialization

# Deserialize from list
restored = PatternInstructionSequence.from_list(sequence_list)
# Creates new sequence from serialized data

# Get sequence summary
summary = sequence.summarize()
# Returns Dict with instruction counts, etc.
```

---

### 13. PresetRepository (`domain/automation/presets.py`)

**Role**: Manages automation action presets

**Responsibilities**:
- Preset CRUD operations (create, read, update, delete)
- Preset import/export
- Preset persistence (JSON-backed storage)

**Key Methods**:
```python
def upsert(name: str, actions: List[DesignAction]) -> None  # Save or update preset
def get(name: str) -> Optional[List[DesignAction]]         # Load preset
def delete(name: str) -> None                              # Delete preset
def names() -> List[str]                                   # List all preset names
def exists(name: str) -> bool                               # Check if preset exists
def duplicate(old_name: str, new_name: str) -> None        # Duplicate preset
def rename(old_name: str, new_name: str) -> None          # Rename preset
def export_to_path(name: str, path: Path) -> None         # Export preset to file
def import_from_path(path: Path, overwrite: bool) -> List[str]  # Import preset from file
```

**Linkages**:
- Used by: Automation tab (preset management UI)
- Connected to: AutomationQueueManager (preset loading), automation workflows

**Usage Examples**:
```python
# Save or update a preset
actions = [DesignAction(...), DesignAction(...)]
preset_repo.upsert(name="MyPreset", actions=actions)
# Creates new preset or updates existing one

# Load a preset
actions = preset_repo.get(name="MyPreset")
# Returns Optional[List[DesignAction]]
# Returns None if preset doesn't exist

# List all preset names
preset_names = preset_repo.names()
# Returns List[str] of all preset names

# Check if preset exists
exists = preset_repo.exists(name="MyPreset")
# Returns bool

# Duplicate a preset
preset_repo.duplicate(old_name="MyPreset", new_name="MyPreset Copy")
# Creates a copy with new name
# Raises ValueError if old_name doesn't exist or new_name already exists

# Rename a preset
preset_repo.rename(old_name="MyPreset", new_name="RenamedPreset")
# Renames preset
# Raises ValueError if old_name doesn't exist or new_name already exists

# Delete a preset
preset_repo.delete(name="MyPreset")
# Removes preset from storage

# Export preset to file
preset_repo.export_to_path(name="MyPreset", path=Path("preset.json"))
# Exports preset to external JSON file

# Import preset from file
imported_names = preset_repo.import_from_path(
    path=Path("preset.json"),
    overwrite=False
)
# Returns List[str] of imported preset names
# Raises ValueError if overwrite=False and preset already exists
```

---

## Feature Inventory

### Core Features

| Feature ID | Feature Name | Description | UI Location | Manager |
|------------|--------------|-------------|-------------|---------|
| **DT-1** | Pattern Creation | Create new blank pattern | Header → "New" button | PatternState |
| **DT-2** | Pattern Loading | Load pattern from file | Header → "Open" button | PatternState |
| **DT-3** | Pattern Export | Export pattern to various formats | Export tab | Export/Import System |
| **DT-4** | Canvas Drawing | Interactive pixel painting | Canvas panel | LayerManager |
| **DT-5** | Color Selection | Choose drawing color | Brushes tab → Palette | DesignToolsTab |
| **DT-6** | Brush Tools | Drawing tools (pen, fill, etc.) | Brushes tab → Drawing tools | MatrixDesignCanvas |
| **DT-7** | Frame Management | Add, delete, duplicate frames | Timeline controls | FrameManager |
| **DT-8** | Layer Management | Multi-layer support per frame | Layers tab | LayerManager |
| **DT-9** | Timeline Navigation | Frame selection and playback | Timeline widget | FrameManager |
| **DT-10** | Playback Control | Play/pause/step animation | Timeline controls | DesignToolsTab |
| **DT-11** | Undo/Redo | History management | Canvas HUD buttons | HistoryManager |
| **DT-12** | Matrix Configuration | Set LED matrix dimensions | Matrix config panel | PatternState |
| **DT-13** | Automation Queue | Build automation action sequences | Automation tab | AutomationQueueManager |
| **DT-14** | LMS Automation | LED Matrix Studio instruction builder | Automation → LMS tab | AutomationQueueManager |
| **DT-15** | Effects Library | Apply visual effects to frames | Effects tab | EffectLibrary |
| **DT-16** | Scratchpads | Temporary reusable pattern storage | Scratchpads tab | ScratchpadManager |
| **DT-17** | Text Animation | Generate text-based animations | Brushes tab → Text | BitmapFontRepository |
| **DT-18** | Image Import | Import images/GIFs as patterns | Import group | ImageImporter |
| **DT-19** | Gradient Tools | Color gradient generation | Brushes tab → Gradient | DesignToolsTab |
| **DT-20** | Zoom Controls | Canvas and timeline zoom | View controls | DesignToolsTab |
| **DT-21** | Preview Mode | Pattern preview simulation | Preview tab (external) | PreviewSimulator |

### Detailed Feature Descriptions

#### DT-1: Pattern Creation
**Workflow**:
1. User clicks "New" button
2. `_on_new_pattern_clicked()` called
3. Creates blank pattern (default 16x16, 1 frame)
4. `load_pattern()` called with new pattern
5. Canvas, timeline, layers initialized

**Error Handling**:
- **Invalid dimensions**: If width or height is ≤ 0, defaults to 16x16
- **Pattern creation failure**: If pattern creation fails, shows error message and keeps existing pattern
- **Manager initialization failure**: If any manager fails to initialize, rolls back and shows error
- **UI update failure**: If canvas/timeline initialization fails, pattern is still created but UI may be incomplete

**Linked Features**: DT-2, DT-3, DT-7, DT-12

---

#### DT-2: Pattern Loading
**Workflow**:
1. User clicks "Open" button
2. File dialog opens (supports DAT, HEX, BIN, LEDS, JSON)
3. **Export/Import System** parser loads file → creates Pattern object
   - `parse_dat_file()`, `parse_hex_file()`, `parse_bin_stream()`, or `parse_leds_file()` called
4. `load_pattern()` called
5. Pattern metadata extracted (dimensions, frames, etc.)
6. All managers updated with new pattern:
   - PatternState.set_pattern()
   - FrameManager.set_pattern()
   - LayerManager.set_pattern()
7. Canvas, timeline, layers refreshed

**Managers Involved**: PatternState, Export/Import System (parsers), FrameManager, LayerManager

**Error Handling**:
- **File not found**: Shows error dialog, pattern remains unchanged
- **Unsupported format**: Shows error dialog with supported formats list
- **Parser failure**: Catches `LMSFormatError` or parsing exceptions, shows user-friendly error message
- **Invalid file data**: Validates file structure, shows error if corrupted or invalid
- **Dimension mismatch**: Warns user if imported dimensions differ from current, allows user to choose
- **Memory errors**: If pattern is too large, shows error and prevents loading
- **User cancellation**: If user cancels file dialog, no changes occur
- **Partial load failure**: If some frames fail to load, shows warning but continues with valid frames

**Linked Features**: DT-1, DT-3, DT-7, DT-9, DT-12, DT-14

---

#### DT-3: Pattern Export
**Workflow**:
1. User clicks "Export" button or goes to Export tab
2. User selects export format (DAT, HEX, BIN, LEDS, JSON, Code Template)
3. User configures export options (color order, serpentine, etc.)
4. User clicks "Export" or "Generate Code"
5. **Export/Import System** export function called (`write_leds_file()`, template renderer, etc.)
6. File dialog opens for save location
7. Pattern data written to file
8. Export complete notification shown

**Error Handling**:
- **No pattern loaded**: Export disabled if no pattern exists
- **No frames**: If pattern has no frames, export may fail or create empty file
- **Invalid export format**: If format is invalid, shows error and prevents export
- **File write failure**: If file cannot be written (permissions, disk full, etc.), shows error dialog
- **Export data corruption**: If export data generation fails, shows error and prevents file write
- **User cancellation**: If user cancels file dialog, no export occurs
- **Template rendering failure**: If code template rendering fails, shows error and prevents export

**Linked Features**: DT-1, DT-2, DT-14

---

#### DT-4: Canvas Drawing
**Workflow**:
1. User clicks/paints on canvas
2. `canvas.pixel_updated(x, y, color)` signal emitted
3. **DesignToolsTab** `_on_canvas_pixel_updated(x, y, color)` called
4. `_pending_paint_state` saved (for undo)
5. If "Broadcast to all frames" checkbox is enabled:
   - **DesignToolsTab** iterates over all frame indices
   - **LayerManager** `apply_pixel(frame_index, x, y, color, width, height, layer_index)` called for **all frames** in pattern
   - Each frame's active layer receives the pixel change
6. Otherwise:
   - **LayerManager** `apply_pixel(frame_index, x, y, color, width, height, layer_index)` called on active layer of current frame only
7. **LayerManager** `sync_frame_from_layers()` updates frame(s)
8. Canvas refreshed
9. On mouse release: **DesignToolsTab** `_commit_paint_operation()` saves to **HistoryManager**

**Brush Broadcast**:
- When "Apply brush strokes to all frames" checkbox is enabled, pixel changes apply to all frames simultaneously
- Useful for drawing backgrounds or patterns that span entire animations
- Implemented in **DesignToolsTab** `_on_canvas_pixel_updated()` by iterating over all frame indices when broadcast is enabled

**Managers Involved**: DesignToolsTab (broadcast logic), LayerManager (pixel application), HistoryManager (undo/redo)

**Error Handling**:
- **Pattern is None**: If no pattern loaded, operation is ignored, no error shown
- **Frame index out of range**: Validates frame index before applying, uses current frame if invalid
- **Layer index invalid**: If active layer index is invalid, defaults to layer 0
- **Coordinates out of bounds**: Validates x, y coordinates against width/height, ignores out-of-bounds pixels
- **Color is None**: If color is None, uses black (0, 0, 0) as default
- **History manager full**: If history stack is full, oldest entry is removed before adding new one
- **Canvas update failure**: If canvas refresh fails, operation still completes but display may be stale

**Linked Features**: DT-5, DT-6, DT-8, DT-11, DT-19

**Key Methods**:
- `_on_canvas_pixel_updated()` - Handles pixel paint
- `_commit_paint_operation()` - Commits paint to history
- `layer_manager.apply_pixel(frame_index, x, y, colour, width, height, layer_index)` - Applies pixel to layer

---

#### DT-7: Frame Management
**Workflow** (Add Frame):
1. User clicks "Add" button
2. `_on_add_frame()` called
3. `frame_manager.add()` creates blank frame
4. `PatternState` updated
5. Timeline refreshed
6. New frame selected

**Workflow** (Delete Frame):
1. User clicks "Delete" button
2. `_on_delete_frame()` called
3. Validation (prevents deleting last frame)
4. `frame_manager.delete()` removes frame
5. Frame indices adjusted
6. Timeline refreshed
7. Previous frame selected if needed

**Workflow** (Duplicate Frame):
1. User clicks "Duplicate" button
2. `_on_duplicate_frame()` called
3. `frame_manager.duplicate()` creates copy
4. Timeline refreshed
5. Duplicate frame selected

**Workflow** (Move/Reorder Frame):
1. User drags frame in timeline to new position
2. `_on_timeline_frame_moved()` or similar handler called
3. `frame_manager.move(src_index, dest_index)` called
4. Frame removed from source position
5. Frame inserted at destination position
6. Current frame index updated to destination
7. `frames_changed` signal emitted
8. Timeline refreshed with new order
9. LayerManager layers remain associated with frame indices

**Error Handling**:
- **No pattern loaded**: If pattern is None, frame operations are disabled or show error
- **Frame index out of range**: Validates index before operations, shows error if invalid
- **Cannot delete last frame**: Validation prevents deleting last frame, shows warning message
- **Invalid source/destination indices**: Move operation validates indices, no-op if invalid
- **Frame creation failure**: If frame creation fails (memory, etc.), shows error and keeps existing frames
- **Timeline refresh failure**: If timeline update fails, frame operation still completes

**Linked Features**: DT-9, DT-10, DT-11

---

#### DT-8: Layer Management
**Workflow** (Add Layer):
1. User clicks "Add Layer" in Layers tab
2. `layer_manager.add_layer()` called
3. New layer created with default pixels (black)
4. Layer panel updated
5. Timeline layer tracks updated
6. `layers_changed` signal emitted

**Workflow** (Apply Pixel to Layer):
1. User paints on canvas
2. Active layer index obtained from layer panel
3. `layer_manager.apply_pixel(frame_index, x, y, color, width, height, layer_index)` called with layer index
4. Pixel updated in layer's pixel array
5. `sync_frame_from_layers()` composites all visible layers
6. Frame pixels updated
7. Canvas refreshed

**Workflow** (Layer Visibility):
1. User toggles layer visibility checkbox
2. `layer_manager.set_layer_visible()` called
3. Layer visibility flag updated
4. `get_composite_pixels()` re-computes (excludes hidden layers)
5. Canvas refreshed

**Workflow** (Layer Opacity Change):
1. User adjusts opacity slider in layer panel
2. `_on_opacity_changed(value)` called (value: 0-100)
3. Opacity converted to float (0.0-1.0)
4. `layer_manager.set_layer_opacity(frame_index, layer_index, opacity)` called
5. Layer opacity property updated
6. `layers_changed` signal emitted
7. `get_composite_pixels()` re-computes with new opacity (alpha blending)
8. `sync_frame_from_layers()` updates frame pixels
9. Canvas refreshed to show opacity change

**Workflow** (Layer Rename):
1. User edits layer name in layer panel text field
2. `_on_name_changed()` called
3. Name text extracted and validated (non-empty)
4. `layer_manager.set_layer_name(frame_index, layer_index, name)` called
5. Layer name property updated
6. `layers_changed` signal emitted
7. Layer panel list refreshed to show new name
8. Timeline layer tracks may update if they display names

**Workflow** (Layer Reorder):
1. User clicks "Move Up" or "Move Down" button in layer panel
2. `_on_move_up()` or `_on_move_down()` called
3. Validation: ensure layer can move (not at boundary)
4. `layer_manager.move_layer(frame_index, from_index, to_index)` called
5. Layer removed from source position
6. Layer inserted at destination position
7. `layer_moved` signal emitted
8. `layers_changed` signal emitted
9. Active layer index updated if needed
10. Layer panel list refreshed
11. `get_composite_pixels()` re-computes (order affects blending)
12. Canvas refreshed

**Error Handling**:
- **Pattern is None**: If no pattern, layer operations are disabled
- **Frame index out of range**: Validates frame index, shows error if invalid
- **Layer index invalid**: If layer index is out of range, operation fails silently or shows error
- **Cannot remove last layer**: Validation prevents removing last layer, shows warning
- **Invalid layer name**: Empty or None names are rejected, shows validation error
- **Opacity out of range**: Opacity is clamped to 0.0-1.0 range automatically
- **Layer move boundary**: Cannot move layer beyond first/last position, operation is ignored
- **Compositing failure**: If layer compositing fails, shows error but keeps layers intact

**Linked Features**: DT-4, DT-9

---

#### DT-9: Timeline Navigation
**Workflow**:
1. User clicks frame in **TimelineWidget**
2. **TimelineWidget** `frameSelected` signal emitted
3. **DesignToolsTab** `_on_frame_selected(index)` called
4. **FrameManager** `select(index)` updates state
5. **DesignToolsTab** `_load_current_frame_into_canvas()` renders frame
   - Calls **LayerManager** `get_composite_pixels(index)` to get blended result
   - Updates canvas with composite pixels
6. Layer panel updates to show frame's layers
7. Timeline playhead moves to selected frame
8. Status labels updated

**Managers Involved**: TimelineWidget (UI component), FrameManager (frame selection), LayerManager (composite rendering), DesignToolsTab (coordination)

**Error Handling**:
- **Pattern is None**: If no pattern, frame selection is disabled
- **Frame index out of range**: Validates index before selection, uses valid index if out of range
- **Invalid frame selection**: If selected frame doesn't exist, selects first available frame
- **Composite rendering failure**: If layer compositing fails, shows error but still switches frame
- **Canvas update failure**: If canvas fails to update, frame selection still completes

**Linked Features**: DT-7, DT-8, DT-10, DT-13

---

#### DT-10: Playback Control
**Workflow** (Play):
1. User clicks Play button
2. `_on_transport_play()` called
3. Playback timer started (based on FPS control for preview)
4. Timer advances frame index
5. `_step_frame(1)` called each interval
6. Canvas updates each frame
7. Timeline playhead moves

**Workflow** (Pause/Stop):
1. Timer stopped
2. Current frame remains displayed

**Playback Timing Clarification**:
- **FPS control** sets global playback speed for preview (overrides per-frame duration during preview)
- **Frame duration** (duration_ms) is stored per-frame for export compatibility and format-specific timing
- During preview: FPS determines timing (all frames play at same rate based on FPS setting)
- During export: Frame duration_ms is used if the export format supports per-frame timing
- These serve different purposes and can coexist - FPS for user preview experience, duration_ms for export accuracy

**Error Handling**:
- **No pattern loaded**: Playback is disabled if no pattern exists
- **No frames**: If pattern has no frames, playback cannot start, shows error
- **Invalid FPS value**: FPS is clamped to valid range (1-60), shows warning if out of range
- **Timer failure**: If playback timer fails to start, shows error and disables play button
- **Frame index out of range during playback**: Automatically wraps to valid range or stops playback

**Linked Features**: DT-7, DT-9

---

#### DT-13: Automation Queue
**Workflow** (Add Action):
1. User selects action type in Automation tab
2. User configures action parameters
3. User clicks "Add Action"
4. `_on_action_add_clicked()` called
5. `DesignAction` object created
6. `automation_manager.enqueue()` called
7. Action added to queue
8. Timeline overlay updated
9. Action list updated

**Workflow** (Apply Actions):
1. User configures frame range (start/end)
2. User clicks "Apply Actions"
3. `_on_apply_actions()` called
4. Actions processed sequentially
5. Each action applied to frame range
6. Pattern modified
7. Timeline refreshed
8. Canvas updated

**Error Handling**:
- **No pattern loaded**: Automation operations disabled if no pattern exists
- **Invalid action parameters**: Action validation fails, shows error message, action not added
- **Frame range invalid**: If start > end or indices out of range, shows error and prevents apply
- **Action application failure**: If action fails to apply to a frame, logs error but continues with other frames
- **Queue full**: If queue reaches limit, shows warning but allows adding (may need queue management)
- **Preview failure**: If preview generation fails, shows error but keeps original pattern

**Linked Features**: DT-7, DT-9, DT-14

---

#### DT-14: LMS Automation
**Workflow** (Build Instruction):
1. User selects LMS action in LMS Builder tab
2. User configures source, code, layer2, mask, repeat
3. User clicks "Add Instruction"
4. **PatternInstructionSequence** `PatternInstruction` created with `LMSInstruction`
5. Instruction added to **DesignToolsTab** `_lms_sequence` (PatternInstructionSequence instance)
6. **PatternInstructionSequence** `add()` or `insert()` called
7. Queue list updated

**Workflow** (Preview):
1. User clicks "Preview Sequence"
2. **PreviewSimulator** initialized with current pattern
3. **PatternInstructionSequence** instructions iterated
4. **PreviewSimulator** applies instructions sequentially
5. Preview pattern generated
6. Preview displayed (can replace main pattern)

**Workflow** (Export):
1. User clicks "Export LEDS"
2. **Export/Import System** `write_leds_file()` called
3. Pattern metadata + **PatternInstructionSequence** (via `to_list()`) written
4. LEDS file saved to disk

**Managers/Components Involved**: 
- **PatternInstructionSequence** (data structure - instruction collection)
- **PreviewSimulator** (preview generation)
- **Export/Import System** (file I/O)
- **DesignToolsTab** (UI coordination, `_lms_sequence` instance)

**Error Handling**:
- **No pattern loaded**: LMS operations disabled if no pattern exists
- **Invalid instruction parameters**: Instruction validation fails, shows error, instruction not added
- **Invalid frame binding**: If source/layer2/mask frame doesn't exist, shows error
- **Preview generation failure**: If PreviewSimulator fails, shows error, original pattern unchanged
- **Export file error**: If file write fails (permissions, disk full, etc.), shows error dialog
- **Empty sequence**: If sequence is empty, export may still succeed with just metadata
- **Instruction execution failure**: If instruction fails during preview, logs error but continues

**Linked Features**: DT-13, DT-21

---

#### DT-15: Effects Library
**Workflow**:
1. User selects effect type in Effects tab
2. User selects specific effect
3. User adjusts intensity/settings
4. User clicks "Preview" → shows effect on current frame
5. User clicks "Apply" → effect applied to selected frames
6. Pattern updated
7. Canvas refreshed

**Error Handling**:
- **No pattern loaded**: Effects disabled if no pattern exists
- **No frames**: If pattern has no frames, effect cannot be applied, shows error
- **Invalid effect**: If selected effect doesn't exist or fails to load, shows error
- **Invalid intensity**: Intensity is clamped to valid range (0-100), shows warning if out of range
- **Frame range invalid**: If selected frame range is invalid, shows error and prevents apply
- **Effect application failure**: If effect fails to apply to a frame, logs error but continues with other frames
- **Preview failure**: If preview generation fails, shows error but keeps original frame

**Linked Features**: DT-7, DT-8

---

#### DT-11: Undo/Redo
**Workflow** (Undo):
1. User presses Ctrl+Z or clicks Undo button
2. `_on_undo()` called
3. `history_manager.undo(frame_index)` called
4. Previous frame state restored from history
5. Layers rebuilt from restored frame state
6. Canvas refreshed

**Workflow** (Redo):
1. User presses Ctrl+Y or clicks Redo button
2. `_on_redo()` called
3. `history_manager.redo(frame_index)` called
4. Next frame state restored from history
5. Layers rebuilt from restored frame state
6. Canvas refreshed

**Error Handling**:
- **No history available**: If history stack is empty, undo/redo is disabled
- **Frame index out of range**: Validates frame index before undo/redo operation
- **History corruption**: If history command is invalid, shows error and clears history
- **State restoration failure**: If frame state cannot be restored, shows error and keeps current state
- **Layer rebuild failure**: If layers cannot be rebuilt, shows error but frame state is still restored

---

#### DT-12: Matrix Configuration
**Workflow**:
1. User changes width or height in matrix config panel
2. `_on_matrix_dimension_changed()` called
3. PatternState metadata updated (width, height)
4. FrameManager: All Frame.pixels arrays resized
5. LayerManager.resize_pixels() called (all layers resized)
6. Canvas size updated
7. Timeline thumbnails refreshed

**Error Handling**:
- **Invalid dimensions**: If width or height is ≤ 0, shows error and reverts to previous values
- **Dimensions too large**: If dimensions exceed maximum (memory limits), shows error and prevents change
- **Resize failure**: If frame/layer resize fails, shows error and attempts to roll back
- **Data loss warning**: If dimensions shrink, warns user about potential data loss
- **Canvas update failure**: If canvas fails to resize, shows error but pattern dimensions still updated

---

#### DT-16: Scratchpads
**Workflow** (Save to Scratchpad):
1. User selects frame or region
2. User clicks "Save to Scratchpad" button
3. `scratchpad_manager.create(name, pixels)` called
4. Pixels saved to scratchpad slot
5. Scratchpad list updated

**Workflow** (Paste from Scratchpad):
1. User selects scratchpad from list
2. User clicks "Paste" button
3. `scratchpad_manager.paste(name)` called
4. Pixels retrieved from scratchpad
5. Pixels applied to current frame/layer
6. Canvas refreshed

**Error Handling**:
- **No pattern loaded**: Scratchpad operations disabled if no pattern exists
- **Invalid scratchpad name**: Empty or invalid names are rejected
- **Scratchpad full**: If all slots are full, shows error or prompts to overwrite
- **Scratchpad not found**: If selected scratchpad doesn't exist, shows error
- **Paste failure**: If paste operation fails, shows error but keeps original frame

---

#### DT-17: Text Animation
**Workflow**:
1. User enters text in text input field
2. User selects font from font combo (BitmapFontRepository)
3. User configures animation settings (scroll, static, etc.)
4. User clicks "Generate" button
5. `_on_generate_text_animation()` called
6. Text rendered to frames using selected font
7. Frames added or updated with text animation
8. Canvas refreshed

**Error Handling**:
- **No pattern loaded**: Text generation disabled if no pattern exists
- **Empty text**: If text is empty, shows error and prevents generation
- **Font not found**: If selected font doesn't exist, falls back to default font or shows error
- **Font loading failure**: If font fails to load, uses default font and shows warning
- **Generation failure**: If text rendering fails, shows error and keeps existing frames
- **Invalid settings**: If animation settings are invalid, shows error and prevents generation

---

#### DT-18: Image Import
**Workflow**:
1. User clicks "Import Image" button
2. File dialog opens (supports PNG, JPG, GIF)
3. User selects image file
4. ImageImporter parses image file
5. Pattern created from image pixels
6. If GIF: Multiple frames created (one per GIF frame)
7. `load_pattern()` called with imported pattern
8. Canvas, timeline, layers initialized

**Error Handling**:
- **File not found**: Shows error dialog, pattern remains unchanged
- **Unsupported format**: Shows error dialog with supported formats list
- **Image parsing failure**: Catches image parsing exceptions, shows user-friendly error
- **Invalid image data**: Validates image structure, shows error if corrupted
- **Image too large**: If image exceeds maximum size, shows error and prevents import
- **Memory errors**: If image is too large for memory, shows error and prevents loading
- **User cancellation**: If user cancels file dialog, no changes occur
- **Dimension mismatch**: Warns user if image dimensions differ from current pattern

---

#### DT-19: Gradient Tools
**Workflow**:
1. User selects gradient tool in Brushes tab
2. User selects start and end colors
3. User clicks/drags on canvas to define gradient area
4. Gradient pixels calculated and applied
5. Pixels applied to active layer
6. Frame synced from layers
7. Canvas refreshed

**Error Handling**:
- **Pattern is None**: Gradient operations disabled if no pattern exists
- **Invalid color values**: Colors are clamped to valid RGB range (0-255)
- **Invalid gradient area**: If gradient area is invalid, operation is ignored
- **Layer index invalid**: If active layer index is invalid, defaults to layer 0
- **Gradient calculation failure**: If gradient calculation fails, shows error and keeps original pixels

---

#### DT-20: Zoom Controls
**Workflow** (Canvas Zoom):
1. User adjusts canvas zoom slider or uses mouse wheel
2. `_on_canvas_zoom_changed()` called
3. Canvas zoom level updated
4. Canvas redrawn at new zoom level

**Workflow** (Timeline Zoom):
1. User adjusts timeline zoom slider
2. `_on_timeline_zoom_changed()` called
3. Timeline zoom level updated
4. Timeline redrawn at new zoom level

**Error Handling**:
- **Invalid zoom value**: Zoom is clamped to valid range (e.g., 0.1x to 10x)
- **Zoom calculation failure**: If zoom calculation fails, uses default zoom level
- **Rendering failure**: If canvas/timeline fails to redraw, shows error but zoom level still updated

---

#### DT-21: Preview Mode
**Workflow**:
1. User opens Preview tab (external dialog)
2. PreviewSimulator initialized with current pattern
3. Preview pattern generated from pattern + any automation instructions
4. Preview displayed in separate window
5. User can interact with preview (play, pause, etc.)
6. Preview updates when pattern changes (if auto-sync enabled)

**Error Handling**:
- **No pattern loaded**: Preview disabled if no pattern exists
- **PreviewSimulator initialization failure**: Shows error and prevents preview
- **Preview generation failure**: If preview cannot be generated, shows error and closes preview
- **Memory errors**: If preview pattern is too large, shows error and prevents preview
- **Auto-sync failure**: If auto-sync fails, preview may become stale but remains open

---

## Feature Linkages & Data Flow

### Linkage Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Design Tools Tab                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ PatternState │◄───│ FrameManager │    │ LayerManager │
│  (Model)     │    │              │    │              │
└──────┬───────┘    └──────────────┘    └──────┬───────┘
       │                                         │
       │                                         │
       ▼                                         ▼
┌──────────────┐                          ┌──────────────┐
│   Canvas     │◄─────────────────────────│   Timeline   │
│   Widget     │                          │   Widget     │
└──────────────┘                          └──────────────┘
       │                                         │
       └─────────────────┬───────────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  UI Components   │
              │  (Brushes, etc.) │
              └──────────────────┘
```

### Key Linkage Patterns

#### 1. Pattern Loading Flow
```
File Load
    ↓
Parser (DAT/HEX/BIN/LEDS)
    ↓
Pattern Object Created
    ↓
load_pattern(pattern)
    ├─→ PatternState.set_pattern()
    ├─→ FrameManager.set_pattern()
    ├─→ LayerManager.set_pattern()
    ├─→ Canvas.set_matrix_size()
    ├─→ Timeline refresh
    └─→ Status labels update
```

#### 2. Pixel Paint Flow
```
Canvas Click
    ↓
_on_canvas_pixel_updated(x, y, color)
    ├─→ Save state (for undo)
    ├─→ Get active layer index
    ├─→ layer_manager.apply_pixel(frame_index, x, y, color, width, height, layer_index)
    ├─→ layer_manager.sync_frame_from_layers(frame_index)
    ├─→ Canvas refresh
    ├─→ pattern_modified signal
    └─→ On release: _commit_paint_operation() → history
```

#### 3. Frame Selection Flow
```
Timeline Click
    ↓
_on_frame_selected(index)
    ├─→ frame_manager.select(index)
    ├─→ _current_frame_index = index
    ├─→ _load_current_frame_into_canvas()
    │   ├─→ layer_manager.get_composite_pixels(index)
    │   └─→ canvas.set_frame_pixels(composite)
    ├─→ Timeline playhead update
    ├─→ Layer panel update
    └─→ Status labels update
```

#### 4. Automation Apply Flow
```
Apply Actions Button
    ↓
_on_apply_actions()
    ├─→ Get frame range (start, end)
    ├─→ Get actions from queue
    ├─→ For each action:
    │   ├─→ For each frame in range:
    │   │   ├─→ Apply action to frame
    │   │   ├─→ Update frame pixels
    │   │   └─→ layer_manager.sync_frame_from_layers()
    │   └─→ Pattern modified
    ├─→ Timeline refresh
    └─→ Canvas update
```

---

## UI Components Mapping

### Header Toolbar
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| New Button | Create pattern | `_on_new_pattern_clicked()` | PatternState |
| Open Button | Load pattern | `_on_open_pattern_clicked()` | PatternState |
| Save/Export Button | Quick export | `_on_header_save_clicked()` | Export system |
| Matrix Status | Show dimensions | Updated via `_update_status_labels()` | PatternState |
| Frame Status | Show frame info | Updated via `_update_status_labels()` | FrameManager |
| FPS Control | Playback speed | `_on_playback_fps_changed()` | DesignToolsTab |
| Loop Toggle | Loop playback | `_on_playback_loop_toggled()` | DesignToolsTab |

### Canvas Panel
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| MatrixDesignCanvas | Pixel painting | `canvas.pixel_updated(x, y, color)` → `_on_canvas_pixel_updated(x, y, color)` | LayerManager |
| Undo Button | Undo operation | `_on_undo()` | HistoryManager |
| Redo Button | Redo operation | `_on_redo()` | HistoryManager |
| Zoom Controls | Canvas zoom | `_on_canvas_zoom_changed()` | DesignToolsTab |
| Geometry Overlay | Show grid/wiring | `_on_canvas_geometry_changed()` | Canvas widget |
| Pixel Shape | Square/round pixels | `_on_canvas_pixel_shape_changed()` | Canvas widget |

### Toolbox Tabs

#### Brushes Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| Drawing Tools | Pen, fill, etc. | `_on_tool_selected()` | MatrixDesignCanvas |
| Palette Grid | Color selection | `_on_palette_selected()` | DesignToolsTab |
| Channel Sliders | RGB adjustment | `_on_channel_slider_changed()` | DesignToolsTab |
| Gradient Tools | Gradient generation | Gradient group | DesignToolsTab |
| Text Animation | Text generation | `_on_generate_text_animation()` | BitmapFontRepository |
| Brush Size | Brush size control | `_on_brush_size_changed()` | MatrixDesignCanvas |
| Broadcast Checkbox | Apply to all frames | `brush_broadcast_checkbox` toggle | DesignToolsTab |

#### Layers Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| LayerPanelWidget | Layer list | Layer panel signals | LayerManager |
| Add Layer | Create layer | `layer_panel.add_layer` | LayerManager |
| Remove Layer | Delete layer | `layer_panel.remove_layer` | LayerManager |
| Visibility Toggle | Show/hide layer | `layer_manager.set_layer_visible()` | LayerManager |
| Opacity Slider | Layer opacity | `layer_manager.set_layer_opacity()` | LayerManager |

#### Automation Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| Action Type Combo | Select action | `_on_action_type_changed()` | AutomationQueueManager |
| Action Parameters | Configure action | Parameter widgets | AutomationQueueManager |
| Add Action Button | Enqueue action | `_on_action_add_clicked()` | AutomationQueueManager |
| Action List | Queue display | `_on_action_list_selection()` | AutomationQueueManager |
| Action Inspector | Edit action | `_load_action_into_inspector()` | AutomationQueueManager |
| Apply Actions | Execute queue | `_on_apply_actions()` | AutomationQueueManager |
| Frame Range | Start/end frames | Frame range spinboxes | AutomationQueueManager |

#### LMS Automation Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| Action Code Combo | LMS action | `_on_lms_action_changed()` | PatternInstructionSequence |
| Source Combo | Pattern source | Source slot selection | PatternInstructionSequence |
| Layer2/Mask | Secondary bindings | Binding selection | PatternInstructionSequence |
| Repeat Spin | Repeat count | Repeat input | PatternInstructionSequence |
| Instruction List | Sequence display | `_on_lms_instruction_selected()` | PatternInstructionSequence |
| Preview Button | Preview sequence | `_on_lms_preview_sequence()` | PreviewSimulator |
| Export LEDS | Save LEDS file | `_on_lms_export_leds()` | `write_leds_file()` |

#### Export Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| Format Combo | Export format | Format selection | Export system |
| Template Combo | Code template | Template selection | ExportTemplates |
| Export Button | Generate export | `_on_open_export_dialog()` | Export system |
| Import Group | Import images | `_on_import_image()` | ImageImporter |

#### Effects Tab
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| Effect Type | Effect category | `_on_effect_type_changed()` | EffectLibrary |
| Effect List | Available effects | `_on_effect_selection_changed()` | EffectLibrary |
| Intensity Slider | Effect strength | Intensity control | EffectLibrary |
| Preview Button | Preview effect | `_on_preview_effect()` | EffectLibrary |
| Apply Button | Apply effect | `_on_apply_effect()` | EffectLibrary |

### Timeline Dock
| Component | Purpose | Connected Handler | Linked Manager |
|-----------|---------|-------------------|----------------|
| TimelineWidget | Frame visualization | `frameSelected` signal → `_on_frame_selected()` | FrameManager |
| Add Frame Button | Create frame | `_on_add_frame()` | FrameManager |
| Duplicate Button | Copy frame | `_on_duplicate_frame()` | FrameManager |
| Delete Button | Remove frame | `_on_delete_frame()` | FrameManager |
| Play Button | Start playback | `_on_transport_play()` | DesignToolsTab |
| Pause Button | Pause playback | `_on_transport_pause()` | DesignToolsTab |
| Duration Spin | Frame duration | `_on_duration_changed()` | FrameManager |
| Zoom Slider | Timeline zoom | `_on_timeline_zoom_changed()` | DesignToolsTab |

---

## Signal/Event Connections

### PatternState Signals
- **Pattern changed**: Triggered when new pattern loaded
  - Listeners: FrameManager, LayerManager, CanvasController, Timeline
  - Note: PatternState may emit signals when pattern is set/updated

### DesignToolsTab Signals
- **`pattern_modified.emit()`**: Pattern has been modified
  - Listeners: MainWindow (external), internal UI refresh handlers
  - Triggers: Save state updates, external tab notifications
  
  **Example - Signal Emission**:
  ```python
  # In DesignToolsTab after any pattern modification
  # After painting, frame operations, layer changes, etc.
  self.pattern_modified.emit()  # Emits to notify pattern has changed
  ```
  
  **Example - Connecting to Signal (External)**:
  ```python
  # In MainWindow
  self.design_tools_tab.pattern_modified.connect(self._on_pattern_modified)
  
  def _on_pattern_modified(self):
      # Update save state, enable save button, etc.
      self._has_unsaved_changes = True
      self.save_action.setEnabled(True)
  ```

- **`pattern_created.emit(Pattern)`**: New pattern created
  - Listeners: MainWindow (external)
  - Argument: The newly created Pattern object
  
  **Example - Signal Emission**:
  ```python
  # In DesignToolsTab._on_new_pattern_clicked()
  new_pattern = Pattern.create_blank(width=16, height=16, frames=1)
  self.load_pattern(new_pattern)
  self.pattern_created.emit(new_pattern)  # Emits the new pattern object
  ```
  
  **Example - Connecting to Signal (External)**:
  ```python
  # In MainWindow
  self.design_tools_tab.pattern_created.connect(self._on_pattern_created)
  
  def _on_pattern_created(self, pattern: Pattern):
      # Update main window state for new pattern
      self._current_pattern = pattern
      self._has_unsaved_changes = False
  ```

### FrameManager Signals
- **`frame_index_changed.emit(int)`**: Frame selection changed
  - Listeners: DesignToolsTab → `_on_manager_frame_selected()`
  - Triggers: Canvas update, layer panel update, status labels
  
  **Example - Signal Emission**:
  ```python
  # In FrameManager.select()
  self._current_index = new_index
  self.frame_index_changed.emit(new_index)  # Emits the new frame index
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.frame_manager.frame_index_changed.connect(self._on_manager_frame_selected)
  
  def _on_manager_frame_selected(self, frame_index: int):
      # Update UI to reflect new frame selection
      self._current_frame_index = frame_index
      self._load_current_frame_into_canvas()
      self._update_status_labels()
  ```

- **`frame_duration_changed.emit(int, int)`**: Frame duration changed
  - Listeners: DesignToolsTab → `_on_manager_duration_changed()`
  - Triggers: Timeline refresh
  
  **Example - Signal Emission**:
  ```python
  # In FrameManager.set_duration()
  frame.duration_ms = duration_ms
  self.frame_duration_changed.emit(frame_index, duration_ms)  # Emits index and duration
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.frame_manager.frame_duration_changed.connect(self._on_manager_duration_changed)
  
  def _on_manager_duration_changed(self, frame_index: int, duration_ms: int):
      # Update timeline to show new duration
      self._refresh_timeline()
  ```

- **`frames_changed.emit()`**: Frame structure changed (add/delete/duplicate/reorder)
  - Listeners: DesignToolsTab → `_refresh_timeline()`, `_refresh_lms_frame_bindings()`
  - Triggers: Timeline refresh, LMS frame binding refresh
  
  **Example - Signal Emission**:
  ```python
  # In FrameManager.add(), delete(), duplicate(), or move()
  pattern.frames.append(new_frame)  # or other frame operation
  self.frames_changed.emit()  # Emits when frame structure changes
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.frame_manager.frames_changed.connect(self._refresh_timeline)
  self.frame_manager.frames_changed.connect(self._refresh_lms_frame_bindings)
  
  def _refresh_timeline(self):
      # Rebuild timeline widget with updated frame list
      self.timeline_widget.set_frames(self._pattern.frames)
  ```

### LayerManager Signals
- **`layers_changed.emit(int)`**: Layer structure changed
  - Listeners: DesignToolsTab → `_on_layers_structure_updated()`
  - Triggers: Timeline refresh, layer panel update
  
  **Example - Signal Emission**:
  ```python
  # In LayerManager.add_layer(), remove_layer(), set_layer_visible(), etc.
  layers.append(new_layer)  # or other layer operation
  self.layers_changed.emit(frame_index)  # Emits frame index where layers changed
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.layer_manager.layers_changed.connect(self._on_layers_structure_updated)
  
  def _on_layers_structure_updated(self, frame_index: int):
      if frame_index == self._current_frame_index:
          # Update layer panel and timeline for current frame
          self.layer_panel.refresh()
          self._refresh_timeline()
  ```

- **`layer_added.emit(int, int)`**: Layer added
  - Listeners: DesignToolsTab → `_on_layers_structure_updated()`
  
  **Example - Signal Emission**:
  ```python
  # In LayerManager.add_layer()
  layers.append(new_layer)
  layer_index = len(layers) - 1
  self.layer_added.emit(frame_index, layer_index)  # Emits frame and layer indices
  self.layers_changed.emit(frame_index)  # Also emits general change signal
  ```

- **`layer_removed.emit(int, int)`**: Layer removed
  - Listeners: DesignToolsTab → `_on_layers_structure_updated()`
  
  **Example - Signal Emission**:
  ```python
  # In LayerManager.remove_layer()
  removed_layer = layers.pop(layer_index)
  self.layer_removed.emit(frame_index, layer_index)  # Emits frame and layer indices
  self.layers_changed.emit(frame_index)  # Also emits general change signal
  ```

- **`frame_pixels_changed.emit(int)`**: Layer pixels changed
  - Listeners: Canvas refresh (implicit via signal propagation)
  - Triggers: Canvas widget update
  
  **Example - Signal Emission**:
  ```python
  # In LayerManager.replace_pixels() or after bulk pixel operations
  layer.pixels = new_pixels
  self.frame_pixels_changed.emit(frame_index)  # Emits frame index
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # Canvas automatically refreshes when frame pixels change
  # The signal triggers canvas update through DesignToolsTab coordination
  ```

- **`pixel_changed.emit(int, int, int, tuple)`**: Individual pixel changed (frame_index, x, y, color)
  - Note: Currently emitted but not actively used by DesignToolsTab
  - Available for future pixel-level tracking or debugging
  
  **Example - Signal Emission**:
  ```python
  # In LayerManager.apply_pixel()
  layer.pixels[pixel_index] = color
  self.pixel_changed.emit(frame_index, x, y, color)  # Emits pixel coordinates and color
  ```

### AutomationQueueManager Signals
- **`queue_changed.emit(list)`**: Action queue changed
  - Listeners: DesignToolsTab → `_on_manager_queue_changed()`
  - Triggers: Timeline overlay update, action list refresh
  
  **Example - Signal Emission**:
  ```python
  # In AutomationQueueManager.enqueue(), remove(), clear(), etc.
  self._actions.append(action)  # or other queue operation
  self.queue_changed.emit(list(self._actions))  # Emits current action list
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.automation_manager.queue_changed.connect(self._on_manager_queue_changed)
  
  def _on_manager_queue_changed(self, actions: List[DesignAction]):
      # Update automation UI and timeline overlays
      self._refresh_automation_list()
      self._refresh_timeline()  # Updates automation overlays
  ```

### Canvas Widget Signals
- **`pixel_updated.emit(int, int, tuple)`**: Pixel clicked/painted (emits x, y, color tuple)
  - Listeners: DesignToolsTab → `_on_canvas_pixel_updated()`
  - Arguments: x coordinate, y coordinate, (r, g, b) color tuple
  
  **Example - Signal Emission**:
  ```python
  # In MatrixDesignCanvas mouse event handler
  self._grid[y][x] = color
  self.pixel_updated.emit(x, y, color)  # Emits pixel coordinates and color
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.canvas.pixel_updated.connect(self._on_canvas_pixel_updated)
  
  def _on_canvas_pixel_updated(self, x: int, y: int, color: Tuple[int, int, int]):
      # Apply pixel to active layer
      self.layer_manager.apply_pixel(
          self._current_frame_index, x, y, color,
          self.state.width(), self.state.height(),
          self.layer_panel.get_active_layer_index()
      )
  ```
  
- **`painting_finished.emit()`**: Painting operation completed (mouse released)
  - Listeners: DesignToolsTab → `_commit_paint_operation()`
  - Emitted when user releases mouse button after painting
  
  **Example - Signal Emission**:
  ```python
  # In MatrixDesignCanvas mouseReleaseEvent()
  if self._is_dragging:
      self._is_dragging = False
      self.painting_finished.emit()  # Emits when mouse is released
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.canvas.painting_finished.connect(self._commit_paint_operation)
  
  def _commit_paint_operation(self):
      # Save paint operation to history for undo/redo
      if self._pending_paint_state is not None:
          command = FrameStateCommand(...)
          self.history_manager.push_command(command, self._current_frame_index)
          self._pending_paint_state = None
  ```

### Timeline Widget Signals
- **`frameSelected.emit(int)`**: Frame selected in timeline
  - Listeners: DesignToolsTab → `_on_frame_selected()`
  
  **Example - Signal Emission**:
  ```python
  # In TimelineWidget when user clicks a frame
  selected_index = self._get_frame_at_position(mouse_pos)
  self.frameSelected.emit(selected_index)  # Emits selected frame index
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.timeline_widget.frameSelected.connect(self._on_frame_selected)
  
  def _on_frame_selected(self, frame_index: int):
      # Switch to selected frame
      self.frame_manager.select(frame_index)
      self._load_current_frame_into_canvas()
  ```

- **`playheadDragged.emit(int)`**: Playhead dragged
  - Listeners: DesignToolsTab → `_on_timeline_playhead_dragged()`
  
  **Example - Signal Emission**:
  ```python
  # In TimelineWidget when user drags playhead
  new_position = self._calculate_frame_from_position(drag_pos)
  self.playheadDragged.emit(new_position)  # Emits new playhead frame index
  ```
  
  **Example - Connecting to Signal**:
  ```python
  # In DesignToolsTab.__init__()
  self.timeline_widget.playheadDragged.connect(self._on_timeline_playhead_dragged)
  
  def _on_timeline_playhead_dragged(self, frame_index: int):
      # Update current frame without starting playback
      self.frame_manager.select(frame_index)
      self._load_current_frame_into_canvas()
  ```

---

## Key Workflows

### Workflow 1: Create and Paint Pattern

```
1. User clicks "New" → New pattern created (16x16, 1 frame)
2. Canvas initialized with blank frame
3. User selects color from palette
4. User selects brush tool (Pen)
5. User clicks/drags on canvas
   ├─ Each click: _on_canvas_pixel_updated(x, y, color)
   ├─ Pixel applied to active layer (layer 0)
   ├─ Frame synced from layers
   └─ Canvas refreshed
6. On mouse release: Paint operation committed to history
7. User can undo (Ctrl+Z) if needed
```

**Linked Features**: DT-1, DT-4, DT-5, DT-6, DT-8, DT-11

---

### Workflow 2: Multi-layer Animation

```
1. Pattern loaded/created
2. User adds new layer (Layer 1) in Layers tab
3. User selects Layer 1 as active
4. User paints background on Layer 0
5. User paints foreground on Layer 1
6. Composite shows both layers blended
7. User adds new frame (Frame 2)
8. User modifies Layer 1 pixels on Frame 2
9. Timeline shows both frames
10. User plays animation → sees layer changes across frames
```

**Linked Features**: DT-7, DT-8, DT-9, DT-10

---

### Workflow 3: Apply Automation

```
1. User selects frames 1-10 in frame range controls
2. User goes to Automation tab
3. User selects action: "Scroll Left"
4. User configures: direction=Left, step=1, repeat=5
5. User clicks "Add Action" → Action enqueued
6. Timeline shows overlay indicating action range
7. User adds more actions to queue
8. User clicks "Apply Actions"
   ├─ For each action in queue:
   │   ├─ For frames 1-10:
   │   │   ├─ Apply action to frame
   │   │   ├─ Update frame pixels
   │   │   └─ Sync layers
   └─ Pattern saved with modifications
9. Timeline refreshed with new frames
```

**Linked Features**: DT-7, DT-13, DT-8

---

### Workflow 4: LMS Export

```
1. User builds pattern with frames
2. User goes to Automation → LMS Builder tab
3. User adds instruction:
   ├─ Source: Pattern1
   ├─ Code: moveLeft1
   ├─ Layer2: NULL
   ├─ Mask: NULL
   └─ Repeat: 10
4. User adds more instructions to sequence
5. User clicks "Preview Sequence" → Preview generated
6. User verifies preview looks correct
7. User clicks "Export LEDS"
8. File dialog opens
9. User saves LEDS file
10. LEDS file contains:
    ├─ Pattern metadata (width, height, frames)
    ├─ Instruction sequence
    └─ Optional frame data
```

**Linked Features**: DT-14, DT-21

---

### Workflow 5: Import and Modify

```
1. User clicks "Open"
2. File dialog → User selects DAT/HEX/BIN/LEDS file
3. Parser loads file → Pattern created
4. Pattern loaded via load_pattern()
   ├─ Dimensions extracted
   ├─ Frames loaded
   ├─ Metadata parsed
   └─ UI updated
5. User modifies pattern (paint, add frames, etc.)
6. User exports to new format
```

**Linked Features**: DT-2, DT-4, DT-7, DT-3

---

## Pattern State Management

### State Updates

When pattern state changes, the following sequence occurs:

```
Pattern Modified
    ↓
PatternState Updated
    ↓
Signals Emitted
    ├─→ FrameManager notified
    ├─→ LayerManager notified
    ├─→ CanvasController notified
    └─→ UI components notified
    ↓
UI Refresh
    ├─→ Canvas redraw
    ├─→ Timeline refresh
    ├─→ Layer panel update
    ├─→ Status labels update
    └─→ Action inspector update (if applicable)
```

### State Synchronization

The Design Tools Tab maintains consistency through:

1. **Single Source of Truth**: PatternState holds the pattern
2. **Manager Updates**: All managers receive state updates
3. **Signal Propagation**: State changes emit signals
4. **UI Refresh**: UI components subscribe to signals

### Source of Truth Clarification

**PatternState vs LayerManager Relationship**:

- **PatternState.frame pixels** are the **authoritative storage** for persistence and export
- **LayerManager** holds **editing layers** that compose into frame pixels
- `sync_frame_from_layers()` performs a **one-way sync**: layers → frame pixels (not bidirectional)
- PatternState is the source of truth for **persistence** (file I/O, export)
- LayerManager is the source of truth for **editing** (user modifications)
- When layers change, they are composited and synced to PatternState frame pixels
- Frame pixels in PatternState are derived from layers during editing, but become authoritative when saved

---

## Timeline Integration

### Timeline Data Sources

The timeline widget displays data from multiple sources:

1. **Frames**: From PatternState → FrameManager
2. **Layers**: From LayerManager (layer tracks)
3. **Automation**: From AutomationQueueManager (overlays)
4. **Markers**: From DesignToolsTab (start/end range)

### Timeline Update Flow

```
State Change
    ↓
_refresh_timeline() called
    ├─→ Build frame thumbnails
    ├─→ Build layer tracks (from LayerManager)
    ├─→ Build automation overlays (from AutomationQueueManager)
    ├─→ Set markers (start/end frame range)
    └─→ Update playhead position
```

### Layer Tracks

Each layer gets a track in the timeline showing:
- **State 0**: Layer doesn't exist in frame
- **State 1**: Layer exists but hidden
- **State 2**: Layer exists and visible
- **State 3**: Layer exists but empty (no pixels)

**Note**: The "empty" state (State 3) is a **derived state** computed by the Timeline widget, not stored in LayerManager. The Timeline checks if a layer has all-black pixels (or no non-black pixels) to determine if it's empty. LayerManager only stores visibility, opacity, and pixel data - it does not maintain an "empty" flag.

---

## Canvas & Drawing System

### Canvas Rendering

The canvas displays the composite of all visible layers:

```
Load Frame Request
    ↓
_load_current_frame_into_canvas()
    ↓
layer_manager.get_composite_pixels(frame_index)
    ├─→ Get all layers for frame
    ├─→ Filter visible layers
    ├─→ Blend layers (alpha compositing)
    └─→ Return composite pixels
    ↓
canvas.set_frame_pixels(composite)
    ↓
Canvas Widget Redraw
```

### Drawing Operations

When user paints:

```
Mouse Down
    ↓
Save pending state (for undo)
    ↓
Mouse Move / Click
    ↓
_on_canvas_pixel_updated(x, y, color)
    ├─→ Get active layer index
    ├─→ layer_manager.apply_pixel(frame_index, x, y, color, width, height, layer_index)
    ├─→ layer_manager.sync_frame_from_layers(frame_index)
    └─→ Canvas refresh
    ↓
Mouse Up
    ↓
_commit_paint_operation()
    ├─→ Create FrameStateCommand
    └─→ history_manager.push_command()
```

### Brush Broadcast

When "Broadcast to all frames" checkbox is enabled:
- Pixel changes apply to **all frames** in the pattern simultaneously
- Implemented in `_on_canvas_pixel_updated()` method
- When enabled, the method iterates over all frame indices and calls `layer_manager.apply_pixel(frame_index, x, y, color, width, height, layer_index)` for each frame
- Useful for drawing backgrounds or patterns that span entire animations
- The checkbox control is located in the Brushes tab UI

---

## Missing Linkages & Issues

### Identified Issues

1. **Matrix Dimension Change**:
   - When dimensions change via `_on_matrix_dimension_changed()`:
     - ✅ PatternState metadata updated (width, height)
     - ✅ FrameManager: All Frame.pixels arrays resized (frames resized directly)
     - ✅ LayerManager.resize_pixels() called (all layers resized)
     - ✅ Canvas size updated
     - ✅ Timeline thumbnails refreshed
     - ⚠️ **Issue**: Frame pixels may not resize correctly if dimensions shrink (data loss possible)
     - ⚠️ **Issue**: Timeline thumbnails may show incorrect aspect ratio until refresh

2. **Layer Sync Timing**:
   - ✅ Layer pixels → Frame pixels sync happens correctly
   - ⚠️ **Issue**: Canvas refresh may happen before sync completes
   - **Fix**: Ensure sync happens before canvas refresh

3. **Automation Apply**:
   - ✅ Actions applied to frame range correctly
   - ⚠️ **Issue**: Layer sync may not happen after automation
   - **Fix**: Ensure `sync_frame_from_layers()` called after automation

4. **History Management**:
   - ✅ Paint operations saved to history
   - ⚠️ **Issue**: Frame operations (add/delete) may not save to history
   - **Issue**: Layer operations may not save to history

5. **Preview Cache**:
   - ✅ Preview patterns cached for performance (PreviewSimulator caches generated preview frames)
   - ✅ Cache invalidated on pattern modification (via `pattern_modified` signal handler)
   - ✅ Cache cleared when exiting preview mode (`_on_lms_exit_preview()`)
   - **Implementation**: `_lms_preview_snapshot` stores original pattern; preview pattern is swapped in for display
   - **Cache Management**: Cache is automatically cleared when pattern changes or preview is exited

---

## Recommendations

### Short-term Fixes

1. **Ensure layer sync after all pixel operations**
   - Add `sync_frame_from_layers()` calls where missing
   - Verify canvas refresh happens after sync

2. **Add history support for frame/layer operations**
   - Create commands for frame add/delete/duplicate
   - Create commands for layer add/remove
   - Push commands to history manager

3. **Clear preview cache on pattern modification**
   - Clear cache in `pattern_modified` signal handler
   - Invalidate cache when pattern changes

### Long-term Improvements

1. **Unified refresh mechanism**
   - Create single `refresh_all()` method
   - Ensure all UI components update consistently

2. **Better error handling**
   - Add try/except blocks around state updates
   - Show user-friendly error messages

3. **Performance optimization**
   - Debounce rapid UI updates
   - Use background threads for heavy operations

---

## Conclusion

The Design Tools Tab is a complex, feature-rich component with multiple managers handling different aspects of pattern editing. The architecture is sound with clear separation of concerns, but some linkages need attention to ensure state consistency and proper UI updates.

**Key Strengths**:
- ✅ Clear separation of concerns (managers)
- ✅ Signal-based communication
- ✅ Single source of truth (PatternState)
- ✅ Comprehensive feature set

**Areas for Improvement**:
- ⚠️ State synchronization timing
- ⚠️ History management completeness
- ⚠️ Error handling robustness
- ⚠️ Performance optimization opportunities

---

**Document End**

