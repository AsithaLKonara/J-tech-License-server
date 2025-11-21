# Information Architecture, States & Responsiveness

## Layout Overview

```
┌──────────────────────────────────────────────────────────────┐
│ Top Bar: Project name • Playback summary • Feedback button   │
├───────────────┬─────────────────────────────┬───────────────┤
│ Layers Panel  │ Canvas / Preview Surface     │ Inspector     │
│ (left)        │ (center)                     │ (right tabs)  │
│               │                              │ Frame/Layer   │
│ Timeline (bottom spanning width)             │ Automation    │
└───────────────┴─────────────────────────────┴───────────────┘
```

- Left: layer stack, automation quick actions.  
- Centre: canvas with overlays.  
- Bottom: timeline with zoom/playhead.  
- Right: inspector tabs.

## Responsive Behaviour

| Width | Behaviour |
| ----- | --------- |
| ≥1600 px | Full layout visible. |
| 1400–1600 px | Inspector collapses to icon tabs. |
| 1200–1400 px | Layer panel iconifies; timeline height reduced. |
| <1200 px | Warn user; stacked layout fallback. |

## State Diagrams

### Frame Selection

```
Idle → Hover → Selected → Edited → (Undo/Redo) → Selected
```

### Layer Selection

```
None → Selected → Edited → Hidden/Locked → Selected
```

### Preset Selection

```
List → Highlighted → (Apply | Preview | Delete)
```

### Focus Management

- Timeline focus indicates keyboard shortcuts apply to frames.  
- Canvas focus toggled via click; shows tool overlay.  
- Inspector focus shifts when editing properties; highlight active panel.

## Adaptive Rules

- Timeline density auto-adjusts; minimum clip width 24 px.  
- Canvas scaling provides fit-to-screen and 1:1 toggles.  
- Preset browser switches between grid/list depending on width.  
- History drawer optional above timeline, collapsible.

