# Wireframes, Interaction Flow & Micro-interactions

## Key Screens

1. **Default Workspace** – canvas centred, timeline bottom, layers left, inspector right.  
2. **Playback Mode** – transport controls expanded, FPS indicator visible.  
3. **Automation Editor** – timeline overlays showing actions.  
4. **Feedback states** – toast notifications, confirmation dialogs.

## Interaction Flow

```
Open Project
  → Adjust matrix (optional)
  → Draw/edit frames ↔ timeline operations
  → Apply automation queue
  → Preview playback
  → Save preset / export
  → Iterate (undo/redo)
```

### Frame Duplication Example

1. Select frame (highlight + inspector update).  
2. Duplicate via shortcut or menu → new frame inserted.  
3. Playhead snaps; canvas ready for edits.  
4. Toast indicates action; undo reverses.

### Automation Application

1. Drag-select frames on timeline.  
2. Choose automation preset.  
3. Preview generates modal with temporary pattern.  
4. Apply commits; history entry created.

## Micro-interactions

- Hover: buttons lighten, timeline clips scale 1.05×.  
- Drag: insertion indicators, snapping cues.  
- Scrubbing: eased playhead, 16 ms debounce.  
- Shortcuts overlay accessible via `?`.  
- Undo/redo: 2 s toast with action name.  
- Progress indicator for long operations with cancel.

## Animation Principles

- Panel transitions: 150 ms ease-out.  
- Playhead movement syncs with FPS.  
- Layer visibility toggle fades over 120 ms.  
- Modals fade/scale 0.95 → 1.0 on entry.

## Error & Feedback

- Inline validation with tooltip details.  
- Confirmation for destructive actions with summary.  
- “Restore defaults” includes confirmation dialog.

## Prototyping Notes

- Use Figma variants for component states.  
- Interactive prototype should cover timeline scrubbing, layer toggles, automation preview.  
- Maintain FigJam flow charts linking personas to tasks.

