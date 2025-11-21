# API Reference

**Document Version**: 1.0  
**Last Updated**: 2025-01-XX  
**Purpose**: Comprehensive API reference for all managers, methods, signals, and data structures in the Design Tools Tab

---

## Table of Contents

1. [PatternState](#patternstate)
2. [FrameManager](#framemanager)
3. [LayerManager](#layermanager)
4. [CanvasController](#canvascontroller)
5. [AutomationQueueManager](#automationqueuemanager)
6. [HistoryManager](#historymanager)
7. [ScratchpadManager](#scratchpadmanager)
8. [EffectLibrary](#effectlibrary)
9. [BitmapFontRepository](#bitmapfontrepository)
10. [ImageImporter](#imageimporter)
11. [Export/Import System](#exportimport-system)
12. [PatternInstructionSequence](#patterninstructionsequence)
13. [PresetRepository](#presetrepository)
14. [Signals Reference](#signals-reference)
15. [Data Structures](#data-structures)
16. [Exceptions](#exceptions)

---

## PatternState

**Module**: `domain/pattern_state.py`  
**Base Class**: `QObject`  
**Role**: Single source of truth for the active pattern

### Methods

#### `pattern() -> Optional[Pattern]`
Get current pattern object.

**Returns**:  
- `Optional[Pattern]`: Current pattern, or `None` if no pattern loaded

**Example**:
```python
pattern = pattern_state.pattern()
if pattern is None:
    return  # No pattern loaded
```

---

#### `frames() -> List[Frame]`
Get all frames in the current pattern.

**Returns**:  
- `List[Frame]`: List of all Frame objects

**Example**:
```python
frames = pattern_state.frames()
for frame in frames:
    print(f"Frame duration: {frame.duration_ms}ms")
```

---

#### `metadata() -> PatternMetadata`
Get pattern metadata.

**Returns**:  
- `PatternMetadata`: Pattern metadata object containing width, height, color_order, etc.

**Example**:
```python
metadata = pattern_state.metadata()
print(f"Pattern: {metadata.width}x{metadata.height}")
```

---

#### `width() -> int`
Get matrix width.

**Returns**:  
- `int`: Pattern width in pixels

**Example**:
```python
width = pattern_state.width()  # e.g., 16
```

---

#### `height() -> int`
Get matrix height.

**Returns**:  
- `int`: Pattern height in pixels

**Example**:
```python
height = pattern_state.height()  # e.g., 16
```

---

#### `set_pattern(pattern: Pattern) -> None`
Load a new pattern.

**Parameters**:  
- `pattern` (Pattern): Pattern object to load

**Raises**:  
- `ValueError`: If pattern is None or invalid

**Example**:
```python
new_pattern = Pattern.create_blank(width=32, height=32, frames=5)
pattern_state.set_pattern(new_pattern)
```

---

## FrameManager

**Module**: `domain/frames.py`  
**Base Class**: `QObject`  
**Role**: Manages frame operations (add, delete, duplicate, move, duration)

### Methods

#### `add() -> int`
Add a new blank frame.

**Returns**:  
- `int`: Index of the newly created frame

**Signals Emitted**:  
- `frames_changed.emit()`

**Example**:
```python
new_frame_index = frame_manager.add()
```

---

#### `duplicate(index: int) -> int`
Duplicate an existing frame.

**Parameters**:  
- `index` (int): Index of frame to duplicate

**Returns**:  
- `int`: Index of the duplicate frame

**Raises**:  
- `IndexError`: If index is out of range

**Signals Emitted**:  
- `frames_changed.emit()`

**Example**:
```python
duplicate_index = frame_manager.duplicate(0)  # Duplicate frame 0
```

---

#### `delete(index: int) -> None`
Delete a frame.

**Parameters**:  
- `index` (int): Index of frame to delete

**Raises**:  
- `IndexError`: If index is out of range
- `ValueError`: If trying to delete the last frame

**Signals Emitted**:  
- `frames_changed.emit()`

**Example**:
```python
frame_manager.delete(1)  # Delete frame 1
```

---

#### `move(src: int, dest: int) -> None`
Move/reorder frames.

**Parameters**:  
- `src` (int): Source frame index
- `dest` (int): Destination frame index

**Raises**:  
- `IndexError`: If src or dest is out of range

**Signals Emitted**:  
- `frames_changed.emit()`

**Example**:
```python
frame_manager.move(src=0, dest=2)  # Move frame 0 to position 2
```

---

#### `select(index: int) -> None`
Select active frame.

**Parameters**:  
- `index` (int): Frame index to select

**Raises**:  
- `IndexError`: If index is out of range

**Signals Emitted**:  
- `frame_index_changed.emit(int)`

**Example**:
```python
frame_manager.select(2)  # Select frame 2
```

---

#### `set_duration(index: int, duration_ms: int) -> None`
Set frame duration.

**Parameters**:  
- `index` (int): Frame index
- `duration_ms` (int): Duration in milliseconds

**Raises**:  
- `IndexError`: If index is out of range
- `ValueError`: If duration_ms is negative

**Signals Emitted**:  
- `frame_duration_changed.emit(int, int)` - (frame_index, duration_ms)

**Example**:
```python
frame_manager.set_duration(frame_index=0, duration_ms=200)
```

---

#### `frame(index: int) -> Frame`
Get frame by index.

**Parameters**:  
- `index` (int): Frame index

**Returns**:  
- `Frame`: Frame object

**Raises**:  
- `IndexError`: If index is out of range

**Example**:
```python
frame = frame_manager.frame(0)
pixels = frame.pixels
```

---

#### `current_index() -> int`
Get current frame index.

**Returns**:  
- `int`: Current frame index

**Example**:
```python
current = frame_manager.current_index()
```

---

### Signals

#### `frame_index_changed.emit(int)`
Emitted when frame selection changes.

**Parameters**:  
- `int`: New frame index

**Listeners**:  
- DesignToolsTab → `_on_manager_frame_selected()`

---

#### `frame_duration_changed.emit(int, int)`
Emitted when frame duration changes.

**Parameters**:  
- `int`: Frame index
- `int`: New duration in milliseconds

**Listeners**:  
- DesignToolsTab → `_on_manager_duration_changed()`

---

#### `frames_changed.emit()`
Emitted when frame structure changes (add/delete/duplicate/reorder).

**Listeners**:  
- DesignToolsTab → `_refresh_timeline()`, `_refresh_lms_frame_bindings()`

---

## LayerManager

**Module**: `domain/layers.py`  
**Base Class**: `QObject`  
**Role**: Multi-layer management per frame with compositing

### Methods

#### `get_layers(frame_index: int) -> List[Layer]`
Get all layers for a frame.

**Parameters**:  
- `frame_index` (int): Frame index

**Returns**:  
- `List[Layer]`: List of Layer objects (creates default layer if none exist)

**Raises**:  
- `IndexError`: If frame_index is out of range

**Example**:
```python
layers = layer_manager.get_layers(frame_index=0)
for layer in layers:
    print(f"Layer: {layer.name}, visible: {layer.visible}")
```

---

#### `add_layer(frame_index: int, name: str) -> int`
Add a new layer.

**Parameters**:  
- `frame_index` (int): Frame index
- `name` (str): Layer name

**Returns**:  
- `int`: Index of the newly created layer

**Raises**:  
- `IndexError`: If frame_index is out of range
- `ValueError`: If name is empty

**Signals Emitted**:  
- `layer_added.emit(int, int)` - (frame_index, layer_index)
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
new_layer_index = layer_manager.add_layer(
    frame_index=0,
    name="Background Layer"
)
```

---

#### `remove_layer(frame_index: int, layer_index: int) -> None`
Remove a layer.

**Parameters**:  
- `frame_index` (int): Frame index
- `layer_index` (int): Layer index to remove

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range
- `ValueError`: If trying to remove the last layer

**Signals Emitted**:  
- `layer_removed.emit(int, int)` - (frame_index, layer_index)
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
layer_manager.remove_layer(frame_index=0, layer_index=1)
```

---

#### `apply_pixel(frame_index: int, x: int, y: int, colour: Optional[Color], width: int, height: int, layer_index: int = 0) -> None`
Apply a pixel to a specific layer.

**Parameters**:  
- `frame_index` (int): Frame index
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `colour` (Optional[Color]): RGB color tuple (r, g, b) or None for black
- `width` (int): Pattern width (for bounds checking)
- `height` (int): Pattern height (for bounds checking)
- `layer_index` (int): Layer index (default: 0)

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range
- `ValueError`: If x or y is out of bounds

**Signals Emitted**:  
- `pixel_changed.emit(int, int, int, tuple)` - (frame_index, x, y, color)
- `frame_pixels_changed.emit(int)` - (frame_index)

**Example**:
```python
layer_manager.apply_pixel(
    frame_index=0,
    x=5,
    y=10,
    colour=(255, 0, 0),  # Red
    width=16,
    height=16,
    layer_index=0
)
```

---

#### `get_composite_pixels(frame_index: int) -> List[RGB]`
Get composite (blended) pixels from all visible layers.

**Parameters**:  
- `frame_index` (int): Frame index

**Returns**:  
- `List[RGB]`: List of RGB tuples representing the composite

**Raises**:  
- `IndexError`: If frame_index is out of range

**Note**: Uses alpha blending from bottom to top layers.

**Example**:
```python
composite = layer_manager.get_composite_pixels(frame_index=0)
# Returns [(r, g, b), ...] with all visible layers alpha-blended
```

---

#### `sync_frame_from_layers(frame_index: int) -> None`
Update frame pixels from layer composite (one-way sync: layers → frame).

**Parameters**:  
- `frame_index` (int): Frame index

**Raises**:  
- `IndexError`: If frame_index is out of range

**Note**: This is the one-way sync point from layers to frames.

**Example**:
```python
layer_manager.sync_frame_from_layers(frame_index=0)
# Updates PatternState.frame.pixels from layer composite
```

---

#### `resize_pixels(width: int, height: int) -> None`
Resize all layers in all frames.

**Parameters**:  
- `width` (int): New width
- `height` (int): New height

**Raises**:  
- `ValueError`: If width or height is ≤ 0

**Signals Emitted**:  
- `frame_pixels_changed.emit(int)` - For all frames

**Example**:
```python
layer_manager.resize_pixels(width=32, height=32)
```

---

#### `replace_pixels(frame_index: int, pixels: List[RGB], layer_index: int = 0) -> None`
Replace all pixels in a layer.

**Parameters**:  
- `frame_index` (int): Frame index
- `pixels` (List[RGB]): List of RGB tuples (must match width × height)
- `layer_index` (int): Layer index (default: 0)

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range
- `ValueError`: If pixels length doesn't match width × height

**Signals Emitted**:  
- `frame_pixels_changed.emit(int)` - (frame_index)

**Example**:
```python
new_pixels = [(255, 255, 255)] * (16 * 16)  # White pixels
layer_manager.replace_pixels(
    frame_index=0,
    pixels=new_pixels,
    layer_index=0
)
```

---

#### `move_layer(frame_index: int, from_index: int, to_index: int) -> bool`
Move/reorder layers.

**Parameters**:  
- `frame_index` (int): Frame index
- `from_index` (int): Source layer index
- `to_index` (int): Destination layer index

**Returns**:  
- `bool`: True if successful, False if indices invalid

**Signals Emitted**:  
- `layer_moved.emit(int, int, int)` - (frame_index, from_index, to_index)
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
success = layer_manager.move_layer(
    frame_index=0,
    from_index=1,
    to_index=0
)
```

---

#### `set_layer_visible(frame_index: int, layer_index: int, visible: bool) -> None`
Set layer visibility.

**Parameters**:  
- `frame_index` (int): Frame index
- `layer_index` (int): Layer index
- `visible` (bool): Visibility flag

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range

**Signals Emitted**:  
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
layer_manager.set_layer_visible(frame_index=0, layer_index=1, visible=False)
```

---

#### `set_layer_opacity(frame_index: int, layer_index: int, opacity: float) -> None`
Set layer opacity.

**Parameters**:  
- `frame_index` (int): Frame index
- `layer_index` (int): Layer index
- `opacity` (float): Opacity value (0.0-1.0, clamped automatically)

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range

**Signals Emitted**:  
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
layer_manager.set_layer_opacity(frame_index=0, layer_index=1, opacity=0.5)
```

---

#### `set_layer_name(frame_index: int, layer_index: int, name: str) -> None`
Set layer name.

**Parameters**:  
- `frame_index` (int): Frame index
- `layer_index` (int): Layer index
- `name` (str): New layer name

**Raises**:  
- `IndexError`: If frame_index or layer_index is out of range
- `ValueError`: If name is empty

**Signals Emitted**:  
- `layers_changed.emit(int)` - (frame_index)

**Example**:
```python
layer_manager.set_layer_name(frame_index=0, layer_index=0, name="Background")
```

---

### Signals

#### `layers_changed.emit(int)`
Emitted when layer structure changes.

**Parameters**:  
- `int`: Frame index where layers changed

**Listeners**:  
- DesignToolsTab → `_on_layers_structure_updated()`

---

#### `layer_added.emit(int, int)`
Emitted when a layer is added.

**Parameters**:  
- `int`: Frame index
- `int`: Layer index

**Listeners**:  
- DesignToolsTab → `_on_layers_structure_updated()`

---

#### `layer_removed.emit(int, int)`
Emitted when a layer is removed.

**Parameters**:  
- `int`: Frame index
- `int`: Layer index

**Listeners**:  
- DesignToolsTab → `_on_layers_structure_updated()`

---

#### `layer_moved.emit(int, int, int)`
Emitted when a layer is reordered.

**Parameters**:  
- `int`: Frame index
- `int`: From index
- `int`: To index

**Listeners**:  
- DesignToolsTab → `_on_layers_structure_updated()`

---

#### `frame_pixels_changed.emit(int)`
Emitted when layer pixels change.

**Parameters**:  
- `int`: Frame index

**Listeners**:  
- Canvas refresh (implicit via signal propagation)

---

#### `pixel_changed.emit(int, int, int, tuple)`
Emitted when an individual pixel changes.

**Parameters**:  
- `int`: Frame index
- `int`: X coordinate
- `int`: Y coordinate
- `tuple`: RGB color (r, g, b)

**Note**: Currently emitted but not actively used by DesignToolsTab. Available for future pixel-level tracking or debugging.

---

## CanvasController

**Module**: `domain/canvas.py`  
**Role**: Controls canvas rendering and interaction

### Methods

#### `render_frame(frame_index: int) -> None`
Render a specific frame to canvas.

**Parameters**:  
- `frame_index` (int): Frame index to render

**Raises**:  
- `IndexError`: If frame_index is out of range

**Example**:
```python
canvas_controller.render_frame(frame_index=0)
```

---

#### `set_frame_supplier(callback: Callable[[int], List[RGB]]) -> None`
Set callback for frame data.

**Parameters**:  
- `callback` (Callable[[int], List[RGB]]): Function that takes frame_index and returns List[RGB]

**Example**:
```python
def get_frame_data(frame_index: int) -> List[RGB]:
    return layer_manager.get_composite_pixels(frame_index)

canvas_controller.set_frame_supplier(get_frame_data)
```

---

## AutomationQueueManager

**Module**: `domain/automation/queue.py`  
**Base Class**: `QObject`  
**Role**: Manages automation action queue

### Methods

#### `enqueue(action: DesignAction) -> None`
Add action to queue.

**Parameters**:  
- `action` (DesignAction): Action object to enqueue

**Signals Emitted**:  
- `queue_changed.emit(list)` - (current action list)

**Example**:
```python
action = DesignAction(
    name="Scroll Left",
    action_type="scroll",
    params={"direction": "Left", "step": 1}
)
automation_manager.enqueue(action)
```

---

#### `actions() -> List[DesignAction]`
Get all actions in queue.

**Returns**:  
- `List[DesignAction]`: List of all actions

**Example**:
```python
actions = automation_manager.actions()
```

---

#### `remove(index: int) -> None`
Remove action by index.

**Parameters**:  
- `index` (int): Action index to remove

**Raises**:  
- `IndexError`: If index is out of range

**Signals Emitted**:  
- `queue_changed.emit(list)` - (current action list)

**Example**:
```python
automation_manager.remove(index=2)
```

---

#### `move(src: int, dest: int) -> None`
Reorder actions.

**Parameters**:  
- `src` (int): Source action index
- `dest` (int): Destination action index

**Raises**:  
- `IndexError`: If src or dest is out of range

**Signals Emitted**:  
- `queue_changed.emit(list)` - (current action list)

**Example**:
```python
automation_manager.move(src=0, dest=2)
```

---

#### `clear() -> None`
Clear all actions.

**Signals Emitted**:  
- `queue_changed.emit(list)` - (empty list)

**Example**:
```python
automation_manager.clear()
```

---

### Signals

#### `queue_changed.emit(list)`
Emitted when queue changes.

**Parameters**:  
- `list`: Current action list

**Listeners**:  
- DesignToolsTab → `_on_manager_queue_changed()`

---

## HistoryManager

**Module**: `domain/history.py`  
**Role**: Undo/Redo functionality

### Methods

#### `push_command(command: Command, frame_index: int) -> None`
Save command to history.

**Parameters**:  
- `command` (Command): Command object (e.g., FrameStateCommand)
- `frame_index` (int): Frame index for frame-specific history

**Example**:
```python
command = FrameStateCommand(
    frame_index=0,
    old_state=old_pixels,
    new_state=new_pixels,
    description="Paint pixels"
)
history_manager.push_command(command, frame_index=0)
```

---

#### `undo(frame_index: int) -> Optional[Command]`
Undo last command.

**Parameters**:  
- `frame_index` (int): Frame index

**Returns**:  
- `Optional[Command]`: Command that was undone, or None if no history

**Example**:
```python
undone = history_manager.undo(frame_index=0)
```

---

#### `redo(frame_index: int) -> Optional[Command]`
Redo last undone command.

**Parameters**:  
- `frame_index` (int): Frame index

**Returns**:  
- `Optional[Command]`: Command that was redone, or None if nothing to redo

**Example**:
```python
redone = history_manager.redo(frame_index=0)
```

---

## ScratchpadManager

**Module**: `domain/scratchpads.py`  
**Role**: Temporary storage for reusable patterns

### Methods

#### `create(name: str, pixels: List[RGB]) -> None`
Save pixels to scratchpad.

**Parameters**:  
- `name` (str): Scratchpad name
- `pixels` (List[RGB]): Pixel array to save

**Raises**:  
- `ValueError`: If name is empty or already exists

**Example**:
```python
pixels = [(255, 0, 0)] * (16 * 16)
scratchpad_manager.create(name="Red Background", pixels=pixels)
```

---

#### `list_all() -> List[str]`
List all scratchpad names.

**Returns**:  
- `List[str]`: List of scratchpad names

**Example**:
```python
names = scratchpad_manager.list_all()
```

---

#### `paste(name: str) -> List[RGB]`
Get scratchpad pixels.

**Parameters**:  
- `name` (str): Scratchpad name

**Returns**:  
- `List[RGB]`: Pixel array from scratchpad

**Raises**:  
- `ValueError`: If scratchpad doesn't exist

**Example**:
```python
pixels = scratchpad_manager.paste(name="Red Background")
```

---

#### `delete(name: str) -> None`
Delete scratchpad.

**Parameters**:  
- `name` (str): Scratchpad name

**Raises**:  
- `ValueError`: If scratchpad doesn't exist

**Example**:
```python
scratchpad_manager.delete(name="Red Background")
```

---

## EffectLibrary

**Module**: `domain/effects/library.py`  
**Role**: Discovers and manages visual effects

### Methods

#### `reload() -> None`
Reload effects from disk.

**Example**:
```python
effect_library.reload()
```

---

#### `categories() -> List[str]`
Get all effect categories.

**Returns**:  
- `List[str]`: List of category names

**Example**:
```python
categories = effect_library.categories()
```

---

#### `effects() -> List[EffectDefinition]`
Get all available effects.

**Returns**:  
- `List[EffectDefinition]`: List of effect definitions

**Example**:
```python
effects = effect_library.effects()
```

---

## BitmapFontRepository

**Module**: `domain/text/bitmap_font.py`  
**Role**: Manages bitmap font assets

### Methods

#### `load_font(name: str) -> Optional[BitmapFont]`
Load font by name.

**Parameters**:  
- `name` (str): Font name

**Returns**:  
- `Optional[BitmapFont]`: Font object, or None if not found

**Example**:
```python
font = font_repo.load_font(name="MyCustomFont")
```

---

#### `save_font(font: BitmapFont) -> None`
Save font to disk.

**Parameters**:  
- `font` (BitmapFont): Font object to save

**Example**:
```python
font = BitmapFont(name="MyFont", glyphs={...})
font_repo.save_font(font)
```

---

#### `list_fonts() -> List[str]`
List all available fonts.

**Returns**:  
- `List[str]`: List of font names

**Example**:
```python
fonts = font_repo.list_fonts()
```

---

## ImageImporter

**Module**: Utility functions  
**Role**: Handles image/GIF import operations

### Functions

#### `import_image(path: Path) -> Pattern`
Import single image as pattern.

**Parameters**:  
- `path` (Path): Path to image file (PNG, JPG)

**Returns**:  
- `Pattern`: Pattern object with single frame

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If image format is unsupported

**Example**:
```python
pattern = import_image(Path("image.png"))
```

---

#### `import_gif(path: Path) -> Pattern`
Import GIF as multi-frame pattern.

**Parameters**:  
- `path` (Path): Path to GIF file

**Returns**:  
- `Pattern`: Pattern object with multiple frames (one per GIF frame)

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If GIF format is invalid

**Example**:
```python
pattern = import_gif(Path("animation.gif"))
```

---

## Export/Import System

**Module**: `core/io/`  
**Role**: Pattern file I/O operations

### Functions

#### `parse_leds_file(path: Path) -> Dict`
Parse LEDS file.

**Parameters**:  
- `path` (Path): Path to LEDS file

**Returns**:  
- `Dict`: Dictionary with metadata, instructions, frame_data

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `LMSFormatError`: If file format is invalid

**Example**:
```python
data = parse_leds_file(Path("pattern.leds"))
```

---

#### `write_leds_file(path: Path, pattern_metadata: Dict, sequence: PatternInstructionSequence, frame_data: Optional[List] = None) -> None`
Write LEDS file.

**Parameters**:  
- `path` (Path): Output file path
- `pattern_metadata` (Dict): Pattern metadata (width, height, frame_count, color_order)
- `sequence` (PatternInstructionSequence): Instruction sequence
- `frame_data` (Optional[List]): Optional frame pixel data

**Raises**:  
- `IOError`: If file cannot be written

**Example**:
```python
write_leds_file(
    path=Path("output.leds"),
    pattern_metadata={"width": 16, "height": 16, "frame_count": 10},
    sequence=instruction_sequence
)
```

---

#### `parse_dat_file(path: Path) -> Pattern`
Parse DAT file.

**Parameters**:  
- `path` (Path): Path to DAT file

**Returns**:  
- `Pattern`: Pattern object

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file format is invalid

**Example**:
```python
pattern = parse_dat_file(Path("pattern.dat"))
```

---

#### `parse_hex_file(path: Path) -> Pattern`
Parse HEX file.

**Parameters**:  
- `path` (Path): Path to HEX file

**Returns**:  
- `Pattern`: Pattern object

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If Intel HEX format is invalid

**Example**:
```python
pattern = parse_hex_file(Path("pattern.hex"))
```

---

#### `parse_bin_stream(stream: BinaryIO) -> Pattern`
Parse BIN file stream.

**Parameters**:  
- `stream` (BinaryIO): Binary file stream

**Returns**:  
- `Pattern`: Pattern object

**Raises**:  
- `ValueError`: If stream format is invalid

**Example**:
```python
with open("pattern.bin", "rb") as f:
    pattern = parse_bin_stream(f)
```

---

## PatternInstructionSequence

**Module**: `core/automation/instructions.py`  
**Role**: Ordered collection of LMS pattern instructions (Data Structure)

### Methods

#### `add(instruction: PatternInstruction) -> None`
Add instruction to end of sequence.

**Parameters**:  
- `instruction` (PatternInstruction): Instruction to add

**Example**:
```python
sequence.add(instruction)
```

---

#### `insert(index: int, instruction: PatternInstruction) -> None`
Insert instruction at specific index.

**Parameters**:  
- `index` (int): Insertion index
- `instruction` (PatternInstruction): Instruction to insert

**Raises**:  
- `IndexError`: If index is out of range

**Example**:
```python
sequence.insert(index=0, instruction=instruction)
```

---

#### `remove_at(index: int) -> None`
Remove instruction by index.

**Parameters**:  
- `index` (int): Index to remove

**Raises**:  
- `IndexError`: If index is out of range

**Example**:
```python
sequence.remove_at(index=2)
```

---

#### `move(old_index: int, new_index: int) -> None`
Reorder instructions.

**Parameters**:  
- `old_index` (int): Source index
- `new_index` (int): Destination index

**Raises**:  
- `IndexError`: If indices are out of range

**Example**:
```python
sequence.move(old_index=0, new_index=2)
```

---

#### `to_list() -> List[Dict]`
Serialize to list.

**Returns**:  
- `List[Dict]`: Serialized instruction list (suitable for JSON)

**Example**:
```python
sequence_list = sequence.to_list()
```

---

#### `from_list(payload: List[Dict]) -> PatternInstructionSequence`
Deserialize from list.

**Parameters**:  
- `payload` (List[Dict]): Serialized instruction list

**Returns**:  
- `PatternInstructionSequence`: New sequence object

**Example**:
```python
restored = PatternInstructionSequence.from_list(sequence_list)
```

---

## PresetRepository

**Module**: `domain/automation/presets.py`  
**Role**: Manages automation action presets

### Methods

#### `upsert(name: str, actions: List[DesignAction]) -> None`
Save or update preset.

**Parameters**:  
- `name` (str): Preset name
- `actions` (List[DesignAction]): Action list

**Example**:
```python
preset_repo.upsert(name="MyPreset", actions=actions)
```

---

#### `get(name: str) -> Optional[List[DesignAction]]`
Load preset.

**Parameters**:  
- `name` (str): Preset name

**Returns**:  
- `Optional[List[DesignAction]]`: Action list, or None if not found

**Example**:
```python
actions = preset_repo.get(name="MyPreset")
```

---

#### `delete(name: str) -> None`
Delete preset.

**Parameters**:  
- `name` (str): Preset name

**Raises**:  
- `ValueError`: If preset doesn't exist

**Example**:
```python
preset_repo.delete(name="MyPreset")
```

---

#### `names() -> List[str]`
List all preset names.

**Returns**:  
- `List[str]`: List of preset names

**Example**:
```python
names = preset_repo.names()
```

---

#### `exists(name: str) -> bool`
Check if preset exists.

**Parameters**:  
- `name` (str): Preset name

**Returns**:  
- `bool`: True if exists, False otherwise

**Example**:
```python
if preset_repo.exists(name="MyPreset"):
    actions = preset_repo.get(name="MyPreset")
```

---

#### `duplicate(old_name: str, new_name: str) -> None`
Duplicate preset.

**Parameters**:  
- `old_name` (str): Source preset name
- `new_name` (str): New preset name

**Raises**:  
- `ValueError`: If old_name doesn't exist or new_name already exists

**Example**:
```python
preset_repo.duplicate(old_name="MyPreset", new_name="MyPreset Copy")
```

---

#### `rename(old_name: str, new_name: str) -> None`
Rename preset.

**Parameters**:  
- `old_name` (str): Current preset name
- `new_name` (str): New preset name

**Raises**:  
- `ValueError`: If old_name doesn't exist or new_name already exists

**Example**:
```python
preset_repo.rename(old_name="MyPreset", new_name="RenamedPreset")
```

---

#### `export_to_path(name: str, path: Path) -> None`
Export preset to file.

**Parameters**:  
- `name` (str): Preset name
- `path` (Path): Output file path

**Raises**:  
- `ValueError`: If preset doesn't exist
- `IOError`: If file cannot be written

**Example**:
```python
preset_repo.export_to_path(name="MyPreset", path=Path("preset.json"))
```

---

#### `import_from_path(path: Path, overwrite: bool = False) -> List[str]`
Import preset from file.

**Parameters**:  
- `path` (Path): Input file path
- `overwrite` (bool): Whether to overwrite existing presets

**Returns**:  
- `List[str]`: List of imported preset names

**Raises**:  
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If overwrite=False and preset already exists

**Example**:
```python
imported = preset_repo.import_from_path(path=Path("preset.json"), overwrite=False)
```

---

## Signals Reference

### DesignToolsTab Signals

#### `pattern_modified.emit()`
Emitted when pattern has been modified.

**Listeners**:  
- MainWindow (external)
- Internal UI refresh handlers

---

#### `pattern_created.emit(Pattern)`
Emitted when new pattern is created.

**Parameters**:  
- `Pattern`: The newly created Pattern object

**Listeners**:  
- MainWindow (external)

---

### Canvas Widget Signals

#### `pixel_updated.emit(int, int, tuple)`
Emitted when pixel is clicked/painted.

**Parameters**:  
- `int`: X coordinate
- `int`: Y coordinate
- `tuple`: RGB color (r, g, b)

**Listeners**:  
- DesignToolsTab → `_on_canvas_pixel_updated()`

---

#### `painting_finished.emit()`
Emitted when painting operation is completed (mouse released).

**Listeners**:  
- DesignToolsTab → `_commit_paint_operation()`

---

### Timeline Widget Signals

#### `frameSelected.emit(int)`
Emitted when frame is selected in timeline.

**Parameters**:  
- `int`: Selected frame index

**Listeners**:  
- DesignToolsTab → `_on_frame_selected()`

---

#### `playheadDragged.emit(int)`
Emitted when playhead is dragged.

**Parameters**:  
- `int`: New playhead frame index

**Listeners**:  
- DesignToolsTab → `_on_timeline_playhead_dragged()`

---

## Data Structures

### Pattern

**Properties**:
- `frames: List[Frame]` - List of Frame objects
- `metadata: PatternMetadata` - Pattern metadata

**Methods**:
- `create_blank(width: int, height: int, frames: int) -> Pattern` - Create blank pattern

---

### Frame

**Properties**:
- `pixels: List[RGB]` - Pixel array (width × height RGB tuples)
- `duration_ms: int` - Frame duration in milliseconds

---

### Layer

**Properties**:
- `name: str` - Layer name
- `pixels: List[RGB]` - Pixel array
- `visible: bool` - Visibility flag
- `opacity: float` - Opacity (0.0-1.0)

---

### PatternInstruction

**Properties**:
- `source: LayerBinding` - Source frame binding
- `instruction: LMSInstruction` - LMS instruction
- `layer2: Optional[LayerBinding]` - Optional secondary binding
- `mask: Optional[LayerBinding]` - Optional mask binding

---

### DesignAction

**Properties**:
- `name: str` - Action name
- `action_type: str` - Action type (e.g., "scroll", "rotate")
- `params: Dict` - Action parameters

---

## Exceptions

### LMSFormatError

Raised when LEDS file format is invalid.

**Example**:
```python
try:
    data = parse_leds_file(path)
except LMSFormatError as e:
    print(f"Invalid LEDS format: {e}")
```

---

### IndexError

Raised when frame or layer index is out of range.

**Example**:
```python
try:
    frame = frame_manager.frame(100)
except IndexError:
    print("Frame index out of range")
```

---

### ValueError

Raised when parameter validation fails.

**Example**:
```python
try:
    frame_manager.set_duration(0, -100)  # Negative duration
except ValueError:
    print("Invalid duration")
```

---

## References

- DESIGN_TOOLS_TAB_COMPLETE_OVERVIEW.md - Complete architecture overview
- PERFORMANCE_CONSIDERATIONS.md - Performance documentation
- `domain/` - Manager implementations
- `core/io/` - Export/Import system implementations

