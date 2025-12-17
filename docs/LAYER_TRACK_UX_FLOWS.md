# Layer Track System - UX Flow Verification

## Overview

This document verifies the user experience flows for the new LayerTrack-based design system, ensuring all interactions work smoothly and intuitively.

## Core UX Flows

### 1. Creating and Managing Layers

**Flow:**
1. User opens Design Tools tab
2. User clicks "Add Layer" button in layer panel
3. New layer track is created spanning all frames
4. Layer appears in layer panel list
5. Layer is automatically available in all frames

**Verification:**
- ✅ Layer track created via `add_layer_track()`
- ✅ Layer appears in panel via `get_layers()` (backward compat)
- ✅ Layer exists in all frames automatically
- ✅ Active layer selection works

### 2. Painting to Layers

**Flow:**
1. User selects a layer in layer panel
2. User paints on canvas
3. Pixels are applied to selected layer track at current frame
4. Canvas shows composite of all visible layers
5. Frame pixels are synced from layer composite

**Verification:**
- ✅ Active layer tracked via `layer_panel.get_active_layer_index()`
- ✅ Painting calls `apply_pixel()` with correct layer index
- ✅ Canvas shows composite via `get_composite_pixels()`
- ✅ Frame sync happens after painting

### 3. Frame Navigation

**Flow:**
1. User selects different frame in timeline
2. Layer panel updates to show layers for that frame
3. Canvas loads composite for that frame
4. Active layer selection persists across frames
5. Layer properties (visibility, opacity) show frame-specific values

**Verification:**
- ✅ `set_frame_index()` called on layer panel
- ✅ Layer panel refreshes via `_refresh_layer_list()`
- ✅ Canvas loads via `_load_current_frame_into_canvas()`
- ✅ Active layer index preserved
- ✅ Properties show effective values (global or per-frame override)

### 4. Layer Visibility Control

**Flow:**
1. User toggles visibility checkbox in layer panel
2. If setting to global value → removes per-frame override
3. If setting to different value → sets per-frame override
4. Canvas updates to show/hide layer
5. Timeline eye icon updates

**Verification:**
- ✅ `set_layer_visible()` handles global vs per-frame
- ✅ Canvas refreshes via `_load_current_frame_into_canvas()`
- ✅ Timeline updates via `_refresh_timeline()`
- ✅ Eye icon reflects visibility state

### 5. Solo Mode

**Flow:**
1. User enables "Solo Mode" checkbox
2. All layers except active are hidden for current frame
3. Original visibility states are stored
4. User disables solo mode
5. Original visibility states are restored

**Verification:**
- ✅ Solo mode stores original visibility in widget (not on Layer objects)
- ✅ Only affects current frame (per-frame override)
- ✅ Original states restored correctly
- ✅ Canvas updates to show only active layer

### 6. Layer Reordering

**Flow:**
1. User drags layer in layer panel list
2. Layer track is moved to new position
3. Z-index is updated for all tracks
4. Rendering order changes
5. Canvas updates to show new composite

**Verification:**
- ✅ Drag-and-drop calls `move_layer_track()`
- ✅ Z-index updated for all tracks
- ✅ Active layer index updated correctly
- ✅ Canvas refreshes with new order

### 7. Adding Layers Across Frames

**Flow:**
1. User adds a new layer track
2. Layer track is created with blank frames for all existing frames
3. Layer appears in layer panel for all frames
4. User can paint on this layer in any frame

**Verification:**
- ✅ `add_layer_track()` creates frames for all existing frames
- ✅ Layer appears in `get_layers()` for all frames
- ✅ Painting works on new layer in any frame

### 8. Per-Frame Property Overrides

**Flow:**
1. User sets layer opacity to 50% in frame 0
2. Frame 0 shows layer at 50% opacity
3. Frame 1 shows layer at global opacity (100%)
4. User changes global opacity to 80%
5. Frame 0 still shows 50% (override), Frame 1 shows 80% (global)

**Verification:**
- ✅ Per-frame overrides stored in LayerFrame
- ✅ Global properties stored in LayerTrack
- ✅ `get_effective_opacity()` returns correct value
- ✅ Compositing uses effective values

### 9. Timeline Layer Tracks Display

**Flow:**
1. Timeline shows layer tracks as rows
2. Each row shows layer blocks across frames
3. User clicks on layer track row
4. Active layer changes in layer panel
5. User can toggle visibility via eye icon

**Verification:**
- ✅ Timeline builds tracks via `_build_timeline_layer_tracks()`
- ✅ Layer selection updates active layer
- ✅ Eye icon toggles visibility
- ✅ Timeline reflects layer state per frame

### 10. Locked Layer Protection

**Flow:**
1. User locks a layer
2. User tries to paint on locked layer
3. Warning dialog appears
4. Painting is prevented
5. User must unlock layer to paint

**Verification:**
- ✅ `is_layer_locked()` checks lock state
- ✅ Painting checks lock before applying pixels
- ✅ Warning dialog shown
- ✅ Lock state spans all frames (global property)

## Potential UX Issues and Solutions

### Issue 1: Visibility Toggle Behavior
**Problem:** User might expect visibility toggle to affect all frames, not just current frame.

**Solution:** Current behavior is correct - toggling sets per-frame override. To set global visibility, user would need to set it to match global value (which removes override). Consider adding "Set Global" button in future.

### Issue 2: Solo Mode Scope
**Problem:** Solo mode only affects current frame. User might expect it to affect all frames.

**Current Behavior:** Solo mode affects only current frame (per-frame override). This is intentional - allows viewing single layer in context of current frame.

**Future Enhancement:** Could add "Solo All Frames" option.

### Issue 3: Layer Panel Shows Per-Frame Layers
**Problem:** Layer panel shows layers for current frame, but layers span frames.

**Current Behavior:** Shows layers for current frame (via backward compat API). This is correct - shows what's visible/editable in current frame.

**Future Enhancement:** Could add indicator showing "Global" vs "Per-Frame" settings.

### Issue 4: Active Layer Persistence
**Current Behavior:** Active layer index persists across frames. This is correct - if editing "Background", stay on "Background" when switching frames.

## Integration Points Verified

1. ✅ **LayerPanelWidget ↔ LayerManager**
   - Uses backward compat API (`get_layers()`, `add_layer()`, etc.)
   - All operations work correctly

2. ✅ **Canvas ↔ LayerManager**
   - Uses `get_composite_pixels()` for display
   - Uses `apply_pixel()` for painting
   - Frame sync via `sync_frame_from_layers()`

3. ✅ **Timeline ↔ LayerManager**
   - Builds tracks via `get_layers()` per frame
   - Shows layer state per frame
   - Handles layer selection and visibility toggle

4. ✅ **DesignToolsTab ↔ All Components**
   - Coordinates frame changes
   - Updates layer panel on frame change
   - Handles active layer selection
   - Manages solo mode

## Test Scenarios

### Scenario 1: Multi-Layer Animation
1. Create "Background" layer (static blue)
2. Create "Foreground" layer (animated red)
3. Paint different content on foreground in each frame
4. Verify background stays same, foreground animates
5. ✅ **PASS** - Layers span frames correctly

### Scenario 2: Per-Frame Visibility
1. Create layer visible in frame 0
2. Hide layer in frame 1
3. Show layer in frame 2
4. Verify visibility per frame
5. ✅ **PASS** - Per-frame overrides work

### Scenario 3: Layer Reordering
1. Create 3 layers
2. Reorder via drag-and-drop
3. Verify z-order changes
4. Verify composite order changes
5. ✅ **PASS** - Reordering works

### Scenario 4: Solo Mode
1. Create 3 layers
2. Enable solo mode
3. Verify only active layer visible
4. Disable solo mode
5. Verify all layers restored
6. ✅ **PASS** - Solo mode works

## Conclusion

All core UX flows are verified and working correctly. The system provides:
- ✅ Smooth layer management
- ✅ Intuitive painting workflow
- ✅ Proper frame navigation
- ✅ Flexible visibility control
- ✅ Correct compositing
- ✅ Backward compatibility

The layer-based design system is fully functional and ready for use.
