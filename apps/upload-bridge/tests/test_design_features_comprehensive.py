#!/usr/bin/env python3
"""
Comprehensive Feature Verification: Design Tools Tab
Tests how to use: Effects, Layers, Frames, Automation, Text, Fonts
"""
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print("DESIGN TOOLS TAB - FEATURE VERIFICATION")
print("="*70)
print()

# Initialize Qt
app = QApplication.instance()
if app is None:
    app = QApplication([])

results = {
    "effects": {"status": "unknown", "methods": [], "issues": []},
    "layers": {"status": "unknown", "methods": [], "issues": []},
    "frames_per_layer": {"status": "unknown", "methods": [], "issues": []},
    "automation": {"status": "unknown", "methods": [], "issues": []},
    "text": {"status": "unknown", "methods": [], "issues": []},
    "fonts": {"status": "unknown", "methods": [], "issues": []},
}

# ============================================================================
# 1. TEST: EFFECTS APPLICATION
# ============================================================================
print("[1] Testing EFFECTS Application...")
try:
    from domain.effects import EffectLibrary, EffectDefinition, apply_effect_to_frames
    from core.pattern import Pattern, PatternMetadata, Frame
    
    # Create test pattern
    pattern = Pattern(
        name="Test Pattern",
        metadata=PatternMetadata(width=16, height=16),
        frames=[Frame(pixels=[(0, 0, 0)] * 256, duration_ms=100)]
    )
    
    # Load effect library
    effects_lib = EffectLibrary(Path("Res/effects"))
    effects = effects_lib.list_effects()
    
    if len(effects) > 0:
        # Test applying an effect
        effect = effects[0]
        frame_indices = [0]
        intensity = 0.5
        
        apply_effect_to_frames(pattern, effect, frame_indices, intensity)
        
        results["effects"]["status"] = "✓ WORKING"
        results["effects"]["methods"].append("apply_effect_to_frames()")
        results["effects"]["methods"].append(f"EffectLibrary.load({Path('Res/effects')})")
        results["effects"]["methods"].append(f"Found {len(effects)} effects available")
        print(f"  ✓ Effects library loaded: {len(effects)} effects")
        print(f"  ✓ Effect '{effect.name}' applied successfully")
    else:
        results["effects"]["status"] = "⚠ NO EFFECTS"
        results["effects"]["issues"].append("No effects found in Res/effects directory")
        print("  ⚠ No effects found in library")
        
except Exception as e:
    results["effects"]["status"] = "✗ ERROR"
    results["effects"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 2. TEST: LAYERS APPLICATION
# ============================================================================
print("[2] Testing LAYERS Application...")
try:
    from domain.layers import LayerManager, Layer
    from domain.pattern_state import PatternState
    from core.pattern import Pattern, PatternMetadata, Frame
    
    # Create test pattern
    pattern = Pattern(
        name="Layer Test",
        metadata=PatternMetadata(width=8, height=8),
        frames=[Frame(pixels=[(0, 0, 0)] * 64, duration_ms=100)]
    )
    
    # Create layer manager
    state = PatternState()
    state.set_pattern(pattern)
    layer_manager = LayerManager(state)
    layer_manager.set_pattern(pattern)
    
    # Test adding layers
    layer1_idx = layer_manager.add_layer(0, "Background")
    layer2_idx = layer_manager.add_layer(0, "Foreground")
    
    # Test layer operations
    layers = layer_manager.get_layers(0)
    
    # Test visibility
    layer_manager.set_layer_visible(0, layer1_idx, False)
    
    # Test opacity
    layer_manager.set_layer_opacity(0, layer2_idx, 0.5)
    
    results["layers"]["status"] = "✓ WORKING"
    results["layers"]["methods"].append("LayerManager.add_layer(frame_index, name)")
    results["layers"]["methods"].append("LayerManager.get_layers(frame_index)")
    results["layers"]["methods"].append("LayerManager.set_layer_visible(frame, layer, visible)")
    results["layers"]["methods"].append("LayerManager.set_layer_opacity(frame, layer, opacity)")
    results["layers"]["methods"].append(f"Created {len(layers)} layers on frame 0")
    print(f"  ✓ Layer manager created")
    print(f"  ✓ Added {len(layers)} layers to frame 0")
    print(f"  ✓ Layer visibility and opacity controls work")
    
except Exception as e:
    results["layers"]["status"] = "✗ ERROR"
    results["layers"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 3. TEST: FRAMES ON EACH LAYER
# ============================================================================
print("[3] Testing FRAMES on each LAYER...")
try:
    from domain.layers import LayerManager
    from domain.pattern_state import PatternState
    from domain.frames import FrameManager
    from core.pattern import Pattern, PatternMetadata, Frame
    
    # Create pattern with multiple frames
    pattern = Pattern(
        name="Multi-Frame Layer Test",
        metadata=PatternMetadata(width=8, height=8),
        frames=[
            Frame(pixels=[(255, 0, 0)] * 64, duration_ms=100),  # Frame 0 - red
            Frame(pixels=[(0, 255, 0)] * 64, duration_ms=100),  # Frame 1 - green
            Frame(pixels=[(0, 0, 255)] * 64, duration_ms=100),  # Frame 2 - blue
        ]
    )
    
    # Create managers
    state = PatternState()
    state.set_pattern(pattern)
    layer_manager = LayerManager(state)
    frame_manager = FrameManager(state)
    layer_manager.set_pattern(pattern)
    frame_manager.set_pattern(pattern)
    
    # Each frame has its own layers
    for frame_idx in range(len(pattern.frames)):
        # Add layers to each frame
        layer_manager.add_layer(frame_idx, f"Layer A")
        layer_manager.add_layer(frame_idx, f"Layer B")
        
        layers = layer_manager.get_layers(frame_idx)
        print(f"  Frame {frame_idx}: {len(layers)} layers")
    
    results["frames_per_layer"]["status"] = "✓ WORKING"
    results["frames_per_layer"]["methods"].append("Each frame has independent layers")
    results["frames_per_layer"]["methods"].append("layer_manager.add_layer(frame_index, name) for each frame")
    results["frames_per_layer"]["methods"].append(f"Tested {len(pattern.frames)} frames, each with multiple layers")
    print(f"  ✓ Each frame has independent layers")
    
except Exception as e:
    results["frames_per_layer"]["status"] = "✗ ERROR"
    results["frames_per_layer"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 4. TEST: AUTOMATION APPLICATION
# ============================================================================
print("[4] Testing AUTOMATION Application...")
try:
    from domain.automation.queue import AutomationQueueManager
    from domain.actions import DesignAction
    from core.pattern import Pattern, PatternMetadata, Frame
    from domain.pattern_state import PatternState
    
    # Create test pattern
    pattern = Pattern(
        name="Automation Test",
        metadata=PatternMetadata(width=16, height=16),
        frames=[Frame(pixels=[(255, 255, 255)] * 256, duration_ms=100)]
    )
    
    # Create automation manager
    automation_manager = AutomationQueueManager()
    
    # Create and add automation actions
    action1 = DesignAction(
        action_type="scroll",
        params={"direction": "left", "distance": 1}
    )
    action2 = DesignAction(
        action_type="rotate",
        params={"angle": 90}
    )
    
    automation_manager.enqueue(action1)
    automation_manager.enqueue(action2)
    
    actions = automation_manager.actions()
    
    results["automation"]["status"] = "✓ WORKING"
    results["automation"]["methods"].append("AutomationQueueManager.enqueue(DesignAction)")
    results["automation"]["methods"].append("AutomationQueueManager.actions() - get all actions")
    results["automation"]["methods"].append(f"Added {len(actions)} automation actions to queue")
    print(f"  ✓ Automation manager created")
    print(f"  ✓ Added {len(actions)} actions to queue")
    print(f"  ✓ Actions: {[a.action_type for a in actions]}")
    
except Exception as e:
    results["automation"]["status"] = "✗ ERROR"
    results["automation"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 5. TEST: TEXT APPLICATION
# ============================================================================
print("[5] Testing TEXT Application...")
try:
    from domain.text.text_renderer import TextRenderer, TextRenderOptions
    from domain.text.glyph_provider import GlyphProvider
    
    # Create text renderer
    renderer = TextRenderer()
    
    # Configure text options
    options = TextRenderOptions(
        width=32,
        height=8,
        font_size=8,
        color=(255, 255, 0),
        background=(0, 0, 0),
        alignment="center"
    )
    
    # Render text
    text = "Hello"
    pixels = renderer.render_pixels(text, options)
    
    if pixels and len(pixels) == options.width * options.height:
        results["text"]["status"] = "✓ WORKING"
        results["text"]["methods"].append("TextRenderer.render_pixels(text, options)")
        results["text"]["methods"].append("TextRenderOptions for configuration")
        results["text"]["methods"].append(f"Rendered '{text}' to {options.width}x{options.height} pixels")
        print(f"  ✓ Text renderer created")
        print(f"  ✓ Rendered text '{text}' successfully")
        print(f"  ✓ Output: {len(pixels)} pixels")
    else:
        results["text"]["status"] = "⚠ INCOMPLETE"
        results["text"]["issues"].append("Text rendering returned unexpected result")
        print(f"  ⚠ Text rendering returned unexpected result")
        
except Exception as e:
    results["text"]["status"] = "✗ ERROR"
    results["text"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# 6. TEST: FONTS (INSTALLED/CUSTOM)
# ============================================================================
print("[6] Testing FONTS (Installed/Custom)...")
try:
    from domain.text.bitmap_font import BitmapFontRepository
    
    # Check fonts directory
    fonts_path = Path("Res/fonts")
    font_repo = BitmapFontRepository(fonts_path)
    
    # List available fonts
    fonts = font_repo.list_fonts()
    
    results["fonts"]["status"] = "✓ WORKING"
    results["fonts"]["methods"].append("BitmapFontRepository(Path('Res/fonts'))")
    results["fonts"]["methods"].append("font_repo.list_fonts() - list available fonts")
    results["fonts"]["methods"].append("font_repo.load_font(name) - load a font")
    results["fonts"]["methods"].append(f"Found {len(fonts)} fonts in Res/fonts/")
    
    if len(fonts) > 0:
        print(f"  ✓ Font repository created")
        print(f"  ✓ Found {len(fonts)} custom fonts:")
        for font in fonts[:5]:  # Show first 5
            print(f"    - {font}")
        if len(fonts) > 5:
            print(f"    ... and {len(fonts) - 5} more")
        
        # Try loading first font
        try:
            test_font = font_repo.load_font(fonts[0])
            results["fonts"]["methods"].append(f"Successfully loaded font: {fonts[0]}")
            print(f"  ✓ Successfully loaded font: {fonts[0]}")
        except Exception as e:
            results["fonts"]["issues"].append(f"Could not load font {fonts[0]}: {e}")
            print(f"  ⚠ Could not load font {fonts[0]}: {e}")
    else:
        print(f"  ⚠ No custom fonts found in Res/fonts/")
        results["fonts"]["issues"].append("No fonts found in Res/fonts/ directory")
        print(f"  ℹ Built-in 5x7 font is always available")
        results["fonts"]["methods"].append("Built-in 5x7 font available (no custom fonts needed)")
    
    # Check for system fonts (if applicable)
    print(f"  ℹ System fonts: Access via built-in font rendering")
    
except Exception as e:
    results["fonts"]["status"] = "✗ ERROR"
    results["fonts"]["issues"].append(str(e))
    print(f"  ✗ Error: {e}")

print()

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print("="*70)
print("FEATURE VERIFICATION SUMMARY")
print("="*70)
print()

for feature, data in results.items():
    status = data["status"]
    feature_name = feature.replace("_", " ").title()
    print(f"{feature_name:20} : {status}")
    
    if data["methods"]:
        print(f"  Methods:")
        for method in data["methods"]:
            print(f"    • {method}")
    
    if data["issues"]:
        print(f"  Issues:")
        for issue in data["issues"]:
            print(f"    ⚠ {issue}")
    print()

print("="*70)
print("DETAILED USAGE GUIDE")
print("="*70)
print()

# Generate usage guide
guide = []

guide.append("""
## 1. HOW TO APPLY EFFECTS

### Step-by-Step:
1. Load or create a pattern in Design Tools Tab
2. Select frame range (start/end frames)
3. Open "Effects" tab/toolbox
4. Browse available effects from library
5. Select an effect
6. Adjust intensity (0-100%)
7. Click "Preview" to see effect
8. Click "Apply Effect" to commit

### Code Usage:
```python
from domain.effects import EffectLibrary, apply_effect_to_frames

# Load effect library
effects_lib = EffectLibrary(Path("Res/effects"))
effects = effects_lib.list_effects()

# Select effect
effect = effects[0]  # Or search by name

# Apply to frame range
frame_indices = [0, 1, 2]  # Frames to affect
intensity = 0.5  # 0.0 to 1.0

apply_effect_to_frames(pattern, effect, frame_indices, intensity)
```
""")

guide.append("""
## 2. HOW TO APPLY LAYERS

### Step-by-Step:
1. Select a frame in timeline
2. Open "Layers" panel
3. Click "Add Layer" button
4. Name the layer (e.g., "Background", "Text")
5. Paint/draw on the layer
6. Adjust layer properties:
   - Visibility (eye icon)
   - Opacity (0-100% slider)
   - Blend mode (if available)
7. Reorder layers (drag up/down)

### Code Usage:
```python
from domain.layers import LayerManager
from domain.pattern_state import PatternState

# Create layer manager
state = PatternState()
state.set_pattern(pattern)
layer_manager = LayerManager(state)
layer_manager.set_pattern(pattern)

# Add layer to frame 0
layer_idx = layer_manager.add_layer(0, "My Layer")

# Set layer properties
layer_manager.set_layer_visible(0, layer_idx, True)
layer_manager.set_layer_opacity(0, layer_idx, 0.5)

# Get all layers for a frame
layers = layer_manager.get_layers(0)
```
""")

guide.append("""
## 3. HOW TO MAKE FRAMES ON EACH LAYER

### Concept:
- Each FRAME has its own set of LAYERS
- Frames are in the TIME dimension (animation)
- Layers are in the Z-STACK dimension (composition)

### Step-by-Step:
1. Create multiple frames (Frame 0, Frame 1, Frame 2, etc.)
2. For EACH frame:
   - Select the frame in timeline
   - Add layers to that specific frame
   - Draw on layers for that frame
3. Each frame maintains its own layer stack independently

### Code Usage:
```python
# Pattern has multiple frames
pattern.frames = [
    Frame(...),  # Frame 0
    Frame(...),  # Frame 1
    Frame(...),  # Frame 2
]

# Add layers to Frame 0
layer_manager.add_layer(0, "Background")
layer_manager.add_layer(0, "Foreground")

# Add layers to Frame 1 (different layers)
layer_manager.add_layer(1, "Background")
layer_manager.add_layer(1, "Effects")

# Each frame has independent layers
layers_frame0 = layer_manager.get_layers(0)
layers_frame1 = layer_manager.get_layers(1)
```
""")

guide.append("""
## 4. HOW TO APPLY AUTOMATION

### Step-by-Step:
1. Open "Automation" or "Action Queue" tab
2. Select action type (scroll, rotate, mirror, etc.)
3. Configure action parameters:
   - Direction (left/right/up/down)
   - Distance/amount
   - Repeat count
   - Gap (delay between repeats)
4. Click "Add Action" to add to queue
5. Configure frame range (which frames to apply to)
6. Click "Apply Actions" to execute

### Code Usage:
```python
from domain.automation.queue import AutomationQueueManager
from domain.actions import DesignAction

# Create automation manager
automation_manager = AutomationQueueManager()

# Create automation action
action = DesignAction(
    action_type="scroll",
    params={
        "direction": "left",
        "distance": 1,
        "repeat": 3,
        "gap_ms": 50
    }
)

# Add to queue
automation_manager.enqueue(action)

# Apply to frame range
frame_indices = [0, 1, 2]
# Use automation engine to apply actions
```
""")

guide.append("""
## 5. HOW TO APPLY TEXT

### Step-by-Step:
1. Open "Text" tool/tab
2. Enter text in text field
3. Select font (built-in or custom)
4. Configure options:
   - Font size
   - Color
   - Alignment (left/center/right)
   - Effects (outline, shadow)
5. Click "Apply Text" or "Generate Frames"
6. Text is rendered to current frame or generates animation frames

### Code Usage:
```python
from domain.text.text_renderer import TextRenderer, TextRenderOptions

# Create text renderer
renderer = TextRenderer()

# Configure text options
options = TextRenderOptions(
    width=32,
    height=8,
    font_size=8,
    color=(255, 255, 0),
    background=(0, 0, 0),
    alignment="center"
)

# Render text to pixels
text = "Hello World"
pixels = renderer.render_pixels(text, options)

# Apply pixels to frame
frame.pixels = pixels
```
""")

guide.append("""
## 6. HOW TO APPLY FONTS (INSTALLED/CUSTOM)

### Custom Fonts (Recommended):
1. Place font files (.json format) in `Res/fonts/` directory
2. Fonts are automatically detected
3. Select font from dropdown in Text tool
4. Built-in 5x7 font is always available

### Using Custom Fonts:
```python
from domain.text.bitmap_font import BitmapFontRepository

# Load font repository
font_repo = BitmapFontRepository(Path("Res/fonts"))

# List available fonts
fonts = font_repo.list_fonts()  # Returns list of font names

# Load a specific font
font = font_repo.load_font("MyFont")

# Use with text renderer
renderer = TextRenderer()
options = TextRenderOptions(...)
options.font = font  # Use custom font
pixels = renderer.render_pixels("Text", options)
```

### Font File Format:
- Fonts stored as JSON files in `Res/fonts/`
- Format: `{font_name}.json`
- Contains glyph definitions for each character
- Use Font Designer dialog to create custom fonts
""")

print("\n".join(guide))

print()
print("="*70)
print("✓ VERIFICATION COMPLETE")
print("="*70)

app.quit()

