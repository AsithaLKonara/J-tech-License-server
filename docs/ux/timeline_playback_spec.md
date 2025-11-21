# Timeline & Playback Component Specification

## Timeline

- Frame thumbnails (32×32, lazy-loaded).  
- Playhead with tooltip, draggable; snapping enabled (Alt to disable).  
- Markers with labels/colour coding (loop, automation).  
- Grouping for multi-frame selection and collapse.  
- Zoom 25%–400% via wheel+modifier; auto-scroll on play.  
- Loop range highlight; double-click to reset.  
- Min clip width 24 px; virtualization for >500 frames.

## Playback Controls

- Buttons: play/pause, prev/next frame, loop toggle, speed selector (0.25×–4×).  
- Display: FPS, current/total frame count.  
- Keyboard: Space (play/pause), arrows (step), Shift+arrows (jump 10), J/K/L optional, Ctrl+L loop toggle.  
- Scrubbing updates canvas after 16 ms debounce.

## Inspector Integration

- Frame selection updates inspector (duration, notes).  
- Layer inspector follows frame selection.  
- Automation overlays clickable to open detail drawer.

## Contextual Menus

- Frame: add, duplicate, delete, rename, set duration, add marker.  
- Group: collapse/expand, apply automation, export selection.  
- Playhead: set loop start/end, snap to marker.

## Automation Overlays

- Colour-coded bars atop timeline; hover shows tooltip.  
- Drag to adjust range; live preview updates.

## Interaction States

- Selected frame accent border; inspector highlight.  
- Hover scale 1.05× with frame number tooltip.  
- Locked frames show reduced opacity + lock icon.  
- Active playback animates playhead; loop region pulses.

## Events & Data

- Listens to `frame_added`, `frame_removed`, `frame_moved`, `queue_updated`.  
- Emits `frame_selected`, `frames_reordered`, `playback_toggled`, `loop_range_changed`.  
- Works with `HistoryManager` for undo.

## Edge Cases

- Large projects show mini-map overview.  
- Empty timeline displays onboarding.  
- If hardware preview unavailable, disable playback with tooltip.

