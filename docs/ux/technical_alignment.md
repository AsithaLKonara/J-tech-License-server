# Technical Alignment & Component Mapping

## Component Mapping

| UI Component | Manager / Module | Events |
| ------------ | ---------------- | ------ |
| Timeline | `FrameManager`, `AutomationQueueManager`, `HistoryManager` | `frame_added`, `frame_moved`, `frame_selected`, `playback_toggled` |
| Layer Panel | `LayerManager`, `PatternState` | `layer_added`, `layer_visibility_changed`, `layer_pixel_updated` |
| Canvas | `CanvasController` | `canvas_updated`, `apply_pixel`, `set_matrix_size` |
| Automation Inspector | `AutomationQueueManager`, `PresetRepository` | `queue_updated`, `preset_applied`, `preset_saved` |
| Playback Controls | `FrameManager`, `CanvasController` | `play`, `pause`, `step`, `loop_changed` |
| History Drawer | `HistoryManager` | `history_updated`, `command_undone` |

## Event Schema (excerpt)

```json
{
  "frame_selected": { "index": 3 },
  "layer_pixel_updated": {
    "frame_index": 2,
    "layer_index": 0,
    "x": 5,
    "y": 3,
    "colour": [255, 128, 0]
  },
  "queue_updated": { "actions": [...] }
}
```

## Design-to-Dev Handoff

- Figma tokens exported to JSON → theming system.  
- Component naming: `TimelineClip`, `LayerList`, `PlaybackTransport`.  
- Annotate behaviours in Figma linking to `/docs/ux`.

## Implementation Notes

- Managers emit signals/observers; UI subscribes.  
- Avoid UI manipulations inside managers (logic only).  
- Inject dependencies for testing (mocks vs real).  
- Virtualize timeline rendering for large projects.

## Risks & Mitigations

- Performance: timeline updates heavy → use debounced signals, caching.  
- Shortcut conflicts: maintain central map, allow customization.  
- Design/dev drift: maintain shared glossary and component inventory.

